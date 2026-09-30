# Fleet

Personal coding-agent configuration shared by Pi, Codex, and Claude Code, with per-harness skill routing.

## Layout

```text
agents/    Agent-specific configuration and code
prompts/   Composed agent instructions, skills, and reference files
scripts/   Idempotent installation and validation scripts
```

Runtime state remains in `~/.pi/agent`, `~/.codex`, and `~/.claude`. Fleet installs managed configuration into those directories without managing credentials, sessions, caches, or Codex system skills. Codex's `config.toml` and Claude Code's `settings.json` stay machine-local. Fleet updates their managed values while preserving other local settings.

## Bootstrap

`CPA_API_KEY` is machine-owned state. It must be exported by the machine environment or secret manager used to launch Pi, Codex, or Claude Code. Fleet does not provision or store its value. Claude Code reads it through `apiKeyHelper` and uses CPA's Anthropic-compatible endpoint with `gpt-6.1-sol` as its default model. No Claude subscription is required.

```bash
cd ~/fleet
mise run bootstrap
```

The bootstrap installs the Pi, Codex, and Claude Code versions declared once in the `tools` task in `mise.toml`, activates them in mise's global config, installs Pi's package dependencies, and installs all three agents' configuration. `mise run update` uses the same tool versions.

Agent instructions are assembled in the stable order declared by `prompts/agents/catalog.yaml`. Shared sections come from `prompts/agents/*.md`; the `harness` slot selects the agent-specific instructions for Pi, Codex, or Claude Code.

Claude Code reads project `AGENTS.md` files directly. Fleet also installs a Claude plugin that lists skills from `.agents/skills/` at session start. Claude reads a matching `SKILL.md` when needed; these project skills are available to the agent but do not become slash commands. The plugin leaves project files untouched.

Fleet installs Claude subagents in `~/.claude/agents`: `reviewer` uses `gpt-6.1-sol` at low effort, while `explorer` and `worker` use `gpt-6-luna` at xhigh effort. Reviewer and explorer are read-only.

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
  harness: [pi, codex, claude]
```

Supported values are `pi`, `codex`, `claude`, and `opencode`. A skill without `metadata.harness` is not linked anywhere. `mise run link` adds selected links and removes obsolete Fleet-managed links, so metadata changes take effect on every run.

Wayfinder and its companion skills (`setup-matt-pocock-skills`, `domain-modeling`, `research`, `prototype`, `to-spec`, and `to-tickets`) are vendored from [mattpocock/skills](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60) at `d81f3a1`, with only Fleet's harness metadata added. Wayfinder uses Fleet's existing `grilling` skill. The upstream MIT license is in `prompts/skills/MATT-POCOCK-LICENSE`. After linking, run `/setup-matt-pocock-skills` in each repository where you want to use `/wayfinder`, `/to-spec`, or `/to-tickets`; it asks before writing repository-specific issue tracker and domain settings.

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
