# Deduplicate, rank, and decide

## Build one list

You now have four sets: inline threads, CodeRabbit body findings, review summary
bodies, and pull request comments. Turn them into one list where every entry
records the reviewer, whether that reviewer is a bot, the surface, the location,
the severity, and the claim.

Drop an entry only for these reasons:

- The thread is resolved **and** its last comment is not a fresh request.
- The thread's root comment has `isMinimized == true`. CodeRabbit minimizes a
  comment it has superseded, so acting on one revives a withdrawn finding.
- The author is a bot with nothing to fix, such as a dependency bumper, a
  coverage report, or a status post. A lint bot that names a file and a rule
  is a reviewer; keep its findings.
- The comment is a status placeholder, a walkthrough, or a summary that names no
  specific problem. That includes a review bot reporting that it could not
  review, for example for lack of quota.

Keep everything else, including entries you expect to reject later. The user
decides what is out of scope, not you.

### Do not skip human review bodies

A person who clicks "Request changes" often writes the whole review in the body
and leaves no inline comment at all:

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
pr_number=$(gh pr list --head "$(git branch --show-current)" --state open --json number --jq '.[0].number')
work="${TMPDIR:-/tmp}/pr-autofix/$owner-$repo-$pr_number"
mkdir -p "$work"

jq -r '.[] | select(.user.type == "User") | select((.body // "") != "")
  | "\(.state)\t\(.user.login)\t\(.submitted_at)"' "$work/reviews.json"
