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
            errors.append(SchemaError("warning", f"default '{default}' not in options values", path))


def validate_block(block: dict, path: str) -> list[SchemaError]:
    """Validate a single block definition."""
    errors = []

    if "type" not in block:
        errors.append(SchemaError("error", "Block missing 'type'", path))
    if "name" not in block and block.get("type") != "@app":
        errors.append(SchemaError("error", "Block missing 'name'", path))

    btype = block.get("type", "<unknown>")
    bpath = f"{path}[{btype}]"

    # @app blocks don't accept limit
    if btype == "@app" and "limit" in block:
        errors.append(SchemaError("error", "@app blocks do not accept 'limit'", bpath))

    # Validate block settings
    settings = block.get("settings", [])
    setting_ids = set()
    for i, setting in enumerate(settings):
        stype = setting.get("type", "")
        if stype in ("header", "paragraph"):
            errors.extend(validate_setting(setting, bpath))
            continue

        sid = setting.get("id", "")
        if sid in setting_ids:
            errors.append(SchemaError("error", f"Duplicate setting id: '{sid}'", bpath))
        setting_ids.add(sid)
        errors.extend(validate_setting(setting, bpath))

    return errors


def validate_schema(schema: dict, filepath: str = "") -> list[SchemaError]:
    """Validate a complete section schema."""
    errors = []
    prefix = filepath or "schema"

    # Required: name
    if "name" not in schema:
        errors.append(SchemaError("error", "Schema missing required 'name' attribute", prefix))

    # Tag validation
    if "tag" in schema:
        if schema["tag"] not in VALID_TAG_VALUES:
            errors.append(SchemaError("error", f"Invalid tag '{schema['tag']}'. Valid: {VALID_TAG_VALUES}", prefix))

    # Limit validation
    if "limit" in schema:
        if schema["limit"] not in VALID_LIMIT_VALUES:
            errors.append(SchemaError("error", f"Section limit must be 1 or 2, got: {schema['limit']}", prefix))

    # Section settings
    section_setting_ids = set()
    for setting in schema.get("settings", []):
        stype = setting.get("type", "")
        if stype in ("header", "paragraph"):
            errors.extend(validate_setting(setting, f"{prefix}.settings"))
            continue
        sid = setting.get("id", "")
        if sid in section_setting_ids:
            errors.append(SchemaError("error", f"Duplicate section setting id: '{sid}'", prefix))
        section_setting_ids.add(sid)
        errors.extend(validate_setting(setting, f"{prefix}.settings"))

    # Blocks validation
    blocks = schema.get("blocks", [])
    block_types = set()
    block_names = set()
    for i, block in enumerate(blocks):
        btype = block.get("type", "")
        bname = block.get("name", "")

        if btype != "@app":
            if btype in block_types:
                errors.append(SchemaError("error", f"Duplicate block type: '{btype}'", prefix))
            block_types.add(btype)

            if bname and bname in block_names:
                errors.append(SchemaError("error", f"Duplicate block name: '{bname}'", prefix))
            block_names.add(bname)

        errors.extend(validate_block(block, f"{prefix}.blocks"))

    # max_blocks validation
    if "max_blocks" in schema:
        mb = schema["max_blocks"]
        if not isinstance(mb, int) or mb < 1:
            errors.append(SchemaError("error", f"max_blocks must be a positive integer", prefix))

    # Presets validation
    for i, preset in enumerate(schema.get("presets", [])):
        if "name" not in preset:
            errors.append(SchemaError("error", f"Preset[{i}] missing 'name'", prefix))

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

    return validate_schema(schema, path.name)


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
