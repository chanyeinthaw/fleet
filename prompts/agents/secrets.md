# Secrets

- Shared credentials are stored as GPG-encrypted files in Fleet's `secrets/` directory and accessed with `gopass`.
- Use `gopass ls` to discover names. Fleet's bootstrap and update configure the root store; `gopass config mounts.path` shows its location.
- Use credentials only for the authorized task. Pipe `gopass show --noparsing <name>` into the consuming command or capture it without printing it. Do not expose decrypted values in tool output, logs, chat, or Git.
- For SSH keys, prefer `gopass show --noparsing <name> | ssh-add -`. If a command requires a file, create it outside the repository with owner-only permissions and remove it after use.
