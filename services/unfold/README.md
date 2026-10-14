# Unfold

Production runs at https://unfold.si14.space from [chanyeinthaw/unfold](https://github.com/chanyeinthaw/unfold). The Friday CLI service remains separate.

## Configure

`services/unfold/production-env` contains the existing Clerk publishable key, JWT public key, encryption key, and R2 credentials, with `UNFOLD_` variable names. `services/unfold/tunnel-token` contains the reused Cloudflare tunnel credential.

Run `scripts/services/unfold configure` to write owner-only runtime files under `~/.local/share/fleet/services/unfold/`.

## Deploy

Run `scripts/services/unfold update v0.0.0-nightly.1`, or omit the tag for the latest release. The updater verifies the immutable `IMAGE` digest, backs up SQLite while the app is stopped, and restores the previous database and image on startup failure.

Install `unfold-update.service` and `unfold-update.timer` in `~/.config/systemd/user/`. Run `systemctl --user daemon-reload` and `systemctl --user enable --now unfold-update.timer`. The timer checks every five minutes with up to 30 seconds of jitter. The former `friday-optmem-update.timer` is disabled.

## Preserved production data

The external Docker volume remains `fleet-services_optmem-data`, with the original `/data/friday.sqlite` database and `wednesday_*` tables. The encryption key, Clerk application and users, and private R2 bucket `friday-optmem-production-attachments` are unchanged. Never run Friday Optmem and Unfold against this volume simultaneously.

The app keeps port `127.0.0.1:3003`, with port 3002 inside the container. The existing Cloudflare tunnel routes to `http://unfold:3002`.

The former `friday.si14.space` host uses a Cloudflare 301 redirect to Unfold, preserving paths and query strings. The `si14.space` Clerk auth domains remain unchanged; Clerk Home URL, application name, logo, and favicon now use Unfold.
