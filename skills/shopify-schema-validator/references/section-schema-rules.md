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
  "max_blocks": 16,                 // optional: positive integer
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

### Tag
Valid values: `article`, `aside`, `div`, `footer`, `header`, `section`
Default: `div`

### Limit
Only `1` or `2` accepted. Restricts section instances per template.

### Uniqueness Constraints
- All block **types** must be unique within the section
- All block **names** must be unique within the section
- All setting **IDs** must be unique within each block
- All section setting **IDs** must be unique within the section

### Max Blocks
- Default limit: 50 blocks per section
- Can be lowered with `max_blocks` attribute (positive integer)

### Blocks
- `type` and `name` are required (except `@app` blocks which only need `type`)
- `@app` blocks do NOT accept `limit`
- Non-`@app` blocks can have a `limit` attribute to restrict how many of that type can be added
- Each block can have its own `settings` array

### enabled_on / disabled_on
- **Cannot use both** in the same schema
- Used to restrict which templates/groups can use the section

### Presets
- Each preset requires a `name`
- Presets make sections available in the theme editor's "Add section" picker

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
| font_picker without default | Schema rejected |
| range with >101 steps | Schema rejected |
| url default not `/collections` or `/collections/all` | Schema rejected |
