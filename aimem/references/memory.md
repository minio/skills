# Memory: where to keep agent context

aimem warms a curated set of well-known agent memory files into
its read cache on mount, so that recalling them from a fresh
sandbox is fast. The table below lists what aimem warms; it is not
a rule about where to save. Save startup context in the instruction
file your agent loads from the directory it opens as its project
(`CLAUDE.md` for Claude Code, `AGENTS.md` for Codex, Cursor and most
others). When that project directory is the mount root, the file is
also warmed. If the project directory is not on the mount, its
instruction file is lost with the sandbox: keep the notes on the
mount, and tell the next session where they are.

Paths are relative to the mount root. The exact set warmed depends on the `--agent` profile the mount was
started with (claude, codex, cursor, or auto — which warms all of
them). The per-vendor conventions below list the files each profile
recognises.

## Per-vendor conventions

| Vendor / family | Files                                   |
| --------------- | --------------------------------------- |
| Claude Code     | `CLAUDE.md`, `.claude/`                 |
| Codex / generic | `AGENTS.md`, `.agents/`, `MEMORY.md`    |
| Cursor          | `.cursorrules`, `.cursor/`, `AGENTS.md` |

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
  command finishes. Use `/tmp`, not the mount.
- **Generated artifacts you can rebuild from source.** They cost
  upload bandwidth and clutter the bucket.
