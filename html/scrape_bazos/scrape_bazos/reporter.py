"""
HTML Report generator and image downloader for Bazos scraper results
"""

import json
from typing import List, Optional
from datetime import datetime
from .scraper import BazosItem


class HTMLReportGenerator:
    """Generate minimal, compact HTML reports from scrape results"""

    def __init__(self):
        self.css_template = """
        <style>
            :root {
                --thumb-size: 150px;
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                color: #333;
                padding: 10px;
            }

            .container {
                max-width: 100%;
                margin: 0 auto;
                background: white;
            }

            .header {
                background: #333;
                color: white;
                padding: 15px 20px;
                position: sticky;
                top: 0;
                z-index: 100;
                box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            }

            .header-top {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 20px;
                margin-bottom: 10px;
            }

            .header h1 {
                font-size: 1.5em;
                margin: 0;
            }

            .header p {
                font-size: 0.9em;
                opacity: 0.8;
                margin: 5px 0 0 0;
            }

            .item-counter {
                font-size: 0.9em;
                opacity: 0.8;
                min-width: 80px;
                text-align: right;
            }

            .item-counter strong {
                opacity: 1;
                font-weight: 600;
                color: #fff;
            }

            .slider-container {
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 0.9em;
            }

            .slider-label {
                white-space: nowrap;
            }

            .slider {
                width: 150px;
                height: 5px;
                border-radius: 5px;
                background: #555;
                outline: none;
                -webkit-appearance: none;
                appearance: none;
                cursor: pointer;
            }

            .slider::-webkit-slider-thumb {
                -webkit-appearance: none;
                appearance: none;
                width: 18px;
                height: 18px;
                border-radius: 50%;
                background: #0066cc;
                cursor: pointer;
                transition: background 0.2s;
            }

            .slider::-webkit-slider-thumb:hover {
                background: #0052a3;
            }

            .slider::-moz-range-thumb {
                width: 18px;
                height: 18px;
                border-radius: 50%;
                background: #0066cc;
                cursor: pointer;
                border: none;
                transition: background 0.2s;
            }

            .slider::-moz-range-thumb:hover {
                background: #0052a3;
            }

            .thumb-size-display {
                min-width: 40px;
                text-align: right;
                font-weight: 600;
            }

            .toggle-btn {
                padding: 6px 12px;
                background: #555;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9em;
                transition: background 0.2s;
            }

            .toggle-btn:hover {
                background: #0066cc;
            }

            .toggle-btn.full {
                background: #0066cc;
            }

            .items-container {
                padding: 0;
            }

            .item {
                padding: 10px 15px;
                border-bottom: 1px solid #e0e0e0;
                transition: background 0.2s;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .item:hover {
                background: #fafafa;
            }

            .item-header {
                display: flex;
                gap: 15px;
                align-items: center;
                flex-wrap: wrap;
                font-size: 0.85em;
            }

            .item-title {
                font-size: 0.95em;
                font-weight: 600;
                color: #333;
                margin: 0;
                word-break: break-word;
                flex: 1;
                min-width: 200px;
            }

            .item-title a {
                color: #0066cc;
                text-decoration: none;
            }

            .item-title a:hover {
                text-decoration: underline;
            }

            .meta-price {
                font-weight: bold;
                color: #d32f2f;
                font-size: 0.95em;
                white-space: nowrap;
            }

            .meta-location {
                color: #666;
                white-space: nowrap;
            }

            .meta-date {
                color: #999;
                white-space: nowrap;
            }

            .item-description {
                font-size: 0.85em;
                color: #666;
                line-height: 1.3;
                margin: 0;
                display: -webkit-box;
                -webkit-box-orient: vertical;
                overflow: hidden;
                transition: -webkit-line-clamp 0.3s ease;
            }

            .item-description.truncated {
                -webkit-line-clamp: 2;
            }

            .item-description.full {
                -webkit-line-clamp: unset;
            }

            .item-images {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                padding-top: 10px;
            }

            .item-thumbnail {
                width: var(--thumb-size);
                height: var(--thumb-size);
                object-fit: cover;
                border-radius: 4px;
                cursor: pointer;
                transition: transform 0.2s;
                border: 1px solid #e0e0e0;
            }

            .item-thumbnail:hover {
                transform: scale(1.1);
                border-color: #0066cc;
            }

            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.8);
                animation: fadeIn 0.3s;
            }

            .modal.show {
                display: flex;
                align-items: center;
                justify-content: center;
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            .modal-content {
                max-width: 90%;
                max-height: 90%;
                position: relative;
                animation: zoomIn 0.3s;
            }

            @keyframes zoomIn {
                from {
                    transform: scale(0.8);
                    opacity: 0;
                }
                to {
                    transform: scale(1);
                    opacity: 1;
                }
            }

            .modal-img {
                max-width: 100%;
                max-height: 85vh;
                object-fit: contain;
            }

            .modal-close {
                position: absolute;
                top: -30px;
                right: 0;
                font-size: 28px;
                font-weight: bold;
                color: white;
                cursor: pointer;
                background: none;
                border: none;
                padding: 0;
            }

            .modal-close:hover {
                color: #ccc;
            }

            @media (max-width: 768px) {
                .header-top {
                    flex-direction: column;
                    align-items: flex-start;
                }

                .slider-container {
                    width: 100%;
                }

                .item-header {
                    flex-direction: column;
                    gap: 6px;
                }

                .item-title {
                    min-width: unset;
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
        truncate_descriptions: bool = False,
    ) -> None:
        """Generate minimal HTML report with interactive features"""

        # Prepare data for JavaScript
        items_data = self._prepare_items_data(items, include_images, image_map)
        items_json = json.dumps(items_data)

        html = f"""
        <!DOCTYPE html>
        <html lang="sk">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bazos.sk - {keyword}</title>
            {self.css_template}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="header-top">
                        <div>
                            <h1>🛒 Bazos.sk Items</h1>
                            <p id="summary"></p>
                        </div>
                        <div class="item-counter">
                            Item <strong id="currentItem">1</strong> / <strong id="totalItems">0</strong>
                        </div>
                        <div class="slider-container">
                            <span class="slider-label">Thumbnails:</span>
                            <input type="range" min="40" max="300" value="150" class="slider" id="sizeSlider">
                            <span class="thumb-size-display" id="sizeDisplay">150px</span>
                        </div>
                        <button id="descriptionToggle" class="toggle-btn" title="Toggle description truncation">📄 Truncate</button>
                    </div>
                </div>

                <div class="items-container" id="items"></div>
            </div>

            <div id="imageModal" class="modal">
                <div class="modal-content">
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                    <img id="modalImg" class="modal-img" src="" alt="">
                </div>
            </div>

            <script>
                const data = {items_json};
                let isDescriptionTruncated = {str(truncate_descriptions).lower()};

                function openImage(src) {{
                    const modal = document.getElementById('imageModal');
                    const img = document.getElementById('modalImg');
                    img.src = src;
                    modal.classList.add('show');
                }}

                function closeModal() {{
                    document.getElementById('imageModal').classList.remove('show');
                }}

                function getImages(item) {{
                    if (item.image_urls && item.image_urls.length > 0) {{
                        return item.image_urls;
                    }}
                    return [item.image_url];
                }}

                function escapeHtml(text) {{
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                }}

                function truncateText(text, maxLength = 180) {{
                    if (text.length > maxLength) {{
                        return text.substring(0, maxLength) + '...';
                    }}
                    return text;
                }}

                function toggleDescriptionTruncation() {{
                    isDescriptionTruncated = !isDescriptionTruncated;
                    const descriptions = document.querySelectorAll('.item-description');
                    const button = document.getElementById('descriptionToggle');

                    descriptions.forEach(desc => {{
                        if (isDescriptionTruncated) {{
                            desc.classList.remove('full');
                            desc.classList.add('truncated');
                        }} else {{
                            desc.classList.remove('truncated');
                            desc.classList.add('full');
                        }}
                    }});

                    // Update button appearance
                    if (isDescriptionTruncated) {{
                        button.classList.remove('full');
                        button.textContent = '📄 Truncate';
                    }} else {{
                        button.classList.add('full');
                        button.textContent = '📄 Full';
                    }}

                    // Save preference to localStorage
                    localStorage.setItem('descriptionTruncated', isDescriptionTruncated);
                }}

                function renderItems() {{
                    const container = document.getElementById('items');
                    const summary = document.getElementById('summary');
                    const totalItemsDisplay = document.getElementById('totalItems');

                    summary.textContent = data.total_items + ' items • ' + data.timestamp;
                    totalItemsDisplay.textContent = data.total_items;

                    data.items.forEach((item, index) => {{
                        const images = getImages(item);
                        const description = (item.full_description || item.description || '').replace(/\\r\\n/g, ' ').replace(/\\s+/g, ' ').trim();

                        let thumbnailsHTML = '';
                        images.forEach(imgSrc => {{
                            if (imgSrc) {{
                                thumbnailsHTML += `<img src="${{imgSrc}}" class="item-thumbnail" onclick="openImage('${{imgSrc}}')" alt="Image" title="Click to expand">`;
                            }}
                        }});

                        const descClass = isDescriptionTruncated ? 'truncated' : 'full';

                        const itemHTML = `
                            <div class="item">
                                <div class="item-header">
                                    <h3 class="item-title">
                                        <a href="${{item.item_url}}" target="_blank">${{escapeHtml(item.title)}}</a>
                                    </h3>
                                    <span class="meta-price">${{escapeHtml(item.price)}}</span>
                                    <span class="meta-location">📍 ${{escapeHtml(item.location)}}</span>
                                    <span class="meta-date">📅 ${{escapeHtml(item.date_posted)}}</span>
                                </div>
                                <p class="item-description ${{descClass}}">${{escapeHtml(description)}}</p>
                                <div class="item-images">
                                    ${{thumbnailsHTML}}
                                </div>
                            </div>
                        `;

                        container.innerHTML += itemHTML;
                    }});

                    // Initialize button state
                    const button = document.getElementById('descriptionToggle');
                    if (!isDescriptionTruncated) {{
                        button.classList.add('full');
                        button.textContent = '📄 Full';
                    }}
                    button.addEventListener('click', toggleDescriptionTruncation);
                }}

                // Modal click outside to close
                document.getElementById('imageModal').addEventListener('click', function(e) {{
                    if (e.target === this) {{
                        closeModal();
                    }}
                }});

                // Thumbnail size slider
                const sizeSlider = document.getElementById('sizeSlider');
                const sizeDisplay = document.getElementById('sizeDisplay');

                sizeSlider.addEventListener('input', function(e) {{
                    const size = e.target.value;
                    document.documentElement.style.setProperty('--thumb-size', size + 'px');
                    sizeDisplay.textContent = size + 'px';
                }});

                // Track scroll position
                window.addEventListener('scroll', function() {{
                    const items = document.querySelectorAll('.item');
                    const headerHeight = document.querySelector('.header').offsetHeight + 50;

                    let currentItemIndex = 1;

                    items.forEach((item, index) => {{
                        const rect = item.getBoundingClientRect();
                        if (rect.top < headerHeight + 10) {{
                            currentItemIndex = index + 1;
                        }}
                    }});

                    document.getElementById('currentItem').textContent = currentItemIndex;
                }});

                // Render items on load
                renderItems();
            </script>
        </body>
        </html>
        """

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✓ HTML report saved to: {output_file}")

    def _prepare_items_data(
        self, items: List[BazosItem], include_images: bool, image_map: Optional[dict] = None
    ) -> dict:
        """Prepare items data for JSON serialization"""
        items_list = []

        for item in items:
            # Get images
            image_urls = []
            if include_images:
                if item.item_details and item.item_details.image_urls:
                    image_urls = item.item_details.image_urls
                elif item.image_url:
                    image_urls = [item.image_url]

            # Get description (prefer full_description from item_details)
            description = ""
            if item.item_details and item.item_details.full_description:
                description = item.item_details.full_description
            elif item.description:
                description = item.description

            items_list.append({
                "title": item.title,
                "price": item.price,
                "location": item.location,
                "date_posted": item.date_posted,
                "description": item.description,
                "full_description": description,
                "image_url": item.image_url,
                "image_urls": image_urls,
                "item_url": item.item_url,
            })

        return {
            "total_items": len(items),
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "items": items_list,
        }
