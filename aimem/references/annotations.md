# Object annotations — durable notes that live with the bytes

You can attach **named notes to any object** on this mount and read back
notes other agents (or you, in an earlier session) left behind. A note is
stored as an AIStor **object annotation** — it lives in the customer's own
store, right next to the object it describes, and travels with the data.
No separate memory database, no extra service: the reasoning you build up
about a file is co-located with that file.

aimem surfaces annotations as files under a synthetic directory that
mirrors the object's path:

```text
.aimem/annot/<object-path>/@<note-name>
```

So notes about `src/auth.rs` live in `.aimem/annot/src/auth.rs/` and a
note named `review` is the file `.aimem/annot/src/auth.rs/@review`. The
leading **`@`** marks it as an annotation (never a real sub-path of the
object), so annotations can never collide with actual keys.

## The habit: read before you edit, write after you reason

**Before** you start working on a file, check what notes prior agents left
on it:

```sh
# List the notes on this object:
ls .aimem/annot/src/auth.rs/
# Read all of them at once (@all is a read-only roll-up):
cat .aimem/annot/src/auth.rs/@all
# Or read one note by name:
cat .aimem/annot/src/auth.rs/@review
```

If there's a `@review`, `@owner`, `@gotcha`, or `@todo`, reading it first
can save you the investigation someone already did. (`ls` an object with
no notes is empty; `@all` returns "No such file" when there are none yet.)

**After** you have reasoned something worth keeping — a non-obvious
constraint, why a change was made, an owner, a follow-up — write it back
onto the object so the next agent inherits it:

```sh
echo 'auth() has no rate limiting; see ticket AUTH-42' \
    > .aimem/annot/src/auth.rs/@review
```

## Reading and writing

| Action                 | Command                                       |
| ---------------------- | --------------------------------------------- |
| List an object's notes | `ls .aimem/annot/<path>/`                     |
| See all notes at once  | `cat .aimem/annot/<path>/@all`                |
| Read one note          | `cat .aimem/annot/<path>/@<name>`             |
| Create / overwrite     | `echo '…' > .aimem/annot/<path>/@<name>`      |
| Append                 | `printf '…\n' >> .aimem/annot/<path>/@<name>` |
| Delete                 | `rm .aimem/annot/<path>/@<name>`              |

A write replaces the whole note; truncating it to empty (`: >`) deletes
it. All of this is plain POSIX — use `open`/`read`/`write` from any
language, no S3 API calls.

## You must know the object first — the namespace is not browsable

You can list a note set **only when you already know the object/file path**
you are working on:

```sh
ls .aimem/annot/src/auth.rs/     # OK — you know the object
```

You **cannot** enumerate the tree to discover which objects have notes:

```sh
ls .aimem/annot/                 # NOT allowed (Operation not supported)
ls .aimem/annot/src/             # a prefix, not an object — lists nothing
```

This is deliberate: `.aimem/annot/` mirrors the object keyspace, and
walking it would mean scanning the whole bucket. So annotation discovery is
always **per known object** — take the file you are about to touch and
`ls`/`cat @all` its directory. There is no "show me every annotated object"
listing. `@all` is read-only.

## Rules

- The **object must already exist** in the bucket. Annotations attach to a
  real object; you cannot annotate a path that has no object.
- Note **names** may use letters, digits, `_`, `.`, `-`; up to 512 bytes;
  not `aws…`/`s3…` (reserved) and not `all` (reserved for the `@all`
  roll-up view). An invalid name fails the create with `EINVAL`.
- A note **payload** is 1 byte to 1 MiB. Oversized writes fail with
  `EFBIG`; keep notes concise — they are reasoning, not blobs.
- Notes are per-object metadata, **not** the object's bytes: editing
  `@review` never changes `src/auth.rs` itself.

## Good notes to leave

- `@review` — what you checked and what you concluded.
- `@gotcha` — a non-obvious constraint or footgun in this file.
- `@owner` / `@contact` — who owns or last touched it.
- `@todo` — follow-up work you deferred.

Prefer a few well-named notes over one sprawling one, so the next agent
can `ls` and read only what it needs.

Annotations are one tool on this mount. For the full workspace orientation
and the rest of the skill, see `SKILL.md` and the sibling references
(`navigation.md`, `workspace.md`, `memory.md`, `metadata.md`).
