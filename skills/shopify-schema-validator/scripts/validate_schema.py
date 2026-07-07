#!/usr/bin/env python3
"""
Shopify Section Schema Validator

Extracts {% schema %} JSON from .liquid files and validates against
Shopify's official specification.

Usage:
  python3 validate_schema.py <file.liquid>
  python3 validate_schema.py <directory>  # validates all .liquid files
"""

import json
import sys
import re
import os
from pathlib import Path
from typing import Any

# ── Setting type definitions ──────────────────────────────────────────

VALID_SETTING_TYPES = {
    # Basic input
    "text", "textarea", "number", "range", "select", "radio", "checkbox",
    # Specialized input
    "color", "color_background", "color_scheme", "color_scheme_group",
    "font_picker", "image_picker", "url", "video", "video_url",
    "text_alignment",
    # Resource pickers
    "product", "product_list", "collection", "collection_list",
    "page", "blog", "article", "article_list", "link_list",
    # Metaobject pickers
    "metaobject", "metaobject_list",
    # Rich content
    "richtext", "inline_richtext", "html", "liquid",
    # Sidebar (non-input)
    "header", "paragraph",
}

REQUIRED_ATTRS = {
    "text":              ["type", "id", "label"],
    "textarea":          ["type", "id", "label"],
    "number":            ["type", "id", "label"],
    "range":             ["type", "id", "label", "min", "max"],
    "select":            ["type", "id", "label", "options"],
    "radio":             ["type", "id", "label", "options"],
    "checkbox":          ["type", "id", "label"],
    "color":             ["type", "id", "label"],
    "color_background":  ["type", "id", "label"],
    "color_scheme":      ["type", "id", "label"],
    "font_picker":       ["type", "id", "label", "default"],
    "image_picker":      ["type", "id", "label"],
    "url":               ["type", "id", "label"],
    "video_url":         ["type", "id", "label", "accept"],
    "product":           ["type", "id", "label"],
    "product_list":      ["type", "id", "label"],
    "collection":        ["type", "id", "label"],
    "collection_list":   ["type", "id", "label"],
    "page":              ["type", "id", "label"],
    "blog":              ["type", "id", "label"],
    "article":           ["type", "id", "label"],
    "article_list":      ["type", "id", "label"],
    "link_list":         ["type", "id", "label"],
    "richtext":          ["type", "id", "label"],
    "inline_richtext":   ["type", "id", "label"],
    "html":              ["type", "id", "label"],
    "liquid":            ["type", "id", "label"],
    "video":             ["type", "id", "label"],
    "text_alignment":    ["type", "id", "label"],
    "metaobject":        ["type", "id", "label", "metaobject_type"],
    "metaobject_list":   ["type", "id", "label", "metaobject_type"],
    "header":            ["type", "content"],
    "paragraph":         ["type", "content"],
}

# Types that do NOT support a default attribute
NO_DEFAULT_TYPES = {
    "image_picker", "video", "product", "collection", "page", "blog", "article",
}

VALID_TAG_VALUES = {"article", "aside", "div", "footer", "header", "section"}
VALID_LIMIT_VALUES = {1, 2}
VALID_URL_DEFAULTS = {"/collections", "/collections/all"}
VALID_LINKLIST_DEFAULTS = {"main-menu", "footer"}
VALID_VIDEO_ACCEPT = {"youtube", "vimeo"}
MAX_LIST_LIMIT = 50
MAX_RANGE_STEPS = 101
MIN_RANGE_STEPS = 2  # Shopify requires at least 3 distinct values: min, intermediate, max
MAX_BLOCKS_LIMIT = 50  # Shopify's hard limit of 50 blocks per section; max_blocks may only lower it
MAX_SECTION_NAME_LENGTH = 25  # longer names may be truncated/rejected by the theme editor
COLOR_DEFAULT_RE = re.compile(r"^(#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})|rgba?\([^)]*\))$")


