# MinIO Agent Skills

Official [Agent Skills](https://agentskills.io) published by MinIO, for any
skills-compatible AI agent (Claude Code, Codex CLI, Cursor, Gemini CLI, GitHub
Copilot, and more).

A skill is a folder with a `SKILL.md` (name + description + instructions) and,
optionally, a `references/` directory the agent loads on demand. Agents discover
skills through progressive disclosure: the name/description are cheap to keep
resident, and the full instructions load only when a task matches.

This repository is the **public home for all MinIO skills** — install any of
them with one command, no MinIO source checkout required.

## Available skills

| Skill                | Install                            | What it does                                                                                     |
| -------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------ |
| [`aimem`](./aimem)   | `npx skills add minio/skills/aimem` | Work inside an [AIMem](https://docs.min.io/aimem) workspace — locate the mount, durability semantics, agent memory, object metadata/annotations, and secrets. |
| `mc` _(planned)_     | —                                  | Work with `mc`, the AIStor command-line client. Coming soon.                                     |

## Installing

These skills follow the open Agent Skills standard, so you can install them with
the [`skills` CLI](https://skills.sh):

```bash
# add a single skill to your agent's skill directory
npx skills add minio/skills/aimem

# discover what's here
npx skills find minio
```

Or install manually — copy a skill folder into your agent's skill directory:

```bash
# Claude Code
cp -r aimem ~/.claude/skills/aimem
# Codex CLI, Cursor, Gemini CLI, Copilot
cp -r aimem ~/.agents/skills/aimem
```

### When do I need to install manually?

AIMem installs the `aimem` skill into your home skill directories
**automatically on every mount**, so if your agent's reasoning runs *inside* the
sandbox where AIMem is mounted, you do not need this repo.

Install from here when your agent's reasoning runs **outside** the sandbox — for
example the OpenAI Agents SDK or other managed-agent harnesses, where the model
lives in a control plane and an in-sandbox install is invisible to it. Add the
skill host-side, alongside your own skills, before the run starts.

## Contributing a skill

Each top-level directory is one skill and must contain a spec-compliant
`SKILL.md`:

- `name` — lowercase, digits, hyphens; **must match the directory name**.
- `description` — what it does and when to use it (≤ 1024 chars).

See the [Agent Skills specification](https://agentskills.io/specification).
Validate locally with `skills-ref validate ./<skill>`.

## License

Apache-2.0 — see [LICENSE](./LICENSE).
