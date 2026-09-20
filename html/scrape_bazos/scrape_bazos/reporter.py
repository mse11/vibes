"""
HTML Report generator and image downloader for Bazos scraper results
"""

import json
import re
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
                /* PERF: skip layout/paint for off-screen items.
                   'auto' remembers the real size once an item has been rendered,
                   so the scrollbar stays stable. Ctrl+F still finds the text. */
                content-visibility: auto;
                contain-intrinsic-size: auto 260px;
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
            }

            /* PERF: truncation is toggled with ONE class on the container instead of
               touching every .item-description node. */
            .items-container.desc-truncated .item-description {
                -webkit-line-clamp: 2;
                line-clamp: 2;
            }

            .items-container.desc-full .item-description {
                -webkit-line-clamp: unset;
                line-clamp: unset;
            }

            .item-description.truncated {
                -webkit-line-clamp: 2;
                line-clamp: 2;
            }

            .item-description.full {
                -webkit-line-clamp: unset;
                line-clamp: unset;
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

            .modal-nav {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                background: rgba(0, 0, 0, 0.5);
                color: white;
                border: none;
                font-size: 30px;
                padding: 10px 15px;
                cursor: pointer;
                border-radius: 3px;
                transition: all 0.2s;
                z-index: 1001;
            }

            .modal-nav:hover {
                background: rgba(0, 0, 0, 0.8);
                transform: translateY(-50%) scale(1.1);
            }

            .modal-nav.prev {
                left: 20px;
            }

            .modal-nav.next {
                right: 20px;
            }

            .modal-nav:disabled {
                opacity: 0.3;
                cursor: not-allowed;
            }

            .modal-nav:disabled:hover {
                transform: translateY(-50%);
                background: rgba(0, 0, 0, 0.5);
            }

            .modal-counter {
                position: absolute;
                bottom: -30px;
                left: 50%;
                transform: translateX(-50%);
                color: white;
                font-size: 0.9em;
                font-weight: 600;
                white-space: nowrap;
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
        category: str = "N/A",
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
            <title>Bazos.sk - {category} - {keyword}</title>
            {self.css_template}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="header-top">
                        <div>
                            <h1>🛒 Bazos.sk Items</h1>
                            <p class="report-subtitle" style="opacity:.85;margin:2px 0 0">📂 {category} &nbsp;·&nbsp; 🔎 {keyword}</p>
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
                    <button class="modal-nav prev" id="prevImageBtn" onclick="previousImage()" title="Previous image (←)">&lsaquo;</button>
                    <img id="modalImg" class="modal-img" src="" alt="">
                    <button class="modal-nav next" id="nextImageBtn" onclick="nextImage()" title="Next image (→)">&rsaquo;</button>
                    <div class="modal-counter"><span id="imageCounter">1 / 1</span></div>
                </div>
            </div>

            <script>
                const data = {items_json};
                let isDescriptionTruncated = {str(truncate_descriptions).lower()};
                let currentImages = [];
                let currentImageIndex = 0;

                // `el` is passed by the delegated click handler; the fallback keeps
                // any inline onclick="openImage(this.src)" working.
                function openImage(src, el) {{
                    const modal = document.getElementById('imageModal');
                    const img = document.getElementById('modalImg');

                    // Find all images in current item
                    const clicked = el || (typeof event !== 'undefined' && event ? event.target : null);
                    const itemDiv = clicked ? clicked.closest('.item') : null;
                    const thumbnails = itemDiv ? Array.from(itemDiv.querySelectorAll('.item-thumbnail')) : [];
                    currentImages = thumbnails.map(t => t.src);
                    currentImageIndex = Math.max(0, thumbnails.indexOf(clicked));

                    img.src = src;
                    modal.classList.add('show');
                    updateImageNavigation();

                    // Add keyboard navigation
                    document.addEventListener('keydown', handleImageKeyboard);
                }}

                function closeModal() {{
                    document.getElementById('imageModal').classList.remove('show');
                    document.removeEventListener('keydown', handleImageKeyboard);
                }}

                function previousImage() {{
                    if (currentImageIndex > 0) {{
                        currentImageIndex--;
                        updateImage();
                    }}
                }}

                function nextImage() {{
                    if (currentImageIndex < currentImages.length - 1) {{
                        currentImageIndex++;
                        updateImage();
                    }}
                }}

                function updateImage() {{
                    const img = document.getElementById('modalImg');
                    img.src = currentImages[currentImageIndex];
                    updateImageNavigation();
                }}

                function updateImageNavigation() {{
                    const prevBtn = document.getElementById('prevImageBtn');
                    const nextBtn = document.getElementById('nextImageBtn');
                    const counter = document.getElementById('imageCounter');

                    prevBtn.disabled = currentImageIndex === 0;
                    nextBtn.disabled = currentImageIndex === currentImages.length - 1;
                    counter.textContent = (currentImageIndex + 1) + ' / ' + currentImages.length;
                }}

                function handleImageKeyboard(e) {{
                    if (!document.getElementById('imageModal').classList.contains('show')) return;

                    if (e.key === 'ArrowLeft') {{
                        previousImage();
                    }} else if (e.key === 'ArrowRight') {{
                        nextImage();
                    }}
                }}

                function getImages(item) {{
                    if (item.image_urls && item.image_urls.length > 0) {{
                        return item.image_urls;
                    }}
                    return [item.image_url];
                }}

                // PERF: pure-string escaping. The old version created a DOM node per
                // call (~5 per item = thousands of throwaway elements per render).
                const HTML_ESCAPES = {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }};
                function escapeHtml(text) {{
                    if (text === null || text === undefined) return '';
                    const s = typeof text === 'string' ? text : String(text);
                    return /[&<>"']/.test(s) ? s.replace(/[&<>"']/g, c => HTML_ESCAPES[c]) : s;
                }}

                function truncateText(text, maxLength = 180) {{
                    if (text.length > maxLength) {{
                        return text.substring(0, maxLength) + '...';
                    }}
                    return text;
                }}

                // PERF: flipping one class on the container beats walking every
                // .item-description node (see the .items-container.desc-* CSS rules).
                function applyTruncationClass() {{
                    const container = document.getElementById('items');
                    container.classList.toggle('desc-truncated', isDescriptionTruncated);
                    container.classList.toggle('desc-full', !isDescriptionTruncated);
                }}

                function toggleDescriptionTruncation() {{
                    isDescriptionTruncated = !isDescriptionTruncated;
                    const button = document.getElementById('descriptionToggle');

                    applyTruncationClass();

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
                    }} catch (e) {{
                        // localStorage not available
                    }}
                }}

                function buildItemHTML(item) {{
                    const images = getImages(item);
                    const description = (item.full_description || item.description || '').replace(/\\r\\n/g, ' ').replace(/\\s+/g, ' ').trim();

                    let thumbnailsHTML = '';
                    for (let i = 0; i < images.length; i++) {{
                        const imgSrc = images[i];
                        if (imgSrc) {{
                            // PERF: lazy + async decode keeps the browser from firing
                            // thousands of image requests at once; the click is handled
                            // by one delegated listener instead of an inline handler.
                            thumbnailsHTML += '<img src="' + escapeHtml(imgSrc) + '" class="item-thumbnail" loading="lazy" decoding="async" alt="Image" title="Click to expand">';
                        }}
                    }}

                    return '<div class="item">'
                        + '<div class="item-header">'
                        + '<h3 class="item-title"><a href="' + escapeHtml(item.item_url) + '" target="_blank" rel="noopener">' + escapeHtml(item.title) + '</a></h3>'
                        + '<span class="meta-price">' + escapeHtml(item.price) + '</span>'
                        + '<span class="meta-location">📍 ' + escapeHtml(item.location) + '</span>'
                        + '<span class="meta-date">📅 ' + escapeHtml(item.date_posted) + '</span>'
                        + '</div>'
                        + '<p class="item-description">' + escapeHtml(description) + '</p>'
                        + '<div class="item-images">' + thumbnailsHTML + '</div>'
                        + '</div>';
                }}

                function renderItems() {{
                    const container = document.getElementById('items');
                    const summary = document.getElementById('summary');
                    const totalItemsDisplay = document.getElementById('totalItems');

                    summary.textContent = data.total_items + ' items • ' + data.timestamp;
                    totalItemsDisplay.textContent = data.total_items;

                    // PERF: build the whole list as one string and parse it ONCE.
                    // The old `container.innerHTML += itemHTML` inside the loop
                    // re-parsed and re-laid-out the entire list on every iteration
                    // (O(n^2)); at 1300+ items that is minutes of work.
                    const parts = new Array(data.items.length);
                    for (let i = 0; i < data.items.length; i++) {{
                        parts[i] = buildItemHTML(data.items[i]);
                    }}
                    container.innerHTML = parts.join('');
                    itemNodes = Array.prototype.slice.call(container.children);

                    applyTruncationClass();
                    measureHeaderOffset();
                    schedulePositionUpdate();
                }}

                // Modal click outside to close
                document.getElementById('imageModal').addEventListener('click', function(e) {{
                    if (e.target === this) {{
                        closeModal();
                    }}
                }});

                // PERF: one delegated listener for every thumbnail in the list.
                document.getElementById('items').addEventListener('click', function(e) {{
                    const target = e.target;
                    if (target && target.classList && target.classList.contains('item-thumbnail')) {{
                        openImage(target.src, target);
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

                // ===== PERF: scroll position counter =====
                // Old version read getBoundingClientRect() for EVERY item on EVERY
                // scroll event (1300+ forced layout reads per event). Now the handler
                // is rAF-throttled and binary-searches the item list, so it touches
                // ~log2(n) ≈ 11 elements per frame.
                let itemNodes = [];
                let positionTickScheduled = false;
                let headerOffset = 0;

                function measureHeaderOffset() {{
                    const header = document.querySelector('.header');
                    headerOffset = (header ? header.offsetHeight : 0) + 60;
                }}

                function updatePositionCounter() {{
                    const counter = document.getElementById('currentItem');
                    if (!counter) return;
                    const n = itemNodes.length;
                    if (n === 0) {{
                        counter.textContent = '0';
                        return;
                    }}

                    let lo = 0, hi = n - 1, found = 0;
                    while (lo <= hi) {{
                        const mid = (lo + hi) >> 1;
                        if (itemNodes[mid].getBoundingClientRect().top < headerOffset) {{
                            found = mid;
                            lo = mid + 1;
                        }} else {{
                            hi = mid - 1;
                        }}
                    }}

                    counter.textContent = found + 1;
                }}

                function schedulePositionUpdate() {{
                    if (positionTickScheduled) return;
                    positionTickScheduled = true;
                    requestAnimationFrame(function() {{
                        positionTickScheduled = false;
                        updatePositionCounter();
                    }});
                }}

                window.addEventListener('scroll', schedulePositionUpdate, {{ passive: true }});
                window.addEventListener('resize', function() {{
                    measureHeaderOffset();
                    schedulePositionUpdate();
                }}, {{ passive: true }});

                // Description toggle button
                const descToggleButton = document.getElementById('descriptionToggle');
                if (!isDescriptionTruncated) {{
                    descToggleButton.classList.add('full');
                    descToggleButton.textContent = '📄 Full';
                }}
                descToggleButton.addEventListener('click', toggleDescriptionTruncation);

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
        category: str = "N/A",
        keyword: str = "N/A",
        include_images: bool = True,
        image_map: Optional[dict] = None,
        truncate_descriptions: bool = False,
    ) -> None:
        """Generate dynamic HTML report with live filtering and cascading keyword search filters"""

        # Prepare data for JavaScript
        items_data = self._prepare_items_data(items, include_images, image_map)
        items_json = json.dumps(items_data)

        # Extract price range for sliders.
        # This must normalise prices exactly the way the page's JavaScript
        # parsePrice() does -- strip everything that is not a digit, dot or
        # comma -- otherwise a price like "1 300 €" is skipped here (float()
        # chokes on the thousands separator) while the browser reads it as
        # 1300, and the default max would silently filter that item out.
        prices = []
        for item in items_data['items']:
            price_str = re.sub(r'[^0-9.,]', '', str(item.get('price', '') or '')).replace(',', '.')
            try:
                price = float(price_str) if price_str else 0
            except (ValueError, AttributeError):
                continue
            if price > 0:
                prices.append(price)

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

            .item-counter .counter-total {
                opacity: 0.7;
                font-weight: 400;
            }

            /* ===== NEW: Cascading Filters Styles ===== */
            .filters-management-section {
                background: rgba(0,0,0,0.2);
                padding: 12px;
                margin-top: 15px;
                border-radius: 3px;
                border: 1px solid rgba(255,255,255,0.2);
            }

            .filters-management-title {
                font-weight: 600;
                font-size: 0.75em;
                color: rgba(255,255,255,0.7);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .filters-list {
                display: flex;
                flex-direction: column;
                gap: 8px;
                margin-bottom: 10px;
            }

            .filter-row {
                display: flex;
                gap: 8px;
                align-items: center;
                background: rgba(255,255,255,0.05);
                padding: 8px;
                border-radius: 3px;
                border: 1px solid rgba(255,255,255,0.1);
                flex-wrap: wrap;
            }

            .filter-row-number {
                font-weight: 600;
                font-size: 0.75em;
                color: #0066cc;
                min-width: 20px;
                text-align: center;
            }

            .filter-key-select {
                flex: 1;
                min-width: 100px;
                padding: 6px 8px;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 3px;
                font-size: 0.85em;
                font-family: inherit;
                background: rgba(255,255,255,0.1);
                color: white;
                cursor: pointer;
                transition: all 0.2s;
            }

            .filter-key-select option {
                background: #333;
                color: white;
            }

            .filter-key-select:focus {
                outline: none;
                border-color: #fff;
                background: rgba(255,255,255,0.2);
            }

            .filter-value-input {
                flex: 2;
                min-width: 120px;
                padding: 6px 10px;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 3px;
                font-size: 0.85em;
                font-family: inherit;
                background: rgba(255,255,255,0.1);
                color: white;
                transition: all 0.2s;
            }

            .filter-value-input::placeholder {
                color: rgba(255,255,255,0.5);
            }

            .filter-value-input:focus {
                outline: none;
                border-color: #fff;
                background: rgba(255,255,255,0.2);
                box-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
            }

            .filter-delete-btn {
                padding: 5px 8px;
                background: rgba(255, 107, 107, 0.8);
                color: white;
                border: 1px solid rgba(255, 107, 107, 1);
                border-radius: 3px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.75em;
                transition: all 0.2s;
                white-space: nowrap;
            }

            .filter-delete-btn:hover {
                background: #ff5252;
                border-color: #ff5252;
                transform: scale(1.05);
            }

            .filters-actions {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
                align-items: center;
            }

            /* Diacritics matching mode selector (Ignore diacritics / Exact) */
            .match-mode {
                display: flex;
                align-items: center;
                gap: 6px;
                margin-left: auto;
                font-size: 0.8em;
                color: rgba(255,255,255,0.75);
                white-space: nowrap;
            }

            .match-mode-select {
                padding: 5px 8px;
                background: rgba(255,255,255,0.1);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 3px;
                cursor: pointer;
                font-size: 1em;
            }

            .match-mode-select option {
                background: #2c3e50;
                color: white;
            }

            .add-filter-btn {
                padding: 6px 12px;
                background: #0066cc;
                color: white;
                border: 1px solid #0066cc;
                border-radius: 3px;
                cursor: pointer;
                font-weight: 600;
                font-size: 0.85em;
                transition: all 0.2s;
                white-space: nowrap;
            }

            .add-filter-btn:hover {
                background: #0052a3;
                border-color: #0052a3;
                transform: scale(1.05);
            }

            .clear-all-filters-btn {
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
            }

            .clear-all-filters-btn:hover {
                background: #ff5252;
                border-color: #ff5252;
                transform: scale(1.05);
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
                /* PERF: skip layout/paint for off-screen items.
                   'auto' remembers the real size once an item has been rendered,
                   so the scrollbar stays stable. Ctrl+F still finds the text. */
                content-visibility: auto;
                contain-intrinsic-size: auto 260px;
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
            }

            /* PERF: truncation is toggled with ONE class on the container instead of
               touching every .item-description node. */
            .items-container.desc-truncated .item-description {
                -webkit-line-clamp: 2;
                line-clamp: 2;
            }

            .items-container.desc-full .item-description {
                -webkit-line-clamp: unset;
                line-clamp: unset;
            }

            .item-description.truncated {
                -webkit-line-clamp: 2;
                line-clamp: 2;
            }

            .item-description.full {
                -webkit-line-clamp: unset;
                line-clamp: unset;
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

            .modal-nav {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                background: rgba(0, 0, 0, 0.5);
                color: white;
                border: none;
                font-size: 30px;
                padding: 10px 15px;
                cursor: pointer;
                border-radius: 3px;
                transition: all 0.2s;
                z-index: 1001;
            }

            .modal-nav:hover {
                background: rgba(0, 0, 0, 0.8);
                transform: translateY(-50%) scale(1.1);
            }

            .modal-nav.prev {
                left: 20px;
            }

            .modal-nav.next {
                right: 20px;
            }

            .modal-nav:disabled {
                opacity: 0.3;
                cursor: not-allowed;
            }

            .modal-nav:disabled:hover {
                transform: translateY(-50%);
                background: rgba(0, 0, 0, 0.5);
            }

            .modal-counter {
                position: absolute;
                bottom: -30px;
                left: 50%;
                transform: translateX(-50%);
                color: white;
                font-size: 0.9em;
                font-weight: 600;
                white-space: nowrap;
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

                .filter-row {
                    flex-direction: column;
                }

                .filter-key-select,
                .filter-value-input {
                    width: 100%;
                    min-width: unset;
                }

                .filters-management-section {
                    margin-top: 10px;
                    padding: 10px;
                }

                .filters-actions {
                    width: 100%;
                }

                .add-filter-btn,
                .clear-all-filters-btn {
                    flex: 1;
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
            <title>Bazos.sk - {category} - {keyword} (Dynamic)</title>
            {css_template}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="header-top">
                        <div>
                            <h1>🛒 Bazos.sk Items - Dynamic</h1>
                            <p class="report-subtitle" style="opacity:.85;margin:2px 0 0">📂 {category} &nbsp;·&nbsp; 🔎 {keyword}</p>
                            <p id="summary"></p>
                        </div>

                        <div class="filters-container">
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

                            <div class="slider-container">
                                <span class="slider-label">Thumbnails:</span>
                                <input type="range" min="40" max="300" value="150" class="slider" id="sizeSlider">
                                <span class="thumb-size-display" id="sizeDisplay">150px</span>
                            </div>

                            <div class="item-counter" title="item you are looking at / items matching the filters (of all scraped items)">
                                <strong id="currentCount">0</strong> / <strong id="totalItems">0</strong><span id="totalAllItems" class="counter-total"></span>
                            </div>
                        </div>

                        <!-- NEW: Cascading Keyword Filters Section -->
                        <div class="filters-management-section">
                            <div class="filters-management-title">
                                🔎 Cascading Keyword Filters
                            </div>
                            <div class="filters-list" id="filtersList">
                                <!-- Filter rows will be added here by JavaScript -->
                            </div>
                            <div class="filters-actions">
                                <button id="addFilterBtn" class="add-filter-btn">+ Add Filter</button>
                                <button id="clearAllFiltersBtn" class="clear-all-filters-btn">Clear All Filters</button>
                                <label class="match-mode" for="matchMode" title="Diacritics-insensitive: 'otocna' also matches 'otočná' (like the bazos.sk search box). Exact: match the letters exactly as typed.">
                                    Matching:
                                    <select id="matchMode" class="match-mode-select">
                                        <option value="fold" selected>Ignore diacritics (č = c)</option>
                                        <option value="exact">Exact</option>
                                    </select>
                                </label>
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
                    <button class="modal-nav prev" id="prevImageBtn" onclick="previousImage()" title="Previous image (←)">&lsaquo;</button>
                    <img id="modalImg" class="modal-img" src="" alt="">
                    <button class="modal-nav next" id="nextImageBtn" onclick="nextImage()" title="Next image (→)">&rsaquo;</button>
                    <div class="modal-counter"><span id="imageCounter">1 / 1</span></div>
                </div>
            </div>

            <script>
                const allData = {items_json};
                let filteredData = allData.items.slice();
                let currentSort = null;
                let isDescriptionTruncated = {str(truncate_descriptions).lower()};
                let currentImages = [];
                let currentImageIndex = 0;

                // NEW: Cascading Filters State
                let filters = [
                    {{ key: 'any', value: '' }}  // Default filter: search every field
                ];
                // 'any' is a virtual key: it searches all of SEARCH_ALL_KEYS at once,
                // which is what the bazos.sk search box does.
                const AVAILABLE_KEYS = ['any', 'title', 'description', 'full_description', 'price', 'location'];
                const SEARCH_ALL_KEYS = ['title', 'description', 'full_description', 'price', 'location'];
                const KEY_LABELS = {{ any: 'any (all fields)' }};
                const DEFAULT_FILTER_KEY = 'any';

                // NEW: keyword matching mode.
                // true  -> diacritics-insensitive (default): 'otocna' matches 'otočná',
                //          'otočná' matches 'otocna'. This is how bazos.sk itself searches.
                // false -> exact: the letters must match as typed.
                let ignoreDiacritics = true;

                // Strip combining marks so č->c, š->s, á->a, ľ->l, ô->o, ...
                function foldDiacritics(text) {{
                    return text.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
                }}

                // ===== IMAGE MODAL FUNCTIONS =====
                function openImage(src) {{
                    const modal = document.getElementById('imageModal');
                    const img = document.getElementById('modalImg');

                    const clicked = event.target;
                    const itemDiv = clicked.closest('.item');
                    const thumbnails = itemDiv.querySelectorAll('.item-thumbnail');
                    currentImages = Array.from(thumbnails).map(t => t.src);
                    currentImageIndex = Array.from(thumbnails).indexOf(clicked);

                    img.src = src;
                    modal.classList.add('show');
                    updateImageNavigation();

                    document.addEventListener('keydown', handleImageKeyboard);
                }}

                function closeModal() {{
                    document.getElementById('imageModal').classList.remove('show');
                    document.removeEventListener('keydown', handleImageKeyboard);
                }}

                function previousImage() {{
                    if (currentImageIndex > 0) {{
                        currentImageIndex--;
                        updateImage();
                    }}
                }}

                function nextImage() {{
                    if (currentImageIndex < currentImages.length - 1) {{
                        currentImageIndex++;
                        updateImage();
                    }}
                }}

                function updateImage() {{
                    const img = document.getElementById('modalImg');
                    img.src = currentImages[currentImageIndex];
                    updateImageNavigation();
                }}

                function updateImageNavigation() {{
                    const prevBtn = document.getElementById('prevImageBtn');
                    const nextBtn = document.getElementById('nextImageBtn');
                    const counter = document.getElementById('imageCounter');

                    prevBtn.disabled = currentImageIndex === 0;
                    nextBtn.disabled = currentImageIndex === currentImages.length - 1;
                    counter.textContent = (currentImageIndex + 1) + ' / ' + currentImages.length;
                }}

                function handleImageKeyboard(e) {{
                    if (!document.getElementById('imageModal').classList.contains('show')) return;

                    if (e.key === 'ArrowLeft') {{
                        previousImage();
                    }} else if (e.key === 'ArrowRight') {{
                        nextImage();
                    }}
                }}

                // ===== UTILITY FUNCTIONS =====
                function getImages(item) {{
                    if (item.image_urls && item.image_urls.length > 0) {{
                        return item.image_urls;
                    }}
                    return [item.image_url];
                }}

                // PERF: pure-string escaping. The old version created a DOM node per
                // call (~5 per item = thousands of throwaway elements per render).
                const HTML_ESCAPES = {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }};
                function escapeHtml(text) {{
                    if (text === null || text === undefined) return '';
                    const s = typeof text === 'string' ? text : String(text);
                    return /[&<>"']/.test(s) ? s.replace(/[&<>"']/g, c => HTML_ESCAPES[c]) : s;
                }}

                function parsePrice(priceStr) {{
                    if (!priceStr) return 0;
                    const cleaned = String(priceStr).replace(/[^0-9.,]/g, '').replace(',', '.');
                    return parseFloat(cleaned) || 0;
                }}

                // ===== PERF: per-item derived-value caches =====
                // Filtering and sorting used to re-lowercase and re-parse the same
                // strings on every keystroke. Each derived value is computed once
                // per item and reused for the life of the page.
                // `folded` picks the diacritics-stripped variant; both variants are
                // cached separately so switching the matching mode costs nothing.
                function lcField(item, key, folded) {{
                    const cacheKey = folded ? '__fd' : '__lc';
                    let cache = item[cacheKey];
                    if (cache === undefined) {{
                        cache = item[cacheKey] = Object.create(null);
                    }}
                    let value = cache[key];
                    if (value === undefined) {{
                        let raw;
                        if (key === 'any') {{
                            // Virtual key: every field joined with a newline so a needle
                            // can never match across a field boundary.
                            const parts = [];
                            for (let k = 0; k < SEARCH_ALL_KEYS.length; k++) {{
                                const v = item[SEARCH_ALL_KEYS[k]];
                                if (v !== null && v !== undefined) parts.push(String(v));
                            }}
                            raw = parts.join('\\n');
                        }} else {{
                            raw = String(item[key] === null || item[key] === undefined ? '' : item[key]);
                        }}
                        value = raw.toLowerCase();
                        if (folded) value = foldDiacritics(value);
                        cache[key] = value;
                    }}
                    return value;
                }}

                function itemPrice(item) {{
                    let p = item.__price;
                    if (p === undefined) {{
                        p = item.__price = parsePrice(item.price);
                    }}
                    return p;
                }}

                function itemCity(item, folded) {{
                    if (folded) {{
                        let cf = item.__cityFd;
                        if (cf === undefined) {{
                            cf = item.__cityFd = foldDiacritics(itemCity(item, false));
                        }}
                        return cf;
                    }}
                    let c = item.__city;
                    if (c === undefined) {{
                        c = item.__city = (item.location || '').split(',')[0].toLowerCase().trim();
                    }}
                    return c;
                }}

                // ===== NEW: CASCADING FILTER FUNCTIONS =====
                function saveFiltersToStorage() {{
                    try {{
                        localStorage.setItem('cascadingFilters', JSON.stringify(filters));
                        localStorage.setItem('filterMatchMode', ignoreDiacritics ? 'fold' : 'exact');
                    }} catch(e) {{
                        // localStorage not available
                    }}
                }}

                function loadFiltersFromStorage() {{
                    try {{
                        const stored = localStorage.getItem('cascadingFilters');
                        if (stored) {{
                            filters = JSON.parse(stored);
                        }}
                        const mode = localStorage.getItem('filterMatchMode');
                        if (mode) {{
                            ignoreDiacritics = mode !== 'exact';
                        }}
                    }} catch(e) {{
                        // localStorage not available
                        filters = [{{ key: DEFAULT_FILTER_KEY, value: '' }}];
                    }}
                    const modeSelect = document.getElementById('matchMode');
                    if (modeSelect) modeSelect.value = ignoreDiacritics ? 'fold' : 'exact';
                }}

                function renderFilterRows() {{
                    const filtersList = document.getElementById('filtersList');
                    filtersList.innerHTML = '';

                    filters.forEach((filter, index) => {{
                        const filterRow = document.createElement('div');
                        filterRow.className = 'filter-row';
                        filterRow.innerHTML = `
                            <div class="filter-row-number">F${{index + 1}}</div>
                            <select class="filter-key-select" data-index="${{index}}">
                                ${{AVAILABLE_KEYS.map(key => `<option value="${{key}}" ${{filter.key === key ? 'selected' : ''}}>${{KEY_LABELS[key] || key}}</option>`).join('')}}
                            </select>
                            <input type="text" class="filter-value-input" data-index="${{index}}" placeholder="Keyword..." value="${{escapeHtml(filter.value)}}">
                            <button class="filter-delete-btn" data-index="${{index}}" title="Delete this filter">✕ Delete</button>
                        `;

                        filterRow.querySelector('.filter-key-select').addEventListener('change', (e) => {{
                            filters[index].key = e.target.value;
                            saveFiltersToStorage();
                            applyAllFilters();
                        }});

                        filterRow.querySelector('.filter-value-input').addEventListener('input', (e) => {{
                            filters[index].value = e.target.value;
                            saveFiltersToStorage();
                            // PERF: debounced - one re-render per typing burst.
                            applyAllFiltersDebounced();
                        }});

                        filterRow.querySelector('.filter-delete-btn').addEventListener('click', () => {{
                            removeFilter(index);
                        }});

                        filtersList.appendChild(filterRow);
                    }});
                }}

                function addFilter() {{
                    filters.push({{ key: DEFAULT_FILTER_KEY, value: '' }});
                    saveFiltersToStorage();
                    renderFilterRows();
                    applyAllFilters();
                }}

                function removeFilter(index) {{
                    filters.splice(index, 1);
                    // Always keep at least one filter
                    if (filters.length === 0) {{
                        filters.push({{ key: DEFAULT_FILTER_KEY, value: '' }});
                    }}
                    saveFiltersToStorage();
                    renderFilterRows();
                    applyAllFilters();
                }}

                function getFilteredData() {{
                    // Get base filters
                    const priceFrom = parseFloat(document.getElementById('priceFrom').value) || 0;
                    const priceTo = parseFloat(document.getElementById('priceTo').value) || Infinity;
                    const fold = ignoreDiacritics;
                    let locationFilter = document.getElementById('locationFilter')?.value.toLowerCase() || '';
                    if (fold && locationFilter) locationFilter = foldDiacritics(locationFilter);

                    // PERF: normalise the active filters once, not once per item.
                    const activeFilters = [];
                    for (let i = 0; i < filters.length; i++) {{
                        let needle = (filters[i].value || '').trim().toLowerCase();
                        if (fold && needle) needle = foldDiacritics(needle);
                        if (needle) activeFilters.push({{ key: filters[i].key, needle: needle }});
                    }}

                    const source = allData.items;
                    const results = [];

                    // PERF: one pass over the data instead of a fresh intermediate
                    // array per filter, using cached lowercase/parsed fields.
                    outer:
                    for (let i = 0; i < source.length; i++) {{
                        const item = source[i];

                        for (let f = 0; f < activeFilters.length; f++) {{
                            if (lcField(item, activeFilters[f].key, fold).indexOf(activeFilters[f].needle) === -1) {{
                                continue outer;
                            }}
                        }}

                        const price = itemPrice(item);
                        if (price < priceFrom || price > priceTo) continue;

                        if (locationFilter && itemCity(item, fold).indexOf(locationFilter) === -1) continue;

                        results.push(item);
                    }}

                    return results;
                }}

                function sortByPrice(ascending) {{
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

                // PERF: flipping one class on the container beats walking every
                // .item-description node (see the .items-container.desc-* CSS rules).
                function applyTruncationClass() {{
                    const container = document.getElementById('items');
                    container.classList.toggle('desc-truncated', isDescriptionTruncated);
                    container.classList.toggle('desc-full', !isDescriptionTruncated);
                }}

                function toggleDescriptionTruncation() {{
                    isDescriptionTruncated = !isDescriptionTruncated;
                    const button = document.getElementById('descriptionToggle');

                    applyTruncationClass();

                    if (isDescriptionTruncated) {{
                        button.classList.remove('full');
                        button.textContent = '📄 Truncate';
                    }} else {{
                        button.classList.add('full');
                        button.textContent = '📄 Full';
                    }}

                    try {{
                        localStorage.setItem('descriptionTruncated', isDescriptionTruncated);
                    }} catch(e) {{
                        // localStorage not available
                    }}
                }}

                // PERF: comparators read cached values (itemPrice / itemCity) instead
                // of re-parsing strings on every one of the n*log(n) comparisons, and
                // location sorting uses a reusable Intl.Collator rather than
                // localeCompare, which builds a collator per call.
                const LOCATION_COLLATOR = typeof Intl !== 'undefined' && Intl.Collator
                    ? new Intl.Collator(undefined, {{ sensitivity: 'base' }})
                    : {{ compare: (a, b) => (a < b ? -1 : a > b ? 1 : 0) }};

                function applySorting(data) {{
                    if (currentSort === 'priceAsc') {{
                        data.sort((a, b) => itemPrice(a) - itemPrice(b));
                    }} else if (currentSort === 'priceDesc') {{
                        data.sort((a, b) => itemPrice(b) - itemPrice(a));
                    }} else if (currentSort === 'locationAsc') {{
                        data.sort((a, b) => LOCATION_COLLATOR.compare(itemCity(a), itemCity(b)));
                    }} else if (currentSort === 'locationDesc') {{
                        data.sort((a, b) => LOCATION_COLLATOR.compare(itemCity(b), itemCity(a)));
                    }}
                    return data;
                }}

                function applyAllFilters() {{
                    filteredData = getFilteredData();
                    filteredData = applySorting(filteredData);
                    renderItems();
                    updateCounter();
                }}

                // PERF: typing in a text/price box fired a full re-filter + full
                // re-render on every keystroke. Coalesce bursts into one render.
                let filterDebounceTimer = null;
                function applyAllFiltersDebounced() {{
                    if (filterDebounceTimer) clearTimeout(filterDebounceTimer);
                    filterDebounceTimer = setTimeout(function() {{
                        filterDebounceTimer = null;
                        applyAllFilters();
                    }}, 150);
                }}

                function updateCounter() {{
                    // currentCount = the item you are scrolled to, totalItems = how many
                    // items match the filters. When a filter is active, also spell out
                    // the full dataset size so "1 / 20" is not mistaken for "no filtering".
                    document.getElementById('totalItems').textContent = filteredData.length;
                    const totalAll = document.getElementById('totalAllItems');
                    if (totalAll) {{
                        const all = allData.items.length;
                        totalAll.textContent = filteredData.length === all ? '' : ' of ' + all;
                    }}
                }}

                // ===== PERF: scroll position counter =====
                // Old version read getBoundingClientRect() for EVERY item on EVERY
                // scroll event (1300+ forced layout reads per event). Now it is
                // rAF-throttled and binary-searches the cached item list, touching
                // ~log2(n) ≈ 11 elements per frame.
                let itemNodes = [];
                let positionTickScheduled = false;
                let headerOffset = 0;

                function measureHeaderOffset() {{
                    const header = document.querySelector('.header');
                    headerOffset = (header ? header.offsetHeight : 0) + 60;
                }}

                function updatePositionCounter() {{
                    const counter = document.getElementById('currentCount');
                    if (!counter) return;
                    const n = itemNodes.length;
                    if (n === 0) {{
                        counter.textContent = '0';
                        return;
                    }}

                    let lo = 0, hi = n - 1, found = 0;
                    while (lo <= hi) {{
                        const mid = (lo + hi) >> 1;
                        if (itemNodes[mid].getBoundingClientRect().top < headerOffset) {{
                            found = mid;
                            lo = mid + 1;
                        }} else {{
                            hi = mid - 1;
                        }}
                    }}

                    counter.textContent = found + 1;
                }}

                function schedulePositionUpdate() {{
                    if (positionTickScheduled) return;
                    positionTickScheduled = true;
                    requestAnimationFrame(function() {{
                        positionTickScheduled = false;
                        updatePositionCounter();
                    }});
                }}

                function buildItemHTML(item) {{
                    const images = getImages(item);
                    const description = (item.full_description || item.description || '').replace(/\\r\\n/g, ' ').replace(/\\s+/g, ' ').trim();

                    let thumbnailsHTML = '';
                    for (let i = 0; i < images.length; i++) {{
                        const imgSrc = images[i];
                        if (imgSrc) {{
                            // PERF: lazy + async decode keeps the browser from firing
                            // thousands of image requests at once; the click is handled
                            // by one delegated listener instead of an inline handler.
                            thumbnailsHTML += '<img src="' + escapeHtml(imgSrc) + '" class="item-thumbnail" loading="lazy" decoding="async" alt="Image" title="Click to expand">';
                        }}
                    }}

                    return '<div class="item">'
                        + '<div class="item-header">'
                        + '<h3 class="item-title"><a href="' + escapeHtml(item.item_url) + '" target="_blank" rel="noopener">' + escapeHtml(item.title) + '</a></h3>'
                        + '<span class="meta-price">' + escapeHtml(item.price) + '</span>'
                        + '<span class="meta-location">📍 ' + escapeHtml(item.location) + '</span>'
                        + '<span class="meta-date">📅 ' + escapeHtml(item.date_posted) + '</span>'
                        + '</div>'
                        + '<p class="item-description">' + escapeHtml(description) + '</p>'
                        + '<div class="item-images">' + thumbnailsHTML + '</div>'
                        + '</div>';
                }}

                function renderItems() {{
                    const container = document.getElementById('items');
                    const noResults = document.getElementById('noResults');
                    const summary = document.getElementById('summary');

                    if (filteredData.length === 0) {{
                        container.textContent = '';
                        itemNodes = [];
                        noResults.style.display = 'block';
                        document.getElementById('currentCount').textContent = '0';
                        return;
                    }}

                    noResults.style.display = 'none';
                    summary.textContent = allData.total_items + ' items total • ' + allData.timestamp;

                    // PERF: build the whole list as one string and parse it ONCE.
                    // The old `container.innerHTML += itemHTML` inside the loop
                    // re-parsed and re-laid-out the entire list on every iteration
                    // (O(n^2)); at 1300+ items that is minutes of work.
                    const parts = new Array(filteredData.length);
                    for (let i = 0; i < filteredData.length; i++) {{
                        parts[i] = buildItemHTML(filteredData[i]);
                    }}
                    container.innerHTML = parts.join('');
                    itemNodes = Array.prototype.slice.call(container.children);

                    applyTruncationClass();
                    measureHeaderOffset();
                    schedulePositionUpdate();
                }}

                function clearAllFilters() {{
                    // Reset filter input
                    document.getElementById('textSearch')?.value ?? '';
                    document.getElementById('priceFrom').value = '0';
                    document.getElementById('priceTo').value = '{max_price}';
                    document.getElementById('locationFilter').value = '';

                    // Reset sorting
                    currentSort = null;
                    updateSortButtons();

                    // Reset cascading filters
                    filters = [{{ key: DEFAULT_FILTER_KEY, value: '' }}];
                    saveFiltersToStorage();
                    renderFilterRows();

                    // Reapply filters
                    applyAllFilters();
                }}

                // ===== EVENT LISTENERS =====
                // PERF: debounced so a burst of keystrokes causes one re-render.
                document.getElementById('priceFrom').addEventListener('input', applyAllFiltersDebounced);
                document.getElementById('priceTo').addEventListener('input', applyAllFiltersDebounced);
                document.getElementById('locationFilter').addEventListener('change', applyAllFilters);
                document.getElementById('clearFilters').addEventListener('click', clearAllFilters);

                document.getElementById('sortPriceAsc').addEventListener('click', () => sortByPrice(true));
                document.getElementById('sortPriceDesc').addEventListener('click', () => sortByPrice(false));
                document.getElementById('sortLocationAsc').addEventListener('click', () => sortByLocation(true));
                document.getElementById('sortLocationDesc').addEventListener('click', () => sortByLocation(false));

                const descToggleBtn = document.getElementById('descriptionToggle');
                descToggleBtn.addEventListener('click', toggleDescriptionTruncation);

                if (!isDescriptionTruncated) {{
                    descToggleBtn.classList.add('full');
                    descToggleBtn.textContent = '📄 Full';
                }} else {{
                    descToggleBtn.textContent = '📄 Truncate';
                }}

                document.getElementById('imageModal').addEventListener('click', function(e) {{
                    if (e.target === this) {{
                        closeModal();
                    }}
                }});

                // PERF: passive + rAF-throttled, and only ~log2(n) rect reads per frame.
                window.addEventListener('scroll', schedulePositionUpdate, {{ passive: true }});
                window.addEventListener('resize', function() {{
                    measureHeaderOffset();
                    schedulePositionUpdate();
                }}, {{ passive: true }});

                // PERF: one delegated listener for every thumbnail in the list,
                // instead of an inline onclick compiled per image.
                document.getElementById('items').addEventListener('click', function(e) {{
                    const target = e.target;
                    if (target && target.classList && target.classList.contains('item-thumbnail')) {{
                        openImage(target.src, target);
                    }}
                }});

                const sizeSlider = document.getElementById('sizeSlider');
                const sizeDisplay = document.getElementById('sizeDisplay');

                sizeSlider.addEventListener('input', function(e) {{
                    const size = e.target.value;
                    document.documentElement.style.setProperty('--thumb-size', size + 'px');
                    sizeDisplay.textContent = size + 'px';
                }});

                // NEW: Cascading Filter Event Listeners
                document.getElementById('addFilterBtn').addEventListener('click', addFilter);
                document.getElementById('clearAllFiltersBtn').addEventListener('click', clearAllFilters);
                document.getElementById('matchMode').addEventListener('change', (e) => {{
                    ignoreDiacritics = e.target.value !== 'exact';
                    saveFiltersToStorage();
                    applyAllFilters();
                }});

                // Initialize
                applyTruncationClass();
                loadFiltersFromStorage();
                renderFilterRows();
                // PERF + correctness: apply any stored filters before the first render
                // instead of rendering all items and immediately re-rendering.
                applyAllFilters();
            </script>
        </body>
        </html>
        """

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"✓ Dynamic HTML report with cascading filters saved to: {output_file}")
