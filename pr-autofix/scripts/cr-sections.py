#!/usr/bin/env python3
"""Extract CodeRabbit findings that live in review bodies instead of inline threads.

Reads a JSON array of PR reviews or issue comments on stdin, as returned by
`gh api repos/OWNER/REPO/pulls/N/reviews --paginate`, and writes one JSON object
per finding to stdout.
"""

import json
import re
import sys

SECTION_RE = re.compile(r"comments\b.*\(\d+\)\s*$", re.IGNORECASE)
PATH_RE = re.compile(r"^(?P<path>\S+?)(?:-(?P<range>\d+-\d+))?\s+\(\d+\)$")
ITEM_RE = re.compile(r"^`?(?P<range>\d+(?:\s*[-–]\s*\d+)?(?:\s*,\s*\d+(?:\s*[-–]\s*\d+)?)*)`?:\s*(?P<meta>.*)$")
META_RE = re.compile(r"_([^_]+)_")
TITLE_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
HASH_RE = re.compile(r"<!--\s*(cr-comment:v1:[0-9a-f]+)\s*-->")
QUOTE_RE = re.compile(r"^\s{0,3}>\s?")
TAG_RE = re.compile(r"<details\b[^>]*>|</details>|<summary>(.*?)</summary>", re.DOTALL)
# The prompt's summary may start with an icon (<picture>, <img>), so anything up
# to the closing tag is allowed before its text.
PROMPT_RE = re.compile(r"<details>\s*<summary>(?:(?!</summary>).)*?Prompt for AI Agents.*?</summary>", re.IGNORECASE | re.DOTALL)
# Since late 2026 a section heading can be a bold line rather than a summary,
# for example `**⚠️ Outside diff range comments (2)**` inside the callout.
HEADING_RE = re.compile(r"^\*\*(?P<label>[^*]*comments\s*\(\d+\))\*\*\s*$", re.IGNORECASE)
# ... and each finding a card: a <details> whose summary reads
# `<severity> · <title> · <code>file:lines</code>`, followed by a line holding
# the full path, `path/to/file.go:121-150`, and a meta line
# `**<severity>** · **<category>** · **<effort>**`.
CARD_RE = re.compile(r"^(?P<severity>[^·]+?)\s*·\s*(?P<title>.+?)\s*·\s*(?P<loc>[^\s·]+:\d+(?:\s*[-–]\s*\d+)?)$")
LOCATION_RE = re.compile(r"^`(?P<path>[^`\s]+?):(?P<range>\d+(?:\s*[-–]\s*\d+)?)`$")
CARD_META_RE = re.compile(r"^\*\*[^*]+\*\*(?:\s*·\s*\*\*[^*]+\*\*)+$")
HTML_TAG_RE = re.compile(r"<[^>]+>")
WRAPPER_RE = re.compile(r"</?(?:details|blockquote|dl|dd)[^>]*>|<br\s*/?>")
SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.DOTALL)


def unquote(line):
    while True:
        stripped = QUOTE_RE.sub("", line, count=1)
        if stripped == line:
            return line
        line = stripped


def strip_html(text):
    return " ".join(HTML_TAG_RE.sub("", text).split())


