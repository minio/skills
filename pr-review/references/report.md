# The review format

Keep the review short enough that the author reads all of it. Lead with the
verdict, then the findings that change it.

Write for a person, not a log:

- Use plain words and short sentences. Say "this can return another user's
  policy", not "cross-tenant cache key collision".
- Describe the code, not the author: "this loop skips the last item", not
  "you forgot the last item".
- Say what to do about each point.
- Follow the `docs` skill's plain-language rules when it is installed.

## Template

```markdown
**Verdict:** <Ready to merge | Merge after fixes | Needs rework> — <the one reason that decides it>

**What this changes:** <one or two sentences of intent, from Step 3>

### Blockers
1. **<file:line> — <what goes wrong, in a few words>**
   <When it happens: the input or call path.>
   <Evidence: the trace, or the test you ran and what it printed.>
   <Fix: the smallest change that solves it.>

### Should fix
1. ...

### Nits
- <file:line> — <one line each, at most three>

### Questions
- <file:line> — <something you could not settle>

**Not reviewed:** <skipped files, tests not run, or "nothing">
```

Leave out any section that has nothing in it. Mark each finding that is
**Likely** rather than verified, so the author knows how much weight to give it.

## Example

```markdown
**Verdict:** Merge after fixes — the new cache can return another user's entry.

**What this changes:** Adds an in-memory cache in front of the policy lookup to cut database reads.

### Blockers
1. **internal/policy/cache.go:58 — cache key ignores the account**
   The key is only the policy name, so two accounts with a policy called `read-only` share one entry.
   Evidence: traced `Lookup(account, name)` → `cache.Get(name)`; the account is never part of the key. A two-account test in the worktree returned account A's policy for account B.
   Fix: key on `account + "/" + name`.

### Should fix
1. **internal/policy/cache.go:91 — entries never expire**
   A changed policy keeps serving the old version until restart. The description says entries live for five minutes, but `ttl` is set and never read.
   Fix: check `ttl` in `Get`, or remove the claim from the description.

### Questions
- internal/policy/cache.go:30 — is the cache shared across server instances? If so, invalidation on update is also needed.

**Not reviewed:** the generated mocks in `internal/policy/mocks/`.
```

## Inline comments

Only after the user has seen the exact text and confirmed (SKILL.md, Step 7).
Post inline comments only for blockers and should-fix findings, one per
finding, on a line the diff changed (GitHub rejects others). Write a review
file and post it in one call so the author gets one notification:

```bash
cat > "${TMPDIR:-/tmp}/pr-review.json" <<'EOF'
{
  "commit_id": "<headRefOid from Step 2>",
  "event": "COMMENT",
  "body": "<the verdict and anything not tied to a line>",
  "comments": [
    {"path": "internal/policy/cache.go", "line": 58, "side": "RIGHT",
     "body": "Cache key ignores the account, so two accounts with the same policy name share an entry. Key on account + name."}
  ]
}
EOF
gh api "repos/{owner}/{repo}/pulls/<number>/reviews" --input "${TMPDIR:-/tmp}/pr-review.json"
```

Use `"event": "COMMENT"` unless the user explicitly asks you to approve or
request changes. A finding on an unchanged line goes in the review body.
