"""Tests for the search metadata baked into the dumped JSON.

The `search` command writes a self-describing dump: alongside the items it
records the search that produced them and the report settings they were
rendered with. `convert-format` reads that block instead of asking for
--category / --keyword / --truncate-descriptions on the command line.
"""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from scrape_bazos.cli import cli
from scrape_bazos.scraper import (
    SCHEMA_VERSION,
    BazosItem,
    BazosItemDetails,
    ReportSettings,
    SearchMetadata,
    item_from_dict,
    load_results,
    save_results_json,
)


@pytest.fixture
def items():
    return [
        BazosItem(
            title="Kingston DDR4 16GB",
            price="45 €",
            location="Bratislava",
            description="RAM modul",
            image_url="https://example.com/a.jpg",
            item_url="https://pc.bazos.sk/inzerat/1/",
            date_posted="20.9. 2026",
            item_details=BazosItemDetails(
                image_urls=["https://example.com/a.jpg", "https://example.com/b.jpg"],
                full_description="Plny popis DDR4 modulu.",
            ),
        ),
        BazosItem(
            title="Crucial DDR4 8GB",
            price="1 300 €",
            location="Kosice",
            description="Druhy modul",
            image_url=None,
            item_url="https://pc.bazos.sk/inzerat/2/",
        ),
    ]


@pytest.fixture
def metadata():
    return SearchMetadata(
        category="pc",
        sub_category="pamet",
        keywords=["DDR4", "kingston"],
        price_from="10",
        price_to="500",
        location="Bratislava",
        radius=50,
        pages_get="all",
        details_all=True,
        format="html_dynamic",
        report=ReportSettings(include_images=True, truncate_descriptions=True),
    )


class TestSearchMetadata:
    def test_display_properties(self, metadata):
        assert metadata.category_display == "pc / pamet"
        assert metadata.keyword_display == "DDR4, kingston"

    def test_display_without_subcategory(self):
        m = SearchMetadata(category="auto", keywords=["skoda"])
        assert m.category_display == "auto"
        assert m.keyword_display == "skoda"

    def test_display_falls_back_when_empty(self):
        m = SearchMetadata()
        assert m.category_display == "Bazos"
        assert m.keyword_display == "Items"

    def test_from_dict_tolerates_singular_and_missing_keys(self):
        m = SearchMetadata.from_dict({"category": "pc", "keyword": "nas", "radius": "25"})
        assert m.keywords == ["nas"]
        assert m.radius == 25
        assert m.report.include_images is True

    def test_from_dict_ignores_garbage_radius(self):
        assert SearchMetadata.from_dict({"radius": "far"}).radius is None

    def test_from_dict_of_none(self):
        assert SearchMetadata.from_dict(None).category is None


class TestDumpShape:
    def test_dump_carries_search_block(self, tmp_path, items, metadata):
        out = tmp_path / "dump.json"
        save_results_json(items, str(out), metadata)
        raw = json.loads(out.read_text(encoding="utf-8"))

        assert raw["schema_version"] == SCHEMA_VERSION
        assert raw["total_items"] == 2
        assert raw["search"]["category"] == "pc"
        assert raw["search"]["sub_category"] == "pamet"
        assert raw["search"]["keywords"] == ["DDR4", "kingston"]
        assert raw["search"]["price_from"] == "10"
        assert raw["search"]["details_all"] is True
        assert raw["search"]["report"]["truncate_descriptions"] is True
        assert raw["search"]["scraped_at"]

    def test_dump_without_metadata_still_has_block(self, tmp_path, items):
        out = tmp_path / "dump.json"
        save_results_json(items, str(out))
        raw = json.loads(out.read_text(encoding="utf-8"))
        assert raw["search"]["category"] is None
        assert raw["search"]["scraped_at"]

    def test_round_trip(self, tmp_path, items, metadata):
        out = tmp_path / "dump.json"
        save_results_json(items, str(out), metadata)
        loaded, m, has_metadata = load_results(str(out))

        assert has_metadata is True
        assert len(loaded) == 2
        assert isinstance(loaded[0].item_details, BazosItemDetails)
        assert loaded[0].full_description == "Plny popis DDR4 modulu."
        assert loaded[0].image_urls == [
            "https://example.com/a.jpg",
            "https://example.com/b.jpg",
        ]
        assert m.category_display == "pc / pamet"
        assert m.report.truncate_descriptions is True