def findings(body):
    stack = []
    item = None
    depth = 0
    heading = None

    def section():
        return next((label for label in reversed(stack) if SECTION_RE.search(label)), heading)

    for raw in body.splitlines():
        line = unquote(raw)
        bold = HEADING_RE.match(strip_html(line))
        if bold and not stack:
            if item:
                yield item
                item = None
            heading = bold.group("label").strip()
            continue
        plain = []
        cursor = 0
        card = None
        for tag in TAG_RE.finditer(line):
            plain.append(line[cursor:tag.start()])
            cursor = tag.end()
            text = tag.group(0)
            if text.startswith("</details"):
                if stack:
                    stack.pop()
                if item and len(stack) < depth:
                    yield item
                    item = None
            elif text.startswith("<details"):
                stack.append("")
            elif stack:
                stack[-1] = (tag.group(1) or "").strip()
                if "<code>" in stack[-1]:
                    card = CARD_RE.match(strip_html(stack[-1]))
        plain.append(line[cursor:])
        current = section()
        if not current:
            continue
        if card:
            if item:
                yield item
            path, _, lines = card.group("loc").rpartition(":")
            depth = len(stack)
            item = {
                "section": current,
                "path": path,
                "lines": lines,
                "category": None,
                "severity": card.group("severity").strip(),
                "effort": None,
                "card_title": card.group("title").strip(),
                "card_head": True,
                "body_lines": [],
            }
            continue
        text = "".join(plain).strip()
        if item and item.get("card_head"):
            # The card's own location and meta lines come before its body,
            # among wrapper tags that carry no text.
            if not WRAPPER_RE.sub("", text).strip():
                continue
            located = LOCATION_RE.match(text)
            if located:
                item["path"], item["lines"] = located.group("path"), located.group("range")
                continue
            item["card_head"] = False
            if CARD_META_RE.match(strip_html(text)):
                parts = [strip_html(part).strip("* ") for part in text.split("·")]
                item["category"] = parts[1] if len(parts) > 1 else None
                item["effort"] = parts[2] if len(parts) > 2 else None
                continue
        anchor = next((PATH_RE.match(label) for label in reversed(stack)
                       if PATH_RE.match(label)), None)
        start = ITEM_RE.match(text)
        if start and not (item and "card_title" in item):
            if item:
                yield item
            head = start.group("meta")
            meta = [part.strip() for part in META_RE.findall(head)]
            labelled = len(meta) > 1 and not META_RE.sub("", head).replace("|", "").strip()
            depth = len(stack)
            item = {
                "section": current,
                "path": anchor.group("path") if anchor else None,
                "lines": start.group("range").strip() or (anchor.group("range") if anchor else None),
                "category": meta[0] if labelled else None,
                "severity": meta[1] if labelled else None,
                "effort": meta[2] if labelled and len(meta) > 2 else None,
                "body_lines": [] if labelled else [head],
            }
        elif item:
            item["body_lines"].append(line)
    if item:
        yield item


def clean(text):
    text = SUMMARY_RE.sub(r"\1", text)
    text = WRAPPER_RE.sub("", text)
    text = HASH_RE.sub("", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def finalize(item, source):
    joined = "\n".join(item.pop("body_lines"))
    marker = HASH_RE.search(joined)
    split = PROMPT_RE.split(joined, maxsplit=1)
    body = clean(split[0])
    title = TITLE_RE.search(body)
    card_title = item.pop("card_title", None)
    item.pop("card_head", None)
    if title:
        item["title"] = " ".join(title.group(1).split())
    elif card_title:
        item["title"] = card_title
    else:
        first = next((line for line in body.splitlines() if line.strip()), "")
        item["title"] = " ".join(first.split())[:120] or None
    item["body"] = body
    item["reviewer_prompt"] = clean(split[1]) if len(split) > 1 else None
    item["marker"] = marker.group(1) if marker else None
    item["source"] = source
    return item


def entries(stream):
    decoder = json.JSONDecoder()
    text = stream.read().strip()
    position = 0
    while position < len(text):
        payload, offset = decoder.raw_decode(text, position)
        position = offset
        while position < len(text) and text[position].isspace():
            position += 1
        yield from (payload if isinstance(payload, list) else [payload])


def is_coderabbit(entry):
    actor = entry.get("user") or entry.get("author") or {}
    kind = actor.get("type") or actor.get("__typename")
    return kind == "Bot" and "coderabbit" in (actor.get("login") or "").lower()


def main():
    for entry in entries(sys.stdin):
        if not is_coderabbit(entry):
            continue
        source = entry.get("html_url") or entry.get("url") or ""
        for item in findings(entry.get("body") or ""):
            print(json.dumps(finalize(item, source)))


if __name__ == "__main__":
    main()
