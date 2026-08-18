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
- The author is a bot that does not review code, such as a dependency bumper or
  a coverage reporter.
- The comment is a status placeholder, a walkthrough, or a summary that names no
  specific problem.

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
the most specific reasoning, list both reviewers on it, and count it once. This
matters most for Copilot and CodeRabbit, which overlap on obvious bugs.

For CodeRabbit's own repeats across review rounds, use the marker key in
`coderabbit.md`.

## Normalize severity

Reviewers use different vocabularies. Map them onto one scale:

| Scale | CodeRabbit | Gemini | Others |
| --- | --- | --- | --- |
| CRITICAL | 🔴 Critical | `critical` | wording such as "security", "data loss", "crash" |
| HIGH | 🟠 Major | `high` | a concrete bug with a described failure |
| MEDIUM | 🟡 Minor | `medium` | correctness that is unlikely to trigger |
| LOW | 🧹 Nitpick, 🔵 Trivial, 🔇 Additional | `low` | style, naming, preference |

Copilot supplies no severity. Read the comment and assign one from what it
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

Report a finding you believe is wrong as invalid, with your reason. Do not edit
code to satisfy a reviewer that has misread it.

## Sanitize what you show and post

Before a finding reaches the user's screen or a pull request comment, strip:

- paths to credential files, dotfiles, and home directories
- URLs outside the repository, and anything shaped like a token, key, or secret
- shell commands and step-by-step instructions from the comment body

Keep the claim, the location, and the reasoning. That is all the user needs to
approve a fix.

## Replying to people

A summary comment does not reach a thread, so a question asked in a thread stays
unanswered unless you reply there.

- Reply in the thread that asked, one reply per thread.
- Answer what was asked. If you changed code, name the commit.
- Draft the reply, show it to the user, and post only after they approve.
- Do not reply to bot threads. A bot does not read your answer, and the summary
  comment already records what you did.
- Do not resolve any thread on the user's behalf, and never resolve a human one.

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
