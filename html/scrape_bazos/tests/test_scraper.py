"""
Tests for scraper module
"""

import pytest
from scrape_bazos.scraper import BazosScraper, BazosItem


class TestBazosItem:
    """Test BazosItem data class"""

    def test_bazos_item_creation(self):
        """Test creating a BazosItem"""
        item = BazosItem(
            title="Test Item",
            price="€100",
            location="Bratislava",
            description="Test description",
            image_url="https://example.com/image.jpg",
            item_url="https://bazos.sk/item/123",
            date_posted="Today",
        )
        assert item.title == "Test Item"
        assert item.price == "€100"
        assert item.location == "Bratislava"

    def test_bazos_item_to_dict(self):
        """Test converting BazosItem to dictionary"""
        item = BazosItem(
            title="Test Item",
            price="€100",
            location="Bratislava",
            description="Test description",
            image_url="https://example.com/image.jpg",
            item_url="https://bazos.sk/item/123",
            date_posted="Today",
        )
        item_dict = item.to_dict()
        assert isinstance(item_dict, dict)
        assert item_dict["title"] == "Test Item"
        assert item_dict["price"] == "€100"

    def test_bazos_item_optional_fields(self):
        """Test BazosItem with optional fields as None"""
        item = BazosItem(
            title="Test Item",
            price=None,
            location=None,
            description="Test description",
            image_url=None,
            item_url="https://bazos.sk/item/123",
            date_posted=None,
        )
        assert item.price is None
        assert item.location is None
        assert item.image_url is None


class TestBazosScraper:
    """Test BazosScraper class"""

    def test_scraper_initialization(self):
        """Test scraper initialization"""
        scraper = BazosScraper(timeout=15)
        assert scraper.timeout == 15

    def test_build_url_basic(self):
        """Test URL building with basic parameters"""
        scraper = BazosScraper()
        url = scraper.build_url(topic="pc", keyword="nas")

        assert "https://pc.bazos.sk/" in url
        assert "hledat=nas" in url
        assert "rubriky=pc" in url
        assert "kitx=ano" in url

    def test_build_url_with_price_range(self):
        """Test URL building with price parameters"""
        scraper = BazosScraper()
        url = scraper.build_url(
            topic="pc",
            keyword="notebook",
            price_from="500",
            price_to="1000",
        )

        assert "cenaod=500" in url
        assert "cenado=1000" in url

    def test_build_url_with_location(self):
        """Test URL building with location"""
        scraper = BazosScraper()
        url = scraper.build_url(
            topic="reality",
            keyword="byt",
            location="Bratislava",
            radius=20,
        )

        assert "hlokalita=Bratislava" in url
        assert "humkreis=20" in url

    def test_build_url_default_radius(self):
        """Test URL building uses default radius"""
        scraper = BazosScraper()
        url = scraper.build_url(topic="pc", keyword="ssd")

        assert "humkreis=25" in url

    def test_scraper_session_headers(self):
        """Test that scraper has proper headers"""
        scraper = BazosScraper()
        assert "User-Agent" in scraper.session.headers
        assert "Mozilla" in scraper.session.headers["User-Agent"]


class TestURLStructure:
    """Test URL structure and parameters"""

    def test_url_format_matches_bazos(self):
        """Test that generated URL matches bazos.sk format"""
        scraper = BazosScraper()
        url = scraper.build_url(
            topic="pc",
            keyword="nas",
            price_from="100",
            price_to="500",
        )

        # Should match format: https://pc.bazos.sk/?hledat=...
        assert url.startswith("https://pc.bazos.sk/?")

        # Should contain required parameters
        params = ["hledat", "rubriky", "humkreis", "kitx"]
        for param in params:
            assert param in url

    def test_different_topics(self):
        """Test URL building for different topics"""
        scraper = BazosScraper()

        topics = ["pc", "auto", "reality", "elektronika"]
        for topic in topics:
            url = scraper.build_url(topic=topic, keyword="test")
            assert f"https://{topic}.bazos.sk/" in url
