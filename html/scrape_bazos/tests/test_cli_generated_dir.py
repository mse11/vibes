"""
Tests for the generated/ output-directory redirection in the CLI.
"""

import os
from pathlib import Path

from click.testing import CliRunner

from scrape_bazos.cli import GENERATED_DIR, _generated_dir, _generated_path, cli


class TestGeneratedPathHelper:
    """Test _generated_path: bare filenames -> generated/, explicit paths respected"""

    def test_bare_filename_redirected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = _generated_path("report.json")
        assert result == str(Path(GENERATED_DIR) / "report.json")
        assert (tmp_path / GENERATED_DIR).is_dir()

    def test_explicit_relative_path_respected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = _generated_path("myfolder/report.json")
        assert result == "myfolder/report.json"
        assert (tmp_path / "myfolder").is_dir()
        assert not (tmp_path / GENERATED_DIR).exists()

    def test_explicit_absolute_path_respected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        abs_target = tmp_path / "elsewhere" / "report.json"
        result = _generated_path(str(abs_target))
        assert result == str(abs_target)
        assert abs_target.parent.is_dir()


class TestGeneratedDirHelper:
    """Test _generated_dir: same redirection rule, but creates the dir itself"""

    def test_bare_dirname_redirected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = _generated_dir("images")
        assert result == str(Path(GENERATED_DIR) / "images")
        assert (tmp_path / GENERATED_DIR / "images").is_dir()

    def test_explicit_dir_respected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = _generated_dir("custom/my_images")
        assert result == "custom/my_images"
        assert (tmp_path / "custom" / "my_images").is_dir()
        assert not (tmp_path / GENERATED_DIR).exists()


class TestPromptWritesToGenerated:
    """End-to-end: prompt's default output lands under generated/"""

    def test_default_output_under_generated(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["prompt", "--type", "pamat"])
            assert result.exit_code == 0, result.output
            assert os.path.isdir(GENERATED_DIR)
            files = os.listdir(GENERATED_DIR)
            assert len(files) == 1
            assert files[0].startswith("prompt_") and files[0].endswith(".md")
            assert not os.path.exists(files[0])  # not left in the cwd

    def test_explicit_output_with_dir_not_redirected(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                ["prompt", "--type", "pamat", "--output", "custom_out/my_prompt.md"],
            )
            assert result.exit_code == 0, result.output
            assert os.path.exists("custom_out/my_prompt.md")
            assert not os.path.isdir(GENERATED_DIR)

    def test_bare_explicit_output_still_redirected(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, ["prompt", "--type", "pamat", "--output", "my_prompt.md"]
            )
            assert result.exit_code == 0, result.output
            assert os.path.exists(os.path.join(GENERATED_DIR, "my_prompt.md"))
            assert not os.path.exists("my_prompt.md")
