"""
Tests for the LLM prompt generator (prompt command backend)
"""

import pytest
from scrape_bazos.prompts import (
    PRESETS,
    PromptConfig,
    PromptType,
    get_preset,
    render_prompt,
    render_prompt_block,
)


class TestPromptConfig:
    """Test PromptConfig validation/normalization"""

    def test_requires_price_tiers(self):
        with pytest.raises(ValueError):
            PromptConfig(product_name="widgets", price_tiers=[])

    def test_rejects_duplicate_tiers(self):
        with pytest.raises(ValueError):
            PromptConfig(product_name="widgets", price_tiers=[100, 100])

    def test_sorts_tiers(self):
        config = PromptConfig(product_name="widgets", price_tiers=[300, 100, 200])
        assert config.price_tiers == [100.0, 200.0, 300.0]

    def test_default_col3_note_references_header(self):
        config = PromptConfig(
            product_name="widgets", price_tiers=[100], col3_header="Widget Specs"
        )
        assert "Widget Specs" in config.col3_note


class TestPromptType:
    """Test the PromptType enum and its code-defined column structure"""

    def test_all_types_render(self):
        for prompt_type in PromptType:
            prompt = render_prompt(get_preset(prompt_type))
            assert prompt.strip()

    def test_get_preset_accepts_string_or_enum(self):
        by_enum = get_preset(PromptType.RAM)
        by_string = get_preset("pamat")
        assert by_enum.col3_header == by_string.col3_header == "RAM Specs (Type & Speed)"

    def test_get_preset_returns_copy(self):
        a = get_preset(PromptType.RAM)
        b = get_preset(PromptType.RAM)
        a.product_name = "mutated"
        assert b.product_name != "mutated"
        assert PRESETS[PromptType.RAM].product_name != "mutated"

    def test_each_type_has_its_own_columns(self):
        pc_cols = get_preset(PromptType.PC)
        ram_cols = get_preset(PromptType.RAM)
        disk_cols = get_preset(PromptType.DISK)
        custom_cols = get_preset(PromptType.CUSTOM)

        assert pc_cols.col3_header == "CPU Specs"
        assert pc_cols.col6_header == "Proxmox & Jellyfin Fit"
        assert ram_cols.col3_header == "RAM Specs (Type & Speed)"
        assert disk_cols.col3_header == "Disk Specs (Type, Interface & Speed)"
        assert custom_cols.col3_header == "Key Specifications"
        assert custom_cols.col6_header == "Compatibility & Ideal Use Case"

    def test_custom_type_has_no_fixed_identity(self):
        """CUSTOM is the only type without preset content -- caller must
        supply product_name/price_tiers themselves (enforced by the CLI)."""
        config = get_preset(PromptType.CUSTOM)
        assert config.product_name == "items"
        assert config.price_tiers == [100.0]

    def test_sodimm_is_notebook_ram_only(self):
        config = get_preset(PromptType.RAM_SODIMM)
        assert "SO-DIMM" in config.product_name
        assert "SO-DIMM" in config.exclude_text or "DIMM" in config.exclude_text
        assert "desktop DIMM" in config.exclude_text
        assert "SO-DIMM" in config.include_text

    def test_udimm_distinguishes_ecc_and_non_ecc(self):
        config = get_preset(PromptType.RAM_UDIMM)
        assert "ECC" in config.product_name
        assert "non-ECC" in config.col3_note
        assert "ECC" in config.col3_note
        assert "RDIMM" in config.exclude_text

    def test_rdimm_is_always_ecc(self):
        config = get_preset(PromptType.RAM_RDIMM)
        assert "registered" in config.product_name.lower()
        assert "always" in config.col3_note.lower()
        assert "ECC" in config.col3_note
        assert "UDIMM" in config.exclude_text
        assert "SO-DIMM" in config.exclude_text

    def test_ram_variants_share_ram_column_layout(self):
        for prompt_type in (
            PromptType.RAM_SODIMM,
            PromptType.RAM_UDIMM,
            PromptType.RAM_RDIMM,
        ):
            config = get_preset(prompt_type)
            assert config.col4_header == "Capacity & Configuration"
            assert config.col6_header == "Compatibility & Ideal Use Case"

    def test_disk_hdd_excludes_ssd(self):
        config = get_preset(PromptType.DISK_HDD)
        assert "HDD" in config.product_name
        assert "SSD" not in config.product_name
        assert "SSD" in config.exclude_text
        assert "HDD" in config.include_text

    def test_disk_ssd_excludes_hdd(self):
        config = get_preset(PromptType.DISK_SSD)
        assert "SSD" in config.product_name
        assert "HDD" not in config.product_name
        assert "HDD" in config.exclude_text
        assert "SSD" in config.include_text

    def test_disk_variants_share_disk_column_layout(self):
        for prompt_type in (
            PromptType.DISK,
            PromptType.DISK_HDD,
            PromptType.DISK_SSD,
        ):
            config = get_preset(prompt_type)
            assert config.col3_header == "Disk Specs (Type, Interface & Speed)"
            assert config.col4_header == "Capacity & Form Factor"
            assert config.col6_header == "Compatibility & Ideal Use Case"


