#!/usr/bin/env bash
set -Eeuo pipefail

log() {
  printf '[friday-runtime] %s\n' "$*"
}

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    printf '[friday-runtime] ERROR: %s is required\n' "$name" >&2
    exit 1
  fi
}

require_env DISCORD_BOT_TOKEN
require_env DISCORD_APPLICATION_ID
require_env DISCORD_PUBLIC_KEY

RUNTIME_UID="$(id -u friday)"
RUNTIME_GID="$(id -g friday)"

if [[ "$(id -u)" == "0" ]]; then
  for directory in /home/friday/.friday /home/friday/.pi /home/friday/.config/gh /home/friday/.ssh; do
    mkdir -p "${directory}"
    chown -R "${RUNTIME_UID}:${RUNTIME_GID}" "${directory}"
  done

  install -d -m 700 -o friday -g friday /home/friday/.ssh
  install -d -m 755 -o friday -g friday /home/friday/workspaces
  printf '%s\n' \
    'export DOCKER_HOST=tcp://friday-docker:2376' \
    'export DOCKER_TLS_VERIFY=1' \
    'export DOCKER_CERT_PATH=/certs/client' >/etc/profile.d/friday-docker.sh
  install -m 600 -o friday -g friday /usr/local/share/friday/authorized_keys /home/friday/.ssh/authorized_keys
  install -d -m 755 /run/sshd /var/lib/tailscale
  install -d -m 700 /var/lib/friday-ssh
  if [[ ! -f /var/lib/friday-ssh/ssh_host_ed25519_key ]]; then
    ssh-keygen -q -t ed25519 -N '' -f /var/lib/friday-ssh/ssh_host_ed25519_key
  fi
  if [[ ! -f /var/lib/friday-ssh/ssh_host_rsa_key ]]; then
    ssh-keygen -q -t rsa -b 3072 -N '' -f /var/lib/friday-ssh/ssh_host_rsa_key
  fi

  exec supervisord -c /etc/supervisor/supervisord.conf
fi

export HOME=/home/friday
export CI=true
export FRIDAY_HOME=/home/friday/.friday
export GH_CONFIG_DIR=/home/friday/.config/gh
export MISE_DATA_DIR=/home/friday/.local/share/mise
export MISE_CONFIG_DIR=/home/friday/.config/mise
export MISE_CACHE_DIR=/home/friday/.cache/mise
export PATH="/home/friday/.local/share/mise/installs/node/26.7.0/bin:/home/friday/.local/share/mise/installs/bun/1.3.14/bin:/home/friday/.local/share/mise/installs/npm-pnpm/10.33.0/node_modules/.bin:/home/friday/.local/share/mise/installs/pi/0.85.1/pi:/home/friday/.local/share/mise/installs/pi/0.85.1:/home/friday/.local/bin:/home/friday/.local/share/mise/shims:${PATH}"

SSH_KEY_DIR="${HOME}/.ssh"

mkdir -p "${SSH_KEY_DIR}" "${FRIDAY_HOME}" "${GH_CONFIG_DIR}"
chmod 700 "${SSH_KEY_DIR}"

if [[ -f "${SSH_KEY_DIR}/id_ed25519" ]]; then
  chmod 600 "${SSH_KEY_DIR}/id_ed25519"
  touch "${SSH_KEY_DIR}/known_hosts"
  if ! ssh-keygen -F github.com -f "${SSH_KEY_DIR}/known_hosts" >/dev/null 2>&1; then
    ssh-keyscan -H github.com >>"${SSH_KEY_DIR}/known_hosts" 2>/dev/null
  fi
  cat >"${SSH_KEY_DIR}/config" <<EOF
Host github.com
  HostName github.com
  User git
  IdentityFile ${SSH_KEY_DIR}/id_ed25519
  IdentitiesOnly yes
  BatchMode yes
  StrictHostKeyChecking yes
  UserKnownHostsFile ${SSH_KEY_DIR}/known_hosts
EOF
  chmod 600 "${SSH_KEY_DIR}/config"
  export GIT_SSH_COMMAND="ssh -F ${SSH_KEY_DIR}/config"
fi

git config --global user.name "${GIT_USER_NAME:-Chan Nyein Thaw}"
git config --global user.email "${GIT_USER_EMAIL:-chanyeinthaw@gmail.com}"
git config --global init.defaultBranch main
git config --global url."git@github.com:".insteadOf "https://github.com/"

log "Installing Fleet agent configuration"
/opt/fleet/scripts/link
# Friday receives its CPA key from the host's fnox profile rather than GPG.
mkdir -p "$HOME/.config/fleet"
python3 - /opt/fleet/agents/pi/models.json "$HOME/.config/fleet/models.json" <<'PY'
import json
import os
import sys
from pathlib import Path

models = json.loads(Path(sys.argv[1]).read_text())
for provider in models["providers"].values():
    if "fleet-fnox" in provider.get("apiKey", ""):
        provider["apiKey"] = os.environ["CPA_API_KEY"]
overrides = Path.home() / ".pi/provider-overrides.json"
if overrides.exists():
    models["providers"].update(json.loads(overrides.read_text())["providers"])
Path(sys.argv[2]).write_text(json.dumps(models, indent=2) + "\n")
Path(sys.argv[2]).chmod(0o600)
PY
ln -sfn "$HOME/.config/fleet/models.json" "$HOME/.pi/agent/models.json"

if [[ ! -f "${FRIDAY_HOME}/friday.sqlite" ]]; then
  printf '[friday-runtime] ERROR: missing Friday database: %s/friday.sqlite\n' "${FRIDAY_HOME}" >&2
  exit 1
fi

mkdir -p "${FRIDAY_HOME}/bin" "${FRIDAY_HOME}/logs" "${FRIDAY_HOME}/run" "${FRIDAY_HOME}/update"

if [[ "${FRIDAY_UPDATE_ON_START:-true}" == "true" ]]; then
  log "Checking for a Friday ${FRIDAY_UPDATE_CHANNEL:-nightly} update"
  if ! /usr/local/bin/friday-install-release latest; then
    log "Update check failed; continuing with the installed runtime binary"
  fi
elif [[ ! -x "${FRIDAY_HOME}/bin/friday" ]]; then
  /usr/local/bin/friday-install-release "${FRIDAY_BOOTSTRAP_VERSION}"
fi

log "Starting Friday"
exec /usr/local/bin/friday-run
