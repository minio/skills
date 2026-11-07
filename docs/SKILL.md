---
name: docs
description: Use when writing or editing documentation and prose in a repository — READMEs, guides, tutorials, API reference, release notes, changelogs, and doc comments, in Markdown, reStructuredText, AsciiDoc, or plain text. Documentation must conform to the ISO 24495-1 Plain Language standard. This skill states that rule, gives the standard's four governing principles (relevant, findable, understandable, usable), sets out the plan, write, evaluate, and revise process, and gives a self-check to run before you save.
license: Apache-2.0
metadata:
  maintainer: MinIO
  homepage: https://docs.min.io
---

# docs — write documentation in plain language

**Every piece of documentation you write or edit must conform to ISO 24495-1
Plain Language.** This is not a preference or a house style you can trade away.
If a sentence does not meet the standard, rewrite it before you save the file.
The rule covers new pages, edits to existing pages, and any prose you add to a
repository: READMEs, guides, tutorials, reference pages, release notes,
changelogs, and doc comments.

## Purpose

ISO 24495-1 is the first international standard for plain language. Its goal is to
help writers create documents that readers can find, understand, and use effectively.

### Definition of plain language

A document uses plain language when its wording, structure, and design enable the intended audience to:

- Find the information they need.
- Understand that information.
- Use the information to achieve their purpose.

## The four governing principles

1. Relevant – Include only information readers need, based on their goals and context.
2. Findable – Organize content so readers can quickly locate what they need.
3. Understandable – Use familiar words, clear sentences, and logical explanations.
4. Usable – Present information so readers can successfully act on it or make decisions.

The standard itself is a paid ISO document, so you will usually not have it.
This page carries what you need to apply it: the principles above, the patterns
below, and the self-check.

## Why the rule is strict

Readers of technical documentation skim. They arrive from a search result in
the middle of a task, many read English as a second language, and more of them
are now agents or translation tools. Each of them stops at the first sentence
they cannot parse. Plain writing is how a page still works for that reader.

## Patterns that meet the standard

- **Lead with the point.** The first sentence of a page or section says what
  the reader gets or must do. Background comes after.
- **One idea per sentence.** Aim for sentences under 25 words. Split a sentence
  that joins two ideas with "and" or a semicolon.
- **Name the actor.** Write "aimem uploads the file", not "the file is
  uploaded". Passive voice hides who does what.
- **Use verbs, not nouns made from verbs.** Write "configure", not "perform the
  configuration of".
- **Talk to the reader.** Use "you". Write each step as an instruction:
  "Run `make test`."
- **Put the condition first.** "If the bucket is versioned, run …" lets the
  reader skip a step that does not apply to them.
- **Choose the structure that fits the content.** Use a numbered list for steps
  in order, bullets for items in no order, and a table to compare options.
- **Write headings that name a task or answer a question.** "Mount a bucket"
  beats "Overview". A reader who skims the headings should find their place.
- **Keep one word for one thing.** Define a term on first use, then use the same
  term every time. Switching between "bucket", "store", and "backend" for one
  thing reads as three things.
- **Be concrete.** Give the number, the name, or the command. Cut "simply",
  "just", "easily", and "various": they tell the reader nothing.

### Before and after

Before:

> In order to facilitate the configuration of the mount, it should be noted
> that the specification of a local directory is required, which will be
> utilized for the purposes of staging and caching.

After:

> Pass a local directory with `--local`. aimem stages your writes there and
> caches reads in it.

The rewrite keeps every fact. It names the flag, says who does what, and drops
the words that carried no meaning.

## The process

Plain language is a loop, not a single pass:

1. **Plan.** Identify the reader, their task, and what they need. Decide what
   the page will not cover.
2. **Write.** Draft against the four principles above.
3. **Evaluate.** Read the draft as the reader. Check it against the four
   principles and the self-check below. Where you can, have a real reader use
   it, or run the instructions yourself.
4. **Revise.** Fix what the evaluation found, then evaluate again.

When you edit someone else's page, run the same loop on the part you touch. Do
not rewrite text that already meets the standard.

## Self-check before you save

Answer each question. Where the answer is no, revise.

- **Relevant.** Does every section help the reader finish their task? Have you
  cut what they do not need?
- **Findable.** Do the headings say what each section holds? Can a reader who
  skims land in the right place?
- **Understandable.** Are the sentences short and active? Is each technical
  term defined the first time you use it?
- **Usable.** Are the steps in the order the reader performs them? Can the
  reader act on the page without guessing?

## What plain language is not

- **It is not simplified content.** You keep the full technical meaning. You
  remove the difficulty the reader gains nothing from.
- **It is not a ban on technical terms.** Storage docs need words like
  "erasure coding" and "idempotent". Define them once and reuse them.
- **It is not shorter at the cost of accuracy.** Accuracy wins. If the plain
  wording would be wrong, write the precise wording and then explain it.
- **It is not informality.** Plain writing can be formal. It cannot be vague.