class TestRenderPrompt:
    """Test the rendered Markdown prompt text"""

    def test_price_categories(self):
        config = PromptConfig(product_name="widgets", price_tiers=[150, 250, 350])
        prompt = render_prompt(config)
        assert "**Up to €150**" in prompt
        assert "**€151 – €250**" in prompt
        assert "**€251 – €350**" in prompt
        assert "**€351+**" in prompt

    def test_single_tier(self):
        config = PromptConfig(product_name="widgets", price_tiers=[100])
        prompt = render_prompt(config)
        assert "**Up to €100**" in prompt
        assert "**€101+**" in prompt

    def test_exclusion_section_only_when_set(self):
        no_exclude = render_prompt(PromptConfig(product_name="widgets", price_tiers=[100]))
        assert "Strict Exclusion" not in no_exclude

        with_exclude = render_prompt(
            PromptConfig(
                product_name="widgets",
                price_tiers=[100],
                exclude_text="broken items",
                include_text="working items",
            )
        )
        assert "**Strict Exclusion:** Do NOT include broken items." in with_exclude
        assert "Only list working items." in with_exclude

    def test_variant_notes_default_on(self):
        prompt = render_prompt(PromptConfig(product_name="widgets", price_tiers=[100]))
        assert "Handling Multi-Item / Variant Listings" in prompt

    def test_variant_notes_can_be_disabled(self):
        config = PromptConfig(
            product_name="widgets", price_tiers=[100], include_variant_notes=False
        )
        assert "Handling Multi-Item / Variant Listings" not in render_prompt(config)

    def test_table_header_uses_configured_columns(self):
        config = PromptConfig(
            product_name="widgets",
            price_tiers=[100],
            col3_header="Widget Specs",
            col4_header="Bundle Size",
            col6_header="Best For",
        )
        prompt = render_prompt(config)
        assert (
            "| Model & Link | Price & Location | Widget Specs | Bundle Size | "
            "Reason for Selection | Best For |" in prompt
        )

    def test_extra_rules_appended(self):
        config = PromptConfig(
            product_name="widgets", price_tiers=[100], extra_rules=["A custom rule."]
        )
        prompt = render_prompt(config)
        assert "7. A custom rule." in prompt

    def test_no_leading_intro_marker(self):
        """Rule 6 always asks the model to skip intro text; make sure our own
        output follows the same discipline before the first table."""
        prompt = render_prompt(get_preset(PromptType.PC))
        assert prompt.startswith("Please analyze the provided dataset")


class TestRenderPromptBlock:
    """Test the PROMPTS-file-style banner wrapper"""

    def test_block_has_banner_and_title(self):
        block = render_prompt_block("RAM", get_preset(PromptType.RAM))
        assert "# PROMPT - RAM" in block
        assert block.count("#" * 51) == 2
