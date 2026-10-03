"""Exercise installation decisions without touching services or privileged files."""

import hashlib
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader("tether_installer", str(Path(__file__).with_name("run")))
spec = importlib.util.spec_from_loader(loader.name, loader)
installer = importlib.util.module_from_spec(spec)
loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / "home"
        self.repo = self.root / "repo"
        self.config = self.home / ".config/tether/config.json"
        self.unit = self.home / ".config/systemd/user/tether.service"
        self.binary = self.home / ".local/bin/tether"
        self.receipt = self.home / ".local/state/fleet/tether/install.json"
        self.data = b"verified-binary"
        self.service = b"# Managed by Fleet: tether\n[Service]\nExecStart=/example/tether\n"
        self.calls = []
        self.active = True
        self.valid = True
        self.write(self.config, b'{"interface":"test0"}')
        self.write(self.repo / "services/tether/tether.service", self.service)
        self.write(self.repo / "scripts/tether/release.json", json.dumps({
            "repo": "test/tether", "version": "v1.0.0",
            "sha256": {"amd64": hashlib.sha256(self.data).hexdigest()},
        }).encode())
        for patcher in [
            patch.object(installer, "REPO", self.repo),
            patch.object(installer.platform, "system", return_value="Linux"),
            patch.object(installer.platform, "machine", return_value="x86_64"),
            patch.object(installer.os, "getuid", return_value=1000),
            patch.object(installer, "prerequisites", return_value="setup"),
            patch.object(installer, "download", return_value=self.data),
            patch.object(installer.subprocess, "run", side_effect=self.fake_run),
        ]:
            patcher.start()
            self.addCleanup(patcher.stop)

    def write(self, path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def fake_run(self, args, **kwargs):
        self.calls.append(args)
        if args[0] == "systemctl" and "--quiet" in args:
            return subprocess.CompletedProcess(args, 0 if self.active else 3, "", "")
        if "-check" in args and not self.valid:
            return subprocess.CompletedProcess(args, 1, "", "invalid profile")
        return subprocess.CompletedProcess(args, 0, "active", "")

    def existing_install(self):
        self.write(self.binary, self.data)
        self.write(self.unit, self.service)
        self.write(self.receipt, json.dumps({
            "version": "v1.0.0", "config_sha256": installer.digest(self.config.read_bytes()),
            "unit_sha256": installer.digest(self.service), "setup_sha256": "setup",
        }).encode())

    def test_disabled_machine_does_nothing_even_on_mac(self):
        with patch.object(installer.platform, "system", return_value="Darwin"):
            installer.reconcile(False, self.home)
        self.assertEqual(self.calls, [])
        installer.prerequisites.assert_not_called()
        installer.download.assert_not_called()

    def test_disable_stops_only_a_fleet_owned_service(self):
        self.write(self.unit, self.service)
        installer.reconcile(False, self.home)
        self.assertEqual(self.calls, [["systemctl", "--user", "disable", "--now", "tether.service"]])
        installer.prerequisites.assert_not_called()
        self.write(self.unit, b"unmanaged service")
        self.calls.clear()
        installer.reconcile(False, self.home)
        self.assertEqual(self.calls, [])

    def test_unchanged_install_does_not_download_or_restart(self):
        self.existing_install()
        installer.reconcile(True, self.home)
        installer.download.assert_not_called()
        self.assertFalse(any("restart" in call or "start" in call for call in self.calls))

    def test_changed_config_restarts_service(self):
        self.existing_install()
        self.config.write_text('{"interface":"other0"}')
        installer.reconcile(True, self.home)
        self.assertIn(["systemctl", "--user", "restart", "tether.service"], self.calls)
        installer.download.assert_not_called()

    def test_new_install_validates_then_starts(self):
        self.active = False
        installer.reconcile(True, self.home)
        self.assertEqual(self.binary.read_bytes(), self.data)
        self.assertIn(["systemctl", "--user", "start", "tether.service"], self.calls)
        self.assertIn(["systemctl", "--user", "daemon-reload"], self.calls)
        self.assertLess(next(i for i, call in enumerate(self.calls) if "-check" in call),
                        self.calls.index(["systemctl", "--user", "start", "tether.service"]))

    def test_invalid_upgrade_preserves_old_binary_and_running_service(self):
        self.existing_install()
        self.binary.write_bytes(b"old-binary")
        self.valid = False
        with self.assertRaisesRegex(RuntimeError, "validation failed"):
            installer.reconcile(True, self.home)
        self.assertEqual(self.binary.read_bytes(), b"old-binary")
        self.assertFalse(any(call[0] == "systemctl" for call in self.calls))

    def test_unmanaged_unit_is_not_replaced(self):
        self.write(self.unit, b"unmanaged")
        with self.assertRaisesRegex(ValueError, "unmanaged unit"):
            installer.reconcile(True, self.home)
        installer.prerequisites.assert_not_called()
        installer.download.assert_not_called()


class ChecksumTests(unittest.TestCase):
    def test_rejects_download_with_wrong_checksum(self):
        with patch.object(installer.urllib.request, "urlopen", return_value=io.BytesIO(b"tampered")):
            with self.assertRaisesRegex(ValueError, "checksum verification failed"):
                installer.download("https://example.com/binary", hashlib.sha256(b"expected").hexdigest())


if __name__ == "__main__":
    unittest.main()
