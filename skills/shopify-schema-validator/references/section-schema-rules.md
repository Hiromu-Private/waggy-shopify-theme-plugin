# Shopify Section Schema Rules

Source: https://shopify.dev/docs/storefronts/themes/architecture/sections/section-schema

## Schema Structure

```json
{% schema %}
{
  "name": "Section Name",           // REQUIRED
  "tag": "section",                  // optional: article|aside|div|footer|header|section
  "class": "my-class",              // optional
  "limit": 1,                       // optional: 1 or 2 only
  "settings": [],                   // optional: section-level settings
  "blocks": [],                     // optional: block definitions
  "max_blocks": 16,                 // optional: positive integer, max 50
  "presets": [],                    // optional: pre-configurations
  "default": {},                    // optional: default configuration
  "locales": {},                    // optional: translations
  "enabled_on": {},                 // optional: template restrictions
  "disabled_on": {}                 // optional: exclusion rules
}
{% endschema %}
```

## Key Rules

### General
- One `{% schema %}` tag per section (no nesting in other Liquid tags)
- Must contain valid JSON
- `name` is the only required attribute
- Keep `name` at 25 characters or fewer (warning above that; `t:` translation keys are exempt)

### Tag
Valid values: `article`, `aside`, `div`, `footer`, `header`, `section`
Default: `div`

### Limit
Only `1` or `2` accepted. Restricts section instances per template.

### Uniqueness Constraints
- All block **types** must be unique within the section (`@theme` may appear only once)
- All block **names** must be unique within the section
- All setting **IDs** must be unique within each block
- All section setting **IDs** must be unique within the section

### Max Blocks
- Default limit: 50 blocks per section (hard Shopify limit)
- Can be lowered with `max_blocks` attribute (positive integer); values above 50 are an error
- Static blocks don't count toward the limit

### Blocks
- Locally defined blocks require `type` and `name`, and may carry a `settings` array and a `limit`
- `@app` and `@theme` entries take **only `type`** — no `name`, no `settings` (settings live in the app/theme block itself)
- `@app` blocks do NOT accept `limit`
- Declaring `{"type": "@theme"}` opts the section into accepting theme blocks (`/blocks/*.liquid`). Type-only entries alongside `@theme` are the documented "recommended blocks" pattern
- A section can also list **specific theme blocks** by type only (no `name`) without `@theme` — the validator downgrades "missing name" to a warning for such entries, and silences it entirely when `/blocks/<type>.liquid` exists
- Sections **cannot support both** locally defined blocks and theme blocks at the same time (warning)

### enabled_on / disabled_on
- **Cannot use both** in the same schema
- Used to restrict which templates/groups can use the section

### Presets
- Each preset requires a `name`
- Presets make sections available in the theme editor's "Add section" picker
- `settings` must be an object whose **keys match section setting ids** (unknown ids are errors — a top cause of broken templates)
- `blocks` may be an **array** or a **hash keyed by block id** (hash form supports a sibling `block_order`; ids in `block_order` must exist in `blocks`)
- Each preset block `type` must be a defined block type, `@app`/`@theme`, or a theme block. Unknown types are errors — downgraded to warnings when the section is in theme-block territory (`@theme` declared, or nested under a theme block reference), and silenced when `/blocks/<type>.liquid` exists
- Preset block `settings` keys are checked against that block's setting ids when the block is locally defined
- Preset blocks can **nest** (`blocks` inside a block, theme blocks generation) — nested levels are validated recursively

## Error-Causing Patterns

| Pattern | Result |
|---------|--------|
| Invalid JSON syntax | Section completely broken |
| text/textarea `"default": ""` | Schema rejected by Shopify |
| image_picker/product/collection/page/blog/article with `default` | Schema rejected |
| range default not matching step | Settings may reset |
| Duplicate block type | Syntax error in editor |
| Duplicate setting ID within block | Syntax error in editor |
| Both enabled_on and disabled_on | Schema rejected |
| @app block with limit | Schema rejected |
| @app/@theme block with `settings` | Schema rejected |
| Duplicate `@theme` entry | Schema rejected |
| font_picker without default | Schema rejected |
| range with >101 steps | Schema rejected |
| url default not `/collections` or `/collections/all` | Schema rejected |
| checkbox default `"true"` (string) | Error — must be boolean |
| number default `"5"` (string) | Error — must be numeric |
| select/radio default not in options values | Setting falls back unpredictably |
| max_blocks > 50 | Schema rejected |
| preset settings key not a section setting id | Broken template on preset insert |
| preset block type not defined / not in `/blocks` | Broken template on preset insert |
| `visible_if` not a string with `{{ ... }}` | Condition silently never applies |
