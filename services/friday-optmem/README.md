# Friday web moved to Unfold

The web app now lives at https://unfold.si14.space and [chanyeinthaw/unfold](https://github.com/chanyeinthaw/unfold). `friday.si14.space` permanently redirects there, preserving paths and query strings.

Use [the Unfold service](../unfold/README.md) and `scripts/services/unfold`. The former updater timer is disabled and its containers are removed. The production volume, Clerk users, encryption key, and attachment bucket were preserved.

The original encrypted credentials and deployment state remain available for rollback. The pre-migration database backup is `~/.local/share/fleet/services/unfold/before-unfold-migration.tar.gz`. Restore the previous service definitions from Git before rolling back, and never run both apps against the same volume.
