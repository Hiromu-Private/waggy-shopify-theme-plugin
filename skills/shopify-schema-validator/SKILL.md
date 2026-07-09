---
name: shopify-schema-validator
description: "Shopify Liquid section schema ({% schema %}) validation and review. Use when: (1) writing or editing Shopify section .liquid files with {% schema %} tags, (2) debugging broken product/collection/page templates, (3) reviewing schema settings for Shopify spec compliance, (4) user mentions 'schema check', 'schema validate', 'Shopify schema', or asks why a template is broken. Automatically validate schemas after writing/editing section files."
---

# Shopify Schema Validator

Validate Shopify Liquid section schemas against official Shopify specifications.

## Workflow

### 1. Resolve the validator path, then run it

The skill runs from a plugin install (any cwd), so resolve the script path dynamically — do NOT assume `scripts/` is relative to cwd:

```bash
VALIDATOR=$(find "$HOME/.claude/plugins" -path '*shopify-schema-validator/scripts/validate_schema.py' 2>/dev/null | head -1)
# Fallback: this skill's own base directory (shown at skill invocation) — <base-dir>/scripts/validate_schema.py
[ -z "$VALIDATOR" ] && VALIDATOR="<この SKILL.md の base directory>/scripts/validate_schema.py"

# Single file
python3 "$VALIDATOR" path/to/section.liquid

# All sections in a directory
python3 "$VALIDATOR" path/to/sections/
```

The script checks:
- JSON syntax validity
- Required attributes per setting type
- `default` value rules (empty string forbidden for text/textarea, restricted values for url/link_list)
- `default` value types (checkbox must be boolean, number must be numeric, text/textarea must be string, select/radio must match an options value, color format sanity)
- Types that do NOT support `default` (image_picker, video, product, collection, page, blog, article)
- `range` step/min/max/default consistency (min 2 steps / ≥3 distinct values, max 101 steps)
- `select`/`radio` option structure and duplicate values
- Block type/name uniqueness
- `@app`/`@theme` block rules (no `name` needed, no `settings` allowed, `@theme` declared once, no mixing `@theme` with locally defined blocks)
- Presets integrity: `settings` keys must match section setting ids, block types must be defined / `@app` / `@theme` / a theme block in `/blocks`, nested preset blocks checked recursively, hash-form `blocks` + `block_order` supported
- Section setting ID uniqueness
- `max_blocks` range (positive integer, max 50)
- `visible_if` format (string containing a `{{ ... }}` Liquid expression)
- Section `name` length (warning above 25 characters)
- `enabled_on`/`disabled_on` mutual exclusion

When validating a file inside a theme's `sections/` directory, the script also reads the sibling `blocks/` directory to verify theme block references exactly (a matching `/blocks/<type>.liquid` silences the corresponding warnings).

### 2. Review errors and apply fixes

Common fixes:
- `text/textarea "default": ""` -> Remove the `"default"` key entirely
- `range default not on step` -> Ensure `(default - min) % step == 0`
- `image_picker with default` -> Remove `"default"` key
- `font_picker missing default` -> Add a valid font identifier as default
- `duplicate block type` -> Rename one of the duplicate types
- `checkbox default "true"` -> Use unquoted boolean `true`
- `number default "5"` -> Use unquoted number `5`
- `preset setting id not found` -> Fix the typo or add the setting to section `settings`
- `preset block type not defined` -> Define the block, or reference an existing theme block in `/blocks`

### 3. Agent mode: auto-validate after edits

When writing or editing `.liquid` section files, always run the validator afterward (resolve `$VALIDATOR` as in step 1):

```bash
python3 "$VALIDATOR" <edited-file>
```

If errors are found, fix them before proceeding.

### Self-test

The validator ships with a unittest suite (stdlib only):

```bash
python3 "$(dirname "$VALIDATOR")/test_validate_schema.py"
```

## Reference docs

- **Setting types**: See [references/setting-types.md](references/setting-types.md) for all setting types, required attributes, and default value rules
- **Section schema rules**: See [references/section-schema-rules.md](references/section-schema-rules.md) for section-level constraints and error patterns

## Critical rules (memorize)

1. `text`/`textarea` type: `"default": ""` is **INVALID** (causes entire schema rejection)
2. `image_picker`, `video`, `product`, `collection`, `page`, `blog`, `article`: `default` attribute **NOT supported**
3. `font_picker`: `default` is **REQUIRED**
4. `range`: default must satisfy `(default - min) % step == 0` and `min <= default <= max`
5. `range`: number of steps must be `2 <= (max - min) / step <= 101` (at least 3 distinct values). For 2-value choices, use `select` instead.
6. All block types and names must be **unique** within a section
7. All setting IDs must be **unique** within each block and within section settings
8. `enabled_on` and `disabled_on` **cannot coexist**
9. Section `limit` accepts only `1` or `2`
10. `@app` blocks do **NOT** accept `limit`
11. `@app`/`@theme` blocks take **no `name` and no `settings`** — never flag a bare `{"type": "@theme"}` as broken
12. A section **cannot mix** `@theme` with locally defined (named) blocks
13. `checkbox` default must be boolean `true`/`false`; `number` default must be a number — quoted `"true"`/`"5"` are **INVALID**
14. `select`/`radio` default must be one of the `options` values
15. Preset `settings` keys must match section setting ids; preset block types must be defined in the section, `@app`/`@theme`, or an existing theme block in `/blocks`
16. `max_blocks` cannot exceed **50** (Shopify's per-section block limit)
17. `visible_if` must be a string containing a `{{ ... }}` Liquid expression
