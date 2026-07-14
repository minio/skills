---
name: aimem
description: Use when working inside an AIMem workspace — an agent-native FUSE filesystem backed by MinIO AIStor, where reads and writes are ordinary POSIX operations against a remote bucket. Covers how to locate your mount, workspace durability semantics, where to keep agent memory, how to read object metadata, and how to use secrets.
license: Apache-2.0
compatibility: Requires a mounted AIMem (MinIO AIStor) FUSE workspace; uses findmnt and the aimem CLI.
metadata:
  maintainer: MinIO
  homepage: https://docs.min.io/aimem
---

# aimem workspace

You are (or may be) operating inside an **AIMem** mount: a FUSE filesystem
that backs every read and write to a remote MinIO AIStor bucket. A write is
durable and survives sandbox restart once `fsync()` or `close()` completes its
upload — see `references/workspace.md` for what is still at risk before that.
Files other agents wrote to the same bucket are visible here too.

## Find your mount

This skill is generic — it doesn't know which bucket you're on or where it's
mounted. Locate your AIMem mount(s) yourself:

```sh
findmnt -S aimem             # AIMem's mount source is "aimem"; prints the mountpoint
                             # portable fallback: mount | grep -E '^aimem on '
```

The path it reports is your workspace root; the reference docs below call it
`<mount-root>`. If nothing is reported, no AIMem mount is present in this
environment and this skill does not apply.

## Reference docs

Read these (co-located with this file, under `references/`) on demand:

- **`references/navigation.md`** — how to identify the bucket/region/endpoint
  of your mount, and the conventional layout of files at the root.
- **`references/workspace.md`** — POSIX semantics: copy-on-write staging,
  close/fsync durability, rename, and what doesn't work.
- **`references/memory.md`** — where to put long-lived agent context
  (CLAUDE.md, AGENTS.md, MEMORY.md) so it survives sandbox restart.
- **`references/metadata.md`** — how to read an object's S3 user metadata and
  tags as xattrs, pre-warmed by `ls`.
- **`references/annotations.md`** — how to attach durable, named notes to any
  object (read before you edit, write after you reason) via
  `.aimem/annot/<path>/@<name>`.
- **`references/secret.md`** — how to read and write secrets via
  `aimem secret` when the mount has secrets configured.
