---
name: mc
description: Use when driving mc, the MinIO AIStor command-line client for S3-compatible object storage, from a shell — connecting to a server with an alias, listing/copying/moving/removing objects and buckets, or configuring versioning, replication, lifecycle, encryption, policies, events, cluster administration, and AIStor Tables. Covers how an agent should authenticate non-interactively, get machine-readable JSON-lines output, build ALIAS/BUCKET/PREFIX paths, discover any command's exact flags, and stay clear of the irreversible destructive operations.
license: Apache-2.0
compatibility: Requires the `mc` binary (MinIO AIStor client) on PATH and network access to at least one S3-compatible endpoint.
metadata:
  maintainer: MinIO
  homepage: https://docs.min.io
---

# mc — MinIO AIStor command-line client

`mc` is a single static binary that talks to any S3-compatible object store
(MinIO AIStor, MinIO, AWS S3, and others) and to the local filesystem. It has
two surfaces: **data-plane** commands that move and inspect objects and
buckets over the S3 API (`ls`, `cp`, `rm`, `mirror`, …), and **control-plane**
`mc admin` commands that manage an AIStor/MinIO server itself (users, config,
healing, replication, tiering). A separate `mc table` surface manages AIStor
Iceberg Tables.

This skill teaches the model — the parts an agent gets wrong or can't cheaply
discover. It does **not** reproduce every flag: for the exact, current flags of
any command, run `mc <command> --help` (and `mc <command> <subcommand> --help`).
That help is authoritative and version-matched; this skill is not.

## 1. An alias is the prerequisite — nothing works without one

Every remote operation targets an **alias**: a named endpoint + credentials.
First discover what already exists, then create one only if needed:

```sh
mc alias list                # what's configured (redacts secret keys)
mc alias list --json         # same, machine-readable
```

Two ways to provide an alias. Prefer the environment form for agents — it
persists nothing to disk and never mutates the user's config:

```sh
# Ephemeral, per-process — the agent's default. Alias name is the suffix.
export MC_HOST_myminio='https://ACCESS_KEY:SECRET_KEY@play.min.io'
mc ls myminio/                             # "myminio" now resolves

# Persisted to ~/.mc/config.json — only when the user wants it saved.
mc alias set myminio https://play.min.io ACCESS_KEY SECRET_KEY
```

Once set, the alias name is the first path segment (`myminio/bucket/key`).
Config lives in `~/.mc/config.json` (override with `--config-dir` or
`MC_CONFIG_DIR`). Full details, the token/STS URL form, TLS and other providers:
**`references/connect.md`**.

## 2. Get machine-readable output

- **`--json` emits JSON Lines (NDJSON), not a JSON array.** One JSON object per
  line — parse line by line (`while read`, `jq -c`, streaming), never
  `json.loads()` on the whole stream. Streaming commands (`ls`, `mirror`, `cp`)
  emit one line per item as it happens.
- Every object has a `"status"` field (`"success"` or `"error"`); on error the
  object carries the message and `mc` exits non-zero.
- `--quiet` suppresses progress bars/spinners; `--no-color` drops ANSI. Prefer
  `--json` for parsing and add `--quiet` for clean logs.
- `mc` returns exit code `0` on success, non-zero on failure — branch on the
  exit code, not on stdout text.

Details and per-command shapes: **`references/output.md`**.

## 3. Path grammar

A target is either a **local path** (`./data`, `/tmp/x`) or an
**alias-qualified S3 path**: `ALIAS/BUCKET/PREFIX/OBJECT`. The first segment is
an alias only if it matches a configured alias — otherwise `mc` treats the whole
token as a local path. So `mc cp file.txt myminio/bucket/` copies local→remote,
and `mc cp myminio/bucket/key ./` copies remote→local. There is no `s3://`
scheme; the alias replaces it.

## 4. Destructive operations — confirm before running

Some `mc` commands are **irreversible** and an agent must treat them as
requiring explicit user confirmation, never running them speculatively:

- `mc rm --recursive --force ALIAS/BUCKET/PREFIX` — bulk object deletion.
  `--force` is *required* to recurse; `--dangerous` (with no prefix) wipes a
  whole site. `--versions` deletes every version.
- `mc rb ALIAS/BUCKET` — removes a bucket and its contents; `--force` /
  `--dangerous` bypass guards.
- `mc mirror --remove …` — deletes destination objects absent from the source
  (makes destination match source, including deletions).
- `mc mirror --overwrite …` / `cp` onto existing keys — replaces object data.
- Config-clearing forms (`mc ilm rule remove --all --force`,
  `mc replicate rm --all --force`, `mc event remove`, `mc anonymous set none`).

Versioning does not save you unless it's enabled on the bucket. When in doubt,
show the user the exact command and the target, and wait. See the "irreversible"
callouts in each reference.

## 5. Command map — pick the right command, then read its `--help`

| Task | Commands |
| --- | --- |
| Connect / configure client | `alias`, `update`, `license`, `support` |
| Inspect objects & buckets | `ls`, `stat`, `head`, `tree`, `du`, `find`, `diff` |
| Move data | `cp`, `get`, `put`, `mv`, `mirror`, `pipe`, `cat`, `od` |
| Delete data | `rm`, `rb`, `undo` |
| Query & watch | `sql`, `watch`, `ping`, `ready` |
| Share / presign | `share` |
| Bucket configuration | `mb`, `version`, `tag`, `retention`, `legalhold`, `quota`, `policy`, `anonymous`, `cors`, `encrypt`, `event` |
| Lifecycle / replication / batch | `ilm`, `replicate`, `inventory`, `batch` |
| Cluster administration | `admin …`, `log`, `qos`, `kms`, `idp` |
| AIStor Iceberg Tables | `table …` |

`kms` and `idp` exist both top-level and under `admin` (`mc admin kms`,
`mc admin idp`); the top-level forms are shortcuts to the same server config —
prefer whichever a task's other steps already use. `log` streams/queries server
logs and `qos` manages quality-of-service (rate) rules — both AIStor-specific.

## Reference docs

Load these (co-located, under `references/`) on demand for the task at hand:

- **`references/connect.md`** — aliases in depth: `MC_HOST_` env forms (with
  session token / STS), `mc alias set/list/remove`, config file, TLS
  (`--insecure`), non-MinIO providers, path-vs-DNS bucket lookup.
- **`references/output.md`** — `--json` NDJSON parsing patterns, exit codes,
  non-interactive/scripting rules, `jq` recipes.
- **`references/objects.md`** — the data plane: `ls cp mv rm get put mirror find
  du tree stat head cat pipe od diff sql watch undo share`, with the exact
  destructive-flag semantics.
- **`references/buckets.md`** — bucket lifecycle & configuration: `mb rb version
  tag retention legalhold quota policy anonymous cors encrypt event`.
- **`references/data-management.md`** — `ilm` (tiering/expiry), `replicate`
  (bucket & site replication), `inventory`, `batch` jobs.
- **`references/admin.md`** — `mc admin` control plane: server info, users &
  policies, config, service/heal/scanner, decom/rebalance, KMS, tiers, SUBNET.
- **`references/tables.md`** — AIStor Iceberg Tables: warehouses, namespaces,
  tables, catalog, shares, replication, maintenance.
