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
PROMPT_RE = re.compile(r"<details>\s*<summary>[^<]*Prompt for AI Agents[^<]*</summary>", re.IGNORECASE)
WRAPPER_RE = re.compile(r"</?(?:details|blockquote)[^>]*>")
SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.DOTALL)


def unquote(line):
    while True:
        stripped = QUOTE_RE.sub("", line, count=1)
        if stripped == line:
            return line
        line = stripped


def findings(body):
    stack = []
    item = None
    depth = 0

    def section():
        return next((label for label in reversed(stack) if SECTION_RE.search(label)), None)

    for raw in body.splitlines():
        line = unquote(raw)
        plain = []
        cursor = 0
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
        plain.append(line[cursor:])
        current = section()
        if not current:
            continue
        anchor = next((PATH_RE.match(label) for label in reversed(stack)
                       if PATH_RE.match(label)), None)
        start = ITEM_RE.match("".join(plain).strip())
        if start:
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
    if title:
        item["title"] = " ".join(title.group(1).split())
    else:
        first = next((line for line in body.splitlines() if line.strip()), "")
        item["title"] = " ".join(first.split())[:120] or None
    item["body"] = body
    item["reviewer_prompt"] = clean(split[1]) if len(split) > 1 else None
    item["marker"] = marker.group(1) if marker else None
    item["source"] = source
    return item


def main():
    payload = json.load(sys.stdin)
    if isinstance(payload, dict):
        payload = [payload]
    for entry in payload:
        actor = entry.get("user") or entry.get("author") or {}
        if "coderabbit" not in (actor.get("login") or "").lower():
            continue
        source = entry.get("html_url") or entry.get("url") or ""
        for item in findings(entry.get("body") or ""):
            print(json.dumps(finalize(item, source)))


if __name__ == "__main__":
    main()
