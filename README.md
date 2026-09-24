# Fleet

Personal coding-agent configuration shared by Pi and Codex, with per-harness skill routing.

## Layout

```text
agents/    Agent-specific configuration and code
prompts/   Composed agent instructions, skills, and reference files
scripts/   Idempotent installation and validation scripts
```

Runtime state remains in `~/.pi/agent` and `~/.codex`. Fleet installs managed configuration into those directories without managing credentials, sessions, caches, or Codex system skills. Codex's `config.toml` stays machine-local. Fleet updates the managed values from `agents/codex/config.base.toml` while preserving project trust and other local state.

## Bootstrap

`CPA_API_KEY` is machine-owned state. It must be exported by the machine environment or secret manager used to launch Pi or Codex. Fleet does not provision or store its value.

```bash
cd ~/fleet
mise run bootstrap
```

The bootstrap installs the pinned Pi and Codex versions from `mise.toml`, activates both tools in mise's global config so they work outside this repository, installs Pi's package dependencies, and installs both agents' configuration.

Agent instructions are assembled in the stable order declared by `prompts/agents/catalog.yaml`. Shared sections come from `prompts/agents/*.md`; the `harness` slot selects either `harness/pi.md` or `harness/codex.md`.

Useful commands:

```bash
mise run link
mise run check
mise run update
```

## Skill harnesses

Skills opt into each harness through an inline list in `SKILL.md` frontmatter metadata:

```yaml
metadata:
  harness: [pi, codex]
```

Supported values are `pi`, `codex`, and `opencode`. A skill without `metadata.harness` is not linked anywhere. `mise run link` adds selected links and removes obsolete Fleet-managed links, so metadata changes take effect on every run.

Codex profiles are available with:

```bash
codex --profile sol
codex --profile terra
codex --profile luna
codex --profile luna-fast
codex --profile muse13
codex --profile glm53f
```

Spawned Codex agents default to `ocg/muse-spark-1.3-contributor` at `max` reasoning. Every Codex profile is also available as a named subagent: `sol`, `terra`, `luna`, `luna-fast`, `muse13`, and `glm53f`.
