# Shopify Schema Setting Types Reference

Source: https://shopify.dev/docs/storefronts/themes/architecture/settings/input-settings

## Setting Type Quick Reference

| Type | Required Attrs | default | Notes |
|------|---------------|---------|-------|
| text | id, label | optional | Empty string `""` is INVALID |
| textarea | id, label | optional | Empty string `""` is INVALID |
| number | id, label | optional | Must be numeric, not string |
| range | id, label, min, max, **default** | **required** | step defaults to 1; min 2 steps (≥3 distinct values), max 101 steps |
| select | id, label, options | optional | options need value+label |
| radio | id, label, options | optional | First option if unspecified |
| checkbox | id, label | optional | Defaults to false |
| color | id, label | optional | |
| color_background | id, label | optional | |
| color_scheme | id, label | **required** | Must match color_scheme_group |
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

## Common Pitfalls

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
