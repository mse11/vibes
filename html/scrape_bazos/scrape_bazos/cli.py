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
    "--topic",
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
    "--pages",
    default=1,
    type=int,
    help="Number of pages to scrape (default: 1)",
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
def search(topic, keyword, price_from, price_to, location, radius, pages, output, format, timeout, display):
    """
    Search for listings on bazos.sk

    Examples:

        scrape-bazos search --topic pc --keyword "nas"

        scrape-bazos search --topic pc --keyword "notebook" --price-from 500 --price-to 1000

        scrape-bazos search --topic auto --keyword "skoda" --price-to 15000 --pages 3

        scrape-bazos search --topic reality --keyword "byt" --location "Bratislava" --radius 10
    """
    try:
        # Create scraper
        scraper = BazosScraper(timeout=timeout)

        # Build URL for reference
        url = scraper.build_url(
            topic=topic,
            keyword=keyword,
            price_from=price_from,
            price_to=price_to,
            radius=radius,
            location=location,
        )
        click.echo(f"🔍 Search URL: {url}\n")

        # Scrape listings
        click.echo(f"📡 Scraping {pages} page(s)...")
        items = scraper.scrape_listings(
            topic=topic,
            keyword=keyword,
            price_from=price_from,
            price_to=price_to,
            radius=radius,
            location=location,
            max_pages=pages,
        )

        click.echo(f"\n✅ Found {len(items)} items\n")

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
                click.echo(f"\nDescription:\n{item.description}\n")

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
@click.option(
    "--topic",
    default="pc",
    help="Category for example (default: pc)",
)
@click.option(
    "--keyword",
    default="nas",
    help="Keyword for example (default: nas)",
)
def example(topic, keyword):
    """
    Run an example search to test the scraper
    """
    click.echo("🔍 Running example search...\n")
    scraper = BazosScraper()

    url = scraper.build_url(topic=topic, keyword=keyword)
    click.echo(f"Search URL: {url}\n")

    items = scraper.scrape_listings(topic=topic, keyword=keyword, max_pages=1)

    click.echo(f"Found {len(items)} items:\n")
    for i, item in enumerate(items[:3], 1):
        click.echo(f"{i}. {item.title}")
        click.echo(f"   Price: {item.price}")
        click.echo(f"   Location: {item.location}")
        click.echo(f"   URL: {item.item_url}\n")


@cli.command()
def categories():
    """
    Show available categories
    """
    categories_list = {
        "pc": "Computers & IT",
        "auto": "Automobiles",
        "reality": "Real Estate",
        "elektronika": "Electronics",
        "domacnost": "Household Items",
        "knihy": "Books",
        "oblecenie": "Clothing",
        "sport": "Sports Equipment",
        "hudka": "Music",
        "byty": "Apartments",
        "motocykle": "Motorcycles",
        "bicykle": "Bicycles",
    }

    click.echo("📂 Available Categories:\n")
    for topic, description in categories_list.items():
        click.echo(f"  {click.style(topic.ljust(15), fg='cyan')} → {description}")
    click.echo()


@cli.command()
def info():
    """
    Show project information
    """
    click.echo(click.style("🔍 Bazos.sk Web Scraper", bold=True, fg="cyan"))
    click.echo("Version: 0.1.0\n")

    click.echo(click.style("Features:", bold=True))
    features = [
        "Full search capability with filtering",
        "Image extraction and downloading",
        "Multiple export formats (JSON, CSV, HTML, Table)",
        "Beautiful responsive HTML reports",
        "Complete test suite with 35+ tests",
    ]
    for feature in features:
        click.echo(f"  ✓ {feature}")

    click.echo(f"\n{click.style('Usage:', bold=True)}")
    click.echo("  scrape-bazos search --topic pc --keyword 'nas'")
    click.echo("  scrape-bazos example")
    click.echo("  scrape-bazos categories")
    click.echo(f"\n{click.style('Documentation:', bold=True)}")
    click.echo("  See README.md for detailed documentation")
    click.echo()


def _save_as_csv(items, output_file: str) -> None:
    """Save items as CSV"""
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        if not items:
            return

        fieldnames = ["title", "price", "location", "description", "image_url", "item_url", "date_posted"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        for item in items:
            writer.writerow(item.to_dict())


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
            f.write(f"\nDescription:\n{item.description}\n")

        f.write("\n" + "=" * 150 + "\n")
        f.write(f"Total items: {len(items)}\n")


if __name__ == "__main__":
    cli()
