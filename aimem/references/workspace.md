# Workspace semantics

This mount runs in **workspace mode**: full POSIX writes via
copy-on-write staging. That means everything you'd expect on a
local filesystem works — random writes, `O_RDWR`, in-place edits,
seek-then-write, append, rename — but the implementation has a
small set of consequences worth understanding.

## What happens on open-for-write

1. aimem copies the current S3 object content into a local staging
   file, under the local staging directory the mount was configured with.
2. Your reads and writes operate on that local file directly. They
   are fast, they support arbitrary seeks, and they never round-trip
   to the network.
3. On close (the last `release` of the file descriptor), aimem
   uploads the local file back to the bucket. The S3 object becomes
   visible to other clients only after this upload completes.

This means:

- **Writes are not durable until close.** If the sandbox crashes
  mid-edit, the in-flight changes are lost. `fsync` flushes the
  staged file to local disk but does _not_ trigger an upload.
- **The staging directory needs free space.** If you're going to
  write a 10 GB file, ensure there are 10 GB free locally before
  opening. aimem warns at mount if free space is below the
  configured threshold.
- **Concurrent writers fight.** If two processes open the same path
  for writing, whichever closes last wins — close order isn't
  guaranteed to match open order — and the other's data is silently
  overwritten. This is this mount's staged-upload policy (the last
  `close()` is what gets uploaded), not a universal POSIX guarantee —
  worth re-stating here because the blast radius is the bucket.

## Rename

`rename(2)` works across the mount. On buckets that implement
server-side rename (e.g. S3 Express One Zone, MinIO AIStor)
aimem uses it directly. On general-purpose S3 buckets it falls
back to `CopyObject + DeleteObject`. Both paths preserve POSIX
semantics from inside the mount; external observers reading the
backing bucket directly may briefly see both source and destination.

## Unlink, mkdir, rmdir

For real workspace paths, all work as expected. `rmdir` requires the
directory to be empty, matching POSIX. There is no concept of a
separate "directory object" in S3, so `mkdir` is essentially free
until you put something inside it.

## What does NOT work

- **Hard links.** S3 has no hard links; `link(2)` returns `EPERM`.
- **Holes / sparse files.** S3 objects are dense byte ranges. Writes
  to offsets past EOF are zero-filled.
- **Permissions / chown / chmod beyond mount-time defaults.** UID,
  GID, mode bits are fixed at mount time. `chmod` and `chown`
  return success but do not persist anything.
