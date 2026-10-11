"""
Tests for the 'categories-prompt' command: lists the PromptType values
available for 'prompt --type' and 'search --prompt-template'.
"""

from click.testing import CliRunner

from mse_scrape_bazos.cli import cli
from mse_scrape_bazos.prompts import PromptType


class TestCategoriesPrompt:
    def test_lists_every_prompt_type_value(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["categories-prompt"])
        assert result.exit_code == 0, result.output
        for prompt_type in PromptType:
            assert prompt_type.value in result.output

    def test_reports_correct_count(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["categories-prompt"])
        assert result.exit_code == 0, result.output
        assert f"Found {len(PromptType)} prompt template type" in result.output

    def test_plain_output_has_no_preset_details(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["categories-prompt"])
        assert result.exit_code == 0, result.output
        assert "Price tiers:" not in result.output
        assert "Columns:" not in result.output

    def test_details_flag_shows_price_tiers_and_columns(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["categories-prompt", "--details"])
        assert result.exit_code == 0, result.output
        assert "Price tiers:" in result.output
        assert "Columns:" in result.output
        assert "Example item:" in result.output

    def test_details_short_flag_matches_long_flag(self):
        runner = CliRunner()
        long_result = runner.invoke(cli, ["categories-prompt", "--details"])
        short_result = runner.invoke(cli, ["categories-prompt", "-d"])
        assert long_result.output == short_result.output

    def test_custom_type_flagged_as_having_no_fixed_preset(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["categories-prompt", "--details"])
        assert result.exit_code == 0, result.output
        assert "No fixed preset" in result.output

    def test_ram_variants_all_listed(self):
        """The RAM/SO-DIMM/UDIMM/RDIMM variants should each get their own line,
        with the SO-DIMM/UDIMM/RDIMM ones prefixed with 'pamat-'."""
        runner = CliRunner()
        result = runner.invoke(cli, ["categories-prompt"])
        assert result.exit_code == 0, result.output
        assert "pamat" in result.output
        assert "pamat-sodimm" in result.output
        assert "pamat-udimm" in result.output
        assert "pamat-rdimm" in result.output

    def test_disk_variants_all_listed(self):
        """The disk/disk-hdd/disk-ssd variants should each get their own line."""
        runner = CliRunner()
        result = runner.invoke(cli, ["categories-prompt"])
        assert result.exit_code == 0, result.output
        assert "disk" in result.output
        assert "disk-hdd" in result.output
        assert "disk-ssd" in result.output

    def test_gpu_variants_all_listed(self):
        """The grafika / grafika-nvidia / grafika-amd variants are each listed."""
        runner = CliRunner()
        result = runner.invoke(cli, ["categories-prompt"])
        assert result.exit_code == 0, result.output
        assert "grafika" in result.output
        assert "grafika-nvidia" in result.output
        assert "grafika-amd" in result.output
