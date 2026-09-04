"""
Bazos.sk Web Scraper - CORRECTED VERSION (Based on Real HTML)
Scrapes classifieds listings from bazos.sk with descriptions and images
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Optional
import json
from datetime import datetime
import re


class BazosItem:
    """Represents a single item from bazos.sk"""

    def __init__(
        self,
        title: str,
        price: Optional[str],
        location: Optional[str],
        description: str,
        image_url: Optional[str],
        item_url: str,
        date_posted: Optional[str] = None,
    ):
        self.title = title
        self.price = price
        self.location = location
        self.description = description
        self.image_url = image_url
        self.item_url = item_url
        self.date_posted = date_posted

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "title": self.title,
            "price": self.price,
            "location": self.location,
            "description": self.description,
            "image_url": self.image_url,
            "item_url": self.item_url,
            "date_posted": self.date_posted,
        }

    def __repr__(self) -> str:
        return f"BazosItem(title={self.title!r}, price={self.price!r})"


class BazosScraper:
    """Main scraper class for bazos.sk"""

    BASE_URL = "https://{topic}.bazos.sk/"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def build_url(
        self,
        category: str,
        keyword: str,
        price_from: Optional[str] = None,
        price_to: Optional[str] = None,
        radius: int = 25,
        location: str = "",
    ) -> str:
        """
        Build the search URL for bazos.sk

        Args:
            category: Category (e.g., 'pc', 'auto', 'reality')
            keyword: Search keyword (e.g., 'nas', 'notebook')
            price_from: Minimum price
            price_to: Maximum price
            radius: Search radius in km
            location: Specific location

        Returns:
            Full search URL
        """
        # Normalize category to lowercase (website URLs use lowercase)
        category = category.lower()
        base = self.BASE_URL.format(topic=category)

        params = {
            "hledat": keyword,
            "rubriky": category,
            "hlokalita": location,
            "humkreis": str(radius),
            "cenaod": price_from or "",
            "cenado": price_to or "",
            "kitx": "ano",
        }

        # Build query string manually to match expected format
        query_parts = []
        for key, value in params.items():
            if value:
                query_parts.append(f"{key}={value}")

        url = base + "?" + "&".join(query_parts)
        return url

    def scrape_listings(
        self,
        category: str,
        keyword: str,
        price_from: Optional[str] = None,
        price_to: Optional[str] = None,
        radius: int = 25,
        location: str = "",
        max_pages: int = 1,
    ) -> List[BazosItem]:
        """
        Scrape listings from bazos.sk

        Args:
            category: Category
            keyword: Search keyword
            price_from: Minimum price
            price_to: Maximum price
            radius: Search radius
            location: Specific location
            max_pages: Maximum pages to scrape

        Returns:
            List of BazosItem objects
        """
        items = []

        for page in range(max_pages):
            url = self.build_url(
                category=category,
                keyword=keyword,
                price_from=price_from,
                price_to=price_to,
                radius=radius,
                location=location,
            )

            # Add page parameter if not first page
            if page > 0:
                url += f"&page={page}"

            print(f"Scraping page {page + 1}: {url}")

            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                page_items = self._parse_listings(response.text, category)
                items.extend(page_items)

                print(f"Found {len(page_items)} items on page {page + 1}")

            except requests.RequestException as e:
                print(f"Error scraping page {page + 1}: {e}")
                continue

        return items

    def _parse_listings(self, html: str, category: str) -> List[BazosItem]:
        """Parse HTML and extract items"""
        soup = BeautifulSoup(html, "lxml")
        items = []

        # Find all item containers with class "inzeratyflex"
        # NOTE: First item might be header (class="listainzerat inzeratyflex"), skip those
        item_containers = soup.find_all("div", class_="inzeratyflex")

        print(f"Found {len(item_containers)} containers with class 'inzeratyflex'")

        for i, container in enumerate(item_containers):
            # Skip header row (has class "listainzerat")
            if "listainzerat" in container.get("class", []):
                print(f"  Skipping header row (index {i})")
                continue

            try:
                item = self._extract_item(container, category)
                if item:
                    items.append(item)
            except Exception as e:
                print(f"Error parsing item {i}: {e}")
                continue

        return items

    def _extract_item(self, container, category: str) -> Optional[BazosItem]:
        """Extract item details from a container - ACTUAL HTML STRUCTURE"""

        try:
            # ========== TITLE EXTRACTION ==========
            # Title is in <h2 class="nadpis"> inside inzeratynadpis div
            title_elem = container.find("h2", class_="nadpis")
            if not title_elem:
                # Fallback: look for any h2
                title_elem = container.find("h2")

            if not title_elem:
                # Last fallback: look for link in nadpis area
                nadpis_div = container.find("div", class_="inzeratynadpis")
                if nadpis_div:
                    title_elem = nadpis_div.find("a")

            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            if not title:
                return None

            # Extract URL - look for link with href
            item_url = ""
            link = container.find("a", href=True)
            if link:
                item_url = link.get("href", "")

            if not item_url:
                return None

            # ========== IMAGE EXTRACTION ==========
            image_url = None
            img_tag = container.find("img", class_="obrazek")
            if not img_tag:
                img_tag = container.find("img")

            if img_tag:
                image_url = img_tag.get("src", "")
                if image_url:
                    # Handle relative URLs
                    if image_url.startswith("./"):
                        # Local file reference - skip these
                        image_url = None
                    elif image_url.startswith("/"):
                        image_url = f"https://bazos.sk{image_url}"
                    elif not image_url.startswith("http"):
                        image_url = f"https://bazos.sk/{image_url}"

            # ========== DESCRIPTION EXTRACTION ==========
            description = ""
            description_elem = container.find("div", class_="popis")
            if description_elem:
                description = description_elem.get_text(strip=True)

            # ========== PRICE EXTRACTION ==========
            # Price is in <div class="inzeratycena"><b><span>price</span></b></div>
            price = None
            price_elem = container.find("div", class_="inzeratycena")
            if price_elem:
                # Get all text content
                price_text = price_elem.get_text(strip=True)
                # Extract only the numeric part with currency
                # Pattern: "250 €" or "250€"
                price_match = re.search(r'(\d+(?:\s*\d{3})*(?:[,\.]\d+)?)\s*€', price_text)
                if price_match:
                    # Get original format from text
                    price = price_match.group(0).strip()
                elif price_text and any(c.isdigit() for c in price_text):
                    price = price_text
                else:
                    price = None

            # ========== LOCATION EXTRACTION ==========
            # Location is in <div class="inzeratylok">Komárno<br/>946 03</div>
            location = None
            location_elem = container.find("div", class_="inzeratylok")
            if location_elem:
                # Get text and clean up line breaks
                loc_text = location_elem.get_text(strip=True)
                # Remove extra whitespace
                location = " ".join(loc_text.split())
                location = location.strip() if location else None

            # ========== DATE EXTRACTION ==========
            # Date is in <span class="velikost10"> with format like "- [4.9. 2026]" or "- TOP - [4.9. 2026]"
            date_posted = None

            # Try to find date span
            date_span = container.find("span", class_="velikost10")
            if date_span:
                date_text = date_span.get_text(strip=True)
                # Extract date pattern [d.m. year]
                date_match = re.search(r'\[(\d+\.\d+\.\s*\d{4})\]', date_text)
                if date_match:
                    date_posted = date_match.group(1)

            # Fallback: search for date pattern anywhere in container
            if not date_posted:
                container_text = container.get_text()
                date_match = re.search(r'\[(\d+\.\d+\.\s*\d{4})\]', container_text)
                if date_match:
                    date_posted = date_match.group(1)

            return BazosItem(
                title=title,
                price=price,
                location=location,
                description=description,
                image_url=image_url,
                item_url=item_url,
                date_posted=date_posted,
            )

        except Exception as e:
            print(f"Error extracting item details: {e}")
            return None

    def get_categories(self) -> Dict[str, str]:
        """
        Fetch available categories from bazos.sk

        Returns:
            Dictionary mapping category codes to descriptions, or empty dict if fetch fails
        """
        try:
            # Fetch the main bazos.sk page to get the categories dropdown
            response = self.session.get("https://pc.bazos.sk/", timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            categories = {}

            # Find the select element with categories (name="rubriky")
            select = soup.find("select", {"name": "rubriky"})

            if not select:
                raise ValueError("Could not find categories select element")

            # Extract all options
            options = select.find_all("option")

            for option in options:
                value = option.get("value", "").strip()
                text = option.get_text(strip=True)

                # Skip empty values
                if value and text:
                    categories[value] = text

            return categories

        except Exception as e:
            print(f"Error fetching categories: {e}")
            # Return empty dict on error
            return {}

    def save_results(self, items: List[BazosItem], output_file: str) -> None:
        """Save results to JSON file"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_items": len(items),
            "items": [item.to_dict() for item in items],
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Results saved to {output_file}")


def main():
    """Example usage"""
    scraper = BazosScraper()

    # Example: Search for NAS in PC category
    items = scraper.scrape_listings(
        category="pc",
        keyword="nas",
        max_pages=1,
    )

    print(f"\nFound {len(items)} items:")
    for i, item in enumerate(items, 1):
        print(f"\n{i}. {item.title}")
        print(f"   Price: {item.price}")
        print(f"   Location: {item.location}")
        print(f"   Description: {item.description[:100]}...")
        print(f"   Image: {item.image_url}")
        print(f"   URL: {item.item_url}")

    # Save to file
    scraper.save_results(items, "bazos_results.json")


if __name__ == "__main__":
    main()
