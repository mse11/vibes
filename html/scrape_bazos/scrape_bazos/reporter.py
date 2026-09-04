"""
HTML Report generator and image downloader for Bazos scraper results
"""

import os
import requests
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .scraper import BazosItem


class ImageDownloader:
    """Download and manage images from listings"""

    def __init__(self, output_dir: str = "bazos_images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download_image(self, url: str, filename: str, timeout: int = 10) -> Optional[str]:
        """
        Download image from URL

        Returns:
            Local path to downloaded image or None if failed
        """
        if not url:
            return None

        try:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            response.raise_for_status()

            file_path = self.output_dir / filename
            with open(file_path, "wb") as f:
                f.write(response.content)

            return str(file_path)
        except Exception as e:
            print(f"Failed to download {url}: {e}")
            return None

    def download_all_images(self, items: List[BazosItem]) -> dict:
        """
        Download all images from items

        Returns:
            Dictionary mapping item URLs to local image paths
        """
        image_map = {}

        for i, item in enumerate(items):
            if item.image_url:
                # Generate unique filename
                ext = Path(item.image_url).suffix or ".jpg"
                filename = f"item_{i:04d}{ext}"

                local_path = self.download_image(item.image_url, filename)
                if local_path:
                    image_map[item.item_url] = local_path
                    print(f"Downloaded image {i+1}/{len(items)}")

        return image_map


class HTMLReportGenerator:
    """Generate beautiful HTML reports from scrape results"""

    def __init__(self):
        self.css_template = """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                padding: 20px;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }

            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }

            .header h1 {
                font-size: 2.5em;
                margin-bottom: 10px;
            }

            .header p {
                font-size: 1.1em;
                opacity: 0.9;
            }

            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                padding: 30px;
                background: #f8f9fa;
                border-bottom: 1px solid #e9ecef;
            }

            .stat {
                text-align: center;
            }

            .stat-value {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
            }

            .stat-label {
                color: #666;
                font-size: 0.9em;
                margin-top: 5px;
            }

            .filters {
                padding: 20px 30px;
                background: #f8f9fa;
                border-bottom: 1px solid #e9ecef;
            }

            .filters p {
                font-size: 0.95em;
                color: #666;
                line-height: 1.6;
            }

            .items-container {
                padding: 30px;
            }

            .item {
                display: grid;
                grid-template-columns: 250px 1fr;
                gap: 20px;
                padding: 20px;
                margin-bottom: 20px;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                transition: transform 0.3s, box-shadow 0.3s;
            }

            .item:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }

            .item-image {
                width: 100%;
                height: 200px;
                object-fit: cover;
                border-radius: 6px;
                background: #f0f0f0;
            }

            .item-content {
                display: flex;
                flex-direction: column;
            }

            .item-title {
                font-size: 1.3em;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
                word-break: break-word;
            }

            .item-title a {
                color: #667eea;
                text-decoration: none;
            }

            .item-title a:hover {
                text-decoration: underline;
            }

            .item-meta {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
                margin-bottom: 15px;
                padding-bottom: 15px;
                border-bottom: 1px solid #e9ecef;
            }

            .meta-item {
                font-size: 0.95em;
            }

            .meta-label {
                color: #999;
                font-weight: 600;
                font-size: 0.85em;
            }

            .meta-value {
                color: #333;
                margin-top: 3px;
            }

            .item-price {
                font-size: 1.5em;
                font-weight: bold;
                color: #28a745;
                margin-bottom: 10px;
            }

            .item-description {
                color: #666;
                font-size: 0.95em;
                line-height: 1.6;
                flex-grow: 1;
                margin-bottom: 15px;
            }

            .item-description.empty {
                color: #999;
                font-style: italic;
            }

            .item-url {
                display: inline-block;
                padding: 8px 16px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                font-size: 0.9em;
                width: fit-content;
                transition: background 0.3s;
            }

            .item-url:hover {
                background: #764ba2;
            }

            .no-image {
                display: flex;
                align-items: center;
                justify-content: center;
                background: #f0f0f0;
                color: #999;
                font-size: 0.9em;
                border-radius: 6px;
                height: 200px;
            }

            .footer {
                padding: 20px 30px;
                background: #f8f9fa;
                border-top: 1px solid #e9ecef;
                text-align: center;
                color: #666;
                font-size: 0.9em;
            }

            @media (max-width: 768px) {
                .item {
                    grid-template-columns: 1fr;
                }

                .header h1 {
                    font-size: 1.8em;
                }

                .stats {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """

    def generate_report(
        self,
        items: List[BazosItem],
        output_file: str = "bazos_report.html",
        topic: str = "N/A",
        keyword: str = "N/A",
        include_images: bool = True,
        image_map: Optional[dict] = None,
    ) -> None:
        """Generate HTML report"""

        html = f"""
        <!DOCTYPE html>
        <html lang="sk">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bazos.sk Scrape Report - {keyword}</title>
            {self.css_template}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 Bazos.sk Scrape Report</h1>
                    <p>Category: <strong>{topic}</strong> | Keyword: <strong>{keyword}</strong></p>
                </div>

                <div class="stats">
                    <div class="stat">
                        <div class="stat-value">{len(items)}</div>
                        <div class="stat-label">Items Found</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{len([i for i in items if i.image_url])}</div>
                        <div class="stat-label">With Images</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{len([i for i in items if i.price])}</div>
                        <div class="stat-label">With Prices</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value">{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</div>
                        <div class="stat-label">Scrape Time</div>
                    </div>
                </div>

                <div class="filters">
                    <p>
                        <strong>Category:</strong> {topic} |
                        <strong>Keyword:</strong> {keyword} |
                        <strong>Total Results:</strong> {len(items)} items
                    </p>
                </div>

                <div class="items-container">
                    {self._generate_items_html(items, include_images, image_map)}
                </div>

                <div class="footer">
                    <p>Generated on {datetime.now().strftime('%d.%m.%Y at %H:%M:%S')} | bazos.sk scraper</p>
                </div>
            </div>
        </body>
        </html>
        """

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✓ HTML report saved to: {output_file}")

    def _generate_items_html(
        self, items: List[BazosItem], include_images: bool, image_map: Optional[dict] = None
    ) -> str:
        """Generate HTML for items"""
        if not items:
            return '<p style="text-align: center; color: #999; padding: 40px;">No items found</p>'

        html_parts = []

        for i, item in enumerate(items, 1):
            image_html = self._get_image_html(item, include_images, image_map)

            description = item.description or ""
            description_class = "empty" if not description else ""

            html_parts.append(f"""
            <div class="item">
                {image_html}
                <div class="item-content">
                    <div class="item-title">
                        <a href="{item.item_url}" target="_blank">{item.title}</a>
                    </div>
                    {f'<div class="item-price">{item.price}</div>' if item.price else ''}
                    <div class="item-meta">
                        {f'<div class="meta-item"><div class="meta-label">📍 LOCATION</div><div class="meta-value">{item.location}</div></div>' if item.location else ''}
                        {f'<div class="meta-item"><div class="meta-label">📅 DATE</div><div class="meta-value">{item.date_posted}</div></div>' if item.date_posted else ''}
                    </div>
                    <div class="item-description {description_class}">
                        {description if description else "No description provided"}
                    </div>
                    <a href="{item.item_url}" target="_blank" class="item-url">View Full Listing →</a>
                </div>
            </div>
            """)

        return "\n".join(html_parts)

    def _get_image_html(
        self, item: BazosItem, include_images: bool, image_map: Optional[dict]
    ) -> str:
        """Generate HTML for item image"""
        if not include_images:
            return '<div class="no-image">No image display mode</div>'

        if image_map and item.item_url in image_map:
            # Use locally downloaded image
            image_path = image_map[item.item_url]
            return f'<img src="{image_path}" alt="{item.title}" class="item-image">'
        elif item.image_url:
            # Use remote image
            return f'<img src="{item.image_url}" alt="{item.title}" class="item-image">'
        else:
            return '<div class="no-image">No image available</div>'
