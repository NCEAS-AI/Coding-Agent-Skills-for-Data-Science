# Updating a skill, or adding one

## How a skill is laid out

Each skill is a folder under `skills/`, in the open [Agent Skills](https://agentskills.io/specification)
format, so it loads in every tool that reads skills:

```
skills/<name>/
├── SKILL.md        # what the agent reads: frontmatter (name, description, ...) + instructions
├── README.md       # for people: what it does, install, setup, requirements, version history
├── references/     # longer guides the agent reads when SKILL.md points to them
├── scripts/        # code the agent runs; each file starts with why it exists and how to use it
├── assets/         # templates, logos, other files used in the output
└── examples/       # real worked examples (public data only), with a README saying what they read
```

What makes a skill work well, learned from building `wri-html-pages`:

- **The description decides when the skill is used.** Say what it does and every way a user might ask
  for it; agents tend to under-use skills, so be generous with trigger phrases (≤ 1024 characters, no
  angle brackets).
- **Keep `SKILL.md` short** (well under 500 lines): the workflow and the rules that apply every time.
  Move detail to `references/`, and say in `SKILL.md` when to read each one.
- **Explain why.** Each preference carries its reason (and who set it, when), so the agent can apply
  it sensibly to cases nobody wrote down.
- **Put repeatable work in scripts,** with checks that stop on known mistakes, rather than in prose the
  agent has to re-derive each time.
- **Real data only** in examples, and nothing private: this repo is public.
- **Personal settings outside the folder** (`~/.config/<name>/`), so updates never overwrite them.
- **Declare** `license`, `compatibility` (what it needs to run) and `metadata.version` in the frontmatter.

## Updating a skill (maintainers)

The maintainer's working copy of a skill is the installed folder they use every day (for
`wri-html-pages`: `~/.claude/skills/wri-html-pages`, its own git history with a tag per version). To
publish a new version here:

1. In the working copy: bump `metadata.version` in `SKILL.md`, add a line to the version history in
   `README.md`, commit, and tag it (`git tag v1.8.0`).
2. Rebuild and republish the reference pages from `examples/` if the look changed, and fix any links
   to them.
3. Here: `python3 tools/skills.py sync wri-html-pages` copies the working copy into `skills/`, checks it
   against the spec, and rebuilds `dist/wri-html-pages.skill`. It never copies `.git`, `__pycache__` or
   `.pyc` files.
4. Read the diff (`git diff --stat`, then the changes): this repo is public, so check that nothing
   private came along (paths to private data, PINs, tokens, unpublished results).
5. Commit with a message that says what a user will notice, push, and update the screenshots in
   `docs/img/` if the look changed.

## Adding a new skill

1. Build it as a working copy in your tool's skills folder and use it for real work until it is stable.
2. `python3 tools/skills.py sync <name> /path/to/working/copy`, which checks and packages it.
3. Add it to the table in `README.md` ("The skills") and to Phase 0 of `agent-setup/SETUP.md`, with its
   requirements in Phase 2 and its questions in Phase 3.
4. Bump the repo version in `CITATION.cff` and in the README's citation.

`python3 tools/skills.py check` validates every skill; run it before each commit.