class SchemaError:
    def __init__(self, level: str, message: str, path: str = ""):
        self.level = level  # "error" or "warning"
        self.message = message
        self.path = path

    def __str__(self):
        prefix = f"[{self.level.upper()}]"
        loc = f" ({self.path})" if self.path else ""
        return f"  {prefix}{loc} {self.message}"


def extract_schema(content: str) -> str | None:
    """Extract JSON from {% schema %} tag."""
    match = re.search(r'\{%[-\s]*schema\s*[-\s]*%\}(.*?)\{%[-\s]*endschema\s*[-\s]*%\}', content, re.DOTALL)
    return match.group(1).strip() if match else None


def validate_setting(setting: dict, path: str) -> list[SchemaError]:
    """Validate a single setting object."""
    errors = []
    stype = setting.get("type", "")

    if stype not in VALID_SETTING_TYPES:
        errors.append(SchemaError("error", f"Unknown setting type: '{stype}'", path))
        return errors

    # visible_if (conditional settings): a string containing a {{ ... }} Liquid expression
    if "visible_if" in setting:
        visible_if = setting["visible_if"]
        if not isinstance(visible_if, str):
            errors.append(SchemaError("error", "'visible_if' must be a string containing a {{ ... }} Liquid expression", path))
        elif "{{" not in visible_if or "}}" not in visible_if:
            errors.append(SchemaError("warning", "'visible_if' should contain a {{ ... }} Liquid expression (e.g. \"{{ section.settings.show_x }}\")", path))

    # Sidebar settings (header/paragraph) have different rules
    if stype in ("header", "paragraph"):
        if "content" not in setting:
            errors.append(SchemaError("error", f"'{stype}' requires 'content' attribute", path))
        return errors

    # Required attributes
    required = REQUIRED_ATTRS.get(stype, [])
    for attr in required:
        if attr not in setting:
            errors.append(SchemaError("error", f"'{stype}' requires '{attr}' attribute", path))

    sid = setting.get("id", "<no id>")
    spath = f"{path}.{sid}"

    # No-default types
    if stype in NO_DEFAULT_TYPES and "default" in setting:
        errors.append(SchemaError("error", f"'{stype}' does not support 'default' attribute", spath))

    # Empty string default for text/textarea/liquid types
    if stype in ("text", "textarea", "liquid") and setting.get("default") == "":
        errors.append(SchemaError("error", f"'{stype}' default cannot be empty string (remove 'default' key instead)", spath))

    # Default value type checks
    if "default" in setting:
        default = setting["default"]
        if stype in ("text", "textarea") and not isinstance(default, str):
            errors.append(SchemaError("error", f"'{stype}' default must be a string, got: {json.dumps(default)}", spath))
        if stype == "checkbox" and not isinstance(default, bool):
            errors.append(SchemaError("error", f"checkbox default must be a boolean true/false (without quotes), got: {json.dumps(default)}", spath))
        if stype == "number" and (isinstance(default, bool) or not isinstance(default, (int, float))):
            errors.append(SchemaError("error", f"number default must be a number, not a string, got: {json.dumps(default)}", spath))
        if stype == "color" and (not isinstance(default, str) or not COLOR_DEFAULT_RE.match(default)):
            errors.append(SchemaError("warning", f"color default {json.dumps(default)} is not a recognized color format (#RGB, #RRGGBB, rgb() or rgba())", spath))

    # color_scheme without default implicitly depends on the first scheme
    if stype == "color_scheme" and "default" not in setting:
        errors.append(SchemaError("warning", "color_scheme has no 'default' — the section will implicitly fall back to the first color scheme (set one explicitly)", spath))

    # Range validation
    if stype == "range":
        _validate_range(setting, spath, errors)

    # Select/Radio validation
    if stype in ("select", "radio"):
        _validate_options(setting, spath, errors)

    # URL default validation
    if stype == "url" and "default" in setting:
        if setting["default"] not in VALID_URL_DEFAULTS:
            errors.append(SchemaError("error", f"url default must be one of: {VALID_URL_DEFAULTS}", spath))

    # Link list default validation
    if stype == "link_list" and "default" in setting:
        if setting["default"] not in VALID_LINKLIST_DEFAULTS:
            errors.append(SchemaError("error", f"link_list default must be one of: {VALID_LINKLIST_DEFAULTS}", spath))

    # Video URL accept validation
    if stype == "video_url" and "accept" in setting:
        accept = setting["accept"]
        if not isinstance(accept, list):
            errors.append(SchemaError("error", "'accept' must be an array", spath))
        else:
            for val in accept:
                if val not in VALID_VIDEO_ACCEPT:
                    errors.append(SchemaError("error", f"video_url accept value '{val}' must be 'youtube' or 'vimeo'", spath))

    # Product/collection/article list limit
    if stype in ("product_list", "collection_list", "article_list") and "limit" in setting:
        if setting["limit"] > MAX_LIST_LIMIT:
            errors.append(SchemaError("error", f"{stype} limit cannot exceed {MAX_LIST_LIMIT}", spath))

    # Richtext default validation
    if stype == "richtext" and "default" in setting:
        default = setting["default"]
        if isinstance(default, str) and default.strip():
            d = default.strip()
            # Translation keys (t:...) are resolved by Shopify at runtime
            if not d.startswith("t:") and not (d.startswith("<p") or d.startswith("<ul")):
                errors.append(SchemaError("warning", "richtext default should be wrapped in <p> or <ul> tags", spath))

    # Font picker requires default
    if stype == "font_picker" and "default" not in setting:
        errors.append(SchemaError("error", "font_picker requires a 'default' value", spath))

    # Liquid content limit
    if stype == "liquid" and "default" in setting:
        default = setting.get("default", "")
        if isinstance(default, str) and len(default.encode("utf-8")) > 50 * 1024:
            errors.append(SchemaError("error", "liquid content exceeds 50KB limit", spath))

    return errors


