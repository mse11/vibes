"""
Tests for reporter module
"""

import pytest
from pathlib import Path
from scrape_bazos.scraper import BazosItem
from scrape_bazos.reporter import HTMLReportGenerator


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
