# Memory: where to keep agent context

aimem warms a curated set of well-known agent memory files into
its read cache on mount, so that recalling them from a fresh
sandbox is fast. Write your project context to one of these
conventional paths and other agents on this mount will be able to
read it without you having to point at it.

The exact set warmed depends on the `--agent` profile the mount was
started with (claude, codex, cursor, or auto — which warms all of
them). The per-vendor conventions below list the files each profile
recognises.

## Per-vendor conventions

| Vendor / family | Files                                     |
| --------------- | ------------------------------------------ |
| Claude Code     | `CLAUDE.md` (root or per-dir), `.claude/`  |
| Codex / generic | `AGENTS.md`, `.agents/`, `MEMORY.md`       |
| Cursor          | `.cursorrules`, `.cursor/`, `AGENTS.md`    |

If you write to one of these paths, the next agent that mounts this
bucket will see it warmed automatically. If you invent a new path,
you may need to pass `--agent-manifest` at mount to teach aimem
about it.

## What to write here

- **Persistent project knowledge.** Architecture decisions, "what is
  this codebase," developer conventions, dead-ends to avoid. Things
  that would belong in a long-lived `CLAUDE.md`.
- **Cross-session memory.** Notes from previous sessions you want
  available next time. Goals in flight, relationships between PRs,
  open questions.
- **Coordination state when multiple agents share the bucket.**
  E.g. a `.agents/inbox/` queue, or task assignments.

## What NOT to write here

- **Secrets.** Never write plaintext API keys or credentials here. Secrets are
  provisioned into the sandbox out-of-band (e.g. as environment variables),
  not stored on the mount.
- **One-shot scratch.** Anything you only need until the current
  command finishes. Use `/tmp` or the staging dir, not the mount.
- **Generated artifacts you can rebuild from source.** They cost
  upload bandwidth and clutter the bucket.
