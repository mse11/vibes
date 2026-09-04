"""
Example usage of the Bazos scraper with proper package imports
"""

from scrape_bazos import BazosScraper, HTMLReportGenerator, ImageDownloader
import json


def example_1_simple_search():
    """Example 1: Simple search for NAS in PC category"""
    print("=" * 80)
    print("EXAMPLE 1: Simple PC Search")
    print("=" * 80)

    scraper = BazosScraper()

    # Build the search URL
    url = scraper.build_url(
        topic="pc",
        keyword="nas",
    )
    print(f"URL: {url}\n")

    # Scrape listings
    items = scraper.scrape_listings(
        topic="pc",
        keyword="nas",
        max_pages=1,
    )

    print(f"Found {len(items)} items\n")

    # Display first 3 items
    for item in items[:3]:
        print(f"Title: {item.title}")
        print(f"Price: {item.price}")
        print(f"Location: {item.location}")
        print(f"Description: {item.description[:80]}...")
        print(f"URL: {item.item_url}\n")

    # Save to JSON
    scraper.save_results(items, "example1_results.json")


def example_2_price_range_search():
    """Example 2: Search with price range"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: PC Search with Price Range")
    print("=" * 80)

    scraper = BazosScraper()

    items = scraper.scrape_listings(
        topic="pc",
        keyword="notebook",
        price_from="500",
        price_to="1000",
        max_pages=1,
    )

    print(f"Found {len(items)} notebooks between €500-€1000\n")

    for item in items[:3]:
        print(f"{item.title} - {item.price}")

    scraper.save_results(items, "example2_notebooks.json")


def example_3_location_search():
    """Example 3: Search with location"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Real Estate Search by Location")
    print("=" * 80)

    scraper = BazosScraper()

    items = scraper.scrape_listings(
        topic="reality",
        keyword="byt",
        location="Bratislava",
        radius=10,
        max_pages=1,
    )

    print(f"Found {len(items)} apartments in Bratislava\n")

    for item in items[:3]:
        print(f"{item.title}")
        print(f"  Price: {item.price}")
        print(f"  Location: {item.location}\n")

    scraper.save_results(items, "example3_apartments.json")


def example_4_generate_html_report():
    """Example 4: Generate HTML report with images"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Generate HTML Report")
    print("=" * 80)

    scraper = BazosScraper()

    # Scrape items
    items = scraper.scrape_listings(
        topic="pc",
        keyword="gpu",
        max_pages=1,
    )

    print(f"Found {len(items)} graphics cards\n")

    # Generate HTML report
    generator = HTMLReportGenerator()
    generator.generate_report(
        items=items,
        output_file="example4_report.html",
        topic="pc",
        keyword="gpu",
        include_images=True,
    )

    print("HTML report generated: example4_report.html")


def example_5_download_images_and_report():
    """Example 5: Download images and generate report"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Download Images & Generate Report")
    print("=" * 80)

    scraper = BazosScraper()

    # Scrape items
    items = scraper.scrape_listings(
        topic="pc",
        keyword="monitor",
        max_pages=1,
    )

    print(f"Found {len(items)} monitors\n")

    # Download images
    print("Downloading images...")
    downloader = ImageDownloader(output_dir="bazos_images")
    image_map = downloader.download_all_images(items)
    print(f"Downloaded {len(image_map)} images\n")

    # Generate report with local images
    generator = HTMLReportGenerator()
    generator.generate_report(
        items=items,
        output_file="example5_report_with_images.html",
        topic="pc",
        keyword="monitor",
        include_images=True,
        image_map=image_map,
    )

    print("Report generated: example5_report_with_images.html")


def example_6_multiple_pages():
    """Example 6: Scrape multiple pages"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Scrape Multiple Pages")
    print("=" * 80)

    scraper = BazosScraper()

    items = scraper.scrape_listings(
        topic="auto",
        keyword="skoda",
        price_to="15000",
        max_pages=3,
    )

    print(f"Found {len(items)} Skodas under €15,000\n")

    # Save results
    scraper.save_results(items, "example6_skodas.json")

    # Generate summary
    if items:
        prices = [p for p in [item.price for item in items] if p]
        print(f"Total cars found: {len(items)}")
        print(f"Cars with prices: {len(prices)}")


def example_7_custom_queries():
    """Example 7: Different categories and keywords"""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Various Search Examples")
    print("=" * 80)

    scraper = BazosScraper()

    searches = [
        ("pc", "keyboard", "Computer keyboards"),
        ("elektronika", "phone", "Mobile phones"),
        ("domacnost", "sofa", "Sofas"),
    ]

    all_items = []

    for topic, keyword, description in searches:
        print(f"\nSearching {description}...")
        items = scraper.scrape_listings(
            topic=topic,
            keyword=keyword,
            max_pages=1,
        )
        print(f"Found {len(items)} items")
        all_items.extend(items)

    # Save combined results
    data = {
        "total": len(all_items),
        "searches": len(searches),
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }

    with open("example7_combined.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"\nTotal items found: {len(all_items)}")


if __name__ == "__main__":
    # Run examples
    try:
        example_1_simple_search()
        example_2_price_range_search()
        example_3_location_search()
        example_4_generate_html_report()
        # Uncomment to download images (slower)
        # example_5_download_images_and_report()
        example_6_multiple_pages()
        example_7_custom_queries()

        print("\n" + "=" * 80)
        print("✓ All examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
