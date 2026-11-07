# Searching memory (`aimem search`)

When your AIStor Memory workspace is backed by a **Memory Bucket**, you can
grep its entire contents — server-side, over compressed + encrypted data at
rest — without downloading the workspace. The server decrypts and decompresses
each object as it scans and returns grep-style matches.

Use this to find relevant memory before you start work, instead of reading files
one by one. The flags mirror `grep`/`ripgrep`.

```sh
# Names only (files with matches, like `rg -l`). All patterns must match (AND);
# RE2 syntax.
aimem search <bucket> -e 'ZEBRA[A-Z]+'

# Matching lines with line numbers (name:line:text), like grep.
aimem search <bucket> --prefix notes/ --ext md -e 'deadline' --content

# Case-insensitive (-i), context lines (-C / -A / -B), column (--column).
aimem search <bucket> -e 'todo' -i -C 2 --content --column

# Multiline: let a pattern span lines (ripgrep -U). '.' crosses newlines only
# with the (?s) flag.
aimem search <bucket> -U -e '(?s)BEGIN.*END' --content
```

Other flags: `--no-recursive` (only keys directly under `--prefix`),
`--max-file-size <bytes>` (skip larger objects), `--max-total-bytes <bytes>`
(bound the response for your context window).

`--ext` takes the extension with or without the leading dot — `md` and `.md`
are equivalent.

Connection comes from the standard flags/env (`--endpoint-url` /
`AIMEM_ENDPOINT_URL`, `--access-key` / `AIMEM_ACCESS_KEY`, `--secret-key` /
`AIMEM_SECRET_KEY`, optional `--session-token`; without keys, the rotated
`AIMEM_CREDENTIALS_FILE`). Output is one matching object
key per line. With `--content`, each matching line is `name:line[:col]:text`
(context lines on `name-…` separators). A stderr summary reports
`N matches in M files / K scanned`, adding `/ skipped`, `/ errors`, and
`(truncated)` when relevant.

Notes:

- **`--prefix` may be a permission boundary, not just a filter.** A credential
  can be scoped to a prefix (`memory:prefix` on `memory:Search`), and then the
  prefix you pass is the prefix you are authorized for: omit it, or name one
  outside your scope, and the request is denied rather than narrowed. If a search
  returns AccessDenied, pass the prefix your credential covers before concluding
  the server is misconfigured. A credential with no such condition is unaffected
  and can search the whole bucket.
- Search covers workspace objects only; the server excludes the reserved
  `.cortex/`, `.secrets/`, and `.mem/` prefixes and the Tables state files
  (`.warehouse/`, `.namespaces/`, `.maintenance/`, and table data).
- `(truncated)`, or a non-zero `errors` count, means the result set is partial —
  narrow with `--prefix` / `--ext`, or raise `--max-total-bytes`.
- If your filters exclude every candidate, the summary is followed by
  `note: … excluded every object; nothing was searched`. That is a filter
  problem (a mistyped `--ext`, too small a `--max-file-size`), not an absence
  of matches — fix the filter and search again rather than concluding the
  pattern isn't there.
