"""
CLI interface for Bazos.sk scraper using Click
"""

import click
import csv
import json
from pathlib import Path
from .scraper import BazosScraper
from .reporter import HTMLReportGenerator


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
    help="Category (e.g., pc, auto, reality, elektronika, domacnost, knihy, oblecenie, sport). Required - run 'categories' command to see all available options",
)
@click.option(
    "--keyword",
    multiple=True,
    required=True,
    help="Search keyword(s). Can specify multiple times: --keyword 'nas' --keyword 'backup' (results will be merged)",
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
    "--sub-category",
    default=None,
    help="Optional subcategory/group within category (e.g., 'predam', 'prenajmu' for reality). Run 'categories -s -c <category>' to see available options",
)
@click.option(
    "--pages-get",
    default="all",
    type=str,
    help="Number of pages to scrape or 'all' (default: all, use a number for quick sample)",
)
@click.option(
    "--output",
    default="",
    type=str,
    help="Output filename (default: bazos_results_<category>_<keyword>.json)",
)
@click.option(
    "--format",
    type=click.Choice(["json", "csv", "table", "html", "html_dynamic"]),
    default="html_dynamic",
    help="Output format (default: html_dynamic - interactive). Use 'json' for data export",
)
@click.option(
    "--timeout",
    default=10,
    type=int,
    help="Request timeout in seconds (default: 10)",
)
@click.option(
    "--max-retries",
    default=3,
    type=int,
    help="Maximum number of retries on connection errors (default: 3)",
)
@click.option(
    "--retry-delay",
    default=1.0,
    type=float,
    help="Initial delay between retries in seconds, uses exponential backoff (default: 1.0)",
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
@click.option(
    "--no-images",
    is_flag=True,
    help="Don't show images in HTML report (only applies to --format html)",
)
@click.option(
    "--download-images",
    is_flag=True,
    help="Download images locally for HTML report (only applies to --format html)",
)
@click.option(
    "--images-dir",
    default="images",
    type=str,
    help="Directory to save downloaded images (default: images, only applies to --format html)",
)
@click.option(
    "--truncate-descriptions",
    is_flag=True,
    help="Truncate descriptions to 2 lines in HTML report (only applies to --format html)",
)
def search(category, keyword, price_from, price_to, location, radius, sub_category, pages_get, output, format, timeout, max_retries, retry_delay, display, pages_count, details_all, no_images, download_images, images_dir, truncate_descriptions):
    """
    Search for listings on bazos.sk

    MULTI-KEYWORD SEARCHING:
    When multiple keywords are provided, results from each keyword are scraped
    separately and then merged (deduplicated by URL). All pages are fetched by
    default for comprehensive results.

    OUTPUT FORMATS:
    Default format is 'html_dynamic' which generates an interactive HTML report
    with filtering, sorting, and search capabilities. Use --format to change
    to json (data export), csv, table, or static html.

    Examples:

        # Single keyword - generates interactive HTML report by default
        scrape-bazos search --category pc --keyword "nas"

        # Multiple keywords - each scraped separately and merged
        scrape-bazos search --category pc --keyword "nas" --keyword "backup"

        # Limit to specific number of pages (quick sample)
        scrape-bazos search --category pc --keyword "nas" --pages-get 2

        # Export as JSON
        scrape-bazos search --category pc --keyword "nas" --format json

        # Static HTML report
        scrape-bazos search --category pc --keyword "nas" --format html

        # Download images with HTML report
        scrape-bazos search --category pc --keyword "nas" --download-images

        # Multiple keywords with page limit
        scrape-bazos search --category pc --keyword "nas" --keyword "backup" --pages-get 2

        # Check available pages for each keyword
        scrape-bazos search --category pc --keyword "nas" --keyword "backup" --pages-count

        scrape-bazos search --category pc --keyword "notebook" --price-from 500 --price-to 1000

        scrape-bazos search --category auto --keyword "skoda" --price-to 15000

        scrape-bazos search --category reality --keyword "byt" --location "Bratislava" --radius 10 --format csv

        scrape-bazos search --category pc --keyword "nas" --pages-get 2 --details-all --display
    """
    try:
        # Validate HTML-specific options
        if format not in ["html", "html_dynamic"] and (no_images or download_images):
            click.echo("⚠️  Note: --no-images and --download-images only apply to --format html and html_dynamic", err=False)

        # Validate keyword is provided
        if not keyword:
            click.echo("❌ At least one --keyword is required", err=True)
            raise SystemExit(1)

        # Validate and process category parameter
        category = category.strip().lower()

        # If category is empty, 'all', or 'www', use 'www'
        if not category or category == "all":
            category = "www"
        else:
            # Try to validate the category against available categories
            scraper_temp = BazosScraper(timeout=timeout, max_retries=max_retries, retry_delay=retry_delay)
            click.echo("📂 Fetching available categories for validation...", err=False)
            available_categories = scraper_temp.get_categories()

            if available_categories:
                # Check if provided category exists in available categories
                if category not in available_categories:
                    click.echo(f"❌ Invalid category: '{click.style(category, bold=True)}'", err=True)
                    click.echo("\n📂 Available Categories:\n", err=True)
                    for cat_code, cat_desc in sorted(available_categories.items()):
                        click.echo(f"  {click.style(cat_code.ljust(15), fg='cyan')} → {cat_desc}", err=True)
                    click.echo(f"\n✅ Found {len(available_categories)} categories", err=True)
                    click.echo("\nUsage: scrape-bazos search --category <category_code> --keyword <keyword>", err=True)
                    raise SystemExit(1)
            else:
                # If we can't fetch categories, log a warning but continue
                click.echo("⚠️  Could not validate category (unable to fetch from bazos.sk), proceeding anyway...", err=False)

        # Create scraper
        scraper = BazosScraper(timeout=timeout, max_retries=max_retries, retry_delay=retry_delay)

        # Validate sub_category if provided
        if sub_category:
            sub_category = sub_category.strip().lower()

            # Try to validate the sub_category against available subcategories for this category
            click.echo("📂 Fetching available subcategories for category validation...", err=False)

            # Try grouped structure first (for categories like 'reality')
            grouped_categories = scraper.get_subcategories_grouped(category)

            # If no grouped structure, try flat structure (for categories like 'pc')
            flat_categories = {}
            if not grouped_categories:
                flat_categories = scraper.get_subcategories(category)

            # Determine which structure we have
            if grouped_categories:
                # Using grouped structure
                if sub_category not in grouped_categories:
                    click.echo(f"❌ Invalid subcategory: '{click.style(sub_category, bold=True)}' for category '{click.style(category, bold=True)}'", err=True)
                    click.echo(f"\n📂 Available Subcategories:\n", err=True)
                    for group_id, group_data in sorted(grouped_categories.items()):
                        group_name = group_data.get('name', group_id)
                        subcat_count = len(group_data.get('subcategories', {}))
                        click.echo(f"  {click.style(group_id.ljust(15), fg='cyan')} → {group_name} ({subcat_count} items)", err=True)
                    click.echo(f"\n✅ Found {len(grouped_categories)} available subcategory/group(s)", err=True)
                    click.echo("\nUsage: scrape-bazos search --category <category> --sub-category <subcategory> --keyword <keyword>", err=True)
                    raise SystemExit(1)
                else:
                    # Show which subcategory was selected
                    group_data = grouped_categories[sub_category]
                    group_name = group_data.get('name', sub_category)
                    subcat_count = len(group_data.get('subcategories', {}))
                    click.echo(f"✅ Valid subcategory '{click.style(group_name, bold=True)}' ({subcat_count} items)\n", err=False)
            elif flat_categories:
                # Using flat structure
                if sub_category not in flat_categories:
                    click.echo(f"❌ Invalid subcategory: '{click.style(sub_category, bold=True)}' for category '{click.style(category, bold=True)}'", err=True)
                    click.echo(f"\n📂 Available Subcategories:\n", err=True)
                    for subcat_id, subcat_name in sorted(flat_categories.items()):
                        click.echo(f"  {click.style(subcat_id.ljust(15), fg='cyan')} → {subcat_name}", err=True)
                    click.echo(f"\n✅ Found {len(flat_categories)} available subcategories", err=True)
                    click.echo("\nUsage: scrape-bazos search --category <category> --sub-category <subcategory> --keyword <keyword>", err=True)
                    raise SystemExit(1)
                else:
                    # Show which subcategory was selected
                    subcat_name = flat_categories[sub_category]
                    click.echo(f"✅ Valid subcategory '{click.style(subcat_name, bold=True)}'\n", err=False)
            else:
                # No subcategories found - reject the provided subcategory
                click.echo(f"❌ Invalid sub-category: '{click.style(sub_category, bold=True)}'", err=True)
                click.echo(f"\n📂 Available Subcategories for '{category}':\n", err=True)
                click.echo(f"  (no subcategories available for this category)", err=True)
                click.echo(f"\nUsage: scrape-bazos search --category <category> --sub-category <subcategory> --keyword <keyword>", err=True)
                raise SystemExit(1)

        # Auto-generate output filename if not provided
        if not output or output == "bazos_results.json":
            # Replace spaces with underscores in category and keywords for safe filenames
            safe_category = category.replace(" ", "_")
            keywords_str = "_".join(k.replace(" ", "_") for k in keyword)

            if format == "html":
                output = f"bazos_report_{safe_category}_{keywords_str}.html"
            elif format == "html_dynamic":
                output = f"bazos_report_dynamic_{safe_category}_{keywords_str}.html"
            elif format == "csv":
                output = f"bazos_results_{safe_category}_{keywords_str}.csv"
            elif format == "table":
                output = f"bazos_results_{safe_category}_{keywords_str}.txt"
            else:  # json
                output = f"bazos_results_{safe_category}_{keywords_str}.json"

        # Show what we're searching for
        click.echo(f"🔍 Searching for keywords: {click.style(', '.join(keyword), bold=True)}\n")

        # If only counting pages, fetch first page and show page info for each keyword
        if pages_count:
            click.echo("📊 Checking available pages for each keyword...\n")
            total_pages_all = 0
            total_items_all = 0

            for kw in keyword:
                page_info = scraper.get_page_count(
                    category=category,
                    keyword=kw,
                    price_from=price_from,
                    price_to=price_to,
                    radius=radius,
                    location=location,
                    sub_category=sub_category,
                )

                if page_info:
                    click.echo(f"  '{kw}': {page_info['total_pages']} pages, ~{page_info['total_items']} items")
                    total_pages_all += page_info['total_pages']
                    total_items_all += page_info['total_items']
                else:
                    click.echo(f"  '{kw}': Could not retrieve page information")

            click.echo(f"\n📄 Total Across All Keywords:")
            click.echo(f"   Total pages: {total_pages_all}")
            click.echo(f"   Total items: ~{total_items_all}\n")

            raise SystemExit(0)

        # Handle pages_get parameter - can be "all" or a number
        if pages_get.lower() == "all":
            # OPTIMIZATION: Don't call get_page_count() - it wastes N requests!
            # Instead, use max_pages=999999 to signal "scrape until end"
            # The scrape_listings() method will:
            # 1. Fetch each page
            # 2. Check if there's a next page link
            # 3. Stop when no next page is found
            # This achieves the same result (scraping all pages) in just N requests instead of 2N

            click.echo("📊 Scraping all available pages (will stop when no more pages)...")
            pages_get_int = 999999  # ← Signal to scrape until pagination ends

        else:
            try:
                pages_get_int = int(pages_get)
                if pages_get_int <= 0:
                    click.echo(f"❌ Invalid value for --pages-get: must be > 0", err=True)
                    raise SystemExit(1)
            except ValueError:
                click.echo(f"❌ Invalid value for --pages-get: '{pages_get}' (use a number or 'all')", err=True)
                raise SystemExit(1)

        # Scrape listings for each keyword and merge results
        if pages_get_int == 999999:
            click.echo(f"📡 Scraping all pages for {len(keyword)} keyword(s)...\n")
        else:
            click.echo(f"📡 Scraping up to {pages_get_int} page(s) for {len(keyword)} keyword(s)...\n")
        all_items = []
        items_by_url = {}  # For deduplication

        for kw in keyword:
            click.echo(f"  Searching for: '{click.style(kw, bold=True)}'")
            items = scraper.scrape_listings(
                category=category,
                keyword=kw,
                price_from=price_from,
                price_to=price_to,
                radius=radius,
                location=location,
                max_pages=pages_get_int,
                sub_category=sub_category,
            )

            click.echo(f"    Found {len(items)} items")

            # Add items, using URL as unique identifier to avoid duplicates
            for item in items:
                if item.item_url not in items_by_url:
                    items_by_url[item.item_url] = item
                    all_items.append(item)

        items = all_items
        click.echo(f"\n✅ Found {len(items)} unique items across all keywords\n")

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
        elif format == "html" or format == "html_dynamic":
            # Use the auto-generated output filename
            html_output = output

            # Handle image downloading if requested
            image_map = None
            if download_images and not no_images:
                click.echo(f"\n🖼️  Downloading images to '{images_dir}' directory...\n")
                try:
                    from .reporter import ImageDownloader
                    downloader = ImageDownloader(output_dir=images_dir)
                    image_map = downloader.download_all_images(items)
                    click.echo(f"✅ Downloaded {len(image_map)} images\n")
                except Exception as e:
                    click.echo(f"⚠️  Could not download images: {e}")
                    click.echo("   Will use remote image URLs instead\n")
                    image_map = None

            # Generate HTML report
            keywords_display = ", ".join(keyword) if len(keyword) > 1 else keyword[0]
            if format == "html_dynamic":
                click.echo(f"📄 Generating dynamic HTML report with filtering...")
                generator = HTMLReportGenerator()
                generator.generate_dynamic_report(
                    items=items,
                    output_file=html_output,
                    topic=category,
                    keyword=keywords_display,
                    include_images=not no_images,
                    image_map=image_map,
                    truncate_descriptions=truncate_descriptions,
                )
            else:
                click.echo(f"📄 Generating HTML report...")
                generator = HTMLReportGenerator()
                generator.generate_report(
                    items=items,
                    output_file=html_output,
                    topic=category,
                    keyword=keywords_display,
                    include_images=not no_images,
                    image_map=image_map,
                    truncate_descriptions=truncate_descriptions,
                )

            # Also save JSON file when using HTML formats
            json_output = Path(html_output).stem + ".json"
            click.echo(f"💾 Also saving JSON file: {click.style(json_output, bold=True)}")
            scraper.save_results(items, json_output)

            output = html_output
            if download_images and not no_images:
                click.echo(f"🖼️  Images saved to: {click.style(images_dir, bold=True)}")

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
    "--show-subcategories",
    "-s",
    is_flag=True,
    help="Show subcategories for each category (fetches from category pages)",
)
@click.option(
    "--category",
    "-c",
    default=None,
    help="Show subcategories for a specific category only (requires --show-subcategories)",
)
@click.option(
    "--details-all",
    "-da",
    is_flag=True,
    help="Show full URL for each subcategory (requires --show-subcategories)",
)
def categories(show_subcategories, category, details_all):
    """
    Show available categories fetched from bazos.sk.

    IMPROVED: Auto-detects grouped vs flat subcategories and displays them appropriately.

    Examples:
        scrape-bazos categories                              # List all main categories
        scrape-bazos categories -s                           # List categories with subcategories
        scrape-bazos categories -s -c pc                     # Show only PC category with its subcategories
        scrape-bazos categories -s -c reality                # Show grouped categories (Predaj, Prenájom, etc.)
        scrape-bazos categories -s -c reality -da            # Show grouped categories with full URLs
    """
    try:
        scraper = BazosScraper()

        if show_subcategories:
            # Show categories with subcategories
            if category:
                # Show only specific category with subcategories
                category = category.lower()
                click.echo(f"📂 Fetching subcategories for '{category}' from bazos.sk...\n")

                # IMPROVED: Try grouped first, fall back to flat
                grouped = scraper.get_subcategories_grouped(category)

                if grouped:
                    # Display grouped structure
                    click.echo(f"📂 Subcategories in '{click.style(category, fg='cyan')}' (grouped):\n")
                    total_subcats = 0

                    for group_id, group_data in sorted(grouped.items()):
                        group_name = group_data.get("name", group_id)
                        subcategories = group_data.get("subcategories", {})

                        click.echo(f"  {click.style('📌 ' + group_name, fg='yellow')}")
                        for subcat_path, subcat_name in sorted(subcategories.items()):
                            # Show full path: group_id/subcat_id
                            full_path = f"{group_id}/{subcat_path}"
                            if details_all:
                                # Show with full URL
                                full_url = f"https://{category}.bazos.sk/{full_path}/"
                                click.echo(f"      {click.style(full_path.ljust(25), fg='green')} → {subcat_name} {click.style(full_url, fg='blue')}")
                            else:
                                # Show without URL
                                click.echo(f"      {click.style(full_path.ljust(25), fg='green')} → {subcat_name}")
                        total_subcats += len(subcategories)

                    click.echo(f"\n✅ Found {len(grouped)} group(s) with {total_subcats} total subcategories")
                else:
                    # Fallback to flat structure
                    subcategories = scraper.get_subcategories(category)

                    if not subcategories:
                        click.echo(f"ℹ️  No subcategories found for category '{category}'", err=False)
                        raise SystemExit(0)

                    click.echo(f"📂 Subcategories in '{click.style(category, fg='cyan')}':\n")
                    for subcat_path, subcat_name in sorted(subcategories.items()):
                        if details_all:
                            # Show with full URL
                            full_url = f"https://{category}.bazos.sk/{subcat_path}/"
                            click.echo(f"  {click.style(subcat_path.ljust(20), fg='green')} → {subcat_name} {click.style(full_url, fg='blue')}")
                        else:
                            # Show without URL
                            click.echo(f"  {click.style(subcat_path.ljust(20), fg='green')} → {subcat_name}")
                    click.echo(f"\n✅ Found {len(subcategories)} subcategories")
            else:
                # Show all categories with subcategories
                click.echo("📂 Fetching all categories and subcategories from bazos.sk...\n")

                # Get main categories first
                categories_list = scraper.get_categories()
                if not categories_list:
                    click.echo("❌ No categories found. Unable to fetch from bazos.sk.", err=True)
                    raise SystemExit(1)

                click.echo("📂 Available Categories with Subcategories:\n")
                total_subcategories = 0
                failed_categories = []

                # Fetch subcategories for each category with progress indicator
                for i, (cat_code, cat_name) in enumerate(sorted(categories_list.items()), 1):
                    click.echo(f"  {click.style(cat_code.ljust(15), fg='cyan')} → {cat_name}", nl=False)

                    try:
                        # IMPROVED: Try grouped first, fall back to flat
                        grouped = scraper.get_subcategories_grouped(cat_code)

                        if grouped:
                            # Grouped structure
                            click.echo()  # New line after category name
                            for group_id, group_data in sorted(grouped.items()):
                                group_name = group_data.get("name", group_id)
                                subcategories = group_data.get("subcategories", {})
                                click.echo(f"      {click.style('📌 ' + group_name, fg='yellow')}")
                                for subcat_path, subcat_name in sorted(subcategories.items()):
                                    # Show full path: group_id/subcat_id
                                    full_path = f"{group_id}/{subcat_path}"
                                    if details_all:
                                        # Show with full URL
                                        full_url = f"https://{cat_code}.bazos.sk/{full_path}/"
                                        click.echo(f"          {click.style(full_path.ljust(20), fg='green')} → {subcat_name} {click.style(full_url, fg='blue')}")
                                    else:
                                        # Show without URL
                                        click.echo(f"          {click.style(full_path.ljust(20), fg='green')} → {subcat_name}")
                                total_subcategories += len(subcategories)
                        else:
                            # Flat structure
                            subcategories = scraper.get_subcategories(cat_code)

                            if subcategories:
                                click.echo()  # New line after category name
                                for subcat_path, subcat_name in sorted(subcategories.items()):
                                    if details_all:
                                        # Show with full URL
                                        full_url = f"https://{cat_code}.bazos.sk/{subcat_path}/"
                                        click.echo(f"      {click.style(subcat_path.ljust(18), fg='green')} → {subcat_name} {click.style(full_url, fg='blue')}")
                                    else:
                                        # Show without URL
                                        click.echo(f"      {click.style(subcat_path.ljust(18), fg='green')} → {subcat_name}")
                                total_subcategories += len(subcategories)
                            else:
                                click.echo(" (no subcategories)")

                    except Exception as e:
                        click.echo(f" {click.style('[TIMEOUT]', fg='yellow')}")
                        failed_categories.append((cat_code, str(e)))

                click.echo(f"\n✅ Found {len(categories_list)} categories with {total_subcategories} total subcategories")

                if failed_categories:
                    click.echo(f"\n⚠️  {len(failed_categories)} categor{'y' if len(failed_categories) == 1 else 'ies'} timed out:")
                    for cat_code, error in failed_categories:
                        click.echo(f"   - {cat_code}: {error}")
                    click.echo(f"\n💡 Tip: Try fetching individual categories with: scrape-bazos categories -s -c {failed_categories[0][0]}")

        else:
            # Show only main categories (original behavior)
            click.echo("📂 Fetching available categories from bazos.sk...\n")
            categories_list = scraper.get_categories()

            if not categories_list:
                click.echo("❌ No categories found. Unable to fetch from bazos.sk.", err=True)
                raise SystemExit(1)

            click.echo("📂 Available Categories:\n")
            for topic, description in sorted(categories_list.items()):
                click.echo(f"  {click.style(topic.ljust(15), fg='cyan')} → {description}")
            click.echo(f"\n✅ Found {len(categories_list)} categories")
            click.echo(f"💡 Tip: Use 'scrape-bazos categories -s' to see subcategories")

        click.echo()

    except Exception as e:
        click.echo(f"❌ Error fetching categories: {e}", err=True)
        raise SystemExit(1)



