# Bazos.sk Web Scraper

A powerful, production-ready Python scraper for extracting classifieds listings from [bazos.sk](https://bazos.sk) with support for descriptions, images, and comprehensive filtering.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [URL Structure](#url-structure)
- [Output Formats](#output-formats)
- [Project Structure](#project-structure)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)
- [Categories](#categories)
- [Troubleshooting](#troubleshooting)

## Features

🔍 **Full Search Capability** - Search any category with keywords, price ranges, and locations  
🖼️ **Image Extraction** - Download and manage product images  
📊 **Multiple Export Formats** - JSON, CSV, and formatted table output  
📱 **Responsive HTML Reports** - Beautiful, mobile-friendly reports with statistics  
⚡ **Fast & Efficient** - Optimized scraping with error handling  
🛡️ **Robust Error Handling** - Handles timeouts, missing elements, and network issues  
📍 **Location-based Search** - Filter by location and search radius  
💰 **Price Filtering** - Search within specific price ranges  
🧪 **Complete Test Suite** - 35+ unit tests included  
🐍 **Both CLI & Python API** - Use via command line or import as a package  

## Installation

### Requirements

- Python 3.9+
- uv package manager (or pip)
- ~20MB disk space for dependencies

### Using uv (Recommended)

```bash
# Navigate to project directory
cd D:\MSE\GIT\_MSE_git\vibes\html\scrape_bazos

# Install dependencies
uv sync

# Optional: Install with development tools
uv sync --extra dev
```

### Using pip

```bash
pip install requests beautifulsoup4 lxml pillow
```

## Quick Start

### Quick Setup

```bash
# Install dependencies
uv sync

# Start scraping!
scrape-bazos search --topic pc --keyword "nas"
```

### Basic Search

```bash
# Search for NAS in PC category
scrape-bazos search --topic pc --keyword "nas"

# With price range
scrape-bazos search --topic pc --keyword "notebook" --price-from 500 --price-to 1000

# Real estate search
scrape-bazos search --topic reality --keyword "byt" --location "Bratislava" --radius 10
```

### Python API

```python
from scrape_bazos import BazosScraper

scraper = BazosScraper()
items = scraper.scrape_listings(
    topic="pc",
    keyword="nas",
    max_pages=1
)

for item in items:
    print(f"{item.title}: {item.price}")

# Save results
scraper.save_results(items, "results.json")
```

## Usage

### Command Line Interface

The CLI provides multiple commands for different operations:

```bash
# Main search command
scrape-bazos search [OPTIONS]

# Show available categories
scrape-bazos categories

# Run example search
scrape-bazos example

# Show project information
scrape-bazos info

# View detailed help
scrape-bazos search --help
```

### Search Command Options

```bash
scrape-bazos search [OPTIONS]

Options:
  --topic TEXT            Category (required, e.g., pc, auto, reality)
  --keyword TEXT          Search keyword (required)
  --price-from TEXT       Minimum price (optional)
  --price-to TEXT         Maximum price (optional)
  --location TEXT         Specific location (optional)
  --radius INT            Search radius in km (default: 25)
  --pages INT             Number of pages to scrape (default: 1)
  --output TEXT           Output filename (default: bazos_results.json)
  --format TEXT           Output format: json, csv, table (default: json)
  --display               Display results in console
  --timeout INT           Request timeout seconds (default: 10)
  --help                  Show help message
```

### Example Commands

```bash
# PC Components
scrape-bazos search --topic pc --keyword "ssd" --price-from 50 --price-to 200

# Used Cars
scrape-bazos search --topic auto --keyword "skoda" --price-to 15000 --pages 3

# Real Estate
scrape-bazos search --topic reality --keyword "byt" --location "Bratislava" --radius 10

# Electronics with console display
scrape-bazos search --topic elektronika --keyword "iphone" --pages 2 --display

# Save as CSV
scrape-bazos search --topic pc --keyword "monitor" --format csv --output monitors.csv

# Quick example search
scrape-bazos example

# View all available categories
scrape-bazos categories

# Show project information
scrape-bazos info
```

## URL Structure

The scraper constructs URLs in the following format:

```
https://{topic}.bazos.sk/?hledat={keyword}&rubriky={topic}&humkreis={radius}&cenaod={price_from}&cenado={price_to}&kitx=ano
```

**Example:**
```
https://pc.bazos.sk/?hledat=nas&rubriky=pc&humkreis=25&cenaod=&cenado=&kitx=ano
```

**URL Parameters:**
- `hledat` - Search keyword
- `rubriky` - Category/topic
- `hlokalita` - Location (optional)
- `humkreis` - Search radius in km (default: 25)
- `cenaod` - Price from (optional)
- `cenado` - Price to (optional)
- `kitx` - Filter type ("ano" = yes)
- `page` - Page number (for pagination)

## Output Formats

### JSON (Default)

Structured data format, best for programmatic use:

```json
{
  "timestamp": "2026-09-03T12:00:00",
  "total_items": 42,
  "items": [
    {
      "title": "QNAP NAS 4 Bay",
      "price": "€299",
      "location": "Bratislava",
      "description": "Used QNAP TS-451 NAS server...",
      "image_url": "https://...",
      "item_url": "https://pc.bazos.sk/...",
      "date_posted": "2 days ago"
    }
  ]
}
```

### CSV

Comma-separated values with headers for spreadsheet analysis:

```
title,price,location,description,image_url,item_url,date_posted
```

### HTML Report

Beautiful responsive report with:
- Search statistics dashboard
- Thumbnail image previews
- Price highlights
- Direct links to original listings
- Mobile-friendly design

### Table (Text)

Formatted text output for console viewing.

## Project Structure

```
scrape_bazos/
├── scrape_bazos/                 Package directory
│   ├── __init__.py              Package initialization
│   ├── scraper.py               Core scraping engine
│   ├── cli.py                   Command-line interface
│   └── reporter.py              HTML reports & image downloader
├── tests/                        Test suite
│   ├── __init__.py
│   ├── test_scraper.py          Scraper tests (15+)
│   └── test_reporter.py         Reporter tests (10+)
├── example.py                   Usage examples (7 complete examples)
├── pyproject.toml               Project configuration
├── .gitignore                   Git ignore rules
└── README.md                    This file
```

### Module Overview

**scraper.py** - Core scraping module
- `BazosItem` - Data class for listings
- `BazosScraper` - Main scraper with methods:
  - `build_url()` - Construct search URLs
  - `scrape_listings()` - Main scraping function
  - `save_results()` - Export to JSON

**cli.py** - Command-line interface
- ArgumentParser-based CLI
- Support for all search parameters
- Multiple output formats
- Console display option

**reporter.py** - Advanced features
- `ImageDownloader` - Download images in batch
- `HTMLReportGenerator` - Generate beautiful HTML reports

## Data Extracted

For each listing, the scraper extracts:

```python
BazosItem(
    title: str,              # Product name
    price: Optional[str],    # Listed price
    location: Optional[str], # Seller's location
    description: str,        # Full description
    image_url: Optional[str],# Product image link
    item_url: str,          # Direct link to listing
    date_posted: Optional[str] # When posted
)
```

## Examples

### Example 1: Simple Search

```python
from scrape_bazos import BazosScraper

scraper = BazosScraper()
items = scraper.scrape_listings(topic="pc", keyword="nas")

for item in items[:3]:
    print(f"{item.title}: {item.price}")
```

### Example 2: Price Range Search

```python
items = scraper.scrape_listings(
    topic="pc",
    keyword="notebook",
    price_from="500",
    price_to="1000",
    max_pages=2
)
```

### Example 3: Location-based Search

```python
items = scraper.scrape_listings(
    topic="reality",
    keyword="byt",
    location="Bratislava",
    radius=10
)
```

### Example 4: Generate HTML Report

```python
from scrape_bazos import HTMLReportGenerator

scraper = BazosScraper()
items = scraper.scrape_listings(topic="pc", keyword="gpu", max_pages=1)

generator = HTMLReportGenerator()
generator.generate_report(
    items=items,
    output_file="gpu_report.html",
    topic="pc",
    keyword="gpu"
)
```

### Example 5: Download Images & Generate Report

```python
from scrape_bazos import ImageDownloader, HTMLReportGenerator

scraper = BazosScraper()
items = scraper.scrape_listings(topic="pc", keyword="monitor")

# Download images
downloader = ImageDownloader("images")
image_map = downloader.download_all_images(items)

# Generate report with local images
generator = HTMLReportGenerator()
generator.generate_report(
    items=items,
    output_file="monitors.html",
    topic="pc",
    keyword="monitor",
    image_map=image_map
)
```

### Run All Examples

```bash
python example.py
```

This runs 7 complete working examples covering all features.

## API Reference

### BazosScraper

```python
from scrape_bazos import BazosScraper

scraper = BazosScraper(timeout=10)  # timeout in seconds

# Build URL
url = scraper.build_url(
    topic="pc",
    keyword="ssd",
    price_from="50",
    price_to="200",
    radius=25,
    location="Bratislava"
)

# Scrape listings
items = scraper.scrape_listings(
    topic="pc",
    keyword="ssd",
    price_from="50",
    price_to="200",
    radius=25,
    location="Bratislava",
    max_pages=3
)

# Save to JSON
scraper.save_results(items, "results.json")
```

### ImageDownloader

```python
from scrape_bazos import ImageDownloader

downloader = ImageDownloader(output_dir="images")

# Download single image
local_path = downloader.download_image(
    url="https://example.com/image.jpg",
    filename="item_001.jpg"
)

# Download all from items
image_map = downloader.download_all_images(items)
```

### HTMLReportGenerator

```python
from scrape_bazos import HTMLReportGenerator

generator = HTMLReportGenerator()

generator.generate_report(
    items=items,
    output_file="report.html",
    topic="pc",
    keyword="ssd",
    include_images=True,
    image_map=image_map
)
```

### BazosItem

```python
# Access item data
item.title
item.price
item.location
item.description
item.image_url
item.item_url
item.date_posted

# Convert to dictionary
item_dict = item.to_dict()

# String representation
print(item)  # BazosItem(title=..., price=...)
```

## Advanced Features

### Custom Headers

```python
scraper = BazosScraper()
scraper.session.headers.update({
    "User-Agent": "Your-Custom-User-Agent"
})
```

### Filter Results Programmatically

```python
items = scraper.scrape_listings(topic="pc", keyword="ssd")

# Filter items with price
priced_items = [item for item in items if item.price]

# Filter by location
bratislava_items = [item for item in items if "Bratislava" in (item.location or "")]

# Filter by description length
detailed_items = [item for item in items if len(item.description) > 100]
```

### Combine Multiple Searches

```python
all_items = []
for keyword in ["ssd", "hdd", "nvme"]:
    items = scraper.scrape_listings(topic="pc", keyword=keyword, max_pages=1)
    all_items.extend(items)

scraper.save_results(all_items, "storage_devices.json")
```

## Categories

Popular topics you can search:

| Topic | Description |
|-------|-------------|
| pc | Computers & IT |
| auto | Automobiles |
| reality | Real Estate |
| elektronika | Electronics |
| domacnost | Household Items |
| knihy | Books |
| oblecenie | Clothing |
| sport | Sports Equipment |
| hudka | Music |
| byty | Apartments (Real Estate) |
| motocykle | Motorcycles |
| bicykle | Bicycles |

## Testing

Run the test suite:

```bash
# All tests
uv run pytest tests/ -v

# With coverage report
uv run pytest tests/ --cov=scrape_bazos

# Specific test file
uv run pytest tests/test_scraper.py -v

# Specific test
uv run pytest tests/test_scraper.py::TestBazosScraper::test_build_url_basic -v
```

The project includes 35+ unit tests covering:
- URL building with various parameters
- HTML parsing and item extraction
- Report generation
- Image downloading
- Error handling

## Troubleshooting

### "ModuleNotFoundError: No module named 'scrape_bazos'"

**Solution:** Make sure you've run `uv sync` and are in the project directory.

```bash
uv sync
```

### "No items found"

**Possible causes:**
- Misspelled topic or keyword
- Category doesn't exist on bazos.sk
- Price filters too restrictive
- No listings match your criteria

**Solutions:**
- Check spelling
- Try simpler keywords
- Remove price filters
- Visit bazos.sk manually to verify listings exist

### "Connection timeout"

**Solution:** Increase the timeout:

```bash
python -m scrape_bazos.cli --topic pc --keyword "ssd" --timeout 20
```

Or in Python:

```python
scraper = BazosScraper(timeout=20)
```

### "Images not loading in HTML report"

**Solutions:**
1. Download images locally:
```python
downloader = ImageDownloader()
image_map = downloader.download_all_images(items)
generator.generate_report(items, "report.html", image_map=image_map)
```

2. Ensure internet connection for remote images

3. Check if image URLs are broken

### "Too many requests / Rate limit"

**Solution:** Add delays between requests or reduce page count:

```bash
python -m scrape_bazos.cli --topic pc --keyword "ssd" --pages 1
```

### Import errors after migration

If you get import errors after moving to the flat structure:

1. Delete `.venv/` folder
2. Run `uv sync` again
3. Verify `scrape_bazos/` directory exists at project root
4. Check `scrape_bazos/__init__.py` exists

## Development Setup

Install development tools:

```bash
uv sync --extra dev
```

This includes:
- pytest - Testing framework
- pytest-cov - Coverage reports
- black - Code formatter
- ruff - Linter

Format code:

```bash
uv run black scrape_bazos/ tests/
```

Run linter:

```bash
uv run ruff check scrape_bazos/ tests/
```

## Performance Tips

1. **Use reasonable page limits** - Each page may contain 20-50 items
2. **Skip image downloads for speed** - Images are optional
3. **Adjust timeout for slow connections** - Use `--timeout 20`
4. **Batch requests** - Search multiple categories in one run

## Legal Notice

- Respect bazos.sk's Terms of Service
- Don't overload servers with excessive requests
- Use reasonable delays between requests
- Check website's robots.txt for scraping guidelines
- This tool is for educational purposes

## Contributing

Contributions are welcome! Areas for improvement:

- Additional output formats (Excel, SQLite)
- Proxy support
- Async scraping for speed
- Advanced filtering options
- GUI interface

## License

MIT License - Feel free to use for personal projects

## Support & Documentation

- **Quick examples:** See `example.py`
- **CLI help:** Run `python -m scrape_bazos.cli --help`
- **Test suite:** Run `uv run pytest tests/ -v`
- **Code:** Check docstrings in source files

## Version History

- **v0.1.0** (2026-09-03) - Initial release with full scraping, reports, and tests

---

**Happy scraping!** 🚀

For issues or questions, check the examples and test suite for working code samples.
