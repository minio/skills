# Bucket lifecycle & configuration

Create/remove buckets and manage their per-bucket configuration. Each command
below has subcommands or actions — run `mc <cmd> --help` for the exact set.

## Create & remove

```sh
mc mb myminio/mybucket [--region us-east-1] [--with-versioning]   # make bucket
mc rb myminio/mybucket                                           # remove bucket
```

`mc rb` **deletes the bucket and everything in it — irreversible.** It prompts
by default; `--force` removes a non-empty bucket unattended, `--purge` clears
even undeletable content, and `--dangerous` targets the whole site. Confirm with
the user before running any of these.

## Versioning — `mc version`

```sh
mc version enable  myminio/mybucket     # turn on object versioning
mc version suspend myminio/mybucket
mc version info    myminio/mybucket
```

Versioning is what makes deletions/overwrites recoverable (and what `mc undo`
depends on). Enabling it early is the main safety net against destructive
object ops.

## Object tagging — `mc tag`

`set` / `list` / `remove` tags on a bucket or object. Tags drive lifecycle and
replication rules, so set them before configuring `ilm`/`replicate` filters.

## Retention & legal hold (WORM) — `mc retention`, `mc legalhold`

Object-lock governance. Requires a bucket created with object lock enabled.

```sh
mc retention set --default governance 30d myminio/mybucket   # bucket default lock
mc retention set compliance 1y myminio/mybucket/key          # per object
mc retention info myminio/mybucket/key
mc legalhold set|clear|info myminio/mybucket/key
```

`COMPLIANCE` mode cannot be shortened or removed even by root until it expires —
treat setting it as irreversible.

## Public/anonymous access — `mc anonymous` (a.k.a. `mc policy`)

Manages the bucket's anonymous access policy:

```sh
mc anonymous set download myminio/mybucket        # public read
mc anonymous set none     myminio/mybucket        # revoke public access
mc anonymous get          myminio/mybucket
mc anonymous set-json FILE myminio/mybucket        # full custom policy
```

Permissions: `none`, `download`, `upload`, `public`. `mc policy` is the older
name for the same feature. This controls *anonymous* access only — IAM
user/policy management is `mc admin policy` (see `references/admin.md`).

## Quota — `mc quota`

`set` / `info` / `clear` a hard capacity quota on a bucket (MinIO/AIStor).

## CORS — `mc cors`

`set FILE` / `get` / `remove` a bucket CORS configuration (XML).

## Encryption defaults — `mc encrypt`

Bucket-level default server-side encryption:

```sh
mc encrypt set sse-s3   myminio/mybucket             # SSE-S3
mc encrypt set sse-kms  my-key-id myminio/mybucket   # SSE-KMS with a key
mc encrypt info  myminio/mybucket
mc encrypt clear myminio/mybucket
```

Per-object encryption at transfer time uses the `--enc-s3` / `--enc-kms` /
`--enc-c` flags on `cp`/`mirror`/`get`/`put` instead.

## Event notifications — `mc event`

```sh
mc event add  myminio/mybucket arn:minio:sqs::PRIMARY:webhook --event put,delete
mc event list myminio/mybucket
mc event remove myminio/mybucket --force
```

The ARN target must already be configured on the server (via
`mc admin config`). To *observe* events ad hoc instead of wiring a target, use
`mc watch` (see `references/objects.md`).
