"""Machine-local Fleet settings shared by agent installers and secret resolution."""

import json
import os
from pathlib import Path
import re
import tempfile
import tomllib
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parents[2]
DEFAULT_URL = "https://cpa1.p.si14.space"
DEFAULT_SECRET = "agents/cpa1-api-key"


def read_config():
    path = REPO / ".fleetrc"
    config = tomllib.loads(path.read_text()) if path.exists() else {}
    if set(config) - {"agents", "author"}:
        raise ValueError(".fleetrc supports the agents and author sections")
    author = config.get("author", {})
    if not isinstance(author, dict) or set(author) - {"name"}:
        raise ValueError(".fleetrc author supports name")
    name = author.get("name", "Chan")
    if not isinstance(name, str) or not name.strip() or any(ord(c) < 32 for c in name):
        raise ValueError("author.name must be a nonempty, single-line string")
    return config


def author_name():
    return read_config().get("author", {}).get("name", "Chan").strip()


def settings():
    config = read_config()
    agents = config.get("agents", {})
    if not isinstance(agents, dict) or set(agents) - {"cpa_url", "cpa_secret"}:
        raise ValueError(".fleetrc agents supports cpa_url and cpa_secret")
    url = agents.get("cpa_url", DEFAULT_URL)
    secret = agents.get("cpa_secret", DEFAULT_SECRET)
    if not isinstance(url, str) or not isinstance(secret, str):
        raise ValueError("CPA settings must be strings")
    parsed = urlsplit(url)
    if any(c in url for c in '\\"\'<>`'):
        raise ValueError("cpa_url contains invalid URL characters")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"} or any(c.isspace() for c in url):
        raise ValueError("cpa_url must be an HTTP(S) origin, without credentials or a /v1 path")
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", secret) or any(p in {"", ".", ".."} for p in secret.split("/")):
        raise ValueError("cpa_secret must be a password-store entry name")
    return url.rstrip("/"), secret


def agent_base(path):
    url, _ = settings()
    return path.read_text().replace(DEFAULT_URL, url)


def fnox_config():
    _, secret = settings()
    if secret == DEFAULT_SECRET:
        return REPO / "fnox.toml"
    # A stable config path lets fnox cache the selected entry across invocations.
    import hashlib
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "fleet" / hashlib.sha256(str(REPO).encode()).hexdigest()[:16]
    root.mkdir(parents=True, exist_ok=True)
    target = root / "fnox.toml"
    content = (REPO / "fnox.toml").read_text()
    content = content.replace('value = "' + DEFAULT_SECRET + '", env = false', 'value = ' + json.dumps(secret) + ', env = false', 1)
    if tomllib.loads(content)["profiles"]["agents"]["secrets"]["CPA_API_KEY"]["value"] != secret:
        raise ValueError("Could not apply the agent secret override")
    if not target.exists() or target.read_text() != content:
        fd, name = tempfile.mkstemp(dir=root)
        temporary = Path(name)
        try:
            with os.fdopen(fd, "w") as file:
                file.write(content)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    return target
