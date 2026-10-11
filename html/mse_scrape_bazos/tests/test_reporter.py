"""
Tests for reporter module
"""

import pytest
from pathlib import Path
from mse_scrape_bazos.scraper import BazosItem
from mse_scrape_bazos.reporter import HTMLReportGenerator


class TestHTMLReportGenerator:
    """Test HTML report generation"""

    def test_generator_initialization(self):
        """Test report generator initialization"""
        generator = HTMLReportGenerator()
        assert generator is not None
        assert hasattr(generator, "css_template")
        assert hasattr(generator, "generate_report")

    def test_css_template_exists(self):
        """Test that CSS template is defined"""
        generator = HTMLReportGenerator()
        assert generator.css_template is not None
        assert "<style>" in generator.css_template
        assert "body" in generator.css_template

    def test_empty_items_list(self):
        """Test report generation with empty items"""
        generator = HTMLReportGenerator()
        html = generator._generate_items_html([], include_images=True, image_map=None)
        assert "No items found" in html

    def test_generate_items_html_with_items(self):
        """Test HTML generation for items"""
        generator = HTMLReportGenerator()

        items = [
            BazosItem(
                title="Test Item 1",
                price="€100",
                location="Bratislava",
                description="Test description 1",
                image_url="https://example.com/img1.jpg",
                item_url="https://bazos.sk/item/1",
                date_posted="Today",
            ),
            BazosItem(
                title="Test Item 2",
                price="€200",
                location="Kosice",
                description="Test description 2",
                image_url=None,
                item_url="https://bazos.sk/item/2",
                date_posted="Yesterday",
            ),
        ]

        html = generator._generate_items_html(items, include_images=True, image_map=None)
        assert "Test Item 1" in html
        assert "Test Item 2" in html
        assert "€100" in html
        assert "€200" in html

    def test_generate_items_without_images(self):
        """Test HTML generation without image display"""
        generator = HTMLReportGenerator()

        items = [
            BazosItem(
                title="Test Item",
                price="€100",
                location="Bratislava",
                description="Test",
                image_url="https://example.com/img.jpg",
                item_url="https://bazos.sk/item/1",
                date_posted="Today",
            )
        ]

        html = generator._generate_items_html(items, include_images=False, image_map=None)
        assert "Test Item" in html
        assert "No image display mode" in html

    def test_image_html_with_url(self):
        """Test image HTML generation with URL"""
        generator = HTMLReportGenerator()

        item = BazosItem(
            title="Test",
            price="€100",
            location="Bratislava",
            description="Test",
            image_url="https://example.com/img.jpg",
            item_url="https://bazos.sk/item/1",
        )

        html = generator._get_image_html(item, include_images=True, image_map=None)
        assert "https://example.com/img.jpg" in html
        assert "<img" in html

    def test_image_html_without_url(self):
        """Test image HTML generation without URL"""
        generator = HTMLReportGenerator()

        item = BazosItem(
            title="Test",
            price="€100",
            location="Bratislava",
            description="Test",
            image_url=None,
            item_url="https://bazos.sk/item/1",
        )

        html = generator._get_image_html(item, include_images=True, image_map=None)
        assert "No image available" in html

    def test_image_html_no_display(self):
        """Test image HTML when display is disabled"""
        generator = HTMLReportGenerator()

        item = BazosItem(
            title="Test",
            price="€100",
            location="Bratislava",
            description="Test",
            image_url="https://example.com/img.jpg",
            item_url="https://bazos.sk/item/1",
        )

        html = generator._get_image_html(item, include_images=False, image_map=None)
        assert "No image display mode" in html


class TestDynamicReportMatching:
    """Test the diacritics-insensitive keyword matching in the dynamic report"""

    @staticmethod
    def _sample_items():
        return [
            BazosItem(
                title="Otočná autosedačka 360",
                price="120 €",
                location="Košice",
                description="Otočná sedačka isofix",
                image_url=None,
                item_url="https://bazos.sk/item/1",
            ),
            BazosItem(
                title="Otocna autosedacka",
                price="90 €",
                location="Kosice",
                description="otocna sedacka",
                image_url=None,
                item_url="https://bazos.sk/item/2",
            ),
        ]

    def test_dynamic_report_has_diacritics_folding(self, tmp_path):
        """Filter matching must strip combining marks so 'otocna' finds 'otočná'"""
        generator = HTMLReportGenerator()
        output = tmp_path / "report.html"

        generator.generate_dynamic_report(
            self._sample_items(), output_file=str(output), category="deti", keyword=""
        )
        html = output.read_text(encoding="utf-8")

        # The folding helper and the exact regex for combining marks
        assert "function foldDiacritics(text)" in html
        assert "text.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '')" in html
        # Both the needle and the cached field are folded
        assert "needle = foldDiacritics(needle)" in html
        assert "lcField(item, activeFilters[f].key, fold)" in html

    def test_dynamic_report_has_match_mode_selector(self, tmp_path):
        """The report exposes an 'ignore diacritics' (default) / 'exact' switch"""
        generator = HTMLReportGenerator()
        output = tmp_path / "report.html"

        generator.generate_dynamic_report(
            self._sample_items(), output_file=str(output), category="deti", keyword=""
        )
        html = output.read_text(encoding="utf-8")

        assert 'id="matchMode"' in html
        assert '<option value="fold" selected>' in html
        assert '<option value="exact">' in html
        # Diacritics-insensitive is the default state
        assert "let ignoreDiacritics = true;" in html

    def test_dynamic_report_has_any_field_key(self, tmp_path):
        """'any' searches every field and is the default filter key"""
        generator = HTMLReportGenerator()
        output = tmp_path / "report.html"

        generator.generate_dynamic_report(
            self._sample_items(), output_file=str(output), category="deti", keyword=""
        )
        html = output.read_text(encoding="utf-8")

        assert (
            "const AVAILABLE_KEYS = ['any', 'title', 'description', "
            "'full_description', 'price', 'location'];" in html
        )
        assert (
            "const SEARCH_ALL_KEYS = ['title', 'description', "
            "'full_description', 'price', 'location'];" in html
        )
        assert "const DEFAULT_FILTER_KEY = 'any';" in html
        # The virtual key joins the fields so a needle cannot span a boundary
        assert "raw = parts.join('\\n');" in html
        # The very first filter row uses it
        assert "{ key: 'any', value: '' }" in html