def _validate_range(setting: dict, path: str, errors: list[SchemaError]):
    """Validate range-specific rules."""
    min_val = setting.get("min")
    max_val = setting.get("max")
    step = setting.get("step", 1)
    default = setting.get("default")

    # default is required for range
    if "default" not in setting:
        errors.append(SchemaError("error", "range requires a 'default' value", path))

    if min_val is not None and max_val is not None:
        if not isinstance(min_val, (int, float)) or not isinstance(max_val, (int, float)):
            errors.append(SchemaError("error", "range min/max must be numeric", path))
            return

        if min_val >= max_val:
            errors.append(SchemaError("error", f"range min ({min_val}) must be less than max ({max_val})", path))

        if not isinstance(step, (int, float)) or step <= 0:
            errors.append(SchemaError("error", f"range step must be a positive number", path))
        else:
            num_steps = (max_val - min_val) / step
            if num_steps > MAX_RANGE_STEPS:
                errors.append(SchemaError("error", f"range has {num_steps:.0f} steps (max {MAX_RANGE_STEPS})", path))
            if num_steps < MIN_RANGE_STEPS:
                errors.append(SchemaError(
                    "error",
                    f"range has {num_steps:.0f} step(s) but Shopify requires at least {MIN_RANGE_STEPS} "
                    f"(i.e. at least 3 distinct values). Consider using 'select' for 2-value choices.",
                    path,
                ))

        if default is not None:
            if not isinstance(default, (int, float)):
                errors.append(SchemaError("error", "range default must be numeric", path))
            else:
                if default < min_val or default > max_val:
                    errors.append(SchemaError("error", f"range default ({default}) out of bounds [{min_val}, {max_val}]", path))
                if step and step != 0:
                    remainder = (default - min_val) % step
                    if abs(remainder) > 1e-9 and abs(remainder - step) > 1e-9:
                        errors.append(SchemaError("error", f"range default ({default}) is not a valid step from min ({min_val}) with step ({step})", path))


