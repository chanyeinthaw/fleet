#!/usr/bin/env bash
set -Eeuo pipefail

log() {
  printf '[blob-1-runtime] %s\n' "$*"
}

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    printf '[blob-1-runtime] ERROR: %s is required\n' "$name" >&2
    exit 1
  fi
}

RUNTIME_UID="$(id -u blob)"
RUNTIME_GID="$(id -g blob)"

if [[ "$(id -u)" == "0" ]]; then
  for directory in /home/blob/.blob-1 /home/blob/.blob-1/data /home/blob/.blob-1/logs /home/blob/.blob-1/run /home/blob/.config/gh /home/blob/.ssh /home/blob/.local/bin; do
    mkdir -p "${directory}"
    chown -R "${RUNTIME_UID}:${RUNTIME_GID}" "${directory}"
  done

  version="${BLOB_1_BOOTSTRAP_VERSION:-0.0.0-latest.20261122.0313}"
  target_dir="/home/blob/.blob-1/runtime/versions/${version}"
  if [[ ! -x "${target_dir}/blob-1" && -d "/usr/local/lib/blob-1/runtime/versions/${version}" ]]; then
    mkdir -p "/home/blob/.blob-1/runtime/versions"
    cp -a "/usr/local/lib/blob-1/runtime/versions/${version}" "${target_dir}"
    chown -R "${RUNTIME_UID}:${RUNTIME_GID}" "/home/blob/.blob-1/runtime"
  fi
  if [[ -x "${target_dir}/blob-1" && ( ! -e "/home/blob/.local/bin/blob-1" || ! -f "/home/blob/.blob-1/runtime/service-state.json" ) ]]; then
    ln -sfn "${target_dir}/blob-1" /home/blob/.local/bin/blob-1
    chown -h "${RUNTIME_UID}:${RUNTIME_GID}" /home/blob/.local/bin/blob-1
    grep -qxF "/home/blob/.local/bin/blob-1" /home/blob/.blob-1/runtime/launchers 2>/dev/null \
      || printf '%s\n' "/home/blob/.local/bin/blob-1" >> /home/blob/.blob-1/runtime/launchers
    chown "${RUNTIME_UID}:${RUNTIME_GID}" /home/blob/.blob-1/runtime/launchers
  fi

  install -d -m 700 -o blob -g blob /home/blob/.ssh
  install -m 600 -o blob -g blob /usr/local/share/blob-1/authorized_keys /home/blob/.ssh/authorized_keys

  printf '%s\n' \
    'export DOCKER_HOST=tcp://docker-in-docker:2376' \
    'export DOCKER_TLS_VERIFY=1' \
    'export DOCKER_CERT_PATH=/certs/client' >/etc/profile.d/docker-in-docker.sh

  printf '%s\n' \
    'export BLOB_1_HOME=/home/blob/.blob-1' \
    'export XDG_DATA_HOME=/home/blob/.blob-1/data' \
    'export GH_CONFIG_DIR=/home/blob/.config/gh' \
    'export MISE_DATA_DIR=/home/blob/.local/share/mise' \
    'export MISE_CONFIG_DIR=/home/blob/.config/mise' \
    'export MISE_CACHE_DIR=/home/blob/.cache/mise' \
    'export PATH="/home/blob/.local/bin:/home/blob/.local/share/mise/shims:$PATH"' >/etc/profile.d/blob-1.sh

  install -d -m 755 /run/sshd /var/lib/tailscale
  install -d -m 700 /var/lib/blob-1-ssh
  if [[ ! -f /var/lib/blob-1-ssh/ssh_host_ed25519_key ]]; then
    ssh-keygen -q -t ed25519 -N '' -f /var/lib/blob-1-ssh/ssh_host_ed25519_key
  fi
  if [[ ! -f /var/lib/blob-1-ssh/ssh_host_rsa_key ]]; then
    ssh-keygen -q -t rsa -b 3072 -N '' -f /var/lib/blob-1-ssh/ssh_host_rsa_key
  fi

  exec supervisord -c /etc/supervisor/supervisord.conf
fi

# BLOB_1_MODE=node runs a remote execution node instead of the primary.
if [[ "${BLOB_1_MODE:-serve}" != node ]]; then
  require_env BLOB_1_APP_KEY
fi

export HOME=/home/blob
export BLOB_1_HOME=/home/blob/.blob-1
export XDG_DATA_HOME=/home/blob/.blob-1/data
export GH_CONFIG_DIR=/home/blob/.config/gh
export MISE_DATA_DIR=/home/blob/.local/share/mise
export MISE_CONFIG_DIR=/home/blob/.config/mise
export MISE_CACHE_DIR=/home/blob/.cache/mise
export PATH="/home/blob/.local/bin:/home/blob/.local/share/mise/shims:${PATH}"

SSH_KEY_DIR="${HOME}/.ssh"
mkdir -p "${SSH_KEY_DIR}" "${BLOB_1_HOME}" "${XDG_DATA_HOME}" "${GH_CONFIG_DIR}"
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

if [[ "${BLOB_1_MODE:-serve}" == node ]]; then
  require_env BLOB_1_NODE_URL
  log "Starting Blob-1 node"
  exec /home/blob/.local/bin/blob-1 node --url "${BLOB_1_NODE_URL}"
fi

log "Starting Blob-1 launcher"
exec /home/blob/.local/bin/blob-1 launcher \
  --web 0.0.0.0:7878 \
  --public-url "${BLOB_1_PUBLIC_URL:-https://blob-1.p.si14.space}"
