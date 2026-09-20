"""
Tests for the 'search' command's --prompt-template option: it should dump a
matching LLM analysis prompt (see 'prompt') as a .md file named after
the results file, e.g. generated/bazos_report_dynamic_pc_pamet_DDR4.md.
"""

import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from scrape_bazos.cli import GENERATED_DIR, cli
from scrape_bazos.scraper import BazosItem

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
    with patch("scrape_bazos.scraper.BazosScraper.get_categories", return_value={"pc": "Computers"}), \
         patch("scrape_bazos.scraper.BazosScraper.get_subcategories_grouped", return_value={}), \
         patch("scrape_bazos.scraper.BazosScraper.get_subcategories", return_value={"pamet": "Pamäť"}), \
         patch("scrape_bazos.scraper.BazosScraper.scrape_listings", return_value=list(ITEMS)):
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

            html_path = os.path.join(GENERATED_DIR, "bazos_report_dynamic_pc_pamet_DDR4.html")
            md_path = os.path.join(GENERATED_DIR, "bazos_report_dynamic_pc_pamet_DDR4.md")
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
