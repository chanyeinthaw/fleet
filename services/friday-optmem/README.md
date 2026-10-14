# Friday Optmem

Production runs at https://friday.si14.space through a dedicated Cloudflare tunnel.
The existing Friday CLI service runs separately.

## Configure

The encrypted `services/friday-optmem/production-env` gopass record contains the Clerk production publishable key, JWT public key, encryption key, and R2 credentials.
The `services/friday-optmem/tunnel-token` record contains the tunnel credential.

Run `scripts/services/optmem configure` to write owner-only runtime files under
`~/.local/share/fleet/services/friday-optmem/`.

## Deploy

Run `scripts/services/optmem update optmem-v0.0.0-nightly.1` to deploy a release.
Omit the tag to select the latest Optmem release.
The updater reads the release's `IMAGE` asset and pulls that immutable digest.
It stops only Friday Optmem before backing up its SQLite volume.
If startup fails, it restores the database backup and previous image.
The backup remains in `database-before-update.tar.gz` until the next update.

Install the user service and timer from this directory into `~/.config/systemd/user/`,
then run `systemctl --user daemon-reload` and
`systemctl --user enable --now friday-optmem-update.timer`.
The timer checks GitHub Releases every five minutes, with up to 30 seconds of jitter.
It requires Docker access and an authenticated `gh` CLI.

The database volume is `fleet-services_optmem-data`.
The app binds to `127.0.0.1:3003` and the tunnel forwards to its container port 3002.
