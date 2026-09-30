# Fleet

Personal development environment configuration shared across machines. Fleet manages coding-agent configuration, prompts, skills, and encrypted secrets, with dotfiles support planned.

## Layout

```text
agents/    Agent-specific configuration and code
prompts/   Composed agent instructions, skills, and reference files
scripts/   link/check entry points; agents/, secrets/, and services/ helpers
secrets/   GPG-encrypted credentials accessed with gopass
services/  Split Docker Compose definitions and fnox secret references
```

Runtime state remains in `~/.pi/agent`, `~/.codex`, and `~/.claude`. Fleet installs managed configuration into those directories without managing sessions, caches, or Codex system skills. Shared secrets live in a GPG-encrypted password store under `secrets/`. Codex's `config.toml` and Claude Code's `settings.json` stay machine-local. Fleet updates their managed values while preserving other local settings.

## Bootstrap

Pi, Codex, and Claude Code retrieve the CPA key through Fleet's `fleet-fnox` helper, including when launched by T3 Code. No `CPA_API_KEY` shell export is needed. Claude Code uses CPA's Anthropic-compatible endpoint with `gpt-6.1-sol` as its default model. No Claude subscription is required.

```bash
cd ~/fleet
mise run bootstrap
```

The bootstrap installs the Pi, Codex, Claude Code, and gopass versions declared once in the `tools` task in `mise.toml`, activates them in mise's global config, installs Pi's package dependencies, and installs all three agents' configuration. It also installs the locally pinned fnox tool. `mise run update` uses the same tool versions. gopass uses mise's Aqua backend to install upstream binaries for Linux and macOS, without Homebrew.

Agent instructions are assembled in the stable order declared by `prompts/agents/catalog.yaml`. Shared sections come from `prompts/agents/*.md`; the `harness` and `computers` slots select the matching instructions for Pi, Codex, or Claude Code. The computers section points to the current harness's global reference file and respects its config directory override.

Claude Code reads project `AGENTS.md` files directly. Fleet also installs a Claude plugin that lists skills from `.agents/skills/` at session start. Claude reads a matching `SKILL.md` when needed; these project skills are available to the agent but do not become slash commands. The plugin leaves project files untouched.

Fleet installs Claude subagents in `~/.claude/agents`: `reviewer` uses `gpt-6.1-sol` at low effort, `explorer` and `worker` use `gpt-6-luna` at xhigh effort, and `uiux` uses `ocg/glm-5.3-flash`. Reviewer and explorer are read-only. UI/UX audits inspect without editing; UI/UX implementation tasks can make scoped changes. CPA's `opencode-session` plugin v0.1.7 or newer derives OCG routing headers from Codex thread metadata and Claude Code session metadata; clients do not send a hardcoded session header.

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

### Secret cache

All configured agent and service secret reads use fnox's in-memory daemon cache through the root `fnox.toml`. To unlock GPG and warm every configured profile:

```bash
mise run secrets warm
```

Add more credentials to `fnox.toml`; the warm command discovers profiles automatically. The CPA key is stored at `agents/cpa1-api-key` in gopass and exposed as `CPA_API_KEY` in the `agents` profile.

Bootstrap and update install `~/.local/bin/fleet-fnox` and configure Pi, Codex, and Claude Code to retrieve the CPA key through it, including when launched by T3 Code. The launcher resolves Fleet's pinned fnox binary from any directory and supplies the gopass adapter, so no global fnox installation or shell export is needed.

Fnox runs a daemon for each profile, all with the same 365-day idle timeout that resets on requests. GPG's one-hour passphrase timeout is unchanged. Secrets stay in memory until the daemon stops, expires, or invalidates its cache after configuration or relevant environment changes. After reboot or a daemon restart, run `mise run secrets warm` again. Fleet writes no decrypted secret cache to disk.

Other arguments pass directly to fnox, for example:

```bash
mise run secrets -P agents daemon status
```

`mise run check` reports the agents profile’s daemon status without decrypting secrets. The launcher uses `/tmp` for fnox's temporary-directory fallback so terminal and service launches find the same socket on macOS. Screen lock does not clear the cache, and processes running as your user can retrieve cached secrets. Restart agent sessions after rotating their credentials, since agents may also cache them in memory.

Use secrets by piping them into the command that needs them. Avoid printing decrypted values into agent output:

```bash
gopass show --noparsing jp-mirai/jump-msb-stg.pem | ssh-add -
```

The imported SSH keys are `jp-mirai/jump-msb-dev.pem` and `jp-mirai/jump-msb-stg.pem`. Their source PEM files remain on Oxygen.

