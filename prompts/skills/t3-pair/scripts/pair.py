#!/usr/bin/env python3
"""Issue a normal or administrative pairing code from an installed T3 CLI."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request


def run_cli(cli, base_dir, *arguments):
    result = subprocess.run(
        [cli, "auth", *arguments, "--base-dir", str(base_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        # CLI output may contain credentials; keep it out of error messages.
        raise RuntimeError(f"T3 auth {' '.join(arguments[:2])} failed")
    return result.stdout


def resolve_cli(base_dir, explicit):
    if explicit:
        return str(Path(explicit).expanduser())
    state = base_dir / "runtime/service-state.json"
    if state.exists():
        version = json.loads(state.read_text()).get("activeVersion")
        if version:
            executable = base_dir / "runtime/versions" / version / "t3"
            if executable.is_file():
                return str(executable)
    executable = shutil.which("t3")
    if executable:
        return executable
    raise RuntimeError("No installed T3 CLI found; supply --cli")


def issue_admin(cli, base_dir, label):
    runtime = json.loads((base_dir / "userdata/server-runtime.json").read_text())
    origin = f"http://127.0.0.1:{runtime['port']}"
    admin = json.loads(run_cli(
        cli, base_dir, "session", "issue", "--ttl", "5m",
        "--label", "temporary pairing issuer", "--json",
    ))
    try:
        scopes = admin["scopes"]
        if "access:write" not in scopes:
            raise RuntimeError("Temporary admin session lacks access:write")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        def request(path, payload=None):
            headers = {"Authorization": "Bearer " + admin["token"]}
            data = None
            if payload is not None:
                headers["Content-Type"] = "application/json"
                data = json.dumps(payload).encode()
            req = urllib.request.Request(origin + path, data=data, headers=headers)
            with opener.open(req, timeout=20) as response:
                return json.load(response)

        pairing = request("/api/auth/pairing-token", {"label": label, "scopes": scopes})
        links = request("/api/auth/pairing-links")
        entries = links if isinstance(links, list) else links["pairingLinks"]
        match = next((entry for entry in entries if entry["id"] == pairing["id"]), None)
        if match is None or set(match["scopes"]) != set(scopes):
            raise RuntimeError("Created pairing code failed scope verification")
        return {**pairing, "scopes": scopes}
    finally:
        try:
            run_cli(cli, base_dir, "session", "revoke", admin["sessionId"])
        except RuntimeError:
            raise RuntimeError(
                f"Temporary admin session {admin['sessionId']} could not be revoked"
            ) from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["normal", "admin"])
    parser.add_argument("--base-dir", type=Path, default=Path.home() / ".t3")
    parser.add_argument("--cli")
    parser.add_argument("--label")
    args = parser.parse_args()
    base_dir = args.base_dir.expanduser().resolve()
    cli = resolve_cli(base_dir, args.cli)
    label = args.label or f"{args.mode} pairing"
    if args.mode == "normal":
        pairing = json.loads(run_cli(
            cli, base_dir, "pairing", "create", "--label", label, "--json",
        ))
    else:
        pairing = issue_admin(cli, base_dir, label)
    print(json.dumps(pairing, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f"Pairing failed: {error}", file=sys.stderr)
        sys.exit(1)
