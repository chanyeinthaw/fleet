# syntax=docker/dockerfile:1.7

ARG BLOB_1_VERSION=0.0.0-latest.20261122.0313

FROM docker:29.7.2-cli AS docker-cli
FROM ghcr.io/astral-sh/uv:latest AS uv

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG BLOB_1_VERSION

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=UTC \
    HOME=/home/blob \
    BLOB_1_HOME=/home/blob/.blob-1 \
    XDG_DATA_HOME=/home/blob/.blob-1/data \
    GH_CONFIG_DIR=/home/blob/.config/gh \
    MISE_DATA_DIR=/home/blob/.local/share/mise \
    MISE_CONFIG_DIR=/home/blob/.config/mise \
    MISE_CACHE_DIR=/home/blob/.cache/mise \
    BLOB_1_BOOTSTRAP_VERSION=${BLOB_1_VERSION} \
    PATH=/home/blob/.local/bin:/home/blob/.local/share/mise/shims:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
      bash \
      build-essential \
      ca-certificates \
      curl \
      fd-find \
      file \
      gh \
      git \
      jq \
      openssh-client \
      openssh-server \
      procps \
      python3 \
      ripgrep \
      sqlite3 \
      sudo \
      supervisor \
      tini \
      unzip \
      wget \
      xz-utils \
      zip \
    && curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.noarmor.gpg \
      -o /usr/share/keyrings/tailscale-archive-keyring.gpg \
    && curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/noble.tailscale-keyring.list \
      -o /etc/apt/sources.list.d/tailscale.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends tailscale \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash --uid 1001 blob \
    && usermod --append --groups sudo blob \
    && echo 'blob ALL=(ALL) NOPASSWD:ALL' >/etc/sudoers.d/blob \
    && chmod 0440 /etc/sudoers.d/blob \
    && mkdir -p /home/blob/.blob-1 /home/blob/.config/gh /home/blob/.ssh /home/blob/.local/bin /run/sshd /var/lib/tailscale /var/lib/blob-1-ssh \
    && chown -R blob:blob /home/blob \
    && printf '%s\n' \
      'PubkeyAuthentication yes' \
      'PasswordAuthentication no' \
      'KbdInteractiveAuthentication no' \
      'PermitEmptyPasswords no' \
      'PermitRootLogin no' \
      'AuthenticationMethods publickey' \
      'AllowUsers blob' \
      'HostKey /var/lib/blob-1-ssh/ssh_host_ed25519_key' \
      'HostKey /var/lib/blob-1-ssh/ssh_host_rsa_key' \
      >/etc/ssh/sshd_config.d/99-blob-1.conf

COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker-cli /usr/local/libexec/docker/cli-plugins/ /usr/local/libexec/docker/cli-plugins/
COPY --from=uv /uv /uvx /usr/local/bin/

USER blob
WORKDIR /home/blob

RUN curl -fsSL https://mise.run | sh
COPY --chown=blob:blob mise.toml /home/blob/.config/mise/config.toml
RUN mise trust -y /home/blob/.config/mise/config.toml && mise install --yes

RUN BLOB_1_VERSION="${BLOB_1_VERSION}" \
    BLOB_1_HOME="/home/blob/.blob-1" \
    BLOB_1_INSTALL_BIN_DIR="/home/blob/.local/bin" \
    sh -c 'curl -fsSL https://raw.githubusercontent.com/chanyeinthaw/blob-1/main/scripts/install.sh | sh'

USER root
RUN mkdir -p /usr/local/lib/blob-1 \
    && cp -a /home/blob/.blob-1/runtime /usr/local/lib/blob-1/runtime

COPY --chmod=0755 entrypoint.sh /usr/local/bin/blob-1-entrypoint
COPY --chmod=0755 tailscale-up.sh /usr/local/bin/blob-1-tailscale-up
COPY --chmod=0755 blob-1-healthcheck /usr/local/bin/blob-1-healthcheck
COPY supervisord.conf /etc/supervisor/supervisord.conf
COPY authorized_keys /usr/local/share/blob-1/authorized_keys

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/blob-1-entrypoint"]
