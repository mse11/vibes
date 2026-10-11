"""
Bazos.sk Web Scraper
A powerful Python scraper for extracting classifieds listings from bazos.sk
"""

__version__ = "0.1.0"
__author__ = "Michal Sestrienka"
__email__ = "michal.sestrienka@gmail.com"

from .scraper import (
    BazosScraper,
    BazosItem,
    BazosItemDetails,
    ReportSettings,
    SearchMetadata,
    SCHEMA_VERSION,
    item_from_dict,
    load_results,
    save_results_json,
)
from .reporter import HTMLReportGenerator
from .prompts import PromptConfig, render_prompt, render_prompt_block, PRESETS

__all__ = [
    "BazosScraper",
    "BazosItem",
    "BazosItemDetails",
    "ReportSettings",
    "SearchMetadata",
    "SCHEMA_VERSION",
    "item_from_dict",
    "load_results",
    "save_results_json",
    "HTMLReportGenerator",
    "PromptConfig",
    "render_prompt",
    "render_prompt_block",
    "PRESETS",
]
