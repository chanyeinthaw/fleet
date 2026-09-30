# Fleet

Personal coding-agent configuration shared by Pi, Codex, and Claude Code, with per-harness skill routing.

## Layout

```text
agents/    Agent-specific configuration and code
prompts/   Composed agent instructions, skills, and reference files
scripts/   Idempotent installation and validation scripts
```

Runtime state remains in `~/.pi/agent`, `~/.codex`, and `~/.claude`. Fleet installs managed configuration into those directories without managing sessions, caches, or Codex system skills. Shared secrets live in a GPG-encrypted password store under `secrets/`. Codex's `config.toml` and Claude Code's `settings.json` stay machine-local. Fleet updates their managed values while preserving other local settings.

## Bootstrap

`CPA_API_KEY` must be exported by the machine environment or secret manager used to launch Pi, Codex, or Claude Code. Fleet does not provision this key. Claude Code reads it through `apiKeyHelper` and uses CPA's Anthropic-compatible endpoint with `gpt-6.1-sol` as its default model. No Claude subscription is required.

```bash
cd ~/fleet
mise run bootstrap
```

The bootstrap installs the Pi, Codex, Claude Code, and gopass versions declared once in the `tools` task in `mise.toml`, activates them in mise's global config, installs Pi's package dependencies, and installs all three agents' configuration. `mise run update` uses the same tool versions. gopass uses mise's Aqua backend to install upstream binaries for Linux and macOS, without Homebrew.

Agent instructions are assembled in the stable order declared by `prompts/agents/catalog.yaml`. Shared sections come from `prompts/agents/*.md`; the `harness` and `computers` slots select the matching instructions for Pi, Codex, or Claude Code. The computers section points to the current harness's global reference file and respects its config directory override.

Claude Code reads project `AGENTS.md` files directly. Fleet also installs a Claude plugin that lists skills from `.agents/skills/` at session start. Claude reads a matching `SKILL.md` when needed; these project skills are available to the agent but do not become slash commands. The plugin leaves project files untouched.

Fleet installs Claude subagents in `~/.claude/agents`: `reviewer` uses `gpt-6.1-sol` at low effort, while `explorer` and `worker` use `gpt-6-luna` at xhigh effort. Reviewer and explorer are read-only.

Useful commands:

```bash
mise run link
mise run check
mise run update
```

## Secrets

Fleet uses [gopass](https://www.gopass.pw/) to access GPG-encrypted secrets tracked in Git. `mise run bootstrap` and `mise run update` install gopass and configure its root store to this checkout's `secrets/` directory; `mise run tools` installs the CLIs and configures the store alone. GPG and Git must already be available on PATH. Make the private key matching `secrets/.gpg-id` available to your local GPG agent. Private keys stay outside Fleet.

After setup, gopass works from any directory:

```bash
gopass ls
gopass insert api/example
gopass insert --multiline jp-mirai/example-ssh-key
```

`gopass config mounts.path` shows the configured store. Running Fleet's tools task sets Fleet as the root store and disables gopass's automatic sync and push because Fleet manages Git. Other gopass settings and mounts are preserved.

Use secrets by piping them into the command that needs them. Avoid printing decrypted values into agent output:

```bash
gopass show --noparsing jp-mirai/jump-msb-stg.pem | ssh-add -
```

The imported SSH keys are `jp-mirai/jump-msb-dev.pem` and `jp-mirai/jump-msb-stg.pem`. Their source PEM files remain on Oxygen.

Only encrypted `.gpg` files and store configuration are eligible for tracking under `secrets/`. Secret names and GPG recipient identifiers are public metadata. Git retains previous encrypted versions; revoke or rotate credentials at their provider when necessary. Keep a recovery copy of your GPG private key outside Git.

Fleet's repository tracks the store directly. gopass uses its filesystem backend because `secrets/` has no `.git` directory, so secret changes are committed through Fleet's normal Git workflow. Do not initialize a nested repository or run `gopass setup` against this existing store. Existing pass-compatible `.gpg` files need no conversion.

## Skill harnesses

Skills opt into each harness through an inline list in `SKILL.md` frontmatter metadata:

```yaml
metadata:
  harness: [pi, codex, claude]
```

Supported values are `pi`, `codex`, `claude`, and `opencode`. A skill without `metadata.harness` is not linked anywhere. `mise run link` adds selected links and removes obsolete Fleet-managed links, so metadata changes take effect on every run.

Wayfinder and its companion skills (`setup-matt-pocock-skills`, `domain-modeling`, `research`, `prototype`, `to-spec`, and `to-tickets`) are vendored from [mattpocock/skills](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60) at `d81f3a1`, with only Fleet's harness metadata added. Wayfinder uses Fleet's existing `grilling` skill. The upstream MIT license is in `prompts/skills/MATT-POCOCK-LICENSE`. After linking, run `/setup-matt-pocock-skills` in each repository where you want to use `/wayfinder`, `/to-spec`, or `/to-tickets`; it asks before writing repository-specific issue tracker and domain settings.

Codex and Claude Code share three named subagent roles: `explorer` investigates code without editing, `reviewer` checks changes without editing, and `worker` implements scoped changes. Explorer and worker use Luna at `xhigh` reasoning; reviewer uses Sol at `low` reasoning.
