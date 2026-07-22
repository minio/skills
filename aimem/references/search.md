# Searching cortex memory (`aimem search`)

When your AIStor Memory workspace is backed by a **cortex** (Memory Bucket), you can
grep its entire contents — server-side, over compressed + encrypted data at
rest — without downloading the workspace. The server decrypts and decompresses
each object as it scans and returns grep-style matches.

Use this to find relevant memory before you start work, instead of reading files
one by one. The flags mirror `grep`/`ripgrep`.

```sh
# Names only (files with matches, like `rg -l`). All patterns must match (AND);
# RE2 syntax.
aimem search <cortex> -e 'ZEBRA[A-Z]+'

# Matching lines with line numbers (name:line:text), like grep.
aimem search <cortex> --prefix notes/ --ext md -e 'deadline' --content

# Case-insensitive (-i), context lines (-C / -A / -B), column (--column).
aimem search <cortex> -e 'todo' -i -C 2 --content --column

# Multiline: let a pattern span lines (ripgrep -U). '.' crosses newlines only
# with the (?s) flag.
aimem search <cortex> -U -e '(?s)BEGIN.*END' --content
```

Other flags: `--no-recursive` (only keys directly under `--prefix`),
`--max-file-size <bytes>` (skip larger objects), `--max-total-bytes <bytes>`
(bound the response for your context window).

Connection comes from the standard flags/env (`--endpoint-url` /
`AIMEM_ENDPOINT_URL`, `--access-key` / `AIMEM_ACCESS_KEY`, `--secret-key` /
`AIMEM_SECRET_KEY`, optional `--session-token`). Output is one matching object
key per line, or — with `--content` — `name:line[:col]:text` matching lines
(context lines on `name-…` separators). A stderr summary reports
`N matches in M files / K scanned`, adding `/ skipped`, `/ errors`, and
`(truncated)` when relevant.

Notes:

- Search covers workspace objects only; the server excludes the reserved
  `.cortex/`, `.secrets/`, and `.mem/` prefixes and the Tables state files
  (`.warehouse/`, `.namespaces/`, `.maintenance/`, and table data).
- `(truncated)`, or a non-zero `errors` count, means the result set is partial —
  narrow with `--prefix` / `--ext`, or raise `--max-total-bytes`.
