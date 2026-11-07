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
3. On close, aimem uploads the local file back to the bucket. The S3
   object becomes visible to other clients only after that upload
   completes. `fsync` flushes the local file to disk but does not
   upload it.

This means:

- **Writes are not durable until close.** Each `write()` lands in the
  local staging file only, and anything not yet uploaded is lost if the
  sandbox goes away mid-edit. `fsync(2)` flushes the local copy to disk
  but does not upload it. To checkpoint to the bucket, close the file and
  reopen it. Only a `close()` in the process that opened the file
  uploads and reports the result. A child's `close()` of a descriptor
  it inherited uploads nothing: the opener's later `close()` uploads the
  child's writes, and if the opener closed first, the upload runs in the
  background after the last descriptor closes and cannot report a
  failure. Open the file in the process that writes and closes it.
  One exception to the `fsync` rule: on an instruction file that carries
  the aimem preamble (`CLAUDE.md`, `AGENTS.md`, `.cursorrules`), `fsync`
  uploads what you have written so far, so an interrupted rewrite can
  leave a partial file in the bucket. If `close()` reports an error, assume the upload did not
  happen and rewrite the whole file with the contents you intended. Do
  not replay an append: the upload may have succeeded after all, and the
  append would land twice. If another process writes the same file,
  stop it first and include its changes in what you write, or your
  rewrite removes them. Reading the file back through the mount proves
  nothing: the mount can still show the bytes it failed to upload.
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
  writes are lost without an error. Give each agent its own paths. A
  `flock` shared across mounts does not make this safe: the other mount
  can still be working from the copy of the file it cached earlier.
  Annotation notes under `.aimem/annot/` are the exception on one mount:
  each writer has its own buffer and the last close wins, so give each
  writer its own note name.

## Rename

`rename(2)` works across the mount, including across directories and
onto an existing name. aimem uses the server's `RenameObject`, which
moves the object in one atomic step, so no client ever sees both the
old and the new name. One exception: when you rename onto a name that
a process on this mount has open, aimem first moves that file aside so
those readers keep their bytes, and another client can briefly find
the destination missing. Readers on other mounts get no such
protection and may read the replacement. There is no copy-then-delete
fallback: on a backend without `RenameObject`, a rename that has to
move an object on the server fails rather than leaving a half-finished
move.

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
  so a crash before close loses them along with the unwritten data.
- **`mmap` works, indirectly.** The FUSE `mmap` op itself is not
  implemented, so the kernel falls back to `read`/`write`. Mapping a file,
  and `exec`ing a binary you just linked on the mount, both behave
  normally.
- **Rewriting a file other processes are reading is safe.** A reader
  with the file open is not broken by another process replacing it — no
  `ESTALE`, and no `SIGBUS` in a mapped page unless the new file is
  shorter: as on any filesystem, touching a mapped page past the new end
  of file raises `SIGBUS`. But unlike a local filesystem,
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
  one: glibc emulates the allocation by writing zeros. That emulation
  fails with `EBADF` on an `O_APPEND` descriptor, and a write made to the
  same range while it runs can be overwritten with zeros.
