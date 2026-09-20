"""
LLM prompt template generator.

Builds the same kind of "organize these listings into price-tiered Markdown
tables" analysis prompt that used to live only as hand-written, copy/pasted
text in the PROMPTS file at the repo root (see the "# PROMPT - ..." sections
there). This module lets that text be generated (and regenerated) from the
CLI instead.

Each product type is a `PromptType` member, and its table-column structure
(which fields matter for that kind of item) is fixed here in code rather
than left to the CLI caller to invent per-run -- a "CPU Specs" column only
makes sense for PCs/notebooks, "RAM Specs" only for RAM, and so on. The CLI
only ever supplies *content* (product name, price ladder, exclusions,
extra rules), never column headers.
"""

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, List, Optional, Sequence, Union

# Generic column structure used by PromptType.CUSTOM, for a product type
# that has no dedicated preset yet.
DEFAULT_COL3_HEADER = "Key Specifications"
DEFAULT_COL4_HEADER = "Capacity & Configuration"
DEFAULT_COL6_HEADER = "Compatibility & Ideal Use Case"
DEFAULT_EXAMPLE_ITEM = "ITEM NAME"

_BANNER = "#" * 51


class PromptType(str, Enum):
    """Known prompt/product types. Column structure for each lives in PRESETS."""

    PC = "pc"
    NOTEBOOK = "notebook"
    RAM = "pamat"
    RAM_SODIMM = "pamat-sodimm"
    RAM_UDIMM = "pamat-udimm"
    RAM_RDIMM = "pamat-rdimm"
    DISK = "disk"
    DISK_HDD = "disk-hdd"
    DISK_SSD = "disk-ssd"
    CUSTOM = "custom"


@dataclass
class PromptConfig:
    """All the knobs needed to render one price-tiered LLM analysis prompt."""

    product_name: str
    price_tiers: Sequence[float]
    exclude_text: Optional[str] = None
    include_text: Optional[str] = None
    col3_header: str = DEFAULT_COL3_HEADER
    col4_header: str = DEFAULT_COL4_HEADER
    col6_header: str = DEFAULT_COL6_HEADER
    col3_note: Optional[str] = None
    example_item: str = DEFAULT_EXAMPLE_ITEM
    extra_rules: Sequence[str] = field(default_factory=tuple)
    include_variant_notes: bool = True

    def __post_init__(self) -> None:
        if not self.price_tiers:
            raise ValueError("At least one --price-tier is required")

        tiers = sorted(float(t) for t in self.price_tiers)
        if len(tiers) != len(set(tiers)):
            raise ValueError("Price tiers must be unique")
        self.price_tiers = tiers

        if self.col3_note is None:
            self.col3_note = (
                "Explicitly note the form factor or key attribute in the "
                f"**{self.col3_header}** column."
            )


