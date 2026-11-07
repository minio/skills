---
name: aimem
description: Use when working inside an AIStor Memory workspace — an agent-native FUSE filesystem backed by MinIO AIStor, where reads and writes are ordinary POSIX operations against a remote bucket that outlives the sandbox. Use it whenever `findmnt -S aimem` reports a mount, the working tree has a `.aimem/` directory, or the task mentions AIStor Memory, a Memory Bucket, or keeping agent memory across sessions. Covers locating the mount, when a write is durable, where to keep long-lived agent memory, reading object metadata, annotating objects, and searching the bucket server-side with `aimem search`.
license: Apache-2.0
compatibility: Requires a mounted AIStor Memory FUSE workspace; uses findmnt and the aimem CLI.
metadata:
  maintainer: MinIO
  homepage: https://docs.min.io/aimem
---

# aimem workspace

You are (or may be) operating inside an **AIStor Memory** mount: a FUSE filesystem
that backs every read and write to a remote MinIO AIStor bucket. A write is
durable and survives sandbox restart once `fsync()` or `close()` completes its
upload — see `references/workspace.md` for what is still at risk before that.
Files other agents wrote to the same bucket are visible here too.

## Find your mount

This skill is generic — it doesn't know which bucket you're on or where it's
mounted. Locate your AIStor Memory mount(s) yourself:

```sh
findmnt -n -o TARGET -S aimem   # AIStor Memory's mount source is "aimem"; prints the mountpoint path
                                # portable fallback: mount | awk '$1=="aimem"{print $3}'
```

The path it reports is your workspace root; the reference docs below call it
`<mount-root>`. If nothing is reported, no AIStor Memory mount is present in this
environment and this skill does not apply.

## Reference docs

Read these (co-located with this file, under `references/`) on demand:

- **`references/navigation.md`** — how to locate your mount and the
  conventional layout of files at its root.
- **`references/workspace.md`** — POSIX semantics: staged writes,
  close/fsync durability, shared writers, rename, and what doesn't work.
- **`references/memory.md`** — where to put long-lived agent context
  (CLAUDE.md, AGENTS.md, MEMORY.md) so it survives sandbox restart.
- **`references/metadata.md`** — how to read an object's S3 user metadata and
  tags as xattrs, pre-warmed by `ls`.
- **`references/annotations.md`** — how to attach durable, named notes to any
  object (read before you edit, write after you reason) via
  `.aimem/annot/<path>/@<name>`. They may be switched off on the server; a
  note write then fails with "Operation not supported". Do not retry it; keep
  what you need in a memory file instead.
- **`references/search.md`** — how to grep the bucket server-side with
  `aimem search`, within whatever prefix your credential is scoped to (regex
  over compressed+encrypted data at rest).
