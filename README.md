# Fleet

My agent setup, dotfiles, encrypted secrets, and Docker services, shared across machines.

## Setup

Install mise, Git, GPG, pnpm, Perl, and Make, then make the GPG private key matching `secrets/.gpg-id` available on the machine.

```sh
cd ~/fleet
mise run bootstrap
```

Bootstrap installs tools, Pi dependencies, and agent configuration. It also installs dotfiles when enabled in `.fleetrc` and reconciles the opted-in Tether user service. Compose services remain separate.

```sh
mise run update  # Refresh tools and configuration
mise run link    # Refresh agent configuration only
mise run check   # Check configuration and installed links
```

Python, fnox, and Stow are pinned in Fleet's local mise config. Agent CLIs and gopass are installed into mise's global config by the `tools` task. Stow builds from a checksum-verified GNU release; gopass uses upstream binaries for Linux and macOS. Neither requires Homebrew.

## Local settings

Copy `.fleetrc.example` to `.fleetrc`. This file is ignored by Git.

```toml
[author]
name = "Chan"

[agents]
cpa_url = "https://cpa1.p.si14.space"
cpa_secret = "agents/cpa1-api-key"

[dotfiles]
enabled = false

[tether]
enabled = false
```

These are the defaults. On a machine hosting CPA1, use `http://127.0.0.1:8320` instead. Supply the origin without `/v1`; Fleet adds it where needed.

Run `mise run link` after changing the author name or CPA URL. The secret helper reads the selected secret name when invoked. The author and CPA settings affect agents. JJ's identity lives in its encrypted config and is independent of `[author]`.

## Agents and skills

Fleet configures Pi, Codex, and Claude Code. Their sessions and caches stay in their own config directories. Fleet updates its settings in Codex's `config.toml` and Claude's `settings.json` while preserving other local settings.

Agents retrieve the CPA key through `~/.local/bin/fleet-fnox`, including when launched by T3 Code. No `CPA_API_KEY` export is needed. Claude uses CPA's Anthropic-compatible endpoint with `gpt-6.1-sol` by default.

`prompts/agents/catalog.yaml` controls the order of shared instructions. The `harness` and `computers` sections select instructions for each agent and point to its global computer reference file.

Codex and Claude share these subagent roles:

| Role | Job | Model | Effort |
| --- | --- | --- | --- |
| `explorer` | Investigate without editing | GPT-6 Luna | xhigh |
| `reviewer` | Review without editing | GPT-6.1 Sol | low |
| `worker` | Implement scoped changes | GPT-6 Luna | xhigh |
| `uiux` | Build UI or audit usability and accessibility | `ocg/glm-5.3-flash` | xhigh |

CPA's `opencode-session` plugin v0.1.7 or newer derives OCG routing headers from session metadata. Clients do not need a hardcoded session header.

Skills select their agents through `SKILL.md` frontmatter:

```yaml
metadata:
  harness: [pi, codex, claude]
```

Supported values are `pi`, `codex`, `claude`, and `opencode`. Skills without this metadata are skipped. `mise run link` adds and removes links to match it.

Claude reads project `AGENTS.md` files directly. Fleet's Claude plugin also lists project skills under `.agents/skills/` at session start. They are available to the agent without becoming slash commands.