# Presets mirroring the hand-written prompts in PROMPTS, extended with the
# "Handling Multi-Item / Variant Listings" guidance so every generated
# prompt correctly prices bundled/variant listings. Column structure is
# fixed per type here -- not something a CLI caller can override.
PRESETS: Dict[PromptType, PromptConfig] = {
    PromptType.PC: PromptConfig(
        product_name="computers",
        price_tiers=[150, 250, 350],
        col3_header="CPU Specs",
        col4_header="RAM & Storage",
        col6_header="Proxmox & Jellyfin Fit",
        col3_note=(
            "Explicitly note the CPU model, core/thread count, and "
            "generation in the **CPU Specs** column."
        ),
        example_item="HP EliteDesk 800 G4",
        extra_rules=[
            'IMPORTANT: Some prices are listed as a minimum/starting price ("od"), '
            "so don't present these as a guaranteed final price.",
        ],
    ),
    PromptType.NOTEBOOK: PromptConfig(
        product_name="notebooks",
        price_tiers=[150, 250, 350],
        col3_header="CPU Specs",
        col4_header="RAM & Storage",
        col6_header="Proxmox & Jellyfin Fit",
        col3_note=(
            "Explicitly note the CPU model, core/thread count, and "
            "generation in the **CPU Specs** column."
        ),
        example_item="ThinkPad P15",
        extra_rules=[
            'IMPORTANT: Some prices are listed as a minimum/starting price ("od"), '
            "so don't present these as a guaranteed final price.",
        ],
    ),
    PromptType.RAM: PromptConfig(
        product_name="RAM memory modules (DIMM and SO-DIMM)",
        price_tiers=[50, 100, 200],
        col3_header="RAM Specs (Type & Speed)",
        col4_header="Capacity & Configuration",
        col6_header="Compatibility & Ideal Use Case",
        col3_note=(
            "Explicitly note the form factor in the **RAM Specs** column "
            "(e.g., *DDR4-3200 MHz DIMM* for desktops or *DDR5-4800 MHz "
            "SO-DIMM* for mini PCs/laptops)."
        ),
        example_item="Corsair Vengeance LPX 32GB",
        exclude_text="complete PCs, laptops/notebooks, or mini PCs",
        include_text="individual RAM modules or factory-sealed RAM kits",
    ),
    PromptType.RAM_SODIMM: PromptConfig(
        product_name="SO-DIMM RAM memory modules (notebook/laptop memory)",
        price_tiers=[50, 100, 200],
        col3_header="RAM Specs (Type & Speed)",
        col4_header="Capacity & Configuration",
        col6_header="Compatibility & Ideal Use Case",
        col3_note=(
            "Explicitly note the form factor and speed in the **RAM Specs** "
            "column (e.g., *DDR4-3200 MHz SO-DIMM* or *DDR5-4800 MHz "
            "SO-DIMM*). Only SO-DIMM (notebook/laptop/mini PC) modules "
            "belong here -- never a full-size desktop DIMM module."
        ),
        example_item="Crucial 32GB DDR4 SO-DIMM",
        exclude_text=(
            "complete PCs, laptops/notebooks, mini PCs, or full-size "
            "desktop DIMM RAM modules"
        ),
        include_text=(
            "individual SO-DIMM RAM modules (for notebooks/laptops/mini "
            "PCs) or factory-sealed SO-DIMM RAM kits"
        ),
    ),
    PromptType.RAM_UDIMM: PromptConfig(
        product_name=(
            "UDIMM RAM memory modules (desktop unbuffered DIMM, ECC and "
            "non-ECC)"
        ),
        price_tiers=[50, 100, 200],
        col3_header="RAM Specs (Type, Speed & ECC)",
        col4_header="Capacity & Configuration",
        col6_header="Compatibility & Ideal Use Case",
        col3_note=(
            "Explicitly note the form factor, speed, and whether the "
            "module is **ECC** or **non-ECC** in the **RAM Specs** column "
            "(e.g., *DDR4-3200 MHz UDIMM (non-ECC)* or *DDR4-3200 MHz "
            "UDIMM (ECC)*). Every listing must be labeled ECC or non-ECC -- "
            "never leave this ambiguous."
        ),
        example_item="Corsair Vengeance LPX 32GB DDR4 UDIMM",
        exclude_text=(
            "complete PCs, laptops/notebooks, mini PCs, SO-DIMM modules, "
            "or registered/RDIMM modules"
        ),
        include_text=(
            "individual desktop UDIMM RAM modules (ECC or non-ECC) or "
            "factory-sealed UDIMM RAM kits"
        ),
    ),
    PromptType.RAM_RDIMM: PromptConfig(
        product_name=(
            "RDIMM RAM memory modules (registered/buffered server ECC "
            "DIMM)"
        ),
        price_tiers=[50, 100, 200],
        col3_header="RAM Specs (Type & Speed)",
        col4_header="Capacity & Configuration",
        col6_header="Compatibility & Ideal Use Case",
        col3_note=(
            "Explicitly note the form factor and speed in the **RAM "
            "Specs** column (e.g., *DDR4-2933 MHz RDIMM*). RDIMM modules "
            "are always registered/buffered ECC memory, so there's no "
            "need to call out ECC separately -- just confirm the listing "
            "is genuinely RDIMM (registered), not UDIMM or SO-DIMM."
        ),
        example_item="Samsung 32GB DDR4 RDIMM ECC Registered",
        exclude_text=(
            "complete PCs, laptops/notebooks, mini PCs, SO-DIMM modules, "
            "or unbuffered/UDIMM modules"
        ),
        include_text=(
            "individual server RDIMM RAM modules or factory-sealed RDIMM "
            "RAM kits (always registered ECC)"
        ),
    ),
    PromptType.DISK: PromptConfig(
        product_name="storage drives (HDDs and SSDs)",
        price_tiers=[100, 200, 400],
        col3_header="Disk Specs (Type, Interface & Speed)",
        col4_header="Capacity & Form Factor",
        col6_header="Compatibility & Ideal Use Case",
        col3_note=(
            "Explicitly note the drive type, interface, and speed in the "
            "**Disk Specs** column (e.g., *NVMe PCIe 4.0 SSD (Up to 7,450 "
            'MB/s)*, *SATA III 6Gb/s 2.5" SSD*, or *7200 RPM 3.5" HDD*).'
        ),
        example_item="Samsung 990 PRO 1TB",
        exclude_text=(
            "complete PCs, laptops/notebooks, external drive enclosures "
            "without pre-installed disks, USB flash drives, or SD/MicroSD "
            "memory cards"
        ),
        include_text="individual internal or external HDDs and SSDs",
    ),
    PromptType.DISK_HDD: PromptConfig(
        product_name="HDDs (traditional spinning hard disk drives)",
        price_tiers=[100, 200, 400],
        col3_header="Disk Specs (Type, Interface & Speed)",
        col4_header="Capacity & Form Factor",
        col6_header="Compatibility & Ideal Use Case",
        col3_note=(
            "Explicitly note the interface, RPM, and form factor in the "
            '**Disk Specs** column (e.g., *7200 RPM SATA III 3.5" HDD* or '
            '*5400 RPM SATA III 2.5" HDD*). Only HDDs (spinning platters) '
            "belong here -- never an SSD."
        ),
        example_item="Seagate BarraCuda 4TB",
        exclude_text=(
            "complete PCs, laptops/notebooks, external drive enclosures "
            "without pre-installed disks, USB flash drives, SD/MicroSD "
            "memory cards, or any SSD (SATA, NVMe, or M.2)"
        ),
        include_text="individual internal or external HDDs (spinning hard disk drives)",
    ),
    PromptType.DISK_SSD: PromptConfig(
        product_name="SSDs (solid-state drives)",
        price_tiers=[100, 200, 400],
        col3_header="Disk Specs (Type, Interface & Speed)",
        col4_header="Capacity & Form Factor",
        col6_header="Compatibility & Ideal Use Case",
        col3_note=(
            "Explicitly note the drive type, interface, and speed in the "
            "**Disk Specs** column (e.g., *NVMe PCIe 4.0 SSD (Up to 7,450 "
            'MB/s)* or *SATA III 6Gb/s 2.5" SSD*). Only SSDs (flash-based) '
            "belong here -- never an HDD."
        ),
        example_item="Samsung 990 PRO 1TB",
        exclude_text=(
            "complete PCs, laptops/notebooks, external drive enclosures "
            "without pre-installed disks, USB flash drives, SD/MicroSD "
            "memory cards, or any HDD (spinning hard disk drive)"
        ),
        include_text="individual internal or external SSDs (SATA, NVMe, or M.2)",
    ),
}