Only encrypted `.gpg` files and store configuration are eligible for tracking under `secrets/`. Secret names and GPG recipient identifiers are public metadata. Git retains previous encrypted versions; revoke or rotate credentials at their provider when necessary. Keep a recovery copy of your GPG private key outside Git.

Fleet's repository tracks the store directly. gopass uses its filesystem backend because `secrets/` has no `.git` directory, so secret changes are committed through Fleet's normal Git workflow. Do not initialize a nested repository or run `gopass setup` against this existing store. Existing pass-compatible `.gpg` files need no conversion.

## Services

Service operations are separate from agent installation. Bootstrap and update never start, stop, or restart containers. Docker with Compose support is required on the service host; fnox is pinned in Fleet's local mise tools.

```bash
mise run services:up
mise run services:down
mise run services:restart
```

Compose arguments can select a service, for example `mise run services:up -- cpa2`. Use `up` after changing configuration or images; `restart` restarts existing containers with their existing configuration. `down` preserves the bind-mounted data.

The root `services/compose.yaml` includes a separate file for each service. CPA1 listens on `127.0.0.1:8320`, CPA2 listens on `127.0.0.1:8321`, and PostgreSQL has no published port. `CPA1_PORT` overrides CPA1's port for staging. Runtime files live in `${XDG_DATA_HOME:-$HOME/.local/share}/fleet/services`, with `cpa1/`, `cpa2/`, and `postgres/` subdirectories. Set `FLEET_SERVICES_DATA_DIR` to override this location. Keep database dumps and other migration backups outside Git as well.

The root `fnox.toml` references GPG-encrypted gopass entries under `services/`. Agent and service launchers use the same `scripts/secrets/fnox` launcher and daemon settings. Warm the cache with `mise run secrets warm` before service operations if GPG is locked. The adapter forwards fnox's `pass` calls to gopass without changing the user's gopass configuration. Only encrypted secret files belong in Fleet; service credentials enter the container environment at runtime.

CPA2 migration retains the original k3s PVC and database for rollback. To roll back, stop Compose CPA2 before scaling `cpa2-cliproxyapi` back to one replica in the `local-services` namespace. The retained k3s database reflects the cutover snapshot; changes made after cutover require a fresh export from Compose before rollback.

Secrets are grouped into `postgres`, `cpa1`, `cpa2`, and `newt` fnox profiles. Select a profile with `fnox -P cpa1 exec -- <command>`, for example. Each CPA profile uses names such as `PGSTORE_DSN` and `MANAGEMENT_PASSWORD`; the service launcher resolves profiles separately and maps them to unique Compose interpolation variables so included service files can distinguish credentials. The encrypted gopass entries keep their existing names.


## Skill harnesses

Skills opt into each harness through an inline list in `SKILL.md` frontmatter metadata:

```yaml
metadata:
  harness: [pi, codex, claude]
```

Supported values are `pi`, `codex`, `claude`, and `opencode`. A skill without `metadata.harness` is not linked anywhere. `mise run link` adds selected links and removes obsolete Fleet-managed links, so metadata changes take effect on every run.

Wayfinder and its companion skills (`setup-matt-pocock-skills`, `domain-modeling`, `research`, `prototype`, `to-spec`, and `to-tickets`) are vendored from [mattpocock/skills](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60) at `d81f3a1`, with only Fleet's harness metadata added. Wayfinder uses Fleet's existing `grilling` skill. The upstream MIT license is in `prompts/skills/MATT-POCOCK-LICENSE`. After linking, run `/setup-matt-pocock-skills` in each repository where you want to use `/wayfinder`, `/to-spec`, or `/to-tickets`; it asks before writing repository-specific issue tracker and domain settings.

Codex and Claude Code share four named subagent roles: `explorer` investigates code without editing, `reviewer` checks changes without editing, `worker` implements scoped changes, and `uiux` implements UI/UX changes or audits usability and accessibility. Explorer and worker use Luna at `xhigh` reasoning; reviewer uses Sol at `low` reasoning; UI/UX uses `ocg/glm-5.3-flash`.

### Pangolin site

The `newt` container uses `fosrl/pangolin-cli` with site ID `p946mt1f12e3jgo` and endpoint `https://app.pangolin.net`. On Silicon, host networking lets the site reach CPA1 at `127.0.0.1:8320` and CPA2 at `127.0.0.1:8321`.

Add the site secret from Fleet's root using the hidden prompt:

```bash
fnox -P newt set SITE_SECRET --provider gopass --key-name services/newt/site-secret
mise run services:up -- --no-recreate newt
```

The secret is encrypted at `secrets/services/newt/site-secret.gpg`. Add it before running service tasks. Keep the existing Silicon Newt service running until the new site is connected and its CPA resources have been switched and verified in Pangolin.
