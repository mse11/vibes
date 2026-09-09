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

    def generate_dynamic_report(
        self,
        items: List[BazosItem],
        output_file: str = "bazos_report_dynamic.html",
        topic: str = "N/A",
        keyword: str = "N/A",
        include_images: bool = True,
        image_map: Optional[dict] = None,
        truncate_descriptions: bool = False,
    ) -> None:
        """Generate dynamic HTML report with live filtering capabilities"""

        # Prepare data for JavaScript
        items_data = self._prepare_items_data(items, include_images, image_map)
        items_json = json.dumps(items_data)

        # Extract price range for sliders
        prices = []
        for item in items_data['items']:
            price_str = str(item.get('price', '0')).replace('€', '').replace(',', '.').strip()
            try:
                price = float(price_str) if price_str else 0
                if price > 0:
                    prices.append(price)
            except (ValueError, AttributeError):
                pass

        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 1000
        min_price = int(min_price)
        max_price = int(max_price) + 1

        # Extract unique locations
        locations = set()
        for item in items_data['items']:
            if item.get('location'):
                locations.add(item['location'].split(',')[0].strip() if ',' in item['location'] else item['location'])
        locations = sorted(list(locations))

        css_template = """
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
                align-items: flex-start;
                gap: 20px;
                margin-bottom: 15px;
                flex-wrap: wrap;
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
                opacity: 0.9;
                min-width: 150px;
                text-align: center;
                font-weight: 600;
                padding: 6px 12px;
                background: rgba(255,255,255,0.1);
                border-radius: 3px;
                border: 1px solid rgba(255,255,255,0.2);
            }

            .item-counter strong {
                opacity: 1;
                font-weight: 700;
                color: #fff;
            }

            .toggle-description-btn {
                padding: 6px 12px;
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                border-radius: 3px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.85em;
                transition: all 0.2s;
                white-space: nowrap;
            }

            .toggle-description-btn:hover {
                background: rgba(255,255,255,0.2);
                border-color: #fff;
            }

            .toggle-description-btn.full {
                background: #0066cc;
                border-color: #0066cc;
            }

            .filters-container {
                display: flex;
                gap: 12px;
                flex-wrap: wrap;
                align-items: center;
                flex: 1;
                min-width: 300px;
            }

            .filter-group {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }

            .filter-label {
                font-weight: 600;
                font-size: 0.7em;
                color: rgba(255,255,255,0.7);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .filter-input {
                padding: 6px 10px;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 3px;
                font-size: 0.85em;
                font-family: inherit;
                background: rgba(255,255,255,0.1);
                color: white;
                transition: all 0.2s;
                min-width: 150px;
            }

            .filter-input::placeholder {
                color: rgba(255,255,255,0.5);
            }

            .filter-input:focus {
                outline: none;
                border-color: #fff;
                background: rgba(255,255,255,0.2);
                box-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
            }

            .price-inputs {
                display: flex;
                gap: 6px;
                align-items: center;
            }

            .price-input {
                width: 80px;
                padding: 6px 10px;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 3px;
                font-size: 0.85em;
                background: rgba(255,255,255,0.1);
                color: white;
            }

            .price-input::placeholder {
                color: rgba(255,255,255,0.5);
            }

            .price-input:focus {
                outline: none;
                border-color: #fff;
                background: rgba(255,255,255,0.2);
            }

            .price-separator {
                font-weight: 600;
                color: rgba(255,255,255,0.6);
                font-size: 0.9em;
            }

            .location-select {
                min-width: 130px;
                padding: 6px 10px;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 3px;
                font-size: 0.85em;
                font-family: inherit;
                background: rgba(255,255,255,0.1);
                color: white;
                cursor: pointer;
                transition: all 0.2s;
            }

            .location-select option {
                background: #333;
                color: white;
            }

            .location-select:focus {
                outline: none;
                border-color: #fff;
                background: rgba(255,255,255,0.2);
            }

            .clear-filters-btn {
                padding: 6px 12px;
                background: rgba(255, 107, 107, 0.8);
                color: white;
                border: 1px solid rgba(255, 107, 107, 1);
                border-radius: 3px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.85em;
                transition: all 0.2s;
                white-space: nowrap;
                height: fit-content;
                align-self: flex-end;
            }

            .clear-filters-btn:hover {
                background: #ff5252;
                border-color: #ff5252;
                transform: scale(1.05);
            }

            .sort-container {
                display: flex;
                gap: 8px;
                align-items: flex-end;
                flex-wrap: wrap;
            }

            .sort-group {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }

            .sort-label {
                font-weight: 600;
                font-size: 0.7em;
                color: rgba(255,255,255,0.7);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }

            .sort-buttons {
                display: flex;
                gap: 4px;
            }

            .sort-btn {
                padding: 6px 8px;
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                border-radius: 3px;
                cursor: pointer;
                font-size: 0.75em;
                font-weight: 600;
                transition: all 0.2s;
                white-space: nowrap;
            }

            .sort-btn:hover {
                background: rgba(255,255,255,0.2);
                border-color: #fff;
            }

            .sort-btn.active {
                background: #0066cc;
                border-color: #0066cc;
                box-shadow: 0 0 8px rgba(0, 102, 204, 0.5);
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

            .no-results {
                padding: 40px 20px;
                text-align: center;
                color: #999;
                font-size: 1.1em;
            }

            @media (max-width: 1200px) {
                .filters-container {
                    gap: 8px;
                }

                .filter-input {
                    min-width: 120px;
                }

                .price-input {
                    width: 65px;
                }

                .location-select {
                    min-width: 110px;
                }
            }

            @media (max-width: 768px) {
                .header-top {
                    flex-direction: column;
                    align-items: stretch;
                }

                .filters-container {
                    flex-direction: row;
                    gap: 8px;
                    flex-wrap: wrap;
                    width: 100%;
                }

                .filter-group {
                    flex: 1;
                    min-width: 100px;
                }

                .filter-input {
                    min-width: 100%;
                }

                .price-inputs {
                    flex-direction: row;
                }

                .price-input {
                    flex: 1;
                    width: auto;
                    min-width: 60px;
                }

                .location-select {
                    min-width: 100%;
                }

                .clear-filters-btn {
                    flex: 1;
                    min-width: 100%;
                }

                .sort-container {
                    width: 100%;
                    gap: 12px;
                    justify-content: space-between;
                }

                .sort-group {
                    flex: 1;
                }

                .sort-buttons {
                    width: 100%;
                }

                .sort-btn {
                    flex: 1;
                }

                .toggle-description-btn {
                    flex: 1;
                    min-width: 100%;
                }

                .item-counter {
                    width: 100%;
                    text-align: left;
                    margin-top: 10px;
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

        locations_select = "\n".join([f'<option value="">{loc}</option>' for loc in locations[:20]])

        html = f"""
        <!DOCTYPE html>
        <html lang="sk">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bazos.sk - {keyword} (Dynamic)</title>
            {css_template}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="header-top">
                        <div>
                            <h1>🛒 Bazos.sk Items - Dynamic</h1>
                            <p id="summary"></p>
                        </div>

                        <div class="filters-container">
                            <div class="filter-group">
                                <label class="filter-label">🔍 Search</label>
                                <input type="text" id="textSearch" class="filter-input" placeholder="Text...">
                            </div>

                            <div class="filter-group">
                                <label class="filter-label">💰 Price</label>
                                <div class="price-inputs">
                                    <input type="number" id="priceFrom" class="price-input" placeholder="Min" value="0" min="0">
                                    <span class="price-separator">-</span>
                                    <input type="number" id="priceTo" class="price-input" placeholder="Max" value="{max_price}">
                                </div>
                            </div>

                            <div class="filter-group">
                                <label class="filter-label">📍 Location</label>
                                <select id="locationFilter" class="location-select">
                                    <option value="">All</option>
                                    {locations_select}
                                </select>
                            </div>

                            <button id="clearFilters" class="clear-filters-btn">🔄 Clear</button>
                        </div>

                        <div class="sort-container">
                            <div class="sort-group">
                                <label class="sort-label">💰 Price</label>
                                <div class="sort-buttons">
                                    <button class="sort-btn" id="sortPriceAsc" title="Sort price ascending">↑</button>
                                    <button class="sort-btn" id="sortPriceDesc" title="Sort price descending">↓</button>
                                </div>
                            </div>

                            <div class="sort-group">
                                <label class="sort-label">📍 Location</label>
                                <div class="sort-buttons">
                                    <button class="sort-btn" id="sortLocationAsc" title="Sort location A-Z">A-Z</button>
                                    <button class="sort-btn" id="sortLocationDesc" title="Sort location Z-A">Z-A</button>
                                </div>
                            </div>

                            <button id="descriptionToggle" class="toggle-description-btn" title="Toggle description truncation">📄 Truncate</button>

                            <div class="item-counter">
                                <strong id="currentCount">0</strong> / <strong id="totalItems">0</strong>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="items-container" id="items"></div>
                <div id="noResults" class="no-results" style="display: none;">No items match your filters</div>
            </div>

            <div id="imageModal" class="modal">
                <div class="modal-content">
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                    <img id="modalImg" class="modal-img" src="" alt="">
                </div>
            </div>

            <script>
                const allData = {items_json};
                let filteredData = allData.items.slice();
                let currentSort = null; // 'priceAsc', 'priceDesc', 'locationAsc', 'locationDesc'
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

                function parsePrice(priceStr) {{
                    if (!priceStr) return 0;
                    const cleaned = String(priceStr).replace(/[^0-9.,]/g, '').replace(',', '.');
                    return parseFloat(cleaned) || 0;
                }}

                function sortByPrice(ascending) {{
                    // Toggle: if already sorted by price, toggle off
                    if ((currentSort === 'priceAsc' && ascending) || (currentSort === 'priceDesc' && !ascending)) {{
                        currentSort = null;
                    }} else {{
                        currentSort = ascending ? 'priceAsc' : 'priceDesc';
                    }}

                    filteredData = getFilteredData();
                    filteredData = applySorting(filteredData);
                    updateSortButtons();
                    renderItems();
                    updateCounter();
                }}

                function sortByLocation(ascending) {{
                    // Toggle: if already sorted by location, toggle off
                    if ((currentSort === 'locationAsc' && ascending) || (currentSort === 'locationDesc' && !ascending)) {{
                        currentSort = null;
                    }} else {{
                        currentSort = ascending ? 'locationAsc' : 'locationDesc';
                    }}

                    filteredData = getFilteredData();
                    filteredData = applySorting(filteredData);
                    updateSortButtons();
                    renderItems();
                    updateCounter();
                }}

                function updateSortButtons() {{
                    document.querySelectorAll('.sort-btn').forEach(btn => {{
                        btn.classList.remove('active');
                    }});

                    if (currentSort === 'priceAsc') {{
                        document.getElementById('sortPriceAsc').classList.add('active');
                    }} else if (currentSort === 'priceDesc') {{
                        document.getElementById('sortPriceDesc').classList.add('active');
                    }} else if (currentSort === 'locationAsc') {{
                        document.getElementById('sortLocationAsc').classList.add('active');
                    }} else if (currentSort === 'locationDesc') {{
                        document.getElementById('sortLocationDesc').classList.add('active');
                    }}
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
                    try {{
                        localStorage.setItem('descriptionTruncated', isDescriptionTruncated);
                    }} catch(e) {{
                        // localStorage not available
                    }}
                }}

                function getFilteredData() {{
                    const textSearch = document.getElementById('textSearch').value.toLowerCase();
                    const priceFrom = parseFloat(document.getElementById('priceFrom').value) || 0;
                    const priceTo = parseFloat(document.getElementById('priceTo').value) || Infinity;
                    const locationFilter = document.getElementById('locationFilter').value.toLowerCase();

                    return allData.items.filter(item => {{
                        // Text search
                        if (textSearch) {{
                            const searchText = (item.title + ' ' + item.description + ' ' + item.full_description).toLowerCase();
                            if (!searchText.includes(textSearch)) return false;
                        }}

                        // Price filter
                        const price = parsePrice(item.price);
                        if (price < priceFrom || price > priceTo) return false;

                        // Location filter
                        if (locationFilter) {{
                            const itemLocation = (item.location || '').split(',')[0].toLowerCase().trim();
                            if (!itemLocation.includes(locationFilter)) return false;
                        }}

                        return true;
                    }});
                }}

                function applySorting(data) {{
                    if (currentSort === 'priceAsc') {{
                        data.sort((a, b) => parsePrice(a.price) - parsePrice(b.price));
                    }} else if (currentSort === 'priceDesc') {{
                        data.sort((a, b) => parsePrice(b.price) - parsePrice(a.price));
                    }} else if (currentSort === 'locationAsc') {{
                        data.sort((a, b) => (a.location || '').split(',')[0].toLowerCase().trim().localeCompare((b.location || '').split(',')[0].toLowerCase().trim()));
                    }} else if (currentSort === 'locationDesc') {{
                        data.sort((a, b) => (b.location || '').split(',')[0].toLowerCase().trim().localeCompare((a.location || '').split(',')[0].toLowerCase().trim()));
                    }}
                    return data;
                }}

                function applyFilters() {{
                    filteredData = getFilteredData();
                    filteredData = applySorting(filteredData);
                    renderItems();
                    updateCounter();
                }}

                function updateCounter() {{
                    document.getElementById('totalItems').textContent = filteredData.length;
                }}

                function updatePositionCounter() {{
                    const items = document.querySelectorAll('.item');
                    const headerHeight = document.querySelector('.header').offsetHeight + 50;
                    let currentItemIndex = 1;

                    items.forEach((item, index) => {{
                        const rect = item.getBoundingClientRect();
                        if (rect.top < headerHeight + 10) {{
                            currentItemIndex = index + 1;
                        }}
                    }});

                    document.getElementById('currentCount').textContent = currentItemIndex;
                }}

                function renderItems() {{
                    const container = document.getElementById('items');
                    const noResults = document.getElementById('noResults');
                    const summary = document.getElementById('summary');

                    container.innerHTML = '';

                    if (filteredData.length === 0) {{
                        noResults.style.display = 'block';
                        document.getElementById('currentCount').textContent = '0';
                        return;
                    }}

                    noResults.style.display = 'none';
                    summary.textContent = allData.total_items + ' items total • ' + allData.timestamp;

                    filteredData.forEach((item, index) => {{
                        const images = getImages(item);
                        const description = (item.full_description || item.description || '').replace(/\\r\\n/g, ' ').replace(/\\s+/g, ' ').trim();

                        let thumbnailsHTML = '';
                        images.forEach(imgSrc => {{
                            if (imgSrc) {{
                                thumbnailsHTML += `<img src="${{imgSrc}}" class="item-thumbnail" onclick="openImage('${{imgSrc}}')" alt="Image" title="Click to expand">`;
                            }}
                        }});

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
                                <p class="item-description ${{isDescriptionTruncated ? 'truncated' : 'full'}}">${{escapeHtml(description)}}</p>
                                <div class="item-images">
                                    ${{thumbnailsHTML}}
                                </div>
                            </div>
                        `;

                        container.innerHTML += itemHTML;
                    }});

                    // Update position counter after rendering
                    updatePositionCounter();
                }}

                function clearAllFilters() {{
                    // Reset all filter inputs
                    document.getElementById('textSearch').value = '';
                    document.getElementById('priceFrom').value = '0';
                    document.getElementById('priceTo').value = '{max_price}';
                    document.getElementById('locationFilter').value = '';

                    // Reset sorting
                    currentSort = null;
                    updateSortButtons();

                    // Reapply filters (which will be empty now) and update counter
                    filteredData = getFilteredData();
                    filteredData = applySorting(filteredData);
                    renderItems();
                    updateCounter();
                }}

                // Event listeners for filters
                document.getElementById('textSearch').addEventListener('input', applyFilters);
                document.getElementById('priceFrom').addEventListener('input', applyFilters);
                document.getElementById('priceTo').addEventListener('input', applyFilters);
                document.getElementById('locationFilter').addEventListener('change', applyFilters);
                document.getElementById('clearFilters').addEventListener('click', clearAllFilters);

                // Event listeners for sorting
                document.getElementById('sortPriceAsc').addEventListener('click', () => sortByPrice(true));
                document.getElementById('sortPriceDesc').addEventListener('click', () => sortByPrice(false));
                document.getElementById('sortLocationAsc').addEventListener('click', () => sortByLocation(true));
                document.getElementById('sortLocationDesc').addEventListener('click', () => sortByLocation(false));

                // Event listener for description toggle
                const descToggleBtn = document.getElementById('descriptionToggle');
                descToggleBtn.addEventListener('click', toggleDescriptionTruncation);

                // Initialize button state
                if (!isDescriptionTruncated) {{
                    descToggleBtn.classList.add('full');
                    descToggleBtn.textContent = '📄 Full';
                }} else {{
                    descToggleBtn.textContent = '📄 Truncate';
                }}

                // Modal click outside to close
                document.getElementById('imageModal').addEventListener('click', function(e) {{
                    if (e.target === this) {{
                        closeModal();
                    }}
                }});

                // Track scroll position for filtered items
                window.addEventListener('scroll', function() {{
                    updatePositionCounter();
                }});

                // Initialize
                renderItems();
                updateCounter();
            </script>
        </body>
        </html>
        """

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✓ Dynamic HTML report saved to: {output_file}")
