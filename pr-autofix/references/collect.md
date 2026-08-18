# Collect the feedback

Fetch each surface into a file. Later steps read the files. Comment text must
never travel through a shell argument, because a body can contain anything.

## Start every command block with the preamble

Shell variables do not survive from one command to the next, so each block below
starts with the same five lines. Copy them. They are cheap, and they make every
block runnable on its own:

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
pr_number=$(gh pr list --head "$(git branch --show-current)" --state open --json number --jq '.[0].number')
work="${TMPDIR:-/tmp}/pr-autofix/$owner-$repo-$pr_number"
mkdir -p "$work"
```

`$work` is derived from the pull request rather than from `mktemp`, so every
block in this run lands in the same directory and a second run reuses it.

## 1. Inline review threads

Threads carry the state that decides whether a comment still counts: resolved,
outdated, and the full reply chain. Only GraphQL exposes that state, and it
pages, so loop until `hasNextPage` is false.

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
pr_number=$(gh pr list --head "$(git branch --show-current)" --state open --json number --jq '.[0].number')
work="${TMPDIR:-/tmp}/pr-autofix/$owner-$repo-$pr_number"
mkdir -p "$work"
: > "$work/threads.jsonl"
rm -f "$work"/page-*.json
cursor=""
page=0

while :; do
  args=(-F owner="$owner" -F repo="$repo" -F pr="$pr_number")
  [ -n "$cursor" ] && args+=(-F cursor="$cursor")

  gh api graphql "${args[@]}" -f query='query($owner:String!, $repo:String!, $pr:Int!, $cursor:String) {
    repository(owner:$owner, name:$repo) {
      pullRequest(number:$pr) {
        title
        author { login }
        reviewThreads(first:50, after:$cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id
            isResolved
            isOutdated
            path
            line
            startLine
            comments(first:50) {
              nodes {
                databaseId
                url
                body
                path
                line
                startLine
                originalLine
                diffHunk
                isMinimized
                createdAt
                author { login __typename }
              }
            }
          }
        }
      }
    }
  }' > "$work/page-$page.json"

  if jq -e '.errors' "$work/page-$page.json" >/dev/null; then
    jq -r '.errors[].message' "$work/page-$page.json"
    break
  fi

  jq -c '.data.repository.pullRequest.reviewThreads.nodes[]' \
    "$work/page-$page.json" >> "$work/threads.jsonl"

  [ "$(jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.hasNextPage' \
        "$work/page-$page.json")" = "true" ] || break
  cursor=$(jq -r '.data.repository.pullRequest.reviewThreads.pageInfo.endCursor' \
    "$work/page-$page.json")
  page=$((page + 1))
done

jq -s . "$work/threads.jsonl" > "$work/threads.json"
```

Each page goes to a file and `jq` reads it from there. Do not hold a page in a
shell variable and pass it with `--argjson`: a pull request with many threads
exceeds the argument size limit, and the fetch fails part-way with
`Argument list too long`. Keeping the data in files also honours the rule that
comment text never becomes a command argument.

`gh` exits zero on a GraphQL error, so the loop checks for an `errors` key and
prints it. If anything is printed, stop the run and report it to the user. Without that check an unreachable pull request leaves an empty
`threads.json` and the run looks like a pull request with no feedback.

`comments(first:50)` fetches the whole chain on purpose. The first comment states
the issue; the **last** comment often withdraws it ("never mind, I misread") or
adds to it. Read the tail before you treat a thread as open.

## 2. Review summary bodies

Every CodeRabbit finding that could not be anchored to a changed line lives
here, so this file is not optional.

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
pr_number=$(gh pr list --head "$(git branch --show-current)" --state open --json number --jq '.[0].number')
work="${TMPDIR:-/tmp}/pr-autofix/$owner-$repo-$pr_number"
mkdir -p "$work"