def _validate_options(setting: dict, path: str, errors: list[SchemaError]):
    """Validate select/radio options."""
    options = setting.get("options", [])
    if not isinstance(options, list):
        errors.append(SchemaError("error", "options must be an array", path))
        return

    if len(options) == 0:
        errors.append(SchemaError("error", "options array cannot be empty", path))
        return

    values_seen = set()
    for i, opt in enumerate(options):
        if not isinstance(opt, dict):
            errors.append(SchemaError("error", f"options[{i}] must be an object", path))
            continue
        if "value" not in opt:
            errors.append(SchemaError("error", f"options[{i}] missing 'value'", path))
        if "label" not in opt:
            errors.append(SchemaError("error", f"options[{i}] missing 'label'", path))
        val = opt.get("value")
        if val in values_seen:
            errors.append(SchemaError("error", f"options[{i}] duplicate value: '{val}'", path))
        values_seen.add(val)

    default = setting.get("default")
    if default is not None:
        valid_values = {opt.get("value") for opt in options if isinstance(opt, dict)}
        if default not in valid_values:
            errors.append(SchemaError("error", f"default '{default}' not in options values", path))


def validate_block(block: dict, path: str, accepts_theme_blocks: bool = False,
                   theme_block_types: set | None = None) -> list[SchemaError]:
    """Validate a single block definition."""
    errors = []

    if "type" not in block:
        errors.append(SchemaError("error", "Block missing 'type'", path))

    btype = block.get("type", "<unknown>")
    bpath = f"{path}[{btype}]"

    # @app / @theme entries take no 'name'; their settings live in the app/theme block itself
    if btype in ("@app", "@theme"):
        if "settings" in block:
            errors.append(SchemaError("error", f"'{btype}' blocks cannot define 'settings' (settings belong to the app/theme block itself)", bpath))
        if btype == "@app" and "limit" in block:
            errors.append(SchemaError("error", "@app blocks do not accept 'limit'", bpath))
        return errors

    if "name" not in block:
        if "settings" in block:
            errors.append(SchemaError("error", "Block missing 'name'", bpath))
        elif theme_block_types is not None and btype in theme_block_types:
            pass  # verified theme block reference: /blocks/<type>.liquid exists
        elif not accepts_theme_blocks:
            # A type-only entry may reference a theme block in /blocks (theme blocks
            # generation) — can't always verify from the schema alone, so don't hard-fail
            checked = f" (no /blocks/{btype}.liquid found either)" if theme_block_types is not None else ""
            errors.append(SchemaError(
                "warning",
                f"Block '{btype}' has no 'name' — valid only if it references a theme block in /blocks; locally defined blocks require 'name'{checked}",
                bpath,
            ))
        # With '@theme' present, type-only entries are the documented
        # "recommended theme blocks" pattern — nothing to flag

    # Validate block settings
    settings = block.get("settings", [])
    if not isinstance(settings, list):
        errors.append(SchemaError("error", "Block 'settings' must be an array", bpath))
        return errors
    setting_ids = set()
    for i, setting in enumerate(settings):
        if not isinstance(setting, dict):
            errors.append(SchemaError("error", f"settings[{i}] must be an object", bpath))
            continue
        stype = setting.get("type", "")
        if stype in ("header", "paragraph"):
            errors.extend(validate_setting(setting, bpath))
            continue

        sid = setting.get("id", "")
        if sid and sid in setting_ids:
            errors.append(SchemaError("error", f"Duplicate setting id: '{sid}'", bpath))
        setting_ids.add(sid)
        errors.extend(validate_setting(setting, bpath))

    return errors


def _validate_preset_settings(psettings: Any, known_ids: set, path: str, errors: list[SchemaError]):
    """Validate a preset's settings object against the section's setting ids."""
    if psettings is None:
        return
    if not isinstance(psettings, dict):
        errors.append(SchemaError("error", "preset 'settings' must be an object mapping setting ids to values", path))
        return
    for key in psettings:
        if key not in known_ids:
            errors.append(SchemaError("error", f"preset setting '{key}' does not match any section setting id", path))


