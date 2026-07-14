# Connecting: aliases, credentials, TLS

Every remote command resolves its first path segment to an **alias**: a stored
`{URL, accessKey, secretKey, api, ...}`. There is no `s3://` scheme — the alias
name is the scheme.

## Discover before you create

```sh
mc alias list                 # all aliases; secret keys are redacted
mc alias list myminio         # one alias
mc alias list --json          # machine-readable
```

Env-defined aliases (below) also appear in `mc alias list`, tagged with source
`env`.

## Environment aliases — the agent default

`mc` reads any variable named `MC_HOST_<alias>` and exposes `<alias>` as if it
were configured. Nothing is written to disk, so this is the safest form for an
agent and for ephemeral/CI use:

```sh
export MC_HOST_myminio='https://ACCESS_KEY:SECRET_KEY@minio.example.net:9000'
mc ls myminio/
```

URL forms accepted in the value:

```
https://ACCESS_KEY:SECRET_KEY@HOST[:PORT]                    # long-term keys
https://ACCESS_KEY:SECRET_KEY:SESSION_TOKEN@HOST[:PORT]      # STS / temporary creds
https://HOST:PORT                                            # anonymous (public buckets)
```

The scheme (`http`/`https`) is part of the value. Special characters in keys
must be URL-encoded. To feed several aliases from a file, point
`MC_CONFIG_ENV_FILE` at a file of `MC_HOST_<alias>=…` lines.

## Persisted aliases

Only when the user wants the alias saved to `~/.mc/config.json`:

```sh
mc alias set myminio https://minio.example.net:9000 ACCESS_KEY SECRET_KEY
mc alias set mys3 https://s3.amazonaws.com ACCESS_KEY SECRET_KEY --api S3v4 --path off
mc alias remove myminio
```

Passing keys as arguments leaks them into shell history — prefer prompting
(omit the keys and `mc` asks) or piping them in. `mc alias set` verifies the
endpoint is reachable before saving; it fails fast on a bad URL or credentials.

## Config location

`~/.mc/config.json` by default (on Windows, `%USERPROFILE%\mc\`). Override the
whole directory with the global flag `--config-dir <path>` or `MC_CONFIG_DIR`.
Give each isolated agent run its own `--config-dir` to avoid clobbering a
user's real config.

## TLS and connectivity

- `--insecure` skips certificate verification (self-signed dev servers). Never
  make this the default; state clearly when it's needed.
- `--resolve HOST:PORT=IP` overrides DNS for one host (e.g. hitting a specific
  node behind a load balancer).
- `mc ready ALIAS` reports whether the cluster is ready to serve; `mc ping
  ALIAS` measures per-endpoint latency. Use these to validate a new alias.

## Other S3 providers

`mc` works against AWS S3 and other S3-compatible stores, not just MinIO.
Choose bucket addressing with `--path`:

- `--path off` → virtual-hosted / DNS-style (`bucket.host`) — required for AWS
  S3 and most managed providers.
- `--path on` → path-style (`host/bucket`) — typical for MinIO and localhost.
- `--path auto` (default) → let `mc` decide.

`mc admin` commands are MinIO/AIStor-specific and will not work against AWS S3.