def get_preset(prompt_type: Union[PromptType, str]) -> PromptConfig:
    """Return a fresh, mutable PromptConfig for a `PromptType`.

    `PromptType.CUSTOM` returns the generic column structure (defined by
    the DEFAULT_COL*/DEFAULT_EXAMPLE_ITEM constants above) with placeholder
    product name/price tiers that the caller is expected to replace -- it
    is the only type without a fixed, code-defined product identity.
    """
    if isinstance(prompt_type, str):
        prompt_type = PromptType(prompt_type)

    if prompt_type is PromptType.CUSTOM:
        return PromptConfig(
            product_name="items",
            price_tiers=[100],
            col3_header=DEFAULT_COL3_HEADER,
            col4_header=DEFAULT_COL4_HEADER,
            col6_header=DEFAULT_COL6_HEADER,
            example_item=DEFAULT_EXAMPLE_ITEM,
        )

    return replace(PRESETS[prompt_type])


def _format_price(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:g}"


def _format_price_categories(price_tiers: Sequence[float]) -> List[str]:
    """Turn ascending breakpoints into bold 'Up to €x' / '€x – €y' labels."""
    labels = [f"Up to €{_format_price(price_tiers[0])}"]
    for lo, hi in zip(price_tiers, price_tiers[1:]):
        labels.append(f"€{_format_price(lo + 1)} – €{_format_price(hi)}")
    labels.append(f"€{_format_price(price_tiers[-1] + 1)}+")
    return [f"**{label}**" for label in labels]


