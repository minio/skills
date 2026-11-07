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
durable and survives sandbox restart once `close()` completes its
upload — see `references/workspace.md` for what is still at risk before that.
Files other agents wrote to the same bucket are visible here too.

## Find your mount

This skill is generic — it doesn't know which bucket you're on or where it's
mounted. Locate your AIStor Memory mount(s) yourself:

```sh
findmnt -n -o TARGET -S aimem   # AIStor Memory's mount source is "aimem"; prints the mountpoint path
                                # portable fallback: mount | sed -n 's/^aimem on \(.*\) type [^ ]* (.*)$/\1/p'
```

The path it reports is your workspace root; the reference docs below call it
`<mount-root>`. If nothing is reported, no AIStor Memory mount is present in this
environment and this skill does not apply.

## Working rules

These hold for every task on the mount. The references explain each in depth.

- **A write reaches the bucket when `close()` returns success.** Until then
  your bytes are only in a local staged copy, and losing the sandbox loses
  them. `fsync` flushes that local copy to disk but does not upload it: to
  checkpoint to the bucket, close the file and reopen it.
  If `close()` fails, assume the upload did not happen: keep your data and
  rewrite the whole file with the contents you intended, rather than
  replaying an append that may already have landed. Reading it back through
  the mount proves nothing, because the mount can still show the bytes it
  failed to upload.
- **Keep what the next session needs in the instruction file your agent
  loads at startup**, in the directory it opens as its project (often the
  mount root): `CLAUDE.md` for Claude Code, `AGENTS.md` for Codex, Cursor and
  most others. Your context window ends with the sandbox; the mount does not.
  If that project directory is not on the mount, its instruction file is lost
  with the sandbox: keep the notes on the mount, and tell whoever starts the
  next session where they are. A note in any other file is read only if
  something tells the next session to read it.
- **Put throwaway output in `/tmp`, not the mount.** Everything under the mount
  is uploaded to the bucket. Build output and downloaded archives there cost
  upload time and fill the bucket.
- **Work through the mount, not around it.** Writing the bucket directly (for
  example with `aws s3 cp`) bypasses the mount, which then keeps serving stale
  bytes and can overwrite your change on its next upload.
- **Keep secrets out of files.** Credentials reach the sandbox as environment
  variables. A key written to the mount is stored in the bucket for every
  later agent to read.

## Which reference to read

The references sit next to this file, under `references/`. Read one when the
task calls for it:

| When you need to…                                                                                          | Read                        |
| ---------------------------------------------------------------------------------------------------------- | --------------------------- |
| Find what is at the mount root, or the mount itself                                                        | `references/navigation.md`  |
| Know whether a write, rename, chmod or mmap behaves as on local disk, or share a file with another process | `references/workspace.md`   |
| Decide where to save notes, plans or context for a later session                                           | `references/memory.md`      |
| Read an object's S3 metadata or tags                                                                       | `references/metadata.md`    |
| Leave or read notes on a specific file for other agents                                                    | `references/annotations.md` |
| Find which files mention something, without reading them all                                               | `references/search.md`      |

Annotations are a tech preview and may be off on the server. If a note write
fails with "Operation not supported", don't retry it; keep the note in a memory
file instead.
