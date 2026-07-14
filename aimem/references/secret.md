# Secrets for this mount

aimem can hold secrets for a mount via envelope encryption backed by
MinKMS, exposed through the `aimem secret` subcommand. Whether secrets
are actually configured depends on how this mount was started — check
by running `aimem secret list`. If it succeeds, secrets are available;
if it errors that no MinKMS endpoint/scope is configured, this mount
has no secrets and `aimem secret` commands will fail until one is
attached.

When secrets are configured, use `aimem secret get NAME` to read a
secret and `aimem secret set NAME` to write one. Prefer piping the
value on stdin (`printf '%s' "$VALUE" | aimem secret set NAME`) or
`aimem secret set NAME --from-file <path>` over passing the value as a
positional argument — a positional value lands in shell history and
process listings (`ps`) in plaintext.

## How envelope encryption works here

When secrets are configured for this mount:

1. `aimem secret set NAME` calls MinKMS to generate a per-secret
   data encryption key (DEK), encrypts your value locally with
   AES-256-GCM, and stores the encrypted blob plus the wrapped
   DEK in the bucket under an internal prefix.
2. `aimem secret get NAME` fetches the blob, asks MinKMS to
   unwrap the DEK, decrypts locally, and prints the plaintext.

Plaintext secrets never touch S3, and AIMem never persists the
plaintext DEK after a single use. Only MinKMS can unwrap a
stored DEK.

## What to put here

- API keys, OAuth client secrets, database passwords.
- Per-environment credentials your code reads at startup.
- Anything you would not commit to `git`.

## What NOT to put here

- Multi-megabyte blobs. Secrets are for short strings.
  For big encrypted artifacts use SSE-KMS bucket encryption
  directly and store the file in the mount as normal.
- Public configuration. There is no benefit to encrypting a
  feature-flag value or a bucket name.
