# What to look for

Work down this list in order. The early sections are where a missed problem
costs the most. You do not need to answer every question for every change:
ask the ones the diff makes relevant.

## Contents

0. Premise
1. Correctness
2. Data safety
3. Security
4. Concurrency
5. Error handling
6. Compatibility
7. Performance
8. Tests
9. What not to report

## 0. Premise

Check what the pull request and its linked issues claim before you check the
code that acts on the claim.

- **Reachable.** Which public call, command or normal background operation
  leads to the trigger, and with which permissions? A reproduction does not
  show that a trigger is reachable when only tests set it, when it calls an
  internal function directly, skips a lock the public path takes, injects a
  hook, edits stored data by hand, or needs several unrelated faults at the
  same time. Trace the public path to the trigger before you call it
  unreachable, and point at the line that allows or blocks it.
- **Known limits.** Does the repository document the case as unsupported or
  undefined? Then it is not a bug.
- **Already fixed.** Is the same fix on the base branch, in a merged pull
  request, or in another open one? Does an existing helper or a dependency
  already enforce the check the pull request adds? Does every `file:line` the description cites
  exist on the base branch, not only on this branch?
- **Impact.** Do the words and labels match the trace? "Data loss",
  "corruption", "takeover" and "escalation" need a path to that result. A
  change is a security fix only when a caller gains something their
  credentials did not already allow. An unreleased feature has no released
  users whose setups a change could break.
- **Proof.** Is there a test that fails without the fix, driven through the
  public behaviour, or a report from a real system with its version and logs?
  A complete trace from the public entry point shows the bug can happen, but
  the fix still needs a test that fails without it. A test that hand-builds
  the bad state can guard against a regression, but it does not show the bug
  can happen.
- **Proportion.** What is the smallest change that closes the reported case,
  and does this one close it? Ask why each new goroutine, retry loop, lock,
  cache, configuration option, wire or storage field and new dependency is
  needed when an existing mechanism could serve, and what it costs per
  request. Unrelated changes belong in their own pull request.

## 1. Correctness

- Does the code do what the description says? Read the intent you wrote in
  Step 3 next to each hunk.
- Boundaries: empty input, one element, the maximum, zero, negative values,
  off-by-one in loops and slices.
- Changed conditions: is an `if` inverted, a `&&` now an `||`, a case missing
  from a `switch`?
- Changed defaults: what happens to callers that relied on the old value?
- Copied code: was every name changed in the copy, or does one still point at
  the original?
- Rebuilt values: when code builds a new struct or record from an old one,
  does it carry over every field the readers need? Check each place it is
  rebuilt, including fallbacks.
- Derived state: when the change stores a count, flag, or summary next to the
  data it describes, does every path that later rewrites that data also clear or
  recompute it?
- Stated invariants: when a comment or doc says a value is "never" or "always"
  something, check every branch that computes it, including the rare ones.

## 2. Data safety

- Can this change lose, overwrite, or corrupt stored data, even under a crash
  or a partial write?
- Is a write made durable before it is acknowledged?
- Does a migration or format change still read data written by the old version?
- Is a delete scoped exactly as intended, or can it match more than it should?

## 3. Security

- Is every new entry point checked for authentication and authorisation?
- Is input from users, files, or the network validated before use: paths,
  sizes, lengths, identifiers?
- Path handling: can `..` or an absolute path escape the intended directory?
- Are secrets kept out of logs, errors, and responses?
- Is untrusted input passed to a shell, a query, or a template without escaping?

## 4. Concurrency

- Is shared state read or written without the lock that protects it elsewhere?
- Can two locks be taken in different orders on different paths?
- Does every goroutine, thread, or background task have a way to stop?
- Are channels or queues closed exactly once, by the sender?
- Does a context or cancellation signal reach the work it is meant to stop?

## 5. Error handling

- Is any returned error ignored, or replaced by a less useful one?
- On failure partway through, is earlier work rolled back or cleaned up?
- Are resources (files, connections, locks) released on every path, including errors?
- Does a retry loop have a limit and a back-off?

## 6. Compatibility

- Does the change alter a public API, a wire format, a configuration key, a
  command-line flag, or a metric name? Is that called out in the description?
- Will a mixed-version deployment (old and new running side by side) work?
- Are removed options or fields still accepted, or does the change break
  existing configuration?

## 7. Performance

Only raise performance when the changed code is on a hot path: per request,
per object, or in a loop over user-sized input.

- Is there new work inside a loop that could move outside it?
- New allocations, copies, or network calls per item?
- A new lock on a path that was lock-free?

Report a performance concern as a question unless you measured it.

## 8. Tests

- Does new or changed behaviour have a test that would fail without the change?
- Does a bug fix include a test that reproduces the bug?
- Do the tests check results, or only that the code did not crash?
- Did the change delete or weaken an existing test? Why?
- Docs and doc comments: does the change make an existing description of the
  behaviour wrong?

## 9. What not to report

- Formatting, import order, or other style rules the repository's linter enforces. Real bugs still count, even when a linter could catch them.
- Naming or structure you would have chosen differently, when the code is clear.
- Problems in code the pull request did not change, unless the change makes
  them worse. Mention those at most once, under "Outside this change".
- Hypothetical problems you cannot connect to a real input or call path. Hold
  the pull request to the same standard: a fix for a problem nobody can
  trigger is itself a finding.
