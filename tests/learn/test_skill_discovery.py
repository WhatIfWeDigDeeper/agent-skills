"""Tests for SKILL.md discovery in learn skill."""

from conftest import run_skill_discovery_script


class TestSkillDiscovery:
    """Test SKILL.md discovery functionality."""

    def test_no_skills_in_empty_project(self, use_fixture):
        """Empty project should have no skills."""
        project = use_fixture("empty-project")
        skills = run_skill_discovery_script(project)
        assert skills == []

    def test_discovers_single_skill(self, use_fixture):
        """Should discover a single skill."""
        project = use_fixture("with-skills/single-skill")
        skills = run_skill_discovery_script(project)
        assert "test-skill" in skills

    def test_discovers_multiple_skills(self, use_fixture):
        """Should discover multiple skills."""
        project = use_fixture("with-skills/multi-skill")
        skills = run_skill_discovery_script(project)
        assert len(skills) == 3

    def test_skill_names_extracted_correctly(self, use_fixture):
        """Should extract skill names from frontmatter."""
        project = use_fixture("with-skills/multi-skill")
        skills = run_skill_discovery_script(project)

        assert "build" in skills
        assert "test-runner" in skills
        assert "deploy" in skills


class TestNestedSkills:
    """Test discovery of skills in nested directories."""

    def test_discovers_nested_skills(self, use_fixture):
        """Should discover skills in subdirectories."""
        project = use_fixture("with-skills/nested-skills")
        skills = run_skill_discovery_script(project)
        assert len(skills) == 2
        assert "component" in skills
        assert "api" in skills


class TestNodeModulesExclusion:
    """Test that node_modules skills are excluded."""

    def test_excludes_node_modules_skills(self, use_fixture):
        """Skills in node_modules should be ignored."""
        project = use_fixture("with-skills/with-node-modules")
        skills = run_skill_discovery_script(project)

        assert "ignored-skill" not in skills

    def test_finds_real_skill_with_node_modules_present(self, use_fixture):
        """Should find real skills even when node_modules exists."""
        project = use_fixture("with-skills/with-node-modules")
        skills = run_skill_discovery_script(project)

        assert "real-skill" in skills


class TestMalformedSkills:
    """Test handling of malformed SKILL.md files."""

    def test_excludes_skill_without_name_field(self, use_fixture):
        """Skills without name field should be excluded."""
        project = use_fixture("with-skills/malformed-skill")
        skills = run_skill_discovery_script(project)

        assert skills == []


class TestNoSkillsDirectory:
    """Test projects without skills directory."""

    def test_handles_no_skills_directory(self, use_fixture):
        """Should handle projects without skills directory gracefully."""
        project = use_fixture("single-configs/claude")
        skills = run_skill_discovery_script(project)

        assert skills == []

    def test_empty_discovery_does_not_error(self, use_fixture):
        """Empty discovery result should not cause errors."""
        project = use_fixture("empty-project")
        # Should not raise any exceptions
        skills = run_skill_discovery_script(project)
        assert isinstance(skills, list)