class TestLegacyFiles:
    def _item_dict(self):
        return {
            "title": "Old item",
            "price": "10 €",
            "location": "Nitra",
            "description": "popis",
            "image_url": None,
            "item_url": "https://pc.bazos.sk/inzerat/9/",
            "date_posted": None,
        }

    def test_legacy_envelope(self, tmp_path):
        p = tmp_path / "legacy.json"
        p.write_text(
            json.dumps({"timestamp": "2026-01-01T00:00:00", "total_items": 1,
                        "items": [self._item_dict()]}),
            encoding="utf-8",
        )
        loaded, m, has_metadata = load_results(str(p))
        assert has_metadata is False
        assert len(loaded) == 1
        assert m.category_display == "Bazos"
        assert m.keyword_display == "Items"
        assert m.scraped_at == "2026-01-01T00:00:00"

    def test_legacy_bare_array(self, tmp_path):
        p = tmp_path / "legacy_array.json"
        p.write_text(json.dumps([self._item_dict()]), encoding="utf-8")
        loaded, m, has_metadata = load_results(str(p))
        assert has_metadata is False
        assert len(loaded) == 1

    def test_unrecognised_shape(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text(json.dumps({"nope": 1}), encoding="utf-8")
        with pytest.raises(ValueError):
            load_results(str(p))

    def test_flat_detail_fields(self):
        item = item_from_dict({
            "title": "x", "price": None, "location": None, "description": "d",
            "image_url": None, "item_url": "u",
            "image_urls": ["https://example.com/z.jpg"],
            "full_description": "full",
        })
        assert item.image_urls == ["https://example.com/z.jpg"]
        assert item.full_description == "full"

    def test_unknown_keys_ignored(self):
        item = item_from_dict({
            "title": "x", "price": None, "location": None, "description": "d",
            "image_url": None, "item_url": "u", "future_field": 42,
        })
        assert item.title == "x"


class TestConvertFormatUsesMetadata:
    @pytest.fixture
    def dump(self, tmp_path, items, metadata):
        p = tmp_path / "dump.json"
        save_results_json(items, str(p), metadata)
        return str(p)

    def _run(self, runner, args, expected_exit=0):
        result = runner.invoke(cli, args, catch_exceptions=False)
        assert result.exit_code == expected_exit, result.output
        return result

    def test_html_heading_comes_from_metadata(self, tmp_path, dump):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            self._run(runner, ["convert-format", "-i", dump, "-o", "r.html"])
            html = Path("generated/r.html").read_text(encoding="utf-8")
            assert "pc / pamet" in html
            assert "DDR4, kingston" in html

    def test_static_html_heading_comes_from_metadata(self, tmp_path, dump):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            self._run(runner, ["convert-format", "-i", dump, "-o", "r.html", "--static"])
            html = Path("generated/r.html").read_text(encoding="utf-8")
            assert "pc / pamet" in html

    def test_json_output_round_trips_metadata(self, tmp_path, dump):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            self._run(runner, ["convert-format", "-i", dump, "-o", "out.json"])
            raw = json.loads(Path("generated/out.json").read_text(encoding="utf-8"))
            assert raw["schema_version"] == SCHEMA_VERSION
            assert raw["search"]["keywords"] == ["DDR4", "kingston"]
            assert raw["items"][0]["item_details"]["full_description"]

            # and the converted file converts again, still labelled
            self._run(runner, ["convert-format", "-i", "generated/out.json",
                               "-o", "again.html"])
            assert "pc / pamet" in Path("generated/again.html").read_text(encoding="utf-8")

    def test_legacy_input_warns_and_still_converts(self, tmp_path, items):
        legacy = tmp_path / "legacy.json"
        legacy.write_text(
            json.dumps({"timestamp": "2026-01-01T00:00:00", "total_items": 1,
                        "items": [{"title": "Old", "price": "5 €", "location": "Nitra",
                                   "description": "d", "image_url": None,
                                   "item_url": "https://pc.bazos.sk/inzerat/9/"}]}),
            encoding="utf-8",
        )
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = self._run(runner, ["convert-format", "-i", str(legacy), "-o", "r.html"])
            assert "No search metadata" in result.output
            assert "Bazos" in Path("generated/r.html").read_text(encoding="utf-8")

    @pytest.mark.parametrize("option,value", [
        ("--category", "pc"),
        ("--keyword", "nas"),
        ("--truncate-descriptions", None),
    ])
    def test_removed_options_are_gone(self, tmp_path, dump, option, value):
        runner = CliRunner()
        args = ["convert-format", "-i", dump, "-o", "r.html", option]
        if value is not None:
            args.append(value)
        result = runner.invoke(cli, args)
        assert result.exit_code != 0
        assert "no such option" in result.output.lower()

    def test_no_images_overrides_metadata(self, tmp_path, dump):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            self._run(runner, ["convert-format", "-i", dump, "-o", "r.html", "--no-images"])
            html = Path("generated/r.html").read_text(encoding="utf-8")
            assert '"image_urls": ["https://example.com/a.jpg"' not in html

    def test_unknown_extension_rejected(self, tmp_path, dump):
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ["convert-format", "-i", dump, "-o", "r.txt"])
            assert result.exit_code == 1
            assert "Cannot tell the output format" in result.output