gh api "repos/$owner/$repo/pulls/$pr_number/reviews" --paginate > "$work/reviews.json"
```

## 3. Pull request comments

Bot status posts and human remarks that are not tied to a line.

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
pr_number=$(gh pr list --head "$(git branch --show-current)" --state open --json number --jq '.[0].number')
work="${TMPDIR:-/tmp}/pr-autofix/$owner-$repo-$pr_number"
mkdir -p "$work"

gh api "repos/$owner/$repo/issues/$pr_number/comments" --paginate > "$work/comments.json"
```

`issues/N/comments` is the correct path for pull request comments.
`pulls/N/comments` returns inline review comments instead, which you already
have as threads.

## Detect a review in progress

Run both checks. They see different states, and neither alone is enough.

### Check A — pending check runs

A review bot that publishes a check run reports it as pending while it works.
This is the reliable signal, and it appears nowhere in any comment body.

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
pr_number=$(gh pr list --head "$(git branch --show-current)" --state open --json number --jq '.[0].number')
work="${TMPDIR:-/tmp}/pr-autofix/$owner-$repo-$pr_number"
mkdir -p "$work"

checks=$(gh pr checks "$pr_number" --json name,bucket,state 2>/dev/null || true)
pending=0
if [ -n "$checks" ]; then
  pending=$(jq '[.[]
    | select(.name | ascii_downcase | test("coderabbit|copilot|gemini|sourcery|qodo|greptile|bugbot|ellipsis|review"))
    | select(.bucket == "pending")] | length' <<<"$checks")
fi
```

`|| true` is required: `gh pr checks` exits non-zero when any check is failing.
Never pipe it into another command and then read `$?`, because that reports the
other command's status. A repository with no review check run yields `0`, which
correctly does not block.

### Check B — placeholder comments

Some reviewers post a placeholder comment instead of, or ahead of, a check run.
A plain text match is not enough, because at least one reviewer leaves a
permanent notice that reads like one: Gemini Code Assist's summary comment says
"I'm currently reviewing this pull request and will post my feedback shortly",
and it still says that long after the review has landed. Matching on the text
alone blocks that pull request forever.

Compare timestamps instead. A reviewer is in flight when its placeholder is
newer than the last review body it published:

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
pr_number=$(gh pr list --head "$(git branch --show-current)" --state open --json number --jq '.[0].number')
work="${TMPDIR:-/tmp}/pr-autofix/$owner-$repo-$pr_number"
mkdir -p "$work"

in_flight=$(jq -n \
  --slurpfile reviews "$work/reviews.json" \
  --slurpfile comments "$work/comments.json" '
  ($reviews[0]
   | map(select(.user.type == "Bot" and ((.body // "") != "")))
   | group_by(.user.login)
   | map({key: .[0].user.login, value: (map(.submitted_at) | max)})
   | from_entries) as $posted
  | $comments[0]
  | map(select(.user.type == "Bot")
        | select((.body // "") | test("come back again in a few minutes|is reviewing|review in progress|review queued"; "i"))
        | select(.updated_at > ($posted[.user.login] // "")))
  | length')
```

This also catches the case that matters most: a reviewer that already reviewed an
earlier commit and is now re-reviewing the one you just pushed. Its old findings
are still on the pull request, and they describe the wrong code.

If `pending` is above zero, or `in_flight` is above zero, stop and tell the user
to try again in a few minutes. Do not read findings while a review is running:
the set changes underneath you, so two queries seconds apart disagree, and the
user ends up approving fixes for code that has moved on.

## Clean up

Delete the directory when the run ends, using the same derivation. The guard on
the last line matters: it refuses to delete when any part of the path came back
empty, so a failed lookup cannot widen what `rm -rf` removes.

```bash
owner=$(gh repo view --json owner --jq '.owner.login')
repo=$(gh repo view --json name --jq '.name')
pr_number=$(gh pr list --head "$(git branch --show-current)" --state open --json number --jq '.[0].number')
work="${TMPDIR:-/tmp}/pr-autofix/$owner-$repo-$pr_number"
[ -n "$owner" ] && [ -n "$repo" ] && [ -n "$pr_number" ] && rm -rf "$work"
```