def _validate_preset_blocks(pblocks: Any, block_order: Any, path: str,
                            defined_types: set, local_setting_ids: dict,
                            lenient: bool, errors: list[SchemaError],
                            theme_block_types: set | None = None):
    """Validate preset blocks (array or hash form), recursing into nested blocks.

    `lenient` means "unknown types are warnings, not errors" — set when the
    surrounding context is theme-block territory ('@theme' declared, or the
    parent preset block is itself a theme block reference), because the set of
    acceptable types then lives outside this section's schema.
    """
    if isinstance(pblocks, dict):
        # Hash form: {"block-id": {...}} with optional sibling "block_order"
        if block_order is not None:
            if not isinstance(block_order, list):
                errors.append(SchemaError("error", "'block_order' must be an array of block ids", path))
            else:
                for bid in block_order:
                    if bid not in pblocks:
                        errors.append(SchemaError("error", f"block_order id '{bid}' not found in 'blocks'", path))
        entries = [(f"{path}.blocks.{bid}", b) for bid, b in pblocks.items()]
    elif isinstance(pblocks, list):
        entries = [(f"{path}.blocks[{i}]", b) for i, b in enumerate(pblocks)]
    else:
        errors.append(SchemaError("error", "preset 'blocks' must be an array or an object", path))
        return

    for bpath, block in entries:
        if not isinstance(block, dict):
            errors.append(SchemaError("error", "preset block must be an object", bpath))
            continue

        bsettings = block.get("settings")
        if bsettings is not None and not isinstance(bsettings, dict):
            errors.append(SchemaError("error", "preset block 'settings' must be an object mapping setting ids to values", bpath))
            bsettings = None

        btype = block.get("type")
        if not isinstance(btype, str) or not btype:
            errors.append(SchemaError("error", "preset block missing 'type'", bpath))
        elif btype in ("@app", "@theme"):
            pass  # app blocks / theme block placeholders are always acceptable
        elif btype in defined_types:
            if bsettings and btype in local_setting_ids:
                for key in bsettings:
                    if key not in local_setting_ids[btype]:
                        errors.append(SchemaError("error", f"preset block setting '{key}' does not match any setting id of block '{btype}'", bpath))
        elif theme_block_types is not None and btype in theme_block_types:
            pass  # verified theme block: /blocks/<type>.liquid exists
        elif lenient:
            if theme_block_types is not None:
                errors.append(SchemaError("warning", f"preset block type '{btype}' is not defined in this section and no /blocks/{btype}.liquid exists — likely a broken reference", bpath))
            else:
                errors.append(SchemaError("warning", f"preset block type '{btype}' is not defined in this section — assuming it is a theme block from /blocks", bpath))
        else:
            checked = f" (no /blocks/{btype}.liquid found either)" if theme_block_types is not None else ""
            errors.append(SchemaError("error", f"preset block type '{btype}' is not defined in this section's blocks{checked}", bpath))

        # Theme blocks generation allows statically nested blocks inside presets.
        # A nested tree under anything but a locally defined block is governed by
        # the referenced theme/app block's own schema, which we can't see here.
        if "blocks" in block:
            child_lenient = lenient or not (isinstance(btype, str) and btype in local_setting_ids)
            _validate_preset_blocks(
                block.get("blocks"), block.get("block_order"), bpath,
                defined_types, local_setting_ids, child_lenient, errors, theme_block_types,
            )