@cli.command()
@click.option(
    "--input",
    "-i",
    required=True,
    type=click.Path(exists=True),
    help="Input JSON file with scraped items (from search command)",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=str,
    help="Output filename. Format auto-detected from extension (.html, .csv, .json). Default: report_{input_name}.html",
)
@click.option(
    "--category",
    default="Bazos",
    type=str,
    help="Category name to display in report (default: Bazos)",
)
@click.option(
    "--keyword",
    default="Items",
    type=str,
    help="Keyword to display in report (default: Items)",
)
@click.option(
    "--no-images",
    is_flag=True,
    help="Don't show images in the HTML report (HTML format only)",
)
@click.option(
    "--download-images",
    is_flag=True,
    help="Download images locally instead of using remote URLs (HTML format only)",
)
@click.option(
    "--images-dir",
    default="images",
    type=str,
    help="Directory to save downloaded images (default: images, HTML format only)",
)
@click.option(
    "--truncate-descriptions",
    is_flag=True,
    help="Truncate descriptions to 2 lines in HTML report (HTML format only)",
)
def convert_format(input, output, category, keyword, no_images, download_images, images_dir, truncate_descriptions):
    """
    Convert scraped data between formats

    This command takes a JSON file created by the 'search' command
    and converts it to various output formats (HTML, CSV, JSON).
    Format is automatically detected from the output file extension.

    Examples:

        scrape-bazos convert-format --input bazos_results.json -o report.html

        scrape-bazos convert-format -i results.json -o my_report.html --category pc --keyword "nas"

        scrape-bazos convert-format -i results.json -o data.csv

        scrape-bazos convert-format -i results.json -o report.html --download-images --images-dir ./images

        scrape-bazos convert-format -i results.json -o formatted_results.json
    """
    try:
        # Load JSON file
        click.echo(f"📂 Loading items from: {click.style(input, bold=True)}...\n")

        with open(input, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both direct array and object with 'items' key
        if isinstance(data, list):
            items_data = data
        elif isinstance(data, dict) and 'items' in data:
            items_data = data['items']
        else:
            click.echo("❌ JSON file format not recognized. Expected array of items or object with 'items' key.", err=True)
            raise SystemExit(1)

        # Convert dictionaries to BazosItem objects
        from .scraper import BazosItem
        items = [BazosItem(**item) if isinstance(item, dict) else item for item in items_data]

        click.echo(f"✅ Loaded {len(items)} items\n")

        # Determine output filename based on format
        input_stem = Path(input).stem
        if output is None:
            if format == "html":
                output = f"report_{input_stem}.html"
            elif format == "csv":
                output = f"report_{input_stem}.csv"
            elif format == "json":
                output = f"report_{input_stem}.json"

        # Warn about image options for non-HTML formats
        if format != "html" and (no_images or download_images):
            click.echo(f"⚠️  Note: --no-images and --download-images only apply to HTML format", err=False)

        # Convert to requested format
        if format == "html":
            click.echo(f"📄 Converting to HTML format...")
            generator = HTMLReportGenerator()

            # Handle image downloading if requested
            image_map = None
            if download_images and not no_images:
                click.echo(f"🖼️  Downloading images to '{images_dir}' directory...\n")
                try:
                    from .reporter import ImageDownloader
                    downloader = ImageDownloader(output_dir=images_dir)
                    image_map = downloader.download_all_images(items)
                    click.echo(f"✅ Downloaded {len(image_map)} images\n")
                except Exception as e:
                    click.echo(f"⚠️  Could not download images: {e}")
                    click.echo("   Will use remote image URLs instead\n")
                    image_map = None

            # Generate HTML report
            generator.generate_report(
                items=items,
                output_file=output,
                topic=category,
                keyword=keyword,
                include_images=not no_images,
                image_map=image_map,
                truncate_descriptions=truncate_descriptions,
            )

            if download_images and not no_images:
                click.echo(f"🖼️  Images saved to: {click.style(images_dir, bold=True)}")

        elif format == "csv":
            click.echo(f"📄 Converting to CSV format...")
            _save_as_csv(items, output)

        elif format == "json":
            click.echo(f"📄 Converting to JSON format...")
            _save_as_json(items, output)

        click.echo(f"✅ Conversion successfully completed!")
        click.echo(f"📊 Contains: {click.style(str(len(items)), bold=True)} items")
        click.echo(f"📁 Saved to: {click.style(output, bold=True)}")

    except KeyboardInterrupt:
        click.echo("\n\n⚠️  Format conversion interrupted by user")
        raise SystemExit(1)
    except FileNotFoundError:
        click.echo(f"❌ File not found: {input}", err=True)
        raise SystemExit(1)
    except json.JSONDecodeError:
        click.echo(f"❌ Invalid JSON file: {input}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
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


def _save_as_json(items, output_file: str) -> None:
    """Save items as JSON"""
    data = [
        {
            "title": item.title,
            "price": item.price,
            "location": item.location,
            "description": item.description,
            "image_url": item.image_url,
            "image_urls": item.image_urls,
            "full_description": item.full_description,
            "item_url": item.item_url,
            "date_posted": item.date_posted,
        }
        for item in items
    ]

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    cli()