def _join_with_and(items: Sequence[str]) -> str:
    items = list(items)
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def render_prompt(config: PromptConfig) -> str:
    """Render the full Markdown analysis prompt described by `config`."""

    categories_str = _join_with_and(_format_price_categories(config.price_tiers))

    lines: List[str] = []
    lines.append(
        "Please analyze the provided dataset or listings and organize the "
        f"recommended **{config.product_name}** into separate section tables "
        f"based on price categories ({categories_str})."
    )
    lines.append("")

    if config.exclude_text:
        exclusion = f"**Strict Exclusion:** Do NOT include {config.exclude_text}."
        if config.include_text:
            exclusion += f" Only list {config.include_text}."
        lines.append(exclusion)
        lines.append("")

    if config.include_variant_notes:
        lines.append("**Handling Multi-Item / Variant Listings:**")
        lines.append(
            "1. If a listing contains multiple options, variants, or bundled "
            "parts, evaluate the **exact price of the specific target item**, "
            "NOT the lowest base listing price for unrelated or cheaper "
            "variant options."
        )
        lines.append(
            "2. Place the item into the price category corresponding to the "
            "actual cost of the specific item variant specified in the table row."
        )
        lines.append(
            "3. In the **Price & Location** column, explicitly note if "
            "selecting a specific variant/option is required to get that "
            "price (e.g., *€PRICE [Selected: VARIANT NAME]*)."
        )
        lines.append("")

    lines.append(
        "For **each category**, create a Markdown table containing the "
        "following exact columns:"
    )
    lines.append("")
    lines.append(
        f"| Model & Link | Price & Location | {config.col3_header} | "
        f"{config.col4_header} | Reason for Selection | {config.col6_header} |"
    )
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    lines.append("")

    rules = [
        "Use standard bold text for each category title above its respective table.",
        (
            "Embed the direct URL inside the **Model & Link** column using "
            f"valid Markdown syntax (e.g., `[{config.example_item}]"
            "(https://direct-link-url.com)`). Ensure full `https://` URLs "
            "are used with no trailing space or search query wrappers."
        ),
        config.col3_note,
        "Do not include any external system citation tags or inline metadata.",
        "Keep descriptions concise and punchy so the table remains easy to read.",
        "Jump straight into the first category table without any introductory text.",
    ]
    rules.extend(config.extra_rules)

    lines.append("**Formatting Rules:**")
    for i, rule in enumerate(rules, 1):
        lines.append(f"{i}. {rule}")

    return "\n".join(lines) + "\n"


def render_prompt_block(title: str, config: PromptConfig) -> str:
    """Render the prompt wrapped in the banner style used by the PROMPTS file."""
    return f"{_BANNER}\n# PROMPT - {title}\n{_BANNER}\n\n{render_prompt(config)}"