def validate_schema(schema: dict, filepath: str = "",
                    theme_block_types: set | None = None) -> list[SchemaError]:
    """Validate a complete section schema.

    theme_block_types: file stems of <theme>/blocks/*.liquid when known.
    Used only to *silence* theme-block-reference diagnostics — never to
    escalate severity.
    """
    errors = []
    prefix = filepath or "schema"

    # Required: name
    if "name" not in schema:
        errors.append(SchemaError("error", "Schema missing required 'name' attribute", prefix))
    else:
        name = schema["name"]
        # Translation keys (t:...) are resolved by Shopify at runtime
        if isinstance(name, str) and not name.startswith("t:") and len(name) > MAX_SECTION_NAME_LENGTH:
            errors.append(SchemaError("warning", f"Section name is {len(name)} characters (recommended max {MAX_SECTION_NAME_LENGTH} — the theme editor may truncate or reject longer names)", prefix))

    # Tag validation
    if "tag" in schema:
        if schema["tag"] not in VALID_TAG_VALUES:
            errors.append(SchemaError("error", f"Invalid tag '{schema['tag']}'. Valid: {VALID_TAG_VALUES}", prefix))

    # Limit validation
    if "limit" in schema:
        if schema["limit"] not in VALID_LIMIT_VALUES:
            errors.append(SchemaError("error", f"Section limit must be 1 or 2, got: {schema['limit']}", prefix))

    # Section settings
    settings_list = schema.get("settings", [])
    if not isinstance(settings_list, list):
        errors.append(SchemaError("error", "'settings' must be an array", prefix))
        settings_list = []
    section_setting_ids = set()
    for i, setting in enumerate(settings_list):
        if not isinstance(setting, dict):
            errors.append(SchemaError("error", f"settings[{i}] must be an object", prefix))
            continue
        stype = setting.get("type", "")
        if stype in ("header", "paragraph"):
            errors.extend(validate_setting(setting, f"{prefix}.settings"))
            continue
        sid = setting.get("id", "")
        if sid and sid in section_setting_ids:
            errors.append(SchemaError("error", f"Duplicate section setting id: '{sid}'", prefix))
        section_setting_ids.add(sid)
        errors.extend(validate_setting(setting, f"{prefix}.settings"))

    # Blocks validation
    blocks = schema.get("blocks", [])
    if not isinstance(blocks, list):
        errors.append(SchemaError("error", "'blocks' must be an array", prefix))
        blocks = []
    accepts_theme_blocks = any(isinstance(b, dict) and b.get("type") == "@theme" for b in blocks)
    block_types = set()
    block_names = set()
    theme_entries = 0
    has_local_named_block = False
    for i, block in enumerate(blocks):
        if not isinstance(block, dict):
            errors.append(SchemaError("error", f"blocks[{i}] must be an object", prefix))
            continue
        btype = block.get("type", "")
        bname = block.get("name", "")

        if btype == "@theme":
            theme_entries += 1
            if theme_entries == 2:
                errors.append(SchemaError("error", "Duplicate '@theme' entry in blocks (declare it once)", prefix))
        elif btype != "@app":
            if btype in block_types:
                errors.append(SchemaError("error", f"Duplicate block type: '{btype}'", prefix))
            block_types.add(btype)

            if bname and bname in block_names:
                errors.append(SchemaError("error", f"Duplicate block name: '{bname}'", prefix))
            block_names.add(bname)
            if bname:
                has_local_named_block = True

        errors.extend(validate_block(block, f"{prefix}.blocks", accepts_theme_blocks, theme_block_types))

    if accepts_theme_blocks and has_local_named_block:
        errors.append(SchemaError(
            "warning",
            "Section declares '@theme' but also defines local blocks with 'name' — sections can't support locally defined blocks and theme blocks at the same time",
            prefix,
        ))

    # max_blocks validation
    if "max_blocks" in schema:
        mb = schema["max_blocks"]
        if not isinstance(mb, int) or isinstance(mb, bool) or mb < 1:
            errors.append(SchemaError("error", f"max_blocks must be a positive integer", prefix))
        elif mb > MAX_BLOCKS_LIMIT:
            errors.append(SchemaError("error", f"max_blocks cannot exceed {MAX_BLOCKS_LIMIT} (Shopify's block limit per section)", prefix))

    # Presets validation
    defined_block_types = {
        b.get("type") for b in blocks
        if isinstance(b, dict) and b.get("type") and not str(b.get("type")).startswith("@")
    }
    local_block_setting_ids = {}
    for b in blocks:
        if not (isinstance(b, dict) and b.get("type") and "name" in b):
            continue  # only locally defined blocks have knowable setting ids
        bsettings = b.get("settings", [])
        local_block_setting_ids[b["type"]] = {
            s.get("id") for s in bsettings if isinstance(s, dict) and s.get("id")
        } if isinstance(bsettings, list) else set()

    presets = schema.get("presets", [])
    if not isinstance(presets, list):
        errors.append(SchemaError("error", "'presets' must be an array", prefix))
        presets = []
    for i, preset in enumerate(presets):
        ppath = f"{prefix}.presets[{i}]"
        if not isinstance(preset, dict):
            errors.append(SchemaError("error", f"Preset[{i}] must be an object", prefix))
            continue
        if "name" not in preset:
            errors.append(SchemaError("error", f"Preset[{i}] missing 'name'", prefix))
        _validate_preset_settings(preset.get("settings"), section_setting_ids, ppath, errors)
        if "blocks" in preset:
            _validate_preset_blocks(
                preset.get("blocks"), preset.get("block_order"), ppath,
                defined_block_types, local_block_setting_ids, accepts_theme_blocks, errors,
                theme_block_types,
            )

    # enabled_on / disabled_on mutual exclusion
    if "enabled_on" in schema and "disabled_on" in schema:
        errors.append(SchemaError("error", "Cannot use both 'enabled_on' and 'disabled_on'", prefix))

    return errors


