# Fleet

Personal coding-agent configuration shared by Pi and Codex.

## Layout

```text
agents/    Agent-specific configuration and code
prompts/   Shared AGENTS.md, skills, and reference files
scripts/   Idempotent installation and validation scripts
```

Runtime state remains in `~/.pi/agent` and `~/.codex`. Fleet links managed configuration into those directories without linking credentials, sessions, caches, or Codex system skills.

## Bootstrap

`CPA_API_KEY` is machine-owned state. It must be exported by the machine environment or secret manager used to launch Pi or Codex. Fleet does not provision or store its value.

```bash
cd ~/fleet
mise run bootstrap
```

Useful commands:

```bash
mise run link
mise run check
mise run update
```

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
