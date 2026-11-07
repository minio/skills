# Navigation

## Locate your mount

This skill ships generically, so it doesn't hard-code your bucket. Find the
mount point (all AIStor Memory mounts share the source `aimem`):

```sh
findmnt -n -o TARGET -S aimem       # prints the mount point path; source "aimem" identifies AIStor Memory
mount | sed -n 's/^aimem on \(.*\) type [^ ]* (.*)$/\1/p'  # same, portable fallback
```

These locate the mount only — they do not expose the bucket, region, or
endpoint (the filesystem source is always `aimem`, not the bucket name). The
mount point is the root of the configured prefix, not necessarily the bucket
itself: `ls <mount-root>` lists the top-level objects under that prefix, plus
the synthetic `.aimem/` namespace (e.g. `.aimem/annot/` for object
annotations). Every ordinary persistent file you read or write under the mount
maps to an object on the backing MinIO AIStor bucket. Entries under `.aimem/`
are agent-native surfaces, not ordinary objects — object annotations are stored
as native AIStor object metadata, not as object bytes.

## How to find things

- For source code, project files, and persistent artifacts: write them under
  the mount as you would on any POSIX filesystem.
- For ephemeral scratch (tmp build output, downloaded archives the user
  doesn't need to keep): write them outside the mount — a normal `/tmp` is
  the conventional place. aimem stages writes to a local directory, so keeping
  throwaway data off the mount avoids needless uploads.
- For agent memory (CLAUDE.md, AGENTS.md, MEMORY.md, project plans): write
  under the mount so they persist across sandbox restarts. See
  `references/memory.md` for the conventions aimem warms on mount.
- For secrets: never put plaintext credentials in mount files. Secrets are
  provisioned into the sandbox out-of-band (e.g. as environment variables),
  not stored on the mount.

## Object metadata & tags

Each file's S3 user metadata and tags are exposed as an effectively read-only
reflection under `user.s3.meta.*` / `user.s3.tags.*` xattrs, pre-warmed by
`ls`/`stat` so you can `getfattr -d -m - <file>` with no extra S3 calls. See
`references/metadata.md`.

## What you should NOT do

- Do not bypass the mount to write directly to the backing bucket (e.g. via
  `aws s3 cp` from inside the sandbox). The mount does not see writes made
  behind it, so a file you have open, or one the mount has cached, can go
  on showing the old bytes, and its next upload overwrites yours.
