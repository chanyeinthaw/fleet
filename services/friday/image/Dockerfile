# syntax=docker/dockerfile:1.7

ARG FRIDAY_VERSION=v0.0.0-nightly.49
ARG FRIDAY_TARGET=linux-x64

FROM docker:29.7.2-cli AS docker-cli

FROM ubuntu:24.04 AS friday-download

ARG DEBIAN_FRONTEND=noninteractive
ARG FRIDAY_VERSION
ARG FRIDAY_TARGET

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl coreutils tar \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/friday
RUN curl -fsSLO "https://github.com/chanyeinthaw/friday/releases/download/${FRIDAY_VERSION}/friday-${FRIDAY_VERSION}-${FRIDAY_TARGET}.tar.gz" \
    && curl -fsSLO "https://github.com/chanyeinthaw/friday/releases/download/${FRIDAY_VERSION}/SHA256SUMS" \
    && grep "friday-${FRIDAY_VERSION}-${FRIDAY_TARGET}.tar.gz" SHA256SUMS | sha256sum --check - \
    && tar -xzf "friday-${FRIDAY_VERSION}-${FRIDAY_TARGET}.tar.gz" \
    && install -m 0755 "friday-${FRIDAY_VERSION}-${FRIDAY_TARGET}" /usr/local/bin/friday

FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG FRIDAY_VERSION

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=UTC \
    HOME=/home/friday \
    FRIDAY_HOME=/home/friday/.friday \
    GH_CONFIG_DIR=/home/friday/.config/gh \
    MISE_DATA_DIR=/home/friday/.local/share/mise \
    MISE_CONFIG_DIR=/home/friday/.config/mise \
    MISE_CACHE_DIR=/home/friday/.cache/mise \
    FRIDAY_BOOTSTRAP_VERSION=${FRIDAY_VERSION} \
    PATH=/home/friday/.friday/bin:/home/friday/.local/share/mise/installs/node/26.7.0/bin:/home/friday/.local/share/mise/installs/bun/1.3.14/bin:/home/friday/.local/share/mise/installs/npm-pnpm/10.33.0/node_modules/.bin:/home/friday/.local/share/mise/installs/pi/1.0.0/pi:/home/friday/.local/share/mise/installs/pi/1.0.0:/home/friday/.local/bin:/home/friday/.local/share/mise/shims:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
      bash \
      build-essential \
      ca-certificates \
      curl \
      fd-find \
      gh \
      git \
      jq \
      openssh-client \
      openssh-server \
      procps \
      python3 \
      ripgrep \
      supervisor \
      sudo \
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
    && useradd --create-home --shell /bin/bash --uid 1001 friday \
    && usermod --append --groups sudo friday \
    && echo 'friday ALL=(ALL) NOPASSWD:ALL' >/etc/sudoers.d/friday \
    && chmod 0440 /etc/sudoers.d/friday \
    && mkdir -p /home/friday/.friday /home/friday/.pi/agent /home/friday/.config/gh /home/friday/.ssh /run/secrets /run/sshd /var/lib/tailscale \
    && chown -R friday:friday /home/friday \
    && printf '%s\n' \
      'PubkeyAuthentication yes' \
      'PasswordAuthentication no' \
      'KbdInteractiveAuthentication no' \
      'PermitEmptyPasswords no' \
      'PermitRootLogin no' \
      'AuthenticationMethods publickey' \
      'AllowUsers friday' \
      'HostKey /var/lib/friday-ssh/ssh_host_ed25519_key' \
      'HostKey /var/lib/friday-ssh/ssh_host_rsa_key' \
      >/etc/ssh/sshd_config.d/99-friday.conf

USER friday
WORKDIR /home/friday

RUN curl https://mise.run | sh
COPY --chown=friday:friday services/friday/image/mise.toml /home/friday/mise.toml
RUN mise trust -y /home/friday/mise.toml && mise install --yes

COPY --from=friday-download --chmod=0755 /usr/local/bin/friday /usr/local/lib/friday/bootstrap/friday
COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker-cli /usr/local/libexec/docker/cli-plugins/ /usr/local/libexec/docker/cli-plugins/
COPY --chmod=0755 services/friday/image/entrypoint.sh /usr/local/bin/friday-runtime-entrypoint
COPY --chmod=0755 services/friday/image/install-friday-release.sh /usr/local/bin/friday-install-release
COPY --chmod=0755 services/friday/image/run-friday.sh /usr/local/bin/friday-run
COPY --chmod=0755 services/friday/image/friday-update /usr/local/bin/friday-update
COPY --chmod=0755 services/friday/image/friday-restart /usr/local/bin/friday-restart
COPY --chmod=0755 services/friday/image/friday-healthcheck /usr/local/bin/friday-healthcheck
COPY services/friday/image/supervisord.conf /etc/supervisor/supervisord.conf
COPY services/friday/image/authorized_keys /usr/local/share/friday/authorized_keys
COPY --chmod=0755 services/friday/image/tailscale-up.sh /usr/local/bin/friday-tailscale-up

COPY --chown=friday:friday agents /opt/fleet/agents
COPY --chown=friday:friday prompts /opt/fleet/prompts
COPY --chown=friday:friday scripts /opt/fleet/scripts
RUN pnpm --dir /opt/fleet/agents/pi install --frozen-lockfile

USER root
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/friday-runtime-entrypoint"]