Wayfinder and its companion skills come from [mattpocock/skills](https://github.com/mattpocock/skills/tree/d81f3a183412e71a5b1e84ca21bc1a35eea03a60), with Fleet's metadata added. The MIT license is in `prompts/skills/MATT-POCOCK-LICENSE`. Run `/setup-matt-pocock-skills` in a project before using `/wayfinder`, `/to-spec`, or `/to-tickets`.

## Secrets

[gopass](https://www.gopass.pw/) reads the GPG-encrypted store in `secrets/`. Bootstrap, update, and `mise run tools` configure this checkout as its root store.

```sh
gopass ls
gopass insert api/example
gopass insert --multiline example/ssh-key
gopass config mounts.path
```

Pipe secrets into the command that needs them rather than printing them:

```sh
gopass show --noparsing jp-mirai/jump-msb-stg.pem | ssh-add -
```

Fleet commits the encrypted files through its own Git repository. gopass uses its filesystem backend, with automatic sync and push disabled. Do not initialize a nested Git repository or run `gopass setup` over this store.

Secret names and recipient IDs are visible in Git. Old encrypted versions remain in history, so rotate compromised credentials at their provider. Keep a recovery copy of the GPG private key outside Git.

### Fnox cache

Agent and service secrets are mapped in `fnox.toml`. Unlock GPG and warm all configured profiles with:

```sh
mise run secrets warm
mise run secrets -P agents daemon status
```

The `agents` profile exposes `agents/cpa1-api-key` as `CPA_API_KEY`. Add other mappings to `fnox.toml`; `warm` discovers profiles automatically. Fleet's adapter sends fnox's `pass` calls to gopass.

Each profile has an in-memory daemon cache with a 365-day idle timeout. GPG's one-hour passphrase timeout stays unchanged. After reboot or a daemon restart, warm the cache again. Screen lock does not clear it, and other processes running as your user can read cached secrets. Restart agent sessions after rotating credentials.

The launcher uses `/tmp` as its temporary-directory fallback so service and terminal launches use the same socket on macOS. `mise run check` reports cache status without decrypting secrets. Dotfiles use GPG directly and require an unlocked key even when fnox is warm.

## Dotfiles

Enable dotfiles in `.fleetrc` to install them during bootstrap and update:

```toml
[dotfiles]
enabled = true
```

The whole `dotfiles/` directory is ignored by Git. Only its encrypted ZIP, `secrets/dotfiles.gpg`, is committed. Fleet creates the ZIP in memory, encrypts it for the recipients in `secrets/.gpg-id`, and verifies decryption before replacing the archive.

The directory is one Stow package, with no manifest:

```text
dotfiles/
  dot-aws/                config and credentials
  dot-config/jj/          config.toml
  dot-config/fleet/       shared shell config and completions
  dot-skm/                all SKM files
  dot-ssh/                config
  dot-sshed
```

Bootstrap/update decrypt the archive and run Stow with `--dotfiles --no-folding`. Files are private to your user. When a home file conflicts, Fleet backs it up and uses its own version. Backups live in `${XDG_STATE_HOME:-$HOME/.local/state}/fleet/dotfile-backups`; successful installs keep the latest three.

Edit the linked files or their copies in `dotfiles/`, then save them with:

```sh
mise run dotfiles:sync
```

Sync before bootstrap/update, since those commands restore the archived version. Commit the updated archive to share your edits. New files under `dotfiles/` are picked up automatically. AWS caches, SSH keys outside `.skm`, and other JJ files remain unmanaged unless added there.

Fleet adds a source block to `.bashrc` or `.zshrc` based on `SHELL`. Both load `~/.config/fleet/shell.sh`, which sources exports, common functions, aliases, and completions. Existing startup content is preserved; Omarchy startup stays in `.bashrc`. Disabling dotfile management skips future installs without removing links.

## Tether

[Tether](https://github.com/chanyeinthaw/tether) monitors Linux Wi-Fi through NetworkManager's D-Bus API, switches between saved profiles in priority order, and limits radio resets to three per outage. Connection attempts continue after resets are exhausted, so restarting the router does not require logging into the machine.

While on a healthy fallback, Tether checks for higher-priority networks once a minute. It switches back when a preferred network appears and passes its health checks. A failed attempt restores the previous fallback and delays further priority checks for five minutes. Configure these timings with `priority_check_interval` and `priority_retry_interval` in `config.json`.

Opt in per machine in the gitignored `.fleetrc`:

```toml
[dotfiles]
enabled = true

[tether]
enabled = true
```

Configure the interface and ordered UUID/SSID pairs in `dotfiles/dot-config/tether/config.json`. Wi-Fi passwords remain in saved NetworkManager profiles. Omit `state_file` to use `~/.local/state/tether/state.json`. Sync the encrypted archive before bootstrap/update, which restores the archived dotfiles:

```sh
mise run dotfiles:sync
mise run update
```

Bootstrap and update install the pinned, checksum-verified release from `scripts/tether/release.json`, install `~/.config/systemd/user/tether.service`, and enable/start it. They restart it only when the binary, configuration, or unit changed. An invalid configuration or failed candidate check prevents replacement of a running binary.

The first enabled run requires administrator authorization to install a root-owned Polkit rule for the invoking user and enable lingering. The rule permits NetworkManager connection control, Wi-Fi scans, and radio toggles without a desktop session. These permissions apply to that user beyond Tether's whitelist. Linux ping sockets need no capabilities; if the user's primary group is excluded from `net.ipv4.ping_group_range`, setup expands the existing range and persists it. Setup is recorded in local Fleet state, so unchanged updates do not request administrator access again.

Missing or `enabled = false` skips installation. If Fleet already manages the user unit, it stops and disables it while preserving the binary, configuration, recovery budget, and one-time system authorization. Other machines receive no system changes while disabled. Tether requires Linux; opting in on another OS fails with an explanation.

```sh
systemctl --user status tether.service
journalctl --user -u tether.service -f
cat ~/.local/state/tether/state.json
```

## Services

Docker with Compose is required on the service host. Service commands are separate from bootstrap/update:

```sh
mise run services:up
mise run services:down
mise run services:restart
mise run services:up -- cpa2
```

Use `up` to apply configuration or image changes. `restart` keeps the existing container configuration. `down` preserves bind-mounted data.

`services/compose.yaml` includes a file for each service. Data lives in `${XDG_DATA_HOME:-$HOME/.local/share}/fleet/services`, or `FLEET_SERVICES_DATA_DIR` when set.

| Service | Access |
| --- | --- |
| CPA1 | `127.0.0.1:8320`; override with `CPA1_PORT` |
| CPA2 | `127.0.0.1:8321` |
| PostgreSQL | Compose network only |
| Newt | Pangolin site with host access to both CPAs |
| Friday | HTTP at `127.0.0.1:4020`, OpenSSH, and Tailscale |
| Sunday | Discord bot; host networking reaches T3 at `localhost:3773` |
| Docker-in-Docker | TLS on the private Compose network |

Secrets use separate fnox profiles. The launcher maps each profile's values to Compose variables and injects credentials at runtime. Warm the cache before service operations if GPG is locked.

### Newt

Newt uses `fosrl/pangolin-cli`, endpoint `https://app.pangolin.net`, and site ID `p946mt1f12e3jgo`. Add its secret with the hidden prompt:

```sh
fnox -P newt set SITE_SECRET --provider gopass --key-name services/newt/site-secret
mise run services:up -- --no-recreate newt
```

Host networking on Silicon lets it reach both CPA localhost ports.

### Friday

Friday's data directories are `home`, `pi`, `gh`, `ssh`, `ssh-host`, and `tailscale`. Its fnox profile supplies Discord, CPA, and Tailscale credentials. The image includes Fleet's agents and skills; sessions, authentication, and custom provider definitions persist outside the image. No GPG private key is copied into it.

Rebuild to pick up Fleet changes:

```sh
mise run services:up -- --build --no-deps friday
```

Startup preserves Friday's binary version. Update it separately with `docker exec --user friday friday friday-update`. OpenCode provider overrides live in `friday/pi/provider-overrides.json`; authentication stays in Pi's `auth.json`.

### Sunday

Sunday runs the checksum-verified `v0.0.0-nightly.4` release from `chanyeinthaw/sunday`. Its config is in `services/sunday/sunday.json`, copied from `Projects/t3-bot`. Clone paths refer to the T3 host. The container uses the invoking user's UID/GID, with owner-only pairing credentials and JSON logs in the service data directory's `sunday` folder.

Coding tasks use T3's project or environment default model and options; configure those in T3. Sunday's internal preparation model remains configured under `llm`.

The landing server listens on `127.0.0.1:3785`; Discord app links use `https://sunday.p.si14.space`. Route that hostname through Pangolin to `http://127.0.0.1:3785`.

The `sunday` fnox profile supplies its Discord token and CPA key. The launcher uses the host's `gh auth login` token for repository metadata and passes it as a BuildKit secret when downloading the private release.

```sh
mise run services:up -- --build --no-deps sunday
```

For initial pairing or an expired session, pipe a fresh normal T3 pairing code to `python scripts/services/compose run --rm --no-deps -T sunday pair`. Existing valid credentials can be copied into the service data directory as `credential.json` with mode `0600` while Sunday is stopped. Normal sessions require pairing again at expiry. Only one running process should use a credential state directory.

Container console logs rotate at 10 MiB with three files retained. The append-only `sunday/logs/sunday.jsonl` file needs separate rotation.

### Shared Docker daemon

Friday and future clients share the privileged `docker-in-docker` service. It exposes neither a host port nor Silicon's Docker socket. Friday includes Docker CLI, Buildx, and Compose, with no memory limit.

Projects needing bind mounts should live in `/home/friday/workspaces` or `/home/friday/.friday`; both paths are shared with the daemon. Nested container ports belong to the sidecar, not Silicon.

Other clients join the `docker-in-docker` network, mount `docker-in-docker-certs` read-only at `/certs/client`, and set:

```sh
DOCKER_HOST=tcp://docker-in-docker:2376
DOCKER_TLS_VERIFY=1
DOCKER_CERT_PATH=/certs/client
```

Clients share containers and images. Mount any additional bind-mount directories into the daemon at the same paths.

## Repository layout

```text
agents/    Agent configuration and plugins
prompts/   Instructions, skills, and computer reference files
scripts/   Installation, secrets, dotfiles, and service commands
secrets/   Encrypted credentials and dotfile archive
services/  Compose definitions and container code
dotfiles/  Decrypted Stow package, ignored by Git
```
