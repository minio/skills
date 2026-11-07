# Workspace semantics

This mount runs in **workspace mode**: full POSIX writes through a
local staged copy of each file. That means everything you'd expect on a
local filesystem works — random writes, `O_RDWR`, in-place edits,
seek-then-write, append, rename — but the implementation has a
small set of consequences worth understanding.

## What happens on open-for-write

1. aimem copies the current S3 object content into a local staging
   file, in the local store the mount was started with (`--local`).
2. Your reads and writes operate on that local file directly. They
   are fast, they support arbitrary seeks, and they never round-trip
   to the network.
3. On `fsync`, and again on close (the last `release` of the file
   descriptor), aimem uploads the local file back to the bucket. The
   S3 object becomes visible to other clients only after an upload
   completes.

This means:

- **Writes are not durable until `fsync` or close.** Each `write()`
  lands in the local staging file only. `fsync(2)` commits it to the
  bucket, so it is a real durability barrier — call it if you need the
  data safe before you are ready to close the descriptor. Otherwise the
  upload happens on close, and anything not yet committed is lost if the
  sandbox crashes mid-edit.
- **The local store needs free space.** If you're going to
  write a 10 GB file, ensure there are 10 GB free locally before
  opening. aimem warns at mount if free space is below the
  configured threshold.
- **Writers on one mount share the file; writers on different mounts
  do not.** Two processes on this mount that open the same path for
  writing both write into one staged copy, as they would on a local
  disk, and the upload holds both sets of writes. Two *mounts* (two
  sandboxes on the same bucket) each stage their own copy, and the
  last upload to complete replaces the object: the other mount's
  writes are lost without an error. Give each agent its own paths, or
  coordinate with `flock`, which arbitrates across mounts.

## Rename

`rename(2)` works across the mount, including across directories and
onto an existing name. aimem uses the server's `RenameObject`, which
moves the object in one atomic step, so no client ever sees both the
old and the new name. There is no copy-then-delete fallback: on a
backend without `RenameObject`, `rename(2)` fails rather than leaving
a half-finished move.

## Unlink, mkdir, rmdir

For real workspace paths, all work as expected. `rmdir` requires the
directory to be empty, matching POSIX. `mkdir` stores a zero-byte
`dir/` marker object, so an empty directory, and the mode you gave
it, survive a remount.

## Permissions, timestamps, and mmap

- **`chmod` / `chown` / `utimes` persist.** Mode bits, UID, GID, and
  atime/mtime take effect immediately for anything reading through the
  mount, and are stored on the object as user metadata, so they survive a
  remount and are visible to the next agent that mounts the bucket. An
  executable bit you set on a script stays set. If the file is already on
  the store, the change is pushed before the call returns; if the file
  has an open writer, the attributes travel with that file's next upload,
  so a crash before `fsync` or close loses them along with the unwritten
  data.
- **`mmap` works, indirectly.** The FUSE `mmap` op itself is not
  implemented, so the kernel falls back to `read`/`write`. Mapping a file,
  and `exec`ing a binary you just linked on the mount, both behave
  normally.
- **Rewriting a file other processes are reading is safe.** A reader
  with the file open is not broken by another process replacing it — no
  `ESTALE`, no `SIGBUS` in a mapped page. But unlike a local filesystem,
  an open descriptor is not pinned to the old contents: every reader of a
  path shares one view of it, so a reader — or a mapped page — may start
  returning the new bytes mid-read. There is no snapshot primitive, and
  re-opening the path is not one either. If you need bytes that cannot
  change under you, copy the file off the mount first and read the copy.

## What does NOT work

- **Hard links.** S3 has no hard links; `link(2)` returns `EPERM`.
  Tools with a `--link-dest` / hard-link mode need it disabled.
- **Holes / sparse files.** S3 objects are dense byte ranges. Writes
  to offsets past EOF are zero-filled, and `fallocate(2)` beyond EOF
  returns `EOPNOTSUPP` with no fallback. `posix_fallocate(3)` does have
  one: glibc emulates the allocation by writing zeros.
