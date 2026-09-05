"""
CLI interface for Bazos.sk scraper using Click
"""

import click
import csv
import json
from pathlib import Path
from .scraper import BazosScraper


@click.group()
@click.version_option(version="0.1.0", prog_name="scrape-bazos")
def cli():
    """
    🔍 Bazos.sk Web Scraper

    A powerful scraper for extracting classifieds listings from bazos.sk
    with support for descriptions, images, and comprehensive filtering.
    """
    pass


@cli.command()
@click.option(
    "--category",
    required=True,
    help="Category (e.g., pc, auto, reality, elektronika, domacnost, knihy, oblecenie, sport)",
)
@click.option(
    "--keyword",
    required=True,
    help="Search keyword (e.g., nas, notebook, skoda)",
)
@click.option(
    "--price-from",
    default=None,
    help="Minimum price (optional)",
)
@click.option(
    "--price-to",
    default=None,
    help="Maximum price (optional)",
)
@click.option(
    "--location",
    default="",
    help="Specific location (optional)",
)
@click.option(
    "--radius",
    default=25,
    type=int,
    help="Search radius in km (default: 25)",
)
@click.option(
    "--pages-get",
    default="1",
    type=str,
    help="Number of pages to scrape or 'all' (default: 1)",
)
@click.option(
    "--output",
    default="bazos_results.json",
    type=str,
    help="Output filename (default: bazos_results.json)",
)
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "table"]),
    default="json",
    help="Output format (default: json)",
)
@click.option(
    "--timeout",
    default=10,
    type=int,
    help="Request timeout in seconds (default: 10)",
)
@click.option(
    "--display",
    is_flag=True,
    help="Display results in console",
)
@click.option(
    "--pages-count",
    is_flag=True,
    help="Only count available pages without scraping",
)
@click.option(
    "--details-all",
    is_flag=True,
    help="Fetch detailed information from each item page (images carousel, full descriptions)",
)
def search(category, keyword, price_from, price_to, location, radius, pages_get, output, format, timeout, display, pages_count, details_all):
    """
    Search for listings on bazos.sk

    Examples:

        scrape-bazos search --category pc --keyword "nas" --pages-count

        scrape-bazos search --category pc --keyword "nas" --pages-get 2

        scrape-bazos search --category pc --keyword "nas" --pages-get all

        scrape-bazos search --category pc --keyword "notebook" --price-from 500 --price-to 1000

        scrape-bazos search --category auto --keyword "skoda" --price-to 15000 --pages-get 3

        scrape-bazos search --category reality --keyword "byt" --location "Bratislava" --radius 10

        scrape-bazos search --category pc --keyword "nas" --pages-get 2 --details-all

        scrape-bazos search --category pc --keyword "nas" --details-all --display
    """
    try:
        # Create scraper
        scraper = BazosScraper(timeout=timeout)

        # Build URL for reference
        url = scraper.build_url(
            category=category,
            keyword=keyword,
            price_from=price_from,
            price_to=price_to,
            radius=radius,
            location=location,
        )
        click.echo(f"🔍 Search URL: {url}\n")

        # If only counting pages, fetch first page and show page info
        if pages_count:
            click.echo("📊 Checking available pages...")
            page_info = scraper.get_page_count(
                category=category,
                keyword=keyword,
                price_from=price_from,
                price_to=price_to,
                radius=radius,
                location=location,
            )

            if page_info:
                click.echo(f"\n📄 Page Information:")
                click.echo(f"   Total pages: {page_info['total_pages']}")
                click.echo(f"   Total items: {page_info['total_items']}\n")
            else:
                click.echo("❌ Could not retrieve page information")

            raise SystemExit(0)

        # Handle pages_get parameter - can be "all" or a number
        if pages_get.lower() == "all":
            click.echo("📊 Detecting total pages...")
            page_info = scraper.get_page_count(
                category=category,
                keyword=keyword,
                price_from=price_from,
                price_to=price_to,
                radius=radius,
                location=location,
            )

            if page_info:
                pages_get_int = page_info['total_pages']
                click.echo(f"Found {pages_get_int} pages total\n")
            else:
                click.echo("❌ Could not detect total pages, defaulting to 1 page")
                pages_get_int = 1
        else:
            try:
                pages_get_int = int(pages_get)
            except ValueError:
                click.echo(f"❌ Invalid value for --pages-get: '{pages_get}' (use a number or 'all')", err=True)
                raise SystemExit(1)

        # Scrape listings
        click.echo(f"📡 Scraping {pages_get_int} page(s)...")
        items = scraper.scrape_listings(
            category=category,
            keyword=keyword,
            price_from=price_from,
            price_to=price_to,
            radius=radius,
            location=location,
            max_pages=pages_get_int,
        )

        click.echo(f"\n✅ Found {len(items)} items\n")

        # Fetch detailed information if requested
        if details_all:
            click.echo("📋 Fetching detailed information for all items...")
            for i, item in enumerate(items, 1):
                click.echo(f"  [{i}/{len(items)}] {item.title[:60]}...", nl=False)
                click.echo("\r", nl=False)
                scraper.fetch_item_details(item)
            click.echo("\n✅ Details fetched for all items\n")

        # Display in console if requested
        if display:
            for i, item in enumerate(items, 1):
                click.echo(f"\n{'='*80}")
                click.echo(f"[{i}/{len(items)}] {item.title}")
                click.echo(f"{'='*80}")
                click.echo(f"Price:       {item.price or 'N/A'}")
                click.echo(f"Location:    {item.location or 'N/A'}")
                click.echo(f"Date:        {item.date_posted or 'N/A'}")
                click.echo(f"URL:         {item.item_url}")
                if item.image_url:
                    click.echo(f"Image:       {item.image_url}")
                if item.image_urls and details_all:
                    click.echo(f"All Images:  {len(item.image_urls)} found")
                    for j, img_url in enumerate(item.image_urls[:5], 1):
                        click.echo(f"  [{j}] {img_url}")
                    if len(item.image_urls) > 5:
                        click.echo(f"  ... and {len(item.image_urls) - 5} more")
                click.echo(f"\nDescription:\n{item.description}\n")
                if item.full_description and details_all and item.full_description != item.description:
                    click.echo(f"Full Description:\n{item.full_description}\n")

        # Save results
        if format == "json":
            scraper.save_results(items, output)
        elif format == "csv":
            _save_as_csv(items, output)
        elif format == "table":
            _save_as_table(items, output)

        click.echo(f"💾 Results saved to: {click.style(output, bold=True)}")
        click.echo(f"📊 Results contain: {click.style(str(len(items)), bold=True)} items")

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Scraping interrupted by user")
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
def categories():
    """
    Show available categories fetched from bazos.sk
    """
    try:
        click.echo("📂 Fetching available categories from bazos.sk...\n")
        scraper = BazosScraper()
        categories_list = scraper.get_categories()

        if not categories_list:
            click.echo("❌ No categories found. Unable to fetch from bazos.sk.", err=True)
            raise SystemExit(1)

        click.echo("📂 Available Categories:\n")
        for topic, description in sorted(categories_list.items()):
            click.echo(f"  {click.style(topic.ljust(15), fg='cyan')} → {description}")
        click.echo(f"\n✅ Found {len(categories_list)} categories")
        click.echo()

    except Exception as e:
        click.echo(f"❌ Error fetching categories: {e}", err=True)
        raise SystemExit(1)


