#!/usr/bin/env python3
"""Tests for cr-sections.py: both review-body layouts CodeRabbit has used.

Run: python3 test_cr_sections.py
"""

import importlib.util
import io
import json
import pathlib
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cr_sections", HERE / "cr-sections.py")
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)

ICON = '<picture><img src="https://example.invalid/major-16.svg" width="16" height="16" alt=""></picture>'
BOT = '<picture><source media="(prefers-color-scheme: dark)" srcset="https://example.invalid/bot-dark.svg"><img src="https://example.invalid/bot.svg" alt=""></picture>'

# The layout from late 2026: a bold section heading in the callout, and one
# <details> card per finding.
CARDS = f"""<!-- coderabbit-ai-generated:v1 -->

> [!CAUTION]
> Some comments are outside the diff and can’t be posted inline due to GitHub limitations.
>
> **⚠️ Outside diff range comments (2)**
>
> <details>
> <summary><strong>{ICON} Major</strong> · Retire only the finished record. · <code>resume.go:121-150</code></summary><blockquote>
> <dl>
> <dd>
> <br>
>
> `internal/service/resume.go:121-150`
> **{ICON} Major** · **Data Integrity & Integration** · **Heavy lift**
>
> **Retire only the finished record.**
>
> The old pipeline can delete the record a newer publish wrote.
>
> <!-- ai-agent-prompt:start -->
>
> <details>
> <summary>{BOT} Prompt for AI Agents</summary>
> <dl>
> <dd>
>
> ```
> Update forgetPublish to retire only its own record.
> ```
>
> </dd>
> </dl>
> </details>
>
> <!-- cr-comment:v1:aaaaaaaaaaaaaaaaaaaaaaaa -->
>
> </dd>
> </dl>
> </blockquote></details>
> <details>
> <summary><strong>{ICON} Trivial</strong> · A truncated summary title… · <code>domains.py:107-114</code></summary><blockquote>
> <dl>
> <dd>
> <br>
>
> `scripts/ci/domains.py:107-114`
> **{ICON} Trivial** · **Functional Correctness** · **Low value**
>
> **A newly added test selects full coverage, not the ledger domain.**
>
> No change is required.
>
> </dd>
> </dl>
> </blockquote></details>

---

<details>
<summary>{BOT} Prompt to fix all issues</summary>

```
Outside diff comments:
Review comments at @resume.go: ...
```

</details>
"""

# The earlier layout: the section and each file are <summary> headings, and
# a finding starts with its line range.
LEGACY = """> [!CAUTION]
> Some comments are outside the diff and can’t be posted inline due to platform limitations.
>
> <details>
> <summary>⚠️ Outside diff range comments (1)</summary><blockquote>
>
> <details>
> <summary>api/projects/views.py (1)</summary><blockquote>
>
> `130-138`: _🗄️ Data Integrity & Integration_ | _🟠 Major_ | _⚡ Quick win_
>
> **Wrap the audit insert and delete in `transaction.atomic()`.**
>
> The two writes can land apart.
>
> <details>
> <summary>🤖 Prompt for AI Agents</summary>
>
> ```
> Wrap both writes in one transaction.
> ```
>
> </details>
>
> <!-- cr-comment:v1:bbbbbbbbbbbbbbbbbbbbbbbb -->
>
> </blockquote></details>
>
> </blockquote></details>
"""


def run(body):
    stdin = io.StringIO(json.dumps([{"user": {"login": "coderabbitai[bot]", "type": "Bot"}, "body": body, "html_url": "u"}]))
    stdout = io.StringIO()
    sys.stdin, sys.stdout = stdin, stdout
    try:
        cr.main()
    finally:
        sys.stdin, sys.stdout = sys.__stdin__, sys.__stdout__
    return [json.loads(line) for line in stdout.getvalue().splitlines()]


class CardLayout(unittest.TestCase):
    def setUp(self):
        self.found = run(CARDS)

    def test_every_card_is_a_finding(self):
        self.assertEqual(2, len(self.found), self.found)

    def test_fields_come_from_the_card(self):
        first = self.found[0]
        self.assertEqual("⚠️ Outside diff range comments (2)", first["section"])
        self.assertEqual("internal/service/resume.go", first["path"], "the full path, not the summary's short one")
        self.assertEqual("121-150", first["lines"])
        self.assertEqual("Major", first["severity"])
        self.assertEqual("Data Integrity & Integration", first["category"])
        self.assertEqual("Heavy lift", first["effort"])
        self.assertEqual("Retire only the finished record.", first["title"])
        self.assertEqual("cr-comment:v1:aaaaaaaaaaaaaaaaaaaaaaaa", first["marker"])

    def test_the_title_is_the_bodys_not_the_truncated_summarys(self):
        self.assertEqual("A newly added test selects full coverage, not the ledger domain.", self.found[1]["title"])

    def test_the_prompt_is_kept_apart_from_the_body(self):
        first = self.found[0]
        self.assertIn("retire only its own record", first["reviewer_prompt"])
        self.assertNotIn("Prompt for AI Agents", first["body"])
        self.assertNotIn("<dl>", first["body"])
        self.assertTrue(first["body"].startswith("**Retire only the finished record.**"), first["body"])


class LegacyLayout(unittest.TestCase):
    def test_a_finding_under_a_file_heading(self):
        found = run(LEGACY)
        self.assertEqual(1, len(found), found)
        item = found[0]
        self.assertEqual("api/projects/views.py", item["path"])
        self.assertEqual("130-138", item["lines"])
        self.assertEqual("🟠 Major", item["severity"])
        self.assertEqual("🗄️ Data Integrity & Integration", item["category"])
        self.assertEqual("Wrap the audit insert and delete in `transaction.atomic()`.", item["title"])
        self.assertIn("one transaction", item["reviewer_prompt"])


class NotCodeRabbit(unittest.TestCase):
    def test_another_authors_body_is_ignored(self):
        stdin = io.StringIO(json.dumps([{"user": {"login": "someone", "type": "User"}, "body": CARDS}]))
        stdout = io.StringIO()
        sys.stdin, sys.stdout = stdin, stdout
        try:
            cr.main()
        finally:
            sys.stdin, sys.stdout = sys.__stdin__, sys.__stdout__
        self.assertEqual("", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
