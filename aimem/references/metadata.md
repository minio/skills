# Object metadata & tags (xattrs)

Every file on this mount is an object on the backing store, and that
object can carry **user metadata** (`x-amz-meta-*`) and **tags**. aimem
surfaces both as POSIX extended attributes (xattrs) so you can read them
with ordinary tools — no S3 API calls, no `aws s3api` needed.

## Where to look

| xattr namespace  | Holds                            | Example                  |
| ----------------- | --------------------------------- | ------------------------ |
| `user.s3.meta.*`  | S3 user metadata (`x-amz-meta-`) | `user.s3.meta.dataset`   |
| `user.s3.tags.*`  | S3 object tags                    | `user.s3.tags.env`       |

So an object with metadata `dataset=imagenet` and tag `env=prod` shows up
as `user.s3.meta.dataset` and `user.s3.tags.env`.

## How to read them

```sh
# All xattrs on a file (need -m - to include the user.* namespace):
getfattr -d -m - path/to/file

# One specific attribute:
getfattr -n user.s3.meta.dataset path/to/file
getfattr -n user.s3.tags.env     path/to/file
```

In code, use the normal xattr syscalls (`getxattr`/`listxattr`), e.g.
Python `os.getxattr(path, "user.s3.meta.dataset")` or
`os.listxattr(path)`.

## Why this is cheap

These attributes are **pre-warmed**: a directory listing (`ls`, `readdir`)
and a `stat`/lookup fetch metadata and tags inline, so reading them
afterward costs nothing extra — no per-file `HeadObject` or
`GetObjectTagging` round trip. For a metadata- or tag-heavy tree, run a
single `ls` over the directory, then `getfattr` each file for free.

The values reflect the object's state **as of the last listing/lookup**;
re-`ls` the directory to refresh after another writer changes an object.

## Important: `user.s3.meta.*` / `user.s3.tags.*` are effectively READ-ONLY

These two namespaces are a *reflection*, re-derived only from the
object's native S3 user metadata (`x-amz-meta-*`) and tags at the last
lookup/listing. The filesystem does not reject a
`setfattr -n user.s3.meta.foo -v bar path` — but it does **not** update
the object's native S3 user metadata or create an S3 tag either. The
value is instead stored under aimem's own private, base64-encoded
`xattr-` header and uploaded under that key on next close/sync; the
`user.s3.meta.*`/`user.s3.tags.*` reflection keeps coming from the
native headers, so your value never appears back under the name you set
it — even though the write itself did persist, just not where you'd look
for it. Treat both namespaces as observe-only.

To attach durable, natively-visible metadata to an object, set it where
the object is produced (the writer/uploader that PUTs it), not via
`setfattr` on the mount.