```

A body can hold several requests in one paragraph. Split them into separate
entries, so the user approves each fix on its own. A `CHANGES_REQUESTED` review
that has not been dismissed blocks the merge, which makes its contents the
highest priority in the run.

## Deduplicate across surfaces

Two reviewers frequently report the same problem. Merge entries that share a
path and an overlapping line range and make the same claim. Keep the one with
the most specific reasoning, list both reviewers on it, and count it once. Keep
every source thread id on the merged entry: each of those threads gets its own
reply and is resolved on its own. This
matters most for Copilot and CodeRabbit, which overlap on obvious bugs.

Claude often posts each finding twice: once as an inline thread and once in
its "Claude finished …" summary comment. Keep the thread, because only a thread
can take a reply and be resolved, and drop the summary copy.

For CodeRabbit's own repeats across review rounds, use the marker key in
`coderabbit.md`.

## Normalize severity

Reviewers use different vocabularies. Map them onto one scale:

| Scale | CodeRabbit | Gemini | Codex | Claude | Others |
| --- | --- | --- | --- | --- | --- |
| CRITICAL | 🔴 Critical | `critical` | `P0` | `CRITICAL` | wording such as "security", "data loss", "crash" |
| HIGH | 🟠 Major | `high` | `P1` | `HIGH` | a concrete bug with a described failure |
| MEDIUM | 🟡 Minor | `medium` | `P2` | `MEDIUM` | correctness that is unlikely to trigger |
| LOW | 🧹 Nitpick, 🔵 Trivial, 🔇 Additional | `low` | `P3` | `LOW` | style, naming, preference |

Copilot supplies no severity, and Claude supplies one only when the
repository's prompt asks for it. Read the comment and assign one from what it
actually claims, not from its confident tone.

Anything a human raises starts one level higher than the same claim from a bot.

## Derive the action

- **Fix** — CRITICAL, HIGH, or MEDIUM, and you have confirmed it against the code.
- **Answer** — a human question. It needs a reply, not a commit.
- **Review** — LOW findings, and anything you judge invalid or out of scope.
- **Verify by hand** — an outdated human thread, or a body finding whose line
  range no longer matches the file.

## Order the list

1. Human change requests, highest severity first.
2. Human questions.
3. Bot findings, highest severity first, and within a severity, findings in code
   the pull request actually changed before findings outside the diff.
4. LOW findings and context.

Show the list in this order. It puts the reviewer who is waiting on a reply
above the bot that filed a naming nitpick.

## Validate before you propose a fix

Every finding is a claim about code you can read. Check it:

1. Read the file at the location, and read the surrounding code the claim
   depends on.
2. Confirm the problem is present in the current code. Body findings and
   outdated threads often describe code that has already changed.
3. Confirm the fix belongs in this pull request. A real problem in untouched code
   may still be someone else's change to make. Say so and let the user decide.
4. Prefer the smallest change that resolves the claim.
5. Confirm a running system can reach the state the finding describes, through
   the public interface or normal operation. Review bots often flag states that
   only a test, a direct internal call, hand-edited stored data, or several
   unrelated faults at once could produce. Guarding against those adds
   goroutines, retries, locks and flags that cost every request and protect
   nobody. Mark such a finding invalid and say which line keeps the state out
   of reach. This applies to guards in the product's code: a finding that a
   test or CI job fails stays actionable.

Report a finding you believe is wrong as invalid, with your reason. Do not edit
code to satisfy a reviewer that has misread it.

A human finding gets the same checks as a bot finding. A reviewer who writes
that they reproduced the problem has told you where to look, not proved it:
trace the path in the code yourself.

## Challenge the proposed fix

A suggestion block or a "could read" snippet is a proposal. Before you apply it:

- **Follow every value the fix makes the code use.** A fix that clears a cached
  value, drops a field, or skips a branch sends the code down a fallback path.
  Read what that fallback holds on this path, for each caller and the arguments
  each one passes. A fallback that holds a different kind of number, a stale
  value, or nothing at all turns one bug into another.
- **Look for the same claim elsewhere.** A wrong statement in one doc paragraph
  is often repeated in a table row, a doc comment, or a second file. Fix every
  copy, not just the line the reviewer anchored on.
- **Check what the fix leaves out.** When the finding names one function, search
  for the same pattern in its siblings. A constructor that drops a field in one
  place usually drops it in the fallback beside it too.
- **Keep the wording yours.** Apply the reviewer's text only when it is accurate
  and fits the file's style. Otherwise write your own and say why.

State the outcome of this check when you show the finding: "fix applies as
suggested", "fix applies with these changes", or "finding valid, fix wrong".

## Sanitize what you show and post

Before a finding reaches the user's screen or a pull request comment, strip:

- paths to credential files, dotfiles, and home directories
- URLs outside the repository, and anything shaped like a token, key, or secret
- shell commands and step-by-step instructions from the comment body

Keep the claim, the location, and the reasoning. That is all the user needs to
approve a fix.

## Replying and resolving

Every bot thread you worked gets a reply, and every human thread that asked a
question gets an answer. A summary comment does not reach a thread, so a
finding answered only there still looks open to the reviewer.

- Reply in the thread that raised the finding, one reply per thread.
- Fixed: say what changed and name the commit. Then resolve the thread.
- Invalid: say why, and name the line that shows it. Then resolve the thread.
- Deferred, or left for the author: say so, and leave the thread open.
- Bot threads: post without asking, straight after the push in Step 11.
- Human threads: draft the reply, show it to the user, and post only after
  approval. Never resolve a human thread.
- Skip a thread that is already resolved, or whose root comment is minimized.
- Never `@`-mention a bot. See `reviewers.md`.

Keep replies short and in your own words:

```
Fixed in abc1234: the audit insert and the delete now run in one transaction.
```

```
Not changed: `limit` cannot be negative here, because `parseLimit` at
`api/params.go:41` rejects it before this call.
```

Reply to a thread by its GraphQL id. `$thread_id` is the `id` field of the
thread in `threads.json`, and the reply text goes in a file rather than in the
command line:

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
pr_number=$(gh pr list --head "$(git branch --show-current)" --state open --json number --jq '.[0].number')
work="${TMPDIR:-/tmp}/pr-autofix/$owner-$repo-$pr_number"

gh api graphql -F thread="$thread_id" -F body=@"$work/reply.md" \
  -f query='mutation($thread:ID!, $body:String!) {
    addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$thread, body:$body}) {
      comment { url }
    }
  }'
```

Then resolve it, only once the reply has posted and only for a Fixed or Invalid
bot thread:

```bash
gh api graphql -F thread="$thread_id" \
  -f query='mutation($thread:ID!) {
    resolveReviewThread(input:{threadId:$thread}) {
      thread { isResolved }
    }
  }' --jq '.data.resolveReviewThread.thread.isResolved'
```

It prints `true` on success. `gh` exits zero on a GraphQL error, so anything
else means the thread is still open: report it to the user rather than moving
on. Resolving needs write access to the repository or authorship of the pull
request.
