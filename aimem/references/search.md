# Searching cortex memory (`aimem search`)

When your AIMem workspace is backed by a **cortex** (Memory Bucket), you can
grep its entire contents — server-side, over compressed + encrypted data at
rest — without downloading the workspace. The server decrypts and decompresses
each object as it scans, so matches come back as plaintext.

Use this to find relevant memory before you start work, instead of reading files
one by one.

```sh
# All patterns must match (AND). RE2 syntax.
aimem search <cortex> --pattern 'ZEBRA[A-Z]+'

# Narrow by prefix and file type; print the matching content, not just names.
aimem search <cortex> --prefix notes/ --ext md --pattern 'deadline' --content

# Case-insensitive.
aimem search <cortex> -e 'todo' --ignore-case
```

Connection comes from the standard flags/env (`--endpoint-url` /
`AIMEM_ENDPOINT_URL`, `--access-key` / `AIMEM_ACCESS_KEY`, `--secret-key` /
`AIMEM_SECRET_KEY`, optional `--session-token`). The command prints one matching
object key per line (or `=== key ===` + content with `--content`), and a
`N matched / M scanned` summary on stderr.

Notes:
- Search covers workspace objects; the reserved `.cortex/`, `.secrets/`, and
  table (`.warehouse/`) prefixes are excluded.
- Results are bounded server-side; a `(truncated)` note means the byte cap was
  hit — narrow with `--prefix` / `--ext`.
