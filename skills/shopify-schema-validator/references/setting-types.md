# Shopify Schema Setting Types Reference

Source: https://shopify.dev/docs/storefronts/themes/architecture/settings/input-settings

## Setting Type Quick Reference

| Type | Required Attrs | default | Notes |
|------|---------------|---------|-------|
| text | id, label | optional | Empty string `""` is INVALID; must be a string (error) |
| textarea | id, label | optional | Empty string `""` is INVALID; must be a string (error) |
| number | id, label | optional | Must be numeric, not string — `"5"` is INVALID (error) |
| range | id, label, min, max, **default** | **required** | step defaults to 1; min 2 steps (≥3 distinct values), max 101 steps |
| select | id, label, options | optional | options need value+label; default must match an options value (error) |
| radio | id, label, options | optional | First option if unspecified; default must match an options value (error) |
| checkbox | id, label | optional | Defaults to false; must be boolean `true`/`false`, not `"true"` (error) |
| color | id, label | optional | `#RGB`/`#RRGGBB`/`rgb()`/`rgba()` — other formats flagged (warning) |
| color_background | id, label | optional | |
| color_scheme | id, label | recommended (warning if missing) | Must match color_scheme_group; without default the section implicitly depends on the first scheme |
| font_picker | id, label, **default** | **required** | Must be valid font identifier |
| image_picker | id, label | **NOT supported** | |
| video | id, label | **NOT supported** | Shopify-hosted video |
| video_url | id, label, accept | optional | accept: ["youtube"], ["vimeo"], or both |
| url | id, label | optional | Only `/collections` or `/collections/all` |
| product | id, label | **NOT supported** | |
| product_list | id, label | optional | limit max 50 |
| collection | id, label | **NOT supported** | |
| collection_list | id, label | optional | limit max 50 |
| page | id, label | **NOT supported** | |
| blog | id, label | **NOT supported** | |
| article | id, label | **NOT supported** | |
| article_list | id, label | optional | limit max 50 |
| link_list | id, label | optional | Only `main-menu` or `footer` |
| richtext | id, label | optional | Must wrap in `<p>` or `<ul>` |
| inline_richtext | id, label | optional | No line breaks |
| html | id, label | optional | Strips html/head/body tags |
| liquid | id, label | optional | Max 50KB content |
| metaobject | id, label | optional | Needs metaobject_type |
| metaobject_list | id, label | optional | Needs metaobject_type |
| text_alignment | id, label | optional | Values: `left`, `center`, `right` |
| color_scheme_group | id, definition, role | N/A | `settings_schema.json` only |
| header | content | N/A | Sidebar only (non-input) |
| paragraph | content | N/A | Sidebar only (non-input) |

## Conditional settings (`visible_if`)

Any input setting can carry a `visible_if` attribute (added late 2024): a **string containing a `{{ ... }}` Liquid expression**, e.g.

```json
{ "type": "text", "id": "cta_label", "label": "CTA label",
  "visible_if": "{{ section.settings.show_cta }}" }
```

- Non-string value → error. String without `{{ ... }}` → warning
- Can reference `section.settings.*`, `block.settings.*`, `settings.*`
- Cannot access runtime/resolved data source values; resource-based settings don't support it

## Common Pitfalls

### checkbox/number defaults must be typed literals
```json
// BAD - strings are rejected by Shopify
{ "type": "checkbox", "id": "show", "label": "Show", "default": "true" }
{ "type": "number", "id": "count", "label": "Count", "default": "5" }

// GOOD
{ "type": "checkbox", "id": "show", "label": "Show", "default": true }
{ "type": "number", "id": "count", "label": "Count", "default": 5 }
```

### text/textarea with empty default
```json
// BAD - Shopify rejects this
{ "type": "text", "id": "desc", "label": "Description", "default": "" }

// GOOD - Omit default entirely
{ "type": "text", "id": "desc", "label": "Description" }
```

### range validation
```json
// BAD - default (5) is not a multiple of step (4) from min (0)
{ "type": "range", "id": "x", "label": "X", "min": 0, "max": 100, "step": 4, "default": 5 }

// GOOD
{ "type": "range", "id": "x", "label": "X", "min": 0, "max": 100, "step": 4, "default": 36 }

// BAD - only 1 step ((2-1)/1=1), Shopify requires at least 2 steps (≥3 distinct values)
{ "type": "range", "id": "cols", "label": "Cols", "min": 1, "max": 2, "step": 1, "default": 2 }

// GOOD - for 2-value choices, use select instead
{
  "type": "select",
  "id": "cols",
  "label": "Cols",
  "default": "2",
  "options": [
    { "value": "1", "label": "1" },
    { "value": "2", "label": "2" }
  ]
}
```

### image_picker with default
```json
// BAD - image_picker does not support default
{ "type": "image_picker", "id": "img", "label": "Image", "default": "something" }

// GOOD
{ "type": "image_picker", "id": "img", "label": "Image" }
```
