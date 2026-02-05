"""Tests for config file detection in learn skill."""

from conftest import run_detection_script


class TestConfigDetection:
    """Test detection of all 8 config formats."""

    def test_empty_project_has_no_configs(self, use_fixture):
        """Empty project should detect no config files."""
        project = use_fixture("empty-project")
        detected = run_detection_script(project)
        assert detected == []

    def test_detects_claude_md(self, use_fixture):
        """Should detect CLAUDE.md."""
        project = use_fixture("single-configs/claude")
        detected = run_detection_script(project)
        assert "CLAUDE.md" in detected

    def test_detects_gemini_md(self, use_fixture):
        """Should detect GEMINI.md."""
        project = use_fixture("single-configs/gemini")
        detected = run_detection_script(project)
        assert "GEMINI.md" in detected

    def test_detects_agents_md(self, use_fixture):
        """Should detect AGENTS.md."""
        project = use_fixture("single-configs/agents")
        detected = run_detection_script(project)
        assert "AGENTS.md" in detected

    def test_detects_cursorrules(self, use_fixture):
        """Should detect .cursorrules."""
        project = use_fixture("single-configs/cursorrules")
        detected = run_detection_script(project)
        assert ".cursorrules" in detected

    def test_detects_cursor_mdc(self, use_fixture):
        """Should detect .cursor/rules/*.mdc files."""
        project = use_fixture("single-configs/cursor-mdc")
        detected = run_detection_script(project)
        mdc_files = [f for f in detected if f.endswith(".mdc")]
        assert len(mdc_files) == 1
        assert "typescript.mdc" in mdc_files[0]

    def test_detects_copilot_instructions(self, use_fixture):
        """Should detect .github/copilot-instructions.md."""
        project = use_fixture("single-configs/copilot")
        detected = run_detection_script(project)
        assert ".github/copilot-instructions.md" in detected

    def test_detects_windsurf_rules(self, use_fixture):
        """Should detect .windsurf/rules/rules.md."""
        project = use_fixture("single-configs/windsurf")
        detected = run_detection_script(project)
        assert ".windsurf/rules/rules.md" in detected

    def test_detects_continuerc_json(self, use_fixture):
        """Should detect .continuerc.json."""
        project = use_fixture("single-configs/continue")
        detected = run_detection_script(project)
        assert ".continuerc.json" in detected


class TestMultipleConfigs:
    """Test detection with multiple config files present."""

    def test_detects_two_configs(self, use_fixture):
        """Should detect both configs when two are present."""
        project = use_fixture("multi-configs/two-configs")
        detected = run_detection_script(project)
        assert len(detected) == 2
        assert "CLAUDE.md" in detected
        assert "GEMINI.md" in detected

    def test_detects_three_configs(self, use_fixture):
        """Should detect all three configs."""
        project = use_fixture("multi-configs/three-configs")
        detected = run_detection_script(project)
        assert len(detected) == 3

    def test_detects_all_config_types(self, use_fixture):
        """Should detect all 8 config types when present."""
        project = use_fixture("multi-configs/all-configs")
        detected = run_detection_script(project)
        # 7 regular files + 1 MDC = 8
        assert len(detected) >= 8


class TestCursorVariations:
    """Test Cursor-specific config variations."""

    def test_cursor_legacy_only(self, use_fixture):
        """Should detect legacy .cursorrules."""
        project = use_fixture("cursor-variations/legacy-only")
        detected = run_detection_script(project)
        assert ".cursorrules" in detected

    def test_cursor_mdc_only(self, use_fixture):
        """Should detect multiple MDC files."""
        project = use_fixture("cursor-variations/mdc-only")
        detected = run_detection_script(project)
        mdc_files = [f for f in detected if f.endswith(".mdc")]
        assert len(mdc_files) == 2

    def test_cursor_both_legacy_and_mdc(self, use_fixture):
        """Should detect both legacy and MDC when present."""
        project = use_fixture("cursor-variations/both")
        detected = run_detection_script(project)
        assert ".cursorrules" in detected
        mdc_files = [f for f in detected if f.endswith(".mdc")]
        assert len(mdc_files) == 1

    def test_cursor_multiple_mdc_files(self, use_fixture):
        """Should detect all MDC files in .cursor/rules/."""
        project = use_fixture("cursor-variations/multi-mdc")
        detected = run_detection_script(project)
        mdc_files = [f for f in detected if f.endswith(".mdc")]
        assert len(mdc_files) == 3
