"""
Tests for the 'search' command's --prompt-template option: it should dump a
matching LLM analysis prompt (see 'prompt') as a .md file named after
the results file, e.g. generated/bazos_report_dynamic_pc_pamet_DDR4.md.

--prompt-template is repeatable: passing it more than once renders one .md
per (non-custom) preset from the same single scrape/results file, each
suffixed with its template name (<output-name>_<template>.md) so they don't
collide on disk. A single --prompt-template still writes the original,
unsuffixed <output-name>.md for backwards compatibility.
"""

import os
from datetime import datetime
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from mse_scrape_bazos.cli import GENERATED_DIR, cli
from mse_scrape_bazos.scraper import BazosItem

ITEMS = [
    BazosItem(
        title="Test RAM",
        price="50 EUR",
        location="BA",
        description="desc",
        image_url=None,
        item_url="https://pc.bazos.sk/item/1",
        date_posted="today",
    ),
]


@pytest.fixture
def mocked_scraper():
    with patch("mse_scrape_bazos.scraper.BazosScraper.get_categories", return_value={"pc": "Computers"}), \
         patch("mse_scrape_bazos.scraper.BazosScraper.get_subcategories_grouped", return_value={}), \
         patch("mse_scrape_bazos.scraper.BazosScraper.get_subcategories", return_value={"pamet": "Pamäť"}), \
         patch("mse_scrape_bazos.scraper.BazosScraper.scrape_listings", return_value=list(ITEMS)):
        yield


class TestSearchPromptTemplate:
    def test_matching_preset_writes_md_next_to_results(self, mocked_scraper):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "search",
                    "--category", "pc",
                    "--sub-category", "pamet",
                    "--keyword", "DDR4",
                    "--prompt-template", "pamat",
                ],
            )
            assert result.exit_code == 0, result.output

            # Note: `search`'s auto-generated filename stamps in today's
            # date (see GENERATED_DIR/_generated_path in cli.py), so the
            # basename isn't the literal "bazos_report_dynamic_pc_pamet_DDR4"
            # -- this was already the case before this change; only the
            # assertion here is updated to match it.
            timestamp = datetime.now().strftime("%Y%m%d")
            base_name = f"bazos_report_dynamic_{timestamp}_pc_pamet_DDR4"
            html_path = os.path.join(GENERATED_DIR, f"{base_name}.html")
            md_path = os.path.join(GENERATED_DIR, f"{base_name}.md")
            assert os.path.exists(html_path)
            assert os.path.exists(md_path)

            with open(md_path, encoding="utf-8") as f:
                content = f.read()
            assert "RAM memory modules" in content
            assert "Handling Multi-Item / Variant Listings" in content

    def test_no_prompt_template_writes_no_md(self, mocked_scraper):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                ["search", "--category", "pc", "--keyword", "ddr4", "--format", "json"],
            )
            assert result.exit_code == 0, result.output
            assert os.path.isdir(GENERATED_DIR)
            assert not any(f.endswith(".md") for f in os.listdir(GENERATED_DIR))

    def test_custom_template_skips_with_warning_no_md(self, mocked_scraper):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "search", "--category", "pc", "--keyword", "ddr4",
                    "--format", "json", "--prompt-template", "custom",
                ],
            )
            assert result.exit_code == 0, result.output
            assert "has no preset content" in result.output
            assert not any(f.endswith(".md") for f in os.listdir(GENERATED_DIR))

    def test_unknown_template_value_rejected(self, mocked_scraper):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, ["search", "--category", "pc", "--keyword", "ddr4", "--prompt-template", "ram"]
            )
            assert result.exit_code != 0
            assert "not one of" in result.output

    def test_md_named_after_csv_output(self, mocked_scraper):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "search", "--category", "pc", "--keyword", "ddr4",
                    "--format", "csv", "--prompt-template", "pamat",
                ],
            )
            assert result.exit_code == 0, result.output
            csv_files = [f for f in os.listdir(GENERATED_DIR) if f.endswith(".csv")]
            md_files = [f for f in os.listdir(GENERATED_DIR) if f.endswith(".md")]
            assert len(csv_files) == 1
            assert len(md_files) == 1
            assert csv_files[0].rsplit(".", 1)[0] == md_files[0].rsplit(".", 1)[0]

    def test_multiple_templates_write_one_md_each_suffixed(self, mocked_scraper):
        """Repeating --prompt-template renders each preset from the same
        results file into its own suffixed .md, so one scrape can drive
        several separate LLM analysis passes."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "search", "--category", "pc", "--keyword", "ddr4",
                    "--format", "json",
                    "--prompt-template", "pamat",
                    "--prompt-template", "disk-ssd",
                ],
            )
            assert result.exit_code == 0, result.output

            md_files = sorted(f for f in os.listdir(GENERATED_DIR) if f.endswith(".md"))
            assert len(md_files) == 2
            pamat_md = next(f for f in md_files if f.endswith("_pamat.md"))
            disk_ssd_md = next(f for f in md_files if f.endswith("_disk-ssd.md"))

            with open(os.path.join(GENERATED_DIR, pamat_md), encoding="utf-8") as f:
                assert "RAM memory modules" in f.read()
            with open(os.path.join(GENERATED_DIR, disk_ssd_md), encoding="utf-8") as f:
                assert "solid-state drives" in f.read()

    def test_duplicate_template_value_deduplicated(self, mocked_scraper):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "search", "--category", "pc", "--keyword", "ddr4",
                    "--format", "json",
                    "--prompt-template", "pamat",
                    "--prompt-template", "pamat",
                ],
            )
            assert result.exit_code == 0, result.output
            md_files = [f for f in os.listdir(GENERATED_DIR) if f.endswith(".md")]
            # A repeated value collapses to a single template -> only one
            # file, kept unsuffixed (same as passing --prompt-template once).
            assert len(md_files) == 1
            assert not md_files[0].endswith("_pamat.md")

    def test_custom_mixed_with_one_real_preset_stays_unsuffixed(self, mocked_scraper):
        """'custom' contributes no file, so mixing it with a single real
        preset should not trigger multi-file suffixing."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "search", "--category", "pc", "--keyword", "ddr4",
                    "--format", "json",
                    "--prompt-template", "custom",
                    "--prompt-template", "pamat",
                ],
            )
            assert result.exit_code == 0, result.output
            assert "has no preset content" in result.output
            md_files = [f for f in os.listdir(GENERATED_DIR) if f.endswith(".md")]
            assert len(md_files) == 1
            assert not md_files[0].endswith("_pamat.md")

    def test_custom_mixed_with_two_real_presets_suffixes_both(self, mocked_scraper):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                [
                    "search", "--category", "pc", "--keyword", "ddr4",
                    "--format", "json",
                    "--prompt-template", "custom",
                    "--prompt-template", "pamat",
                    "--prompt-template", "disk-hdd",
                ],
            )
            assert result.exit_code == 0, result.output
            assert "has no preset content" in result.output
            md_files = sorted(f for f in os.listdir(GENERATED_DIR) if f.endswith(".md"))
            assert len(md_files) == 2
            assert any(f.endswith("_pamat.md") for f in md_files)
            assert any(f.endswith("_disk-hdd.md") for f in md_files)