def _save_as_csv(items, output_file: str) -> None:
    """Save items as CSV"""
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        if not items:
            return

        fieldnames = [
            "title",
            "price",
            "location",
            "description",
            "image_url",
            "image_urls",
            "full_description",
            "item_url",
            "date_posted",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for item in items:
            row = {
                "title": item.title,
                "price": item.price,
                "location": item.location,
                "description": item.description,
                "image_url": item.image_url,
                "image_urls": json.dumps(item.image_urls) if item.image_urls else "",
                "full_description": item.full_description or "",
                "item_url": item.item_url,
                "date_posted": item.date_posted,
            }
            writer.writerow(row)


def _save_as_table(items, output_file: str) -> None:
    """Save items as formatted table text"""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("BAZOS.SK SCRAPE RESULTS\n")
        f.write("=" * 150 + "\n\n")

        for i, item in enumerate(items, 1):
            f.write(f"\n{'='*80}\n")
            f.write(f"[{i}] {item.title}\n")
            f.write(f"{'='*80}\n")
            f.write(f"Price:       {item.price or 'N/A'}\n")
            f.write(f"Location:    {item.location or 'N/A'}\n")
            f.write(f"Date:        {item.date_posted or 'N/A'}\n")
            f.write(f"URL:         {item.item_url}\n")
            if item.image_url:
                f.write(f"Image:       {item.image_url}\n")
            if item.image_urls:
                f.write(f"\nAll Images ({len(item.image_urls)} total):\n")
                for j, img_url in enumerate(item.image_urls, 1):
                    f.write(f"  [{j}] {img_url}\n")
            f.write(f"\nDescription:\n{item.description}\n")
            if item.full_description and item.full_description != item.description:
                f.write(f"\nFull Description:\n{item.full_description}\n")

        f.write("\n" + "=" * 150 + "\n")
        f.write(f"Total items: {len(items)}\n")


if __name__ == "__main__":
    cli()
