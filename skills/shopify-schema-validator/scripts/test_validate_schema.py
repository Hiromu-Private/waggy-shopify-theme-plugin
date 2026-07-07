#!/usr/bin/env python3
"""
Unit tests for validate_schema.py (stdlib unittest only, no pytest).

Usage:
  python3 scripts/test_validate_schema.py
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validate_schema import validate_schema, validate_file  # noqa: E402


def make_schema(**overrides) -> dict:
    schema = {"name": "Test Section"}
    schema.update(overrides)
    return schema


def setting_schema(setting: dict) -> dict:
    return make_schema(settings=[setting])


class ValidatorTestCase(unittest.TestCase):
    """Shared assertion helpers."""

    def run_schema(self, schema):
        return validate_schema(schema, "test.liquid")

    def errors_of(self, results):
        return [e for e in results if e.level == "error"]

    def warnings_of(self, results):
        return [e for e in results if e.level == "warning"]

    def assert_clean(self, schema):
        results = self.run_schema(schema)
        self.assertEqual([], [str(e) for e in results])

    def assert_no_errors(self, schema):
        results = self.run_schema(schema)
        self.assertEqual([], [str(e) for e in self.errors_of(results)])
        return results

    def assert_error(self, schema, fragment):
        results = self.run_schema(schema)
        matches = [e for e in self.errors_of(results) if fragment in e.message]
        self.assertTrue(matches, f"expected error containing {fragment!r}, got: {[str(e) for e in results]}")
        return results

    def assert_warning(self, schema, fragment):
        results = self.run_schema(schema)
        matches = [e for e in self.warnings_of(results) if fragment in e.message]
        self.assertTrue(matches, f"expected warning containing {fragment!r}, got: {[str(e) for e in results]}")
        return results

    def assert_not_reported(self, schema, fragment):
        results = self.run_schema(schema)
        matches = [e for e in results if fragment in e.message]
        self.assertEqual([], [str(e) for e in matches])
        return results


class TestFullyValidSchema(ValidatorTestCase):
    def test_rich_valid_schema_produces_no_diagnostics(self):
        schema = {
            "name": "Hero Banner",
            "tag": "section",
            "class": "hero",
            "limit": 1,
            "max_blocks": 12,
            "settings": [
                {"type": "header", "content": "Layout"},
                {"type": "text", "id": "title", "label": "Title", "default": "Hello"},
                {"type": "checkbox", "id": "show_text", "label": "Show text", "default": True},
                {"type": "number", "id": "columns", "label": "Columns", "default": 3},
                {"type": "range", "id": "padding", "label": "Padding", "min": 0, "max": 100, "step": 5, "default": 50},
                {"type": "select", "id": "align", "label": "Align", "default": "left",
                 "options": [{"value": "left", "label": "Left"}, {"value": "right", "label": "Right"}]},
                {"type": "color", "id": "bg", "label": "Background", "default": "#FF4416"},
                {"type": "color_scheme", "id": "scheme", "label": "Scheme", "default": "scheme-1"},
                {"type": "font_picker", "id": "font", "label": "Font", "default": "helvetica_n4"},
                {"type": "image_picker", "id": "image", "label": "Image"},
                {"type": "url", "id": "link", "label": "Link", "default": "/collections"},
                {"type": "richtext", "id": "body", "label": "Body", "default": "<p>Hi</p>",
                 "visible_if": "{{ section.settings.show_text }}"},
            ],
            "blocks": [
                {"type": "item", "name": "Item", "settings": [
                    {"type": "text", "id": "heading", "label": "Heading"},
                ]},
                {"type": "@app"},
            ],
            "presets": [
                {"name": "Hero Banner",
                 "settings": {"title": "Welcome", "show_text": True},
                 "blocks": [{"type": "item", "settings": {"heading": "Hi"}}]},
            ],
        }
        self.assert_clean(schema)


class TestThemeBlocks(ValidatorTestCase):
    def test_theme_and_app_entries_are_not_flagged(self):
        # Regression: '@theme' used to be reported as "Block missing 'name'"
        schema = make_schema(blocks=[{"type": "@theme"}, {"type": "@app"}])
        self.assert_clean(schema)

    def test_theme_block_with_settings_is_error(self):
        schema = make_schema(blocks=[{"type": "@theme", "settings": [
            {"type": "text", "id": "x", "label": "X"},
        ]}])
        self.assert_error(schema, "'@theme' blocks cannot define 'settings'")

    def test_app_block_with_settings_is_error(self):
        schema = make_schema(blocks=[{"type": "@app", "settings": []}])
        self.assert_error(schema, "'@app' blocks cannot define 'settings'")

    def test_duplicate_theme_entry_is_error(self):
        schema = make_schema(blocks=[{"type": "@theme"}, {"type": "@theme"}])
        self.assert_error(schema, "Duplicate '@theme' entry")

    def test_theme_plus_local_named_block_is_warning(self):
        schema = make_schema(blocks=[
            {"type": "@theme"},
            {"type": "item", "name": "Item"},
        ])
        self.assert_warning(schema, "can't support locally defined blocks and theme blocks")

    def test_recommended_theme_blocks_alongside_theme_entry_are_ok(self):
        # Documented pattern: highlight specific theme blocks next to '@theme'
        schema = make_schema(blocks=[{"type": "@theme"}, {"type": "slide"}])
        self.assert_clean(schema)

    def test_type_only_block_without_theme_entry_is_warning_not_error(self):
        # Could be a section accepting specific theme blocks — don't hard-fail
        schema = make_schema(blocks=[{"type": "slide"}])
        results = self.assert_no_errors(schema)
        self.assertTrue(any("has no 'name'" in e.message for e in self.warnings_of(results)))

    def test_block_with_settings_but_no_name_is_still_error(self):
        schema = make_schema(blocks=[{"type": "item", "settings": []}])
        self.assert_error(schema, "Block missing 'name'")


class TestPresets(ValidatorTestCase):
    def test_preset_unknown_setting_id_is_error(self):
        schema = make_schema(
            settings=[{"type": "text", "id": "title", "label": "Title"}],
            presets=[{"name": "Default", "settings": {"titel": "typo"}}],
        )
        self.assert_error(schema, "preset setting 'titel' does not match any section setting id")

    def test_preset_known_setting_id_is_ok(self):
        schema = make_schema(
            settings=[{"type": "text", "id": "title", "label": "Title"}],
            presets=[{"name": "Default", "settings": {"title": "ok"}}],
        )
        self.assert_clean(schema)

    def test_preset_settings_not_object_is_error(self):
        schema = make_schema(presets=[{"name": "Default", "settings": ["not", "a", "dict"]}])
        self.assert_error(schema, "preset 'settings' must be an object")

    def test_preset_not_object_is_error(self):
        schema = make_schema(presets=[42])
        self.assert_error(schema, "Preset[0] must be an object")

    def test_presets_not_array_is_error(self):
        schema = make_schema(presets={"name": "Default"})
        self.assert_error(schema, "'presets' must be an array")

    def test_preset_missing_name_is_error(self):
        schema = make_schema(presets=[{}])
        self.assert_error(schema, "Preset[0] missing 'name'")

    def test_preset_undefined_block_type_is_error_without_theme(self):
        schema = make_schema(
            blocks=[{"type": "item", "name": "Item"}],
            presets=[{"name": "Default", "blocks": [{"type": "bogus"}]}],
        )
        self.assert_error(schema, "preset block type 'bogus' is not defined")

    def test_preset_undefined_block_type_is_warning_with_theme(self):
        schema = make_schema(
            blocks=[{"type": "@theme"}],
            presets=[{"name": "Default", "blocks": [{"type": "text"}]}],
        )
        results = self.assert_no_errors(schema)
        self.assertTrue(any("assuming it is a theme block" in e.message for e in self.warnings_of(results)))

    def test_preset_app_block_type_is_ok(self):
        schema = make_schema(
            blocks=[{"type": "@app"}],
            presets=[{"name": "Default", "blocks": [{"type": "@app"}]}],
        )
        self.assert_clean(schema)

    def test_preset_block_unknown_setting_id_is_error(self):
        schema = make_schema(
            blocks=[{"type": "item", "name": "Item", "settings": [
                {"type": "text", "id": "heading", "label": "Heading"},
            ]}],
            presets=[{"name": "Default", "blocks": [{"type": "item", "settings": {"heding": "typo"}}]}],
        )
        self.assert_error(schema, "preset block setting 'heding' does not match any setting id of block 'item'")

    def test_preset_block_missing_type_is_error(self):
        schema = make_schema(presets=[{"name": "Default", "blocks": [{"settings": {}}]}])
        self.assert_error(schema, "preset block missing 'type'")

    def test_preset_block_settings_not_object_is_error(self):
        schema = make_schema(
            blocks=[{"type": "item", "name": "Item"}],
            presets=[{"name": "Default", "blocks": [{"type": "item", "settings": []}]}],
        )
        self.assert_error(schema, "preset block 'settings' must be an object")

    def test_preset_nested_blocks_are_checked_recursively(self):
        schema = make_schema(
            blocks=[{"type": "item", "name": "Item"}],
            presets=[{"name": "Default", "blocks": [
                {"type": "item", "blocks": [{"type": "bogus_child"}]},
            ]}],
        )
        self.assert_error(schema, "preset block type 'bogus_child' is not defined")

    def test_preset_nested_blocks_with_theme_are_warnings(self):
        # Horizon-style static nesting: group > text
        schema = make_schema(
            blocks=[{"type": "@theme"}],
            presets=[{"name": "Default", "blocks": [
                {"type": "group", "blocks": [{"type": "text"}]},
            ]}],
        )
        results = self.assert_no_errors(schema)
        self.assertEqual(2, len([e for e in self.warnings_of(results) if "assuming it is a theme block" in e.message]))

    def test_preset_hash_form_blocks_with_block_order(self):
        schema = make_schema(
            blocks=[{"type": "item", "name": "Item"}],
            presets=[{"name": "Default",
                      "blocks": {"item-1": {"type": "item"}},
                      "block_order": ["item-1"]}],
        )
        self.assert_clean(schema)

    def test_preset_block_order_referencing_missing_id_is_error(self):
        schema = make_schema(
            blocks=[{"type": "item", "name": "Item"}],
            presets=[{"name": "Default",
                      "blocks": {"item-1": {"type": "item"}},
                      "block_order": ["item-1", "ghost"]}],
        )
        self.assert_error(schema, "block_order id 'ghost' not found")

    def test_preset_blocks_invalid_container_is_error(self):
        schema = make_schema(presets=[{"name": "Default", "blocks": "nope"}])
        self.assert_error(schema, "preset 'blocks' must be an array or an object")

    def test_nested_blocks_under_theme_block_reference_are_lenient(self):
        # Real-world pattern (Store_MeVER slideshow-blocks): section lists a
        # theme block by type only; its preset nests children whose accepted
        # types live in /blocks/slide.liquid's own schema — must not hard-fail
        schema = make_schema(
            blocks=[{"type": "slide"}],
            presets=[{"name": "Default", "blocks": [
                {"type": "slide", "blocks": [{"type": "slide-heading"}]},
            ]}],
        )
        results = self.assert_no_errors(schema)
        self.assertTrue(any("slide-heading" in e.message for e in self.warnings_of(results)))

    def test_nested_blocks_under_local_block_stay_strict(self):
        schema = make_schema(
            blocks=[{"type": "item", "name": "Item"}],
            presets=[{"name": "Default", "blocks": [
                {"type": "item", "blocks": [{"type": "bogus_child"}]},
            ]}],
        )
        self.assert_error(schema, "preset block type 'bogus_child' is not defined")


class TestThemeBlockFilesystem(ValidatorTestCase):
    """theme_block_types (from <theme>/blocks/*.liquid) silences verified references."""

    def test_verified_theme_block_types_produce_no_diagnostics(self):
        schema = make_schema(
            blocks=[{"type": "slide"}],
            presets=[{"name": "Default", "blocks": [
                {"type": "slide", "blocks": [{"type": "slide-heading"}]},
            ]}],
        )
        results = validate_schema(schema, "test.liquid", theme_block_types={"slide", "slide-heading"})
        self.assertEqual([], [str(e) for e in results])

    def test_unverified_type_mentions_blocks_dir_in_message(self):
        schema = make_schema(
            blocks=[{"type": "@theme"}],
            presets=[{"name": "Default", "blocks": [{"type": "ghost"}]}],
        )
        results = validate_schema(schema, "test.liquid", theme_block_types={"text"})
        warnings = [e for e in results if e.level == "warning"]
        self.assertTrue(any("ghost" in e.message and "/blocks" in e.message for e in warnings))
        self.assertEqual([], [str(e) for e in results if e.level == "error"])

    def test_validate_file_discovers_blocks_directory(self):
        with tempfile.TemporaryDirectory() as root:
            os.makedirs(os.path.join(root, "sections"))
            os.makedirs(os.path.join(root, "blocks"))
            with open(os.path.join(root, "blocks", "slide.liquid"), "w", encoding="utf-8") as f:
                f.write("{% schema %}{\"name\": \"Slide\"}{% endschema %}")
            section = os.path.join(root, "sections", "slideshow.liquid")
            with open(section, "w", encoding="utf-8") as f:
                f.write(
                    '{% schema %}\n'
                    '{"name": "Slideshow", "blocks": [{"type": "slide"}],\n'
                    ' "presets": [{"name": "Slideshow", "blocks": [{"type": "slide"}]}]}\n'
                    '{% endschema %}\n'
                )
            errors = validate_file(section)
            self.assertEqual([], [str(e) for e in errors])


class TestDefaultTypes(ValidatorTestCase):
    def test_checkbox_string_default_is_error(self):
        schema = setting_schema({"type": "checkbox", "id": "flag", "label": "Flag", "default": "true"})
        self.assert_error(schema, "checkbox default must be a boolean")

    def test_checkbox_boolean_default_is_ok(self):
        schema = setting_schema({"type": "checkbox", "id": "flag", "label": "Flag", "default": False})
        self.assert_clean(schema)

    def test_number_string_default_is_error(self):
        schema = setting_schema({"type": "number", "id": "count", "label": "Count", "default": "5"})
        self.assert_error(schema, "number default must be a number, not a string")

    def test_number_numeric_default_is_ok(self):
        schema = setting_schema({"type": "number", "id": "count", "label": "Count", "default": 5})
        self.assert_clean(schema)

    def test_number_boolean_default_is_error(self):
        schema = setting_schema({"type": "number", "id": "count", "label": "Count", "default": True})
        self.assert_error(schema, "number default must be a number")

    def test_color_invalid_default_is_warning(self):
        schema = setting_schema({"type": "color", "id": "bg", "label": "BG", "default": "not-a-color"})
        results = self.assert_no_errors(schema)
        self.assertTrue(any("not a recognized color format" in e.message for e in self.warnings_of(results)))

    def test_color_named_color_is_warning(self):
        schema = setting_schema({"type": "color", "id": "bg", "label": "BG", "default": "red"})
        self.assert_warning(schema, "not a recognized color format")

    def test_color_empty_string_is_warning(self):
        schema = setting_schema({"type": "color", "id": "bg", "label": "BG", "default": ""})
        self.assert_warning(schema, "not a recognized color format")

    def test_color_valid_formats_are_ok(self):
        for value in ("#fff", "#FF4416", "rgb(0, 0, 0)", "rgba(0,0,0,0.5)"):
            schema = setting_schema({"type": "color", "id": "bg", "label": "BG", "default": value})
            self.assert_clean(schema)

    def test_select_default_not_in_options_is_error(self):
        schema = setting_schema({
            "type": "select", "id": "align", "label": "Align", "default": "middle",
            "options": [{"value": "left", "label": "Left"}, {"value": "right", "label": "Right"}],
        })
        self.assert_error(schema, "default 'middle' not in options values")

    def test_radio_default_not_in_options_is_error(self):
        schema = setting_schema({
            "type": "radio", "id": "align", "label": "Align", "default": "middle",
            "options": [{"value": "left", "label": "Left"}, {"value": "right", "label": "Right"}],
        })
        self.assert_error(schema, "default 'middle' not in options values")

    def test_text_non_string_default_is_error(self):
        schema = setting_schema({"type": "text", "id": "title", "label": "Title", "default": 5})
        self.assert_error(schema, "'text' default must be a string")

    def test_color_scheme_missing_default_is_warning(self):
        schema = setting_schema({"type": "color_scheme", "id": "scheme", "label": "Scheme"})
        self.assert_warning(schema, "color_scheme has no 'default'")

    def test_color_scheme_with_default_is_ok(self):
        schema = setting_schema({"type": "color_scheme", "id": "scheme", "label": "Scheme", "default": "scheme-1"})
        self.assert_clean(schema)


class TestMaxBlocks(ValidatorTestCase):
    def test_max_blocks_999_is_error(self):
        schema = make_schema(max_blocks=999)
        self.assert_error(schema, f"max_blocks cannot exceed 50")

    def test_max_blocks_50_is_ok(self):
        schema = make_schema(max_blocks=50)
        self.assert_clean(schema)

    def test_max_blocks_zero_is_error(self):
        schema = make_schema(max_blocks=0)
        self.assert_error(schema, "max_blocks must be a positive integer")

    def test_max_blocks_string_is_error(self):
        schema = make_schema(max_blocks="16")
        self.assert_error(schema, "max_blocks must be a positive integer")


class TestVisibleIf(ValidatorTestCase):
    def test_visible_if_valid_expression_is_ok(self):
        schema = setting_schema({
            "type": "text", "id": "title", "label": "Title",
            "visible_if": "{{ section.settings.show_title }}",
        })
        self.assert_clean(schema)

    def test_visible_if_non_string_is_error(self):
        schema = setting_schema({
            "type": "text", "id": "title", "label": "Title",
            "visible_if": True,
        })
        self.assert_error(schema, "'visible_if' must be a string")

    def test_visible_if_without_liquid_braces_is_warning(self):
        schema = setting_schema({
            "type": "text", "id": "title", "label": "Title",
            "visible_if": "section.settings.show_title",
        })
        self.assert_warning(schema, "'visible_if' should contain a {{ ... }} Liquid expression")


class TestSectionName(ValidatorTestCase):
    def test_name_26_chars_is_warning(self):
        schema = make_schema(name="A" * 26)
        self.assert_warning(schema, "recommended max 25")

    def test_name_25_chars_is_ok(self):
        schema = make_schema(name="A" * 25)
        self.assert_clean(schema)

    def test_translation_key_name_is_not_length_checked(self):
        schema = make_schema(name="t:sections.hero_banner.name.with_a_very_long_key")
        self.assert_not_reported(schema, "recommended max 25")


class TestRegressions(ValidatorTestCase):
    """Existing checks that must keep working after the extension."""

    def test_range_with_1_step_is_error(self):
        schema = setting_schema({
            "type": "range", "id": "cols", "label": "Cols",
            "min": 1, "max": 2, "step": 1, "default": 1,
        })
        self.assert_error(schema, "Shopify requires at least 2")

    def test_range_with_102_steps_is_error(self):
        schema = setting_schema({
            "type": "range", "id": "pad", "label": "Pad",
            "min": 0, "max": 102, "step": 1, "default": 0,
        })
        self.assert_error(schema, "max 101")

    def test_range_default_off_step_is_error(self):
        schema = setting_schema({
            "type": "range", "id": "pad", "label": "Pad",
            "min": 0, "max": 100, "step": 4, "default": 5,
        })
        self.assert_error(schema, "not a valid step")

    def test_duplicate_section_setting_id_is_error(self):
        schema = make_schema(settings=[
            {"type": "text", "id": "title", "label": "Title"},
            {"type": "text", "id": "title", "label": "Title 2"},
        ])
        self.assert_error(schema, "Duplicate section setting id: 'title'")

    def test_duplicate_block_setting_id_is_error(self):
        schema = make_schema(blocks=[{"type": "item", "name": "Item", "settings": [
            {"type": "text", "id": "x", "label": "X"},
            {"type": "text", "id": "x", "label": "X2"},
        ]}])
        self.assert_error(schema, "Duplicate setting id: 'x'")

    def test_enabled_on_and_disabled_on_together_is_error(self):
        schema = make_schema(enabled_on={"templates": ["index"]}, disabled_on={"groups": ["header"]})
        self.assert_error(schema, "Cannot use both 'enabled_on' and 'disabled_on'")

    def test_text_empty_string_default_is_error(self):
        schema = setting_schema({"type": "text", "id": "title", "label": "Title", "default": ""})
        self.assert_error(schema, "default cannot be empty string")

    def test_image_picker_with_default_is_error(self):
        schema = setting_schema({"type": "image_picker", "id": "img", "label": "Image", "default": "x"})
        self.assert_error(schema, "does not support 'default'")

    def test_font_picker_without_default_is_error(self):
        schema = setting_schema({"type": "font_picker", "id": "font", "label": "Font"})
        self.assert_error(schema, "font_picker requires a 'default'")

    def test_app_block_with_limit_is_error(self):
        schema = make_schema(blocks=[{"type": "@app", "limit": 1}])
        self.assert_error(schema, "@app blocks do not accept 'limit'")

    def test_url_invalid_default_is_error(self):
        schema = setting_schema({"type": "url", "id": "link", "label": "Link", "default": "/pages/about"})
        self.assert_error(schema, "url default must be one of")

    def test_duplicate_block_type_is_error(self):
        schema = make_schema(blocks=[
            {"type": "item", "name": "Item"},
            {"type": "item", "name": "Item 2"},
        ])
        self.assert_error(schema, "Duplicate block type: 'item'")

    def test_duplicate_option_value_is_error(self):
        schema = setting_schema({
            "type": "select", "id": "align", "label": "Align",
            "options": [{"value": "left", "label": "Left"}, {"value": "left", "label": "Left 2"}],
        })
        self.assert_error(schema, "duplicate value: 'left'")

    def test_section_limit_3_is_error(self):
        schema = make_schema(limit=3)
        self.assert_error(schema, "Section limit must be 1 or 2")

    def test_unknown_setting_type_is_error(self):
        schema = setting_schema({"type": "slider", "id": "x", "label": "X"})
        self.assert_error(schema, "Unknown setting type: 'slider'")


class TestFileLevel(ValidatorTestCase):
    def _validate_liquid(self, body: str):
        with tempfile.NamedTemporaryFile("w", suffix=".liquid", delete=False, encoding="utf-8") as f:
            f.write(body)
            tmp = f.name
        try:
            return validate_file(tmp)
        finally:
            os.unlink(tmp)

    def test_valid_liquid_file_passes(self):
        errors = self._validate_liquid('<div></div>\n{% schema %}\n{"name": "Hero"}\n{% endschema %}\n')
        self.assertEqual([], [str(e) for e in errors])

    def test_invalid_json_is_error(self):
        errors = self._validate_liquid('{% schema %}\n{"name": "Hero",}\n{% endschema %}\n')
        self.assertTrue(any("Invalid JSON" in e.message for e in errors))

    def test_multiple_schema_tags_is_error(self):
        errors = self._validate_liquid(
            '{% schema %}{"name": "A"}{% endschema %}\n{% schema %}{"name": "B"}{% endschema %}\n'
        )
        self.assertTrue(any("Multiple {% schema %}" in e.message for e in errors))

    def test_file_without_schema_is_skipped(self):
        errors = self._validate_liquid('<div>{{ product.title }}</div>\n')
        self.assertEqual([], errors)


if __name__ == "__main__":
    unittest.main(verbosity=2)
