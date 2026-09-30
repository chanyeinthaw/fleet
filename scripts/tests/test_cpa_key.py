"""Exercise cache lifetime and permissions without real credentials or GPG."""

import contextlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


loader = importlib.machinery.SourceFileLoader("cpa_key", str(Path(__file__).parents[1] / "cpa-key"))
spec = importlib.util.spec_from_loader(loader.name, loader)
assert spec is not None
helper = importlib.util.module_from_spec(spec)
loader.exec_module(helper)
runtime_directory = helper.runtime_directory
boot_id = helper.boot_id


class CacheTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name) / "fleet"
        for target, value in [("runtime_directory", self.directory), ("boot_id", "boot-1")]:
            mock = patch.object(helper, target, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)
        mock = patch.object(helper, "decrypt_key", return_value="test-key")
        self.decrypt = mock.start()
        self.addCleanup(mock.stop)

    def run_helper(self, action):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            helper.run(action)
        return output.getvalue()

    def test_reuses_key_without_gpg_and_uses_private_permissions(self):
        self.assertEqual(self.run_helper("warm"), "CPA key cached for this boot\n")
        self.decrypt.side_effect = RuntimeError("GPG cache expired")
        self.assertEqual(self.run_helper("get"), "test-key\n")
        self.decrypt.assert_called_once()
        self.assertEqual(self.directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.directory / "cpa1-api-key").stat().st_mode & 0o777, 0o600)

    def test_previous_boot_requires_decryption(self):
        self.run_helper("warm")
        with patch.object(helper, "boot_id", return_value="boot-2"):
            self.decrypt.return_value = "new-key"
            self.assertEqual(self.run_helper("get"), "new-key\n")
        self.assertEqual(self.decrypt.call_count, 2)

    def test_status_never_decrypts_or_prints_key(self):
        self.assertEqual(self.run_helper("status"), "CPA key is not cached\n")
        self.decrypt.assert_not_called()
        self.run_helper("warm")
        self.assertNotIn("test-key", self.run_helper("status"))

    def test_refresh_and_clear(self):
        self.run_helper("warm")
        self.decrypt.return_value = "rotated-key"
        self.run_helper("refresh")
        self.assertEqual(self.run_helper("get"), "rotated-key\n")
        self.run_helper("clear")
        self.assertFalse((self.directory / "cpa1-api-key").exists())

    def test_failed_refresh_preserves_working_cache(self):
        self.run_helper("warm")
        self.decrypt.side_effect = RuntimeError("locked")
        with self.assertRaises(RuntimeError):
            self.run_helper("refresh")
        self.assertEqual(self.run_helper("get"), "test-key\n")

    def test_rejects_symlink_and_readable_cache(self):
        self.run_helper("warm")
        path = self.directory / "cpa1-api-key"
        path.chmod(0o644)
        with self.assertRaises(RuntimeError):
            self.run_helper("get")
        path.unlink()
        path.symlink_to(self.directory / ".cpa-key.lock")
        with self.assertRaises(OSError):
            self.run_helper("get")

    def test_rejects_symlink_directory(self):
        target = self.directory.parent / "target"
        target.mkdir(mode=0o700)
        self.directory.symlink_to(target)
        with self.assertRaises(RuntimeError):
            self.run_helper("warm")

    def test_macos_uses_canonical_user_temp_directory_and_boot_time(self):
        with patch.object(helper.platform, "system", return_value="Darwin"), \
             patch.object(helper.subprocess, "check_output", side_effect=[str(self.directory.parent)+"\n", "{ sec = 123, usec = 4 }\n"]) as command:
            self.assertEqual(runtime_directory(), self.directory)
            self.assertEqual(boot_id(), "{ sec = 123, usec = 4 }")
            self.assertEqual(command.call_args_list[0].args[0], ["/usr/bin/getconf", "DARWIN_USER_TEMP_DIR"])
            self.assertEqual(command.call_args_list[1].args[0], ["/usr/sbin/sysctl", "-n", "kern.boottime"])


if __name__ == "__main__":
    unittest.main()