def validate_file(filepath: str) -> list[SchemaError]:
    """Validate a .liquid file's schema."""
    errors = []
    path = Path(filepath)

    if not path.exists():
        return [SchemaError("error", f"File not found: {filepath}")]

    content = path.read_text(encoding="utf-8")

    # Check for multiple schema tags
    schema_count = len(re.findall(r'\{%[-\s]*schema\s*[-\s]*%\}', content))
    if schema_count > 1:
        return [SchemaError("error", "Multiple {% schema %} tags found (only one allowed)", str(path))]
    if schema_count == 0:
        return []  # No schema tag = not a section file, skip

    raw_json = extract_schema(content)
    if raw_json is None:
        return [SchemaError("error", "Could not extract schema JSON", str(path))]

    # JSON syntax check
    try:
        schema = json.loads(raw_json)
    except json.JSONDecodeError as e:
        return [SchemaError("error", f"Invalid JSON: {e}", str(path))]

    if not isinstance(schema, dict):
        return [SchemaError("error", "Schema must be a JSON object", str(path))]

    # Theme blocks live in <theme root>/blocks/*.liquid — collect their file
    # stems so type-only theme block references can be verified, not guessed
    theme_block_types = None
    blocks_dir = path.resolve().parent.parent / "blocks"
    if path.resolve().parent.name == "sections" and blocks_dir.is_dir():
        theme_block_types = {p.stem for p in blocks_dir.glob("*.liquid")}

    return validate_schema(schema, path.name, theme_block_types)


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_schema.py <file.liquid|directory>")
        sys.exit(1)

    target = sys.argv[1]
    all_errors = []
    files_checked = 0

    if os.path.isdir(target):
        for liquid_file in sorted(Path(target).rglob("*.liquid")):
            file_errors = validate_file(str(liquid_file))
            if file_errors:
                all_errors.append((str(liquid_file), file_errors))
            files_checked += 1
    else:
        file_errors = validate_file(target)
        if file_errors:
            all_errors.append((target, file_errors))
        files_checked = 1

    # Output results
    total_errors = sum(1 for _, errs in all_errors for e in errs if e.level == "error")
    total_warnings = sum(1 for _, errs in all_errors for e in errs if e.level == "warning")

    if all_errors:
        for filepath, errs in all_errors:
            print(f"\n{filepath}:")
            for e in errs:
                print(str(e))

    print(f"\n{'='*50}")
    print(f"Files checked: {files_checked}")
    print(f"Errors: {total_errors}")
    print(f"Warnings: {total_warnings}")

    if total_errors == 0 and total_warnings == 0:
        print("All schemas valid!")

    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
