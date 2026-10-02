---
name: t3-pair
description: Use when we need to issue a T3 Code pairing code.
metadata:
  harness: [pi, codex, claude]
---

# T3 pairing

Issue a fresh code for the requested T3 Code environment. Use normal pairing unless the user requests admin access, all scopes, or permission to create and revoke other clients' pairing tokens.

Run the bundled helper with Python 3:

```bash
python3 scripts/pair.py normal
python3 scripts/pair.py admin
```

Resolve `scripts/pair.py` relative to this skill's directory. Both routes default to `~/.t3`; use `--base-dir` for another environment and `--cli` to select a specific installed T3 executable. The helper otherwise resolves the active version from that environment's service state, then falls back to `t3` on PATH. Do not use an outdated source checkout or the desktop launcher.

- **Normal:** Use `t3 auth pairing create`. This grants standard client scopes for working with agents and terminals, without access management.
- **Admin:** Issue a temporary administrative bearer session, pass its complete scope list to `POST /api/auth/pairing-token` on the running local service, verify the stored pairing scopes, and revoke the temporary session in `finally`. The CLI pairing command has no admin scope flag in v0.0.44.

Print the returned pairing code directly in the reply, with its actual expiry converted to the user's timezone and whether it is normal or admin. Pairing codes are short-lived and single-use. Generate a replacement when requested; do not reuse an expired or consumed code. Do not print the temporary bearer token or save credentials in the repository.

The admin API controls the pairing expiry; a longer temporary bearer lifetime does not extend it. In v0.0.44 the API issues codes valid for about five minutes.

Do not restart the service, change its bind address, modify the desktop launcher, or alter existing sessions to issue a code. If issuance or scope verification fails, report the failure instead of claiming success. If temporary-session revocation fails, report its session ID and the cleanup failure; do not expose its bearer token.

The web Connections tab requires both `access:write` and the primary backend's `remote-reachable` auth policy to show pairing management. A loopback bind reports `loopback-browser` and hides those controls even with admin scopes; desktop uses its native network-exposure state. See the upstream [Connections settings checks](https://github.com/pingdotgg/t3code/blob/99e08526e5ec84f294940cba5929841518c52fec/apps/web/src/components/settings/ConnectionsSettings.tsx#L2102-L2104). Check the paired session's scopes and auth policy before diagnosing a missing control. Changing the bind address is a separate task requiring user authorization.
