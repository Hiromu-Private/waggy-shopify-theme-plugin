---
name: shopify-schema-validator
description: "Shopify Liquid section schema ({% schema %}) validation and review. Use when: (1) writing or editing Shopify section .liquid files with {% schema %} tags, (2) debugging broken product/collection/page templates, (3) reviewing schema settings for Shopify spec compliance, (4) user mentions 'schema check', 'schema validate', 'Shopify schema', or asks why a template is broken. Automatically validate schemas after writing/editing section files."
---

# Shopify Schema Validator

Validate Shopify Liquid section schemas against official Shopify specifications.

## Workflow

### 1. Run the validator script

```bash
# Single file
python3 scripts/validate_schema.py path/to/section.liquid

# All sections in a directory
python3 scripts/validate_schema.py path/to/sections/
```

The script checks:
- JSON syntax validity
- Required attributes per setting type
- `default` value rules (empty string forbidden for text/textarea, restricted values for url/link_list)
- Types that do NOT support `default` (image_picker, video, product, collection, page, blog, article)
- `range` step/min/max/default consistency (max 101 steps)
- `select`/`radio` option structure and duplicate values
- Block type/name uniqueness
- Section setting ID uniqueness
- `enabled_on`/`disabled_on` mutual exclusion
- `@app` block restrictions

### 2. Review errors and apply fixes

Common fixes:
- `text/textarea "default": ""` -> Remove the `"default"` key entirely
- `range default not on step` -> Ensure `(default - min) % step == 0`
- `image_picker with default` -> Remove `"default"` key
- `font_picker missing default` -> Add a valid font identifier as default
- `duplicate block type` -> Rename one of the duplicate types

### 3. Agent mode: auto-validate after edits

When writing or editing `.liquid` section files, always run the validator afterward:

```bash
python3 scripts/validate_schema.py <edited-file>
```

If errors are found, fix them before proceeding.

## Reference docs

- **Setting types**: See [references/setting-types.md](references/setting-types.md) for all setting types, required attributes, and default value rules
- **Section schema rules**: See [references/section-schema-rules.md](references/section-schema-rules.md) for section-level constraints and error patterns

## Critical rules (memorize)

1. `text`/`textarea` type: `"default": ""` is **INVALID** (causes entire schema rejection)
2. `image_picker`, `video`, `product`, `collection`, `page`, `blog`, `article`: `default` attribute **NOT supported**
3. `font_picker`: `default` is **REQUIRED**
4. `range`: default must satisfy `(default - min) % step == 0` and `min <= default <= max`
5. `range`: max number of steps is 101: `(max - min) / step <= 101`
6. All block types and names must be **unique** within a section
7. All setting IDs must be **unique** within each block and within section settings
8. `enabled_on` and `disabled_on` **cannot coexist**
9. Section `limit` accepts only `1` or `2`
10. `@app` blocks do **NOT** accept `limit`
