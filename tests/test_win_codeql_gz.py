"""Tests for win-codeql-action-sync-gz.yml workflow.

Validates YAML structure, GitHub Actions schema requirements, asset-filter
logic (keeps .tar.gz, removes .tar.zst), and parity with the -zst variant.
"""

import fnmatch
import re
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
GZ_FILE = REPO_ROOT / "win-codeql-action-sync-gz.yml"
ZST_FILE = REPO_ROOT / "win-codeql-action-sync-zst.yml"


def load_workflow(path: Path) -> dict:
    return yaml.safe_load(path.read_text())


def extract_keep_patterns(workflow: dict) -> list[str]:
    """Pull the -like patterns from the 'Remove unnecessary release assets' step."""
    step = next(
        s for s in workflow["jobs"]["sync"]["steps"]
        if "Remove unnecessary release assets" in s.get("name", "")
    )
    return re.findall(r"-like\s+'([^']+)'", step["run"])


def asset_decision(filename: str, patterns: list[str]) -> bool:
    """Simulate the PowerShell switch: return True (keep) if any pattern matches."""
    return any(fnmatch.fnmatch(filename, pat) for pat in patterns)


class TestYAMLValidity(unittest.TestCase):
    """Ensure the workflow file is parseable YAML."""

    def test_gz_file_exists(self):
        self.assertTrue(GZ_FILE.exists(), f"{GZ_FILE.name} not found")

    def test_parses_as_yaml(self):
        wf = load_workflow(GZ_FILE)
        self.assertIsInstance(wf, dict)


class TestWorkflowStructure(unittest.TestCase):
    """Verify required GitHub Actions workflow keys."""

    @classmethod
    def setUpClass(cls):
        cls.wf = load_workflow(GZ_FILE)

    def test_has_name(self):
        self.assertIn("name", self.wf)

    def test_has_on_trigger(self):
        self.assertIn(True, self.wf)  # PyYAML parses 'on' as True

    def test_has_jobs(self):
        self.assertIn("jobs", self.wf)
        self.assertIn("sync", self.wf["jobs"])

    def test_runs_on_windows(self):
        self.assertEqual(self.wf["jobs"]["sync"]["runs-on"], "Ent_Windows_runners")

    def test_all_steps_use_pwsh(self):
        for step in self.wf["jobs"]["sync"]["steps"]:
            if "run" in step:
                self.assertEqual(step.get("shell"), "pwsh", f"Step '{step['name']}' must use pwsh")

    def test_expected_step_names(self):
        names = [s["name"] for s in self.wf["jobs"]["sync"]["steps"]]
        for expected in [
            "Checkout repository",
            "Download codeql-action-sync tool",
            "Download CodeQL-Action bundle and assets",
            "Remove unnecessary release assets",
            "Sync assets to GHES",
            "Mark latest release on GHES",
        ]:
            self.assertIn(expected, names)


class TestAssetFilterLogic(unittest.TestCase):
    """Core test: the gz variant keeps .tar.gz and removes .tar.zst."""

    @classmethod
    def setUpClass(cls):
        cls.patterns = extract_keep_patterns(load_workflow(GZ_FILE))

    # .tar.gz bundles should be KEPT
    def test_keeps_linux_tar_gz(self):
        self.assertTrue(asset_decision("codeql-bundle-linux64.tar.gz", self.patterns))

    def test_keeps_win_tar_gz(self):
        self.assertTrue(asset_decision("codeql-bundle-win64.tar.gz", self.patterns))

    def test_keeps_linux_tar_gz_checksum(self):
        self.assertTrue(asset_decision("codeql-bundle-linux64.tar.gz.checksum.txt", self.patterns))

    def test_keeps_win_tar_gz_checksum(self):
        self.assertTrue(asset_decision("codeql-bundle-win64.tar.gz.checksum.txt", self.patterns))

    # .tar.zst bundles should be REMOVED
    def test_removes_linux_tar_zst(self):
        self.assertFalse(asset_decision("codeql-bundle-linux64.tar.zst", self.patterns))

    def test_removes_win_tar_zst(self):
        self.assertFalse(asset_decision("codeql-bundle-win64.tar.zst", self.patterns))

    def test_removes_linux_tar_zst_checksum(self):
        self.assertFalse(asset_decision("codeql-bundle-linux64.tar.zst.checksum.txt", self.patterns))

    def test_removes_win_tar_zst_checksum(self):
        self.assertFalse(asset_decision("codeql-bundle-win64.tar.zst.checksum.txt", self.patterns))

    # macOS assets should be REMOVED regardless of extension
    def test_removes_osx_tar_gz(self):
        self.assertFalse(asset_decision("codeql-bundle-osx64.tar.gz", self.patterns))

    def test_removes_osx_tar_zst(self):
        self.assertFalse(asset_decision("codeql-bundle-osx64.tar.zst", self.patterns))

    # Universal bundles should be REMOVED
    def test_removes_universal_tar_gz(self):
        self.assertFalse(asset_decision("codeql-bundle.tar.gz", self.patterns))

    def test_removes_universal_tar_zst(self):
        self.assertFalse(asset_decision("codeql-bundle.tar.zst", self.patterns))

    # Dependabot proxy and CLI metadata should be KEPT
    def test_keeps_update_job_proxy_linux(self):
        self.assertTrue(asset_decision("update-job-proxy-linux-amd64", self.patterns))

    def test_keeps_update_job_proxy_win(self):
        self.assertTrue(asset_decision("update-job-proxy-win-amd64.exe", self.patterns))

    def test_removes_update_job_proxy_osx(self):
        self.assertFalse(asset_decision("update-job-proxy-osx-amd64", self.patterns))

    def test_keeps_cli_version_txt(self):
        self.assertTrue(asset_decision("cli-version-2.16.0.txt", self.patterns))


class TestZstVariantParity(unittest.TestCase):
    """The gz and zst files should be identical except for the filter patterns."""

    @classmethod
    def setUpClass(cls):
        cls.gz_text = GZ_FILE.read_text()
        cls.zst_text = ZST_FILE.read_text()

    def test_only_filter_lines_differ(self):
        gz_lines = self.gz_text.splitlines()
        zst_lines = self.zst_text.splitlines()
        self.assertEqual(len(gz_lines), len(zst_lines), "Files should have the same number of lines")
        diffs = [
            (i + 1, g, z)
            for i, (g, z) in enumerate(zip(gz_lines, zst_lines))
            if g != z
        ]
        for lineno, gz_line, zst_line in diffs:
            self.assertTrue(
                "tar.gz" in gz_line or "tar.zst" in gz_line
                or "tar.gz" in zst_line or "tar.zst" in zst_line,
                f"Unexpected diff at line {lineno}:\n  gz:  {gz_line}\n  zst: {zst_line}",
            )

    def test_zst_variant_keeps_zst(self):
        patterns = extract_keep_patterns(load_workflow(ZST_FILE))
        self.assertTrue(asset_decision("codeql-bundle-linux64.tar.zst", patterns))
        self.assertFalse(asset_decision("codeql-bundle-linux64.tar.gz", patterns))

    def test_gz_variant_keeps_gz(self):
        patterns = extract_keep_patterns(load_workflow(GZ_FILE))
        self.assertTrue(asset_decision("codeql-bundle-linux64.tar.gz", patterns))
        self.assertFalse(asset_decision("codeql-bundle-linux64.tar.zst", patterns))


if __name__ == "__main__":
    unittest.main()
