"""
Bazos.sk Web Scraper - CORRECTED VERSION (Based on Real HTML)
Scrapes classifieds listings from bazos.sk with descriptions and images
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict
import json
from datetime import datetime
import re


@dataclass
class BazosItemDetails:
    """Represents detailed information fetched from an item's detail page"""

    full_url: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)
    full_description: Optional[str] = None

    def __repr__(self) -> str:
        return f"BazosItemDetails(images={len(self.image_urls)}, desc_len={len(self.full_description) if self.full_description else 0}, url={self.full_url})"


@dataclass
class BazosItem:
    """Represents a single item from bazos.sk"""

    title: str
    price: Optional[str]
    location: Optional[str]
    description: str
    image_url: Optional[str]
    item_url: str
    date_posted: Optional[str] = None
    item_details: BazosItemDetails = field(default_factory=BazosItemDetails)
    category: Optional[str] = None

    @property
    def image_urls(self) -> List[str]:
        """Get all image URLs from details"""
        return self.item_details.image_urls if self.item_details else []

    @property
    def full_description(self) -> Optional[str]:
        """Get full description from details"""
        return self.item_details.full_description if self.item_details else None

    def __repr__(self) -> str:
        return f"BazosItem(title={self.title!r}, price={self.price!r})"


class BazosScraper:
    """Main scraper class for bazos.sk"""

    BASE_URL = "https://{topic}.bazos.sk/"

    def __init__(self, timeout: int = 10, max_retries: int = 3, retry_delay: float = 1.0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
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
        sub_category: Optional[str] = None,
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
            sub_category: Optional subcategory/group within category (e.g., 'predam', 'prenajmu' for reality)

        Returns:
            Full search URL
        """
        # Normalize category to lowercase (website URLs use lowercase)
        category = category.lower()
        base = self.BASE_URL.format(topic=category)

        # If sub_category is provided, include it in the base path
        # e.g., "https://reality.bazos.sk/" becomes "https://reality.bazos.sk/predam/"
        if sub_category:
            sub_category = sub_category.lower().strip("/")

            # Layer 4: Runtime Format Validation
            # Check for invalid characters (only alphanumeric, hyphens, and underscores allowed)
            if not all(c.isalnum() or c in '-_' for c in sub_category):
                raise ValueError(
                    f"Invalid subcategory format: '{sub_category}'. "
                    "Only alphanumeric characters, hyphens, and underscores allowed."
                )

            base = f"{base}{sub_category}/"

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
        sub_category: Optional[str] = None,
    ) -> List[BazosItem]:
        """
        Scrape listings from bazos.sk with OPTIMIZED pagination

        OPTIMIZATION: Uses dynamic next-page detection instead of pre-calculating page count

        Args:
            category: Category
            keyword: Search keyword
            price_from: Minimum price
            price_to: Maximum price
            radius: Search radius
            location: Specific location
            max_pages: Maximum pages to scrape
                      - Normal number (e.g., 5): Stop at page 5
                      - Large number (999999): Scrape all until no next page found
                      - This allows --pages-get all to work without separate get_page_count() call
            sub_category: Optional subcategory/group within category (e.g., 'predam', 'prenajmu' for reality)

        Returns:
            List of BazosItem objects
        """
        items = []

        try:
            url = self.build_url(
                category=category,
                keyword=keyword,
                price_from=price_from,
                price_to=price_to,
                radius=radius,
                location=location,
                sub_category=sub_category,
            )
        except ValueError as e:
            print(f"❌ Error building URL: {e}")
            return []  # Return empty list on format error

        page = 1

        while True:
            # Stop if reached max_pages limit
            if page > max_pages:
                print(f"Reached max_pages limit ({max_pages}), stopping pagination")
                break

            print(f"Scraping page {page}: {url}")

            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                page_items = self._parse_listings(response.text, category)
                items.extend(page_items)

                print(f"Found {len(page_items)} items on page {page}")

                # OPTIMIZATION: Check for next page on THIS response
                # If no next page exists, we've reached the end
                next_page_url = self._get_next_page_url_v2(response.text)
                if not next_page_url:
                    print(f"No next page found, stopping pagination")
                    break

                # Build URL for next page
                if next_page_url.startswith("/"):
                    # Page 2+ style: relative URL with path prefix
                    topic = category.lower()
                    url = f"https://{topic}.bazos.sk{next_page_url}"
                else:
                    # Page 1 style: query parameters only
                    base_url = url.split("&kitx=")[0] if "&kitx=" in url else url
                    url = base_url + next_page_url

                print(f"  Next page URL: {url}")
                page += 1

            except requests.RequestException as e:
                print(f"Error scraping page {page}: {e}")
                break

        return items

    def _get_next_page_url(self, html: str) -> Optional[str]:
        """
        Extract the next page URL from pagination div.strankovani

        Bazos.sk uses JavaScript-based pagination with onclick handlers on <span class="paction"> elements.
        Each span has an onclick that sets form fields:
        - kitx='ne'
        - crp={20, 40, 60, 80, ...} (page offset)

        Args:
            html: HTML content of the page

        Returns:
            Next page URL with correct parameters or None if no next page found
        """
        soup = BeautifulSoup(html, "lxml")

        # Find the pagination div with class "strankovani"
        pagination_div = soup.find("div", class_="strankovani")
        if not pagination_div:
            print("  DEBUG: No pagination div found")
            return None

        print(f"  DEBUG: Pagination HTML: {pagination_div}")

        # Find all span elements with class "paction" (pagination action buttons)
        paction_spans = pagination_div.find_all("span", class_="paction")
        print(f"  DEBUG: Found {len(paction_spans)} paction spans")

        if not paction_spans:
            print("  DEBUG: No paction spans found")
            return None

        # Extract the "Ďalšia" (Next) button - it's usually the last paction span
        # or look for one with text containing "ďalš"
        next_span = None

        # First, try to find the explicit "next" button
        for i, span in enumerate(paction_spans):
            span_text = span.get_text(strip=True)
            onclick = span.get("onclick", "")
            print(f"    paction[{i}]: text='{span_text}' has_onclick={bool(onclick)}")

            if "ďalš" in span_text.lower():
                next_span = span
                print(f"  DEBUG: Found 'next' button at index {i}")
                break

        # If not found, use the last paction span (which should be next)
        if not next_span and paction_spans:
            next_span = paction_spans[-1]
            print(f"  DEBUG: Using last paction span as next")

        if not next_span:
            print("  DEBUG: No next_span selected")
            return None

        # Extract the onclick attribute
        onclick = next_span.get("onclick", "")
        if not onclick:
            print("  DEBUG: No onclick attribute found on next_span")
            return None

        print(f"  DEBUG: onclick='{onclick}'")

        # Parse the crp value from onclick
        # Pattern: document.getElementById('crp').value=20;
        import re
        crp_match = re.search(r"document\.getElementById\('crp'\)\.value=(\d+)", onclick)

        if not crp_match:
            print("  DEBUG: Could not extract crp value from onclick")
            return None

        crp_value = crp_match.group(1)
        print(f"  DEBUG: Found next page with crp={crp_value}")

        # Build the next page URL by modifying the current URL
        # We need to change kitx from 'ano' to 'ne' and add the crp parameter
        # The URL format should be: ?hledat=nas&rubriky=pc&humkreis=25&kitx=ne&crp={value}

        # For now, we'll return a modified URL with the new parameters
        # The scraper will construct it properly with the current base parameters
        return f"&kitx=ne&crp={crp_value}"

    def _get_next_page_url_v2(self, html: str) -> Optional[str]:
        """
        Extract the next page URL from pagination div.strankovani

        Bazos.sk uses TWO different pagination structures:

        Page 1: Uses <span class="paction"> with onclick handlers
        Page 2+: Uses regular <a> tags with href attributes

        Both have a "Ďalšia" (Next) button that we need to extract.

        Args:
            html: HTML content of the page

        Returns:
            Next page URL or None if no next page found
        """
        soup = BeautifulSoup(html, "lxml")

        # Find the pagination div with class "strankovani"
        pagination_div = soup.find("div", class_="strankovani")
        if not pagination_div:
            return None

        # FIRST TRY: Look for <span class="paction"> with onclick (Page 1 style)
        paction_spans = pagination_div.find_all("span", class_="paction")

        if paction_spans:
            print("  DEBUG: Using paction span pagination (Page 1 style)")
            # Find the "Ďalšia" button
            for span in paction_spans:
                span_text = span.get_text(strip=True)
                if "ďalš" in span_text.lower():
                    onclick = span.get("onclick", "")
                    if onclick:
                        # Parse the crp value from onclick
                        import re
                        crp_match = re.search(r"document\.getElementById\('crp'\)\.value=(\d+)", onclick)
                        if crp_match:
                            crp_value = crp_match.group(1)
                            print(f"  DEBUG: Found next page with crp={crp_value}")
                            return f"&kitx=ne&crp={crp_value}"

        # SECOND TRY: Look for regular <a> tags with href (Page 2+ style)
        links = pagination_div.find_all("a", href=True)

        if links:
            print("  DEBUG: Using <a> tag pagination (Page 2+ style)")
            # Find the "Ďalšia" button
            for link in links:
                link_text = link.get_text(strip=True)
                if "ďalš" in link_text.lower():
                    href = link.get("href", "")
                    if href:
                        print(f"  DEBUG: Found next page with href={href}")
                        # Return the href as-is (it's a relative URL like /40/?...)
                        # We'll need to convert it to include the query parameters
                        return href

        print("  DEBUG: No next page found")
        return None

    def get_page_count(
        self,
        category: str,
        keyword: str,
        price_from: Optional[str] = None,
        price_to: Optional[str] = None,
        radius: int = 25,
        location: str = "",
        retry: bool = True,
        sub_category: Optional[str] = None,
    ) -> Optional[Dict]:
        """
        Get page count information by traversing all pages

        Args:
            category: Category
            keyword: Search keyword
            price_from: Minimum price
            price_to: Maximum price
            radius: Search radius
            location: Specific location
            retry: Whether to retry on failure (default: True)
            sub_category: Optional subcategory/group within category (e.g., 'predam', 'prenajmu' for reality)

        Returns:
            Dictionary with page info or None if error after all retries
        """
        import time

        try:
            url = self.build_url(
                category=category,
                keyword=keyword,
                price_from=price_from,
                price_to=price_to,
                radius=radius,
                location=location,
                sub_category=sub_category,
            )
        except ValueError as e:
            print(f"❌ Error building URL: {e}")
            return None  # Return None on format error

        print(f"Traversing pages to find total count...")
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                total_pages = 1
                total_items = 0
                current_url = url

                while True:
                    print(f"  Checking page {total_pages}...")
                    response = self.session.get(current_url, timeout=self.timeout)
                    response.raise_for_status()

                    soup = BeautifulSoup(response.text, "lxml")

                    # Count items on THIS page
                    item_containers = soup.find_all("div", class_="inzeratyflex")
                    items_on_page = len([c for c in item_containers if "listainzerat" not in c.get("class", [])])
                    total_items += items_on_page
                    print(f"    Page {total_pages}: {items_on_page} items (total so far: {total_items})")

                    # Find pagination div
                    pagination_div = soup.find("div", class_="strankovani")
                    if not pagination_div:
                        break

                    # Check if there's a next page
                    next_page_url = self._get_next_page_url_v2(soup.decode())

                    if not next_page_url:
                        # No next page found, we've reached the end
                        break

                    # Prepare URL for next page
                    if next_page_url.startswith("/"):
                        # Page 2+ style: relative URL with path prefix
                        topic = category.lower()
                        current_url = f"https://{topic}.bazos.sk{next_page_url}"
                    else:
                        # Page 1 style: query parameters only
                        base_url = current_url.split("&kitx=")[0] if "&kitx=" in current_url else current_url
                        current_url = base_url + next_page_url

                    total_pages += 1

                    # Safety limit to prevent infinite loops
                    if total_pages > 1000:
                        break

                return {
                    "total_pages": total_pages,
                    "total_items": total_items,
                }

            except requests.exceptions.Timeout as e:
                last_error = e
                if retry and attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    print(f"  ⚠️  Timeout on attempt {attempt}/{self.max_retries}: {e}")
                    print(f"  ⏳ Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"  ❌ Timeout after {attempt} attempt(s): {e}")
                    return None

            except requests.exceptions.RequestException as e:
                last_error = e
                if retry and attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    print(f"  ⚠️  Connection error on attempt {attempt}/{self.max_retries}: {e}")
                    print(f"  ⏳ Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"  ❌ Connection error after {attempt} attempt(s): {e}")
                    return None

            except Exception as e:
                print(f"  ❌ Unexpected error getting page count: {e}")
                return None

        return None

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

            # Convert relative URLs to full URLs immediately
            if not item_url.startswith("http"):
                # Use category subdomain if available, otherwise default to www
                category_domain = category.lower() if category else "www"
                item_url = f"https://{category_domain}.bazos.sk{item_url}"

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
                category=category,
            )

        except Exception as e:
            print(f"Error extracting item details: {e}")
            return None

    def fetch_item_details(self, item: BazosItem) -> BazosItem:
        """
        Fetch detailed information from the item's detail page.
        Extracts all carousel images and full description.

        Args:
            item: BazosItem to enrich with details

        Returns:
            Updated BazosItem with item_details populated
        """
        try:
            # item_url is already a full URL from _extract_item()
            url = item.item_url

            # Try to fetch the page
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            # ========== EXTRACT ALL CAROUSEL IMAGES ==========
            image_urls = []

            # METHOD 1: Look for carousel cells with images (primary method)
            carousel_cells = soup.find_all("div", class_="carousel-cell")
            if carousel_cells:
                for cell in carousel_cells:
                    img = cell.find("img", class_="carousel-cell-image")
                    if img:
                        # Try src first, then data-src for lazy-loaded images
                        img_src = img.get("src") or img.get("data-src")
                        if img_src:
                            # Normalize URL
                            if img_src.startswith("http"):
                                if img_src not in image_urls:
                                    image_urls.append(img_src)
                            elif img_src.startswith("/"):
                                full_url = f"https://www.bazos.sk{img_src}"
                                if full_url not in image_urls:
                                    image_urls.append(full_url)

            # METHOD 2: ALWAYS look for flinavigace (thumbnail gallery) - extracts ALL images
            # NOTE: This runs regardless of METHOD 1 results to ensure we get all available images
            flinavigace_div = soup.find("div", class_="flinavigace")
            if flinavigace_div:
                thumbnails = flinavigace_div.find_all("img", class_="obrazekflithumb")
                if thumbnails:
                    print(f"    Found {len(thumbnails)} thumbnails in flinavigace gallery")
                    for thumb in thumbnails:
                        # Extract thumbnail URL
                        thumb_src = thumb.get("src") or thumb.get("data-src")
                        if thumb_src:
                            # Convert thumbnail URL (img/Nt/) to full-size (img/N/)
                            # Pattern: /img/1t/763/195144763.jpg → /img/1/763/195144763.jpg
                            # Replace pattern like "1t/" with "1/"
                            import re as regex_module
                            img_src = regex_module.sub(r'/img/(\d+)t/', r'/img/\1/', thumb_src)

                            if img_src.startswith("http"):
                                if img_src not in image_urls:
                                    image_urls.append(img_src)
                                    print(f"      Added: {img_src}")
                            elif img_src.startswith("/"):
                                full_url = f"https://www.bazos.sk{img_src}"
                                if full_url not in image_urls:
                                    image_urls.append(full_url)
                                    print(f"      Added: {full_url}")

            # METHOD 3: Fallback - look for all img tags with src containing bazos
            if not image_urls:
                all_imgs = soup.find_all("img", src=True)
                for img in all_imgs:
                    src = img.get("src") or img.get("data-src")
                    # Filter to actual product images (from bazos.sk or www.bazos.sk)
                    if src and "bazos.sk" in src and ".jpg" in src.lower():
                        if src not in image_urls:  # Avoid duplicates
                            if src.startswith("http"):
                                image_urls.append(src)
                            elif src.startswith("/"):
                                full_url = f"https://www.bazos.sk{src}"
                                if full_url not in image_urls:
                                    image_urls.append(full_url)

            if image_urls and not item.image_url:
                # Update primary image if not set
                item.image_url = image_urls[0]

            # ========== EXTRACT FULL DESCRIPTION ==========
            # Look for detailed description in div.popisdetail or similar
            full_description = None

            # Try to find popisdetail div
            desc_div = soup.find("div", class_="popisdetail")
            if desc_div:
                # Replace <br> tags with newlines to preserve formatting
                import re as regex_module
                html_str = str(desc_div)
                # Replace <br>, <br/>, <br /> with newlines
                html_str = regex_module.sub(r'<br\s*/?>', '\n', html_str, flags=regex_module.IGNORECASE)
                # Remove HTML tags
                clean_text = regex_module.sub(r'<[^>]+>', '', html_str)
                # Clean up excessive whitespace while preserving newlines
                clean_text = regex_module.sub(r'\n\s*\n', '\n', clean_text)  # Remove multiple blank lines
                clean_text = regex_module.sub(r'[ \t]+', ' ', clean_text)    # Collapse spaces/tabs on same line
                full_description = clean_text.strip()

            # Fallback: if no popisdetail found, use the item's description
            if not full_description:
                full_description = item.description

            # ========== CREATE ITEM_DETAILS OBJECT ==========
            item.item_details = BazosItemDetails(
                image_urls=image_urls,
                full_description=full_description,
                full_url=url,
            )

            print(f"  ✓ Fetched details for: {item.title[:50]}...")
            print(f"    - Found {len(image_urls)} image(s)")
            print(f"    - Full description length: {len(full_description) if full_description else 0} chars")

            return item

        except Exception as e:
            print(f"  ⚠ Error fetching details for {item.item_url}: {e}")
            # Return item with empty details but still store the full URL
            # Reconstruct full URL in case of error
            full_url = item.item_url
            if not full_url.startswith("http"):
                category = item.category.lower() if item.category else "www"
                full_url = f"https://{category}.bazos.sk{full_url}"
            item.item_details = BazosItemDetails(full_url=full_url)
            return item

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

    def get_subcategories(self, category: str) -> Dict[str, str]:
        """
        Fetch sub-categories for a given category from the category page.
        Sub-categories are found in <div class="barvaleva"> with <a> tags.

        Args:
            category: Category code (e.g., 'pc', 'auto', 'reality')

        Returns:
            Dictionary mapping subcategory paths to names, or empty dict if fetch fails

        Note:
            Includes retry logic with exponential backoff for timeout errors.
            Will retry up to max_retries times before giving up.
        """
        import time
        from requests.exceptions import Timeout, ConnectionError

        category = category.lower()
        url = f"https://{category}.bazos.sk/"
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")
                subcategories = {}

                # Find the barvaleva div containing subcategories
                barvaleva_div = soup.find("div", class_="barvaleva")

                if not barvaleva_div:
                    # No subcategories found for this category
                    return {}

                # Extract all links from the barvaleva div
                links = barvaleva_div.find_all("a", href=True)

                for link in links:
                    href = link.get("href", "").strip()
                    text = link.get_text(strip=True)

                    # Skip empty values
                    if href and text:
                        # Normalize href to extract just the subcategory path
                        # Can be absolute URL (https://...) or relative (/subcategory/)
                        if href.startswith("http"):
                            # Extract just the path after the domain
                            # e.g., "https://foto.bazos.sk/" → "foto" (different domain)
                            # or "https://pc.bazos.sk/notebook/" → "notebook"
                            from urllib.parse import urlparse
                            parsed = urlparse(href)
                            path = parsed.path.strip("/")
                            # If it's a different domain, use the domain name as key
                            if parsed.netloc != f"{category}.bazos.sk":
                                # Different domain, extract category from domain
                                domain_category = parsed.netloc.split(".")[0]
                                subcategories[domain_category] = text
                            else:
                                # Same domain, use path
                                if path:
                                    subcategories[path] = text
                        else:
                            # Relative URL - clean up the path
                            path = href.strip("/")
                            if path:
                                subcategories[path] = text

                return subcategories

            except (Timeout, ConnectionError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    print(f"  ⚠️  Timeout on attempt {attempt}/{self.max_retries} for '{category}', retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    print(f"  ❌ Failed to fetch subcategories for '{category}' after {attempt} attempt(s): {e}")

            except Exception as e:
                print(f"Error fetching subcategories for '{category}': {e}")
                # Return empty dict on error
                return {}

        # All retries exhausted
        raise last_error if last_error else Exception(f"Failed to fetch subcategories for '{category}'")

    def get_subcategories_grouped(self, category: str) -> Dict:
        """
        Fetch sub-categories organized by groups (for categories like 'reality').

        Some categories have grouped subcategories:
        - Reality (reality) has: Predaj (Sale) and Prenájom (Rent) groups
        - Each group contains its own subcategories

        Structure of <div class="menuleft">:
            <div class="nadpismenu"><a>Group Name</a></div>
            <div class="barvalmenu">
                <div class="barvaleva">
                    <a href="/group/subcat/">Subcategory</a>
                </div>
            </div>

        Args:
            category: Category code (e.g., 'reality', 'auto')

        Returns:
            Dictionary with grouped structure:
            {
                "group_id": {
                    "name": "Group Name",
                    "url": "/group/",
                    "subcategories": {
                        "subcat": "Subcategory Name",
                        ...
                    }
                },
                ...
            }

            Returns flat dict if no groups found (falls back to get_subcategories behavior)
        """
        import time
        from requests.exceptions import Timeout, ConnectionError

        category = category.lower()
        url = f"https://{category}.bazos.sk/"
        attempt = 0
        last_error = None

        while attempt < self.max_retries:
            attempt += 1
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")
                grouped_categories = {}

                # Find the menuleft div (contains grouped subcategories)
                menuleft_div = soup.find("div", class_="menuleft")

                if not menuleft_div:
                    # No grouped structure, return empty and caller will use flat structure
                    return {}

                # Find all group headers (nadpismenu)
                group_headers = menuleft_div.find_all("div", class_="nadpismenu")

                if not group_headers:
                    # No groups found
                    return {}

                # For each group header, find the associated subcategories
                for i, group_header in enumerate(group_headers):
                    # Get group name and URL from the link
                    group_link = group_header.find("a", href=True)
                    if not group_link:
                        continue

                    group_name = group_link.get_text(strip=True)
                    group_url = group_link.get("href", "").strip()

                    if not group_name or not group_url:
                        continue

                    # Extract group ID from URL
                    # e.g., "/predam/" → "predam"
                    group_id = group_url.strip("/")

                    # Find the associated barvalmenu - it should be the next sibling
                    barvalmenu = group_header.find_next_sibling("div", class_="barvalmenu")

                    if not barvalmenu:
                        continue

                    # IMPROVED: Find ALL <div class="barvaleva"> within this barvalmenu
                    # Some categories may have multiple barvaleva sections in one barvalmenu
                    barvaleva_divs = barvalmenu.find_all("div", class_="barvaleva")

                    if not barvaleva_divs:
                        continue

                    # Extract subcategories for this group
                    subcategories = {}

                    # Process all barvaleva divs in this group
                    for barvaleva in barvaleva_divs:
                        links = barvaleva.find_all("a", href=True)

                        for link in links:
                            href = link.get("href", "").strip()
                            text = link.get_text(strip=True)

                            if not href or not text:
                                continue

                            # Parse the subcategory path
                            if href.startswith("http"):
                                # Absolute URL
                                from urllib.parse import urlparse
                                parsed = urlparse(href)
                                path = parsed.path.strip("/")

                                if parsed.netloc != f"{category}.bazos.sk":
                                    # Different domain (e.g., sluzby.bazos.sk from reality)
                                    # Skip external domains
                                    continue
                                else:
                                    # Same domain - extract just the subcat part
                                    # e.g., "/predam/byt/" → "byt"
                                    parts = path.split("/")
                                    if len(parts) >= 2:
                                        subcat_id = parts[1]  # Skip group, get subcat
                                        if subcat_id not in subcategories:  # Avoid duplicates
                                            subcategories[subcat_id] = text
                            else:
                                # Relative URL
                                # e.g., "/predam/byt/" or "/ubytovanie/" (external)
                                path = href.strip("/")

                                # Check if it's a path with group prefix
                                parts = path.split("/")
                                if len(parts) >= 2:
                                    # Has group prefix like "/predam/byt/"
                                    subcat_id = parts[1]
                                    if subcat_id not in subcategories:  # Avoid duplicates
                                        subcategories[subcat_id] = text
                                elif len(parts) == 1 and parts[0]:
                                    # No group prefix (external), use as-is
                                    if parts[0] not in subcategories:
                                        subcategories[parts[0]] = text

                    if subcategories:
                        grouped_categories[group_id] = {
                            "name": group_name,
                            "url": group_url,
                            "subcategories": subcategories
                        }

                return grouped_categories

            except (Timeout, ConnectionError) as e:
                last_error = e
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** (attempt - 1))
                    print(f"  ⚠️  Timeout on attempt {attempt}/{self.max_retries} for grouped categories in '{category}'...")
                    time.sleep(wait_time)
                else:
                    print(f"  ❌ Failed to fetch grouped categories for '{category}': {e}")

            except Exception as e:
                print(f"Error fetching grouped categories for '{category}': {e}")
                return {}

        # All retries exhausted
        return {}

    def get_all_categories_with_subcategories(self) -> Dict[str, Dict[str, str]]:
        """
        Fetch all categories and their subcategories.

        Returns:
            Dictionary mapping category codes to dictionaries of subcategories
            Structure: {"pc": {"notebook": "Notebooky", "monitor": "LCD monitory", ...}, ...}
        """
        try:
            categories = self.get_categories()
            categories_with_subs = {}

            for category_code in categories:
                subcategories = self.get_subcategories(category_code)
                categories_with_subs[category_code] = subcategories

            return categories_with_subs

        except Exception as e:
            print(f"Error fetching all categories with subcategories: {e}")
            return {}

    def save_results(self, items: List[BazosItem], output_file: str) -> None:
        """Save results to JSON file"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "total_items": len(items),
            "items": [asdict(item) for item in items],
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
    scraper.save_results(items, "bazos_results_pc_nas.json")


if __name__ == "__main__":
    main()
