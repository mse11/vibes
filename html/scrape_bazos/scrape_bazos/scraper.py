"""
Bazos.sk Web Scraper
Scrapes classifieds listings from bazos.sk with descriptions and images
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Optional
import json
from datetime import datetime


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

        # Find all item containers - current structure on bazos.sk
        # Items are in div with class containing "inzeraty" and "inzeratyflex"
        item_containers = soup.find_all("div", class_="inzeratyflex")

        if not item_containers:
            # Try alternative: div with both classes
            item_containers = soup.find_all("div", attrs={"class": lambda x: x and "inzeraty" in x and "flex" in x})

        if not item_containers:
            # Fallback: try just inzeraty
            item_containers = soup.find_all("div", class_="inzeraty")

        if not item_containers:
            # Try alternative selectors for older versions
            item_containers = soup.find_all("div", class_="inzeratMain")

        for container in item_containers:
            try:
                item = self._extract_item(container, category)
                if item:
                    items.append(item)
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue

        return items

    def _extract_item(self, container, category: str) -> Optional[BazosItem]:
        """Extract item details from a container"""

        try:
            # Extract title and URL
            title_link = container.find("a", class_="nadpis")
            if not title_link:
                # Try alternative
                title_link = container.find("a")

            if not title_link:
                return None

            title = title_link.get_text(strip=True)
            item_url = title_link.get("href", "")

            if not item_url.startswith("http"):
                item_url = f"https://{category}.bazos.sk/{item_url}"

            # Extract image
            image_url = None
            img_tag = container.find("img")
            if img_tag:
                image_url = img_tag.get("src", "")
                if image_url and not image_url.startswith("http"):
                    image_url = f"https://bazos.sk{image_url}"

            # Extract description
            description_elem = container.find("div", class_="popis")
            if not description_elem:
                description_elem = container.find("span", class_="popis")

            description = ""
            if description_elem:
                description = description_elem.get_text(strip=True)

            # Extract price
            price = None
            price_elem = container.find("span", class_="cena")
            if not price_elem:
                price_elem = container.find("b")

            if price_elem:
                price = price_elem.get_text(strip=True)

            # Extract location
            location = None
            location_elem = container.find("span", class_="lokality")
            if not location_elem:
                # Try to find location in text
                text_content = container.get_text()
                if "lokalita" in text_content.lower():
                    parts = text_content.split("lokalita")
                    if len(parts) > 1:
                        location = parts[1].split("\n")[0].strip()
            else:
                location = location_elem.get_text(strip=True)

            # Extract date
            date_posted = None
            date_elem = container.find("span", class_="datum")
            if date_elem:
                date_posted = date_elem.get_text(strip=True)

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
