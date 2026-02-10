"""Tests for package manager detection in package-json-maintenance skill."""

from conftest import (
    detect_package_manager,
    detect_package_manager_field,
    run_pm_detection_script,
)


class TestLockFileDetection:
    """Test package manager detection from lock files (SKILL.md step 2)."""

    def test_detects_bun_from_lockb(self, use_fixture):
        """bun.lockb should detect bun."""
        project = use_fixture("pm-detection/bun")
        assert run_pm_detection_script(project) == "bun"

    def test_detects_pnpm_from_lock_yaml(self, use_fixture):
        """pnpm-lock.yaml should detect pnpm."""
        project = use_fixture("pm-detection/pnpm")
        assert run_pm_detection_script(project) == "pnpm"

    def test_detects_yarn_from_lock(self, use_fixture):
        """yarn.lock should detect yarn."""
        project = use_fixture("pm-detection/yarn")
        assert run_pm_detection_script(project) == "yarn"

    def test_detects_npm_from_package_lock(self, use_fixture):
        """package-lock.json should detect npm (falls through to else)."""
        project = use_fixture("pm-detection/npm")
        assert run_pm_detection_script(project) == "npm"

    def test_defaults_to_npm_without_lockfile(self, use_fixture):
        """No lock file should default to npm."""
        project = use_fixture("pm-detection/no-lockfile")
        assert run_pm_detection_script(project) == "npm"


class TestLockFilePrecedence:
    """Test that lock files are checked in correct order."""

    def test_bun_takes_precedence_over_yarn(self, use_fixture):
        """When bun.lockb and yarn.lock both exist, bun wins."""
        project = use_fixture("pm-detection/multiple-lockfiles")
        assert run_pm_detection_script(project) == "bun"

    def test_pnpm_over_yarn(self, temp_dir):
        """When pnpm-lock.yaml and yarn.lock both exist, pnpm wins."""
        (temp_dir / "package.json").write_text('{"name": "test"}')
        (temp_dir / "pnpm-lock.yaml").write_text("lockfileVersion: '6.0'\n")
        (temp_dir / "yarn.lock").write_text("# yarn\n")
        assert run_pm_detection_script(temp_dir) == "pnpm"

    def test_bun_over_pnpm(self, temp_dir):
        """When bun.lockb and pnpm-lock.yaml both exist, bun wins."""
        (temp_dir / "package.json").write_text('{"name": "test"}')
        (temp_dir / "bun.lockb").write_bytes(b"\x00")
        (temp_dir / "pnpm-lock.yaml").write_text("lockfileVersion: '6.0'\n")
        assert run_pm_detection_script(temp_dir) == "bun"


class TestPackageManagerField:
    """Test packageManager field detection from package.json."""

    def test_reads_pnpm_field(self, use_fixture):
        """Should parse 'pnpm' from packageManager: 'pnpm@8.6.0'."""
        project = use_fixture("pm-detection/field-pnpm")
        assert detect_package_manager_field(project) == "pnpm"

    def test_reads_yarn_field_without_version(self, use_fixture):
        """Should parse 'yarn' from packageManager: 'yarn' (no version)."""
        project = use_fixture("edge-cases/pm-no-version")
        assert detect_package_manager_field(project) == "yarn"

    def test_returns_none_without_field(self, use_fixture):
        """Should return None when no packageManager field exists."""
        project = use_fixture("pm-detection/npm")
        assert detect_package_manager_field(project) is None

    def test_returns_none_for_missing_package_json(self, temp_dir):
        """Should return None when package.json doesn't exist."""
        assert detect_package_manager_field(temp_dir) is None

    def test_returns_none_for_malformed_json(self, use_fixture):
        """Should return None when package.json is invalid JSON."""
        project = use_fixture("edge-cases/malformed-json")
        assert detect_package_manager_field(project) is None


class TestCombinedDetection:
    """Test full detection logic: packageManager field takes precedence over lock files."""

    def test_field_overrides_lockfile(self, use_fixture):
        """packageManager field should override conflicting lock file."""
        project = use_fixture("pm-detection/field-overrides-lockfile")
        # yarn.lock exists, but packageManager: pnpm@8.6.0 should win
        assert detect_package_manager(project) == "pnpm"

    def test_falls_back_to_lockfile(self, use_fixture):
        """Without packageManager field, lock file detection is used."""
        project = use_fixture("pm-detection/yarn")
        assert detect_package_manager(project) == "yarn"

    def test_falls_back_to_npm_default(self, use_fixture):
        """Without field or lock file, defaults to npm."""
        project = use_fixture("pm-detection/no-lockfile")
        assert detect_package_manager(project) == "npm"
