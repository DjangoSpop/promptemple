"""
apps/templates/tests.py
=======================
Test suite for inflate_templates management command and Template model validation.

Run locally:
    python manage.py test apps.templates --verbosity=2
"""

import re
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.templates.management.commands.inflate_templates import (
    CATEGORIES_DATASET,
    TEMPLATES_DATASET,
)
from apps.templates.models import Template, TemplateCategory, PromptField, TemplateField

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_PLACEHOLDER_RE = re.compile(r"\{\{[a-z][a-z0-9_]*\}\}")
INVALID_PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")

CHOICE_FIELD_TYPES = {"dropdown", "radio", "checkbox"}
VALID_FIELD_TYPES = {"text", "textarea", "dropdown", "checkbox", "radio", "number"}


# ===========================================================================
# 1. Placeholder Validation — every {{placeholder}} must be snake_case
# ===========================================================================

class PlaceholderValidationTests(TestCase):
    """All template_content placeholders must use {{snake_case}} format only."""

    def test_no_uppercase_in_placeholders(self):
        errors = []
        for t in TEMPLATES_DATASET:
            all_placeholders = INVALID_PLACEHOLDER_RE.findall(t["template_content"])
            valid_placeholders = VALID_PLACEHOLDER_RE.findall(t["template_content"])
            invalid = set(all_placeholders) - set(valid_placeholders)
            if invalid:
                errors.append(
                    f"[{t['external_id']}] Invalid placeholders: {invalid}"
                )
        self.assertFalse(
            errors,
            "\n".join(["Uppercase or malformed placeholders found:"] + errors),
        )

    def test_no_handlebars_block_syntax(self):
        """Ensure no {{#section}} or {{/section}} Handlebars syntax crept in."""
        errors = []
        for t in TEMPLATES_DATASET:
            if re.search(r"\{\{[#/^]", t["template_content"]):
                errors.append(
                    f"[{t['external_id']}] Contains Handlebars block syntax"
                )
        self.assertFalse(errors, "\n".join(errors))

    def test_all_templates_have_at_least_one_placeholder(self):
        errors = []
        for t in TEMPLATES_DATASET:
            if not VALID_PLACEHOLDER_RE.search(t["template_content"]):
                errors.append(
                    f"[{t['external_id']}] template_content has no {{{{placeholders}}}}"
                )
        self.assertFalse(errors, "\n".join(errors))


# ===========================================================================
# 2. PromptField Validation — dropdown/radio must have options
# ===========================================================================

class PromptFieldValidationTests(TestCase):
    """Validate field-level rules across all TEMPLATES_DATASET entries."""

    def test_choice_fields_have_non_empty_options(self):
        errors = []
        for t in TEMPLATES_DATASET:
            for f in t.get("fields", []):
                if f.get("field_type") in CHOICE_FIELD_TYPES:
                    if not f.get("options"):
                        errors.append(
                            f"[{t['external_id']}] field '{f['label']}' "
                            f"({f['field_type']}) has no options"
                        )
        self.assertFalse(errors, "\n".join(errors))

    def test_choice_fields_default_value_in_options_or_empty(self):
        errors = []
        for t in TEMPLATES_DATASET:
            for f in t.get("fields", []):
                if f.get("field_type") in {"dropdown", "radio"}:
                    default = f.get("default_value", "")
                    options = f.get("options", [])
                    if default and default not in options:
                        errors.append(
                            f"[{t['external_id']}] field '{f['label']}': "
                            f"default_value '{default}' not in options {options}"
                        )
        self.assertFalse(errors, "\n".join(errors))

    def test_all_field_types_are_valid(self):
        errors = []
        for t in TEMPLATES_DATASET:
            for f in t.get("fields", []):
                ft = f.get("field_type", "")
                if ft not in VALID_FIELD_TYPES:
                    errors.append(
                        f"[{t['external_id']}] field '{f['label']}' "
                        f"has unknown field_type '{ft}'"
                    )
        self.assertFalse(errors, "\n".join(errors))

    def test_all_fields_have_label(self):
        errors = []
        for t in TEMPLATES_DATASET:
            for i, f in enumerate(t.get("fields", [])):
                if not f.get("label", "").strip():
                    errors.append(
                        f"[{t['external_id']}] field index {i} has no label"
                    )
        self.assertFalse(errors, "\n".join(errors))

    def test_field_order_is_sequential(self):
        errors = []
        for t in TEMPLATES_DATASET:
            orders = [f.get("order", 0) for f in t.get("fields", [])]
            for idx, order in enumerate(orders):
                if order != idx:
                    errors.append(
                        f"[{t['external_id']}] field at index {idx} "
                        f"has order={order}, expected {idx}"
                    )
        self.assertFalse(errors, "\n".join(errors))


# ===========================================================================
# 3. Dataset Integrity — required keys, unique IDs, category slugs
# ===========================================================================

class DatasetIntegrityTests(TestCase):
    """Structural integrity of TEMPLATES_DATASET and CATEGORIES_DATASET."""

    REQUIRED_TEMPLATE_KEYS = {
        "external_id", "title", "description", "category_slug",
        "template_content", "tags", "fields",
    }

    def test_all_templates_have_required_keys(self):
        errors = []
        for t in TEMPLATES_DATASET:
            missing = self.REQUIRED_TEMPLATE_KEYS - t.keys()
            if missing:
                ext_id = t.get("external_id", "UNKNOWN")
                errors.append(f"[{ext_id}] Missing keys: {missing}")
        self.assertFalse(errors, "\n".join(errors))

    def test_external_ids_are_unique(self):
        ids = [t["external_id"] for t in TEMPLATES_DATASET]
        duplicates = [eid for eid in ids if ids.count(eid) > 1]
        self.assertEqual(
            [], list(set(duplicates)),
            f"Duplicate external_ids found: {set(duplicates)}"
        )

    def test_all_external_ids_have_infl_prefix(self):
        errors = [
            t["external_id"]
            for t in TEMPLATES_DATASET
            if not t["external_id"].startswith("INFL-")
        ]
        self.assertFalse(errors, f"Missing INFL- prefix: {errors}")

    def test_all_category_slugs_exist_in_categories_dataset(self):
        known_slugs = {c["slug"] for c in CATEGORIES_DATASET}
        errors = []
        for t in TEMPLATES_DATASET:
            if t["category_slug"] not in known_slugs:
                errors.append(
                    f"[{t['external_id']}] Unknown category_slug: '{t['category_slug']}'"
                )
        self.assertFalse(errors, "\n".join(errors))

    def test_category_slugs_are_unique(self):
        slugs = [c["slug"] for c in CATEGORIES_DATASET]
        duplicates = [s for s in slugs if slugs.count(s) > 1]
        self.assertEqual([], list(set(duplicates)), f"Duplicate category slugs: {set(duplicates)}")

    def test_minimum_template_count(self):
        self.assertGreaterEqual(
            len(TEMPLATES_DATASET), 80,
            f"Expected at least 80 templates, got {len(TEMPLATES_DATASET)}"
        )

    def test_required_subscription_values(self):
        valid = {"free", "basic", "premium", "enterprise"}
        errors = []
        for t in TEMPLATES_DATASET:
            rs = t.get("required_subscription", "free")
            if rs not in valid:
                errors.append(
                    f"[{t['external_id']}] invalid required_subscription: '{rs}'"
                )
        self.assertFalse(errors, "\n".join(errors))

    def test_tags_are_lists(self):
        errors = []
        for t in TEMPLATES_DATASET:
            if not isinstance(t.get("tags", []), list):
                errors.append(f"[{t['external_id']}] tags must be a list")
        self.assertFalse(errors, "\n".join(errors))


# ===========================================================================
# 4. Idempotency Tests — second run must not create duplicates
# ===========================================================================

class InflateTemplatesIdempotencyTests(TestCase):
    """Running inflate_templates twice must not create duplicate records."""

    def test_second_run_creates_zero_new_templates(self):
        call_command("inflate_templates", verbosity=0)
        count_after_first = Template.objects.filter(
            external_id__startswith="INFL-"
        ).count()

        call_command("inflate_templates", verbosity=0)
        count_after_second = Template.objects.filter(
            external_id__startswith="INFL-"
        ).count()

        self.assertEqual(
            count_after_first,
            count_after_second,
            "Second run created new templates — idempotency broken",
        )

    def test_second_run_reports_all_skipped(self):
        call_command("inflate_templates", verbosity=0)

        stdout = StringIO()
        call_command("inflate_templates", stdout=stdout, verbosity=0)
        output = stdout.getvalue()

        self.assertIn("Created: 0", output)
        self.assertIn("Errors: 0", output)

    def test_prompt_fields_not_duplicated(self):
        call_command("inflate_templates", verbosity=0)
        field_count_first = PromptField.objects.count()

        call_command("inflate_templates", verbosity=0)
        field_count_second = PromptField.objects.count()

        self.assertEqual(field_count_first, field_count_second)


# ===========================================================================
# 5. Command Integration Tests — create, rollback, dry-run, category filter
# ===========================================================================

class InflateTemplatesCommandTests(TestCase):
    """Integration tests for the inflate_templates management command."""

    # ── Creation ─────────────────────────────────────────────────────────────

    def test_command_creates_all_templates(self):
        call_command("inflate_templates", verbosity=0)
        created = Template.objects.filter(external_id__startswith="INFL-").count()
        self.assertEqual(created, len(TEMPLATES_DATASET))

    def test_command_creates_categories(self):
        call_command("inflate_templates", verbosity=0)
        for cat_data in CATEGORIES_DATASET:
            self.assertTrue(
                TemplateCategory.objects.filter(slug=cat_data["slug"]).exists(),
                f"Category '{cat_data['slug']}' was not created",
            )

    def test_template_fields_linked_via_through_model(self):
        call_command("inflate_templates", verbosity=0)
        template = Template.objects.filter(external_id="INFL-FE-001").first()
        self.assertIsNotNone(template)
        link_count = TemplateField.objects.filter(template=template).count()
        self.assertGreater(link_count, 0, "INFL-FE-001 has no linked fields")

    def test_template_field_order_is_sequential(self):
        call_command("inflate_templates", verbosity=0)
        template = Template.objects.filter(external_id="INFL-FE-001").first()
        orders = list(
            TemplateField.objects.filter(template=template)
            .order_by("order")
            .values_list("order", flat=True)
        )
        self.assertEqual(orders, list(range(len(orders))))

    def test_monetization_fields_stored_correctly(self):
        call_command("inflate_templates", verbosity=0)
        t = Template.objects.get(external_id="INFL-FE-001")
        self.assertFalse(t.is_premium_required)
        self.assertEqual(t.required_subscription, "free")
        self.assertEqual(t.token_cost, 0)
        self.assertIsNone(t.copy_limit_per_day)

    # ── Dry-run ───────────────────────────────────────────────────────────────

    def test_dry_run_creates_nothing(self):
        call_command("inflate_templates", dry_run=True, verbosity=0)
        count = Template.objects.filter(external_id__startswith="INFL-").count()
        self.assertEqual(count, 0, "dry-run must not write to the database")

    def test_dry_run_output_contains_dry_run_marker(self):
        stdout = StringIO()
        call_command("inflate_templates", dry_run=True, stdout=stdout, verbosity=0)
        self.assertIn("[DRY RUN]", stdout.getvalue())

    # ── Rollback ──────────────────────────────────────────────────────────────

    def test_rollback_removes_all_infl_templates(self):
        call_command("inflate_templates", verbosity=0)
        self.assertGreater(
            Template.objects.filter(external_id__startswith="INFL-").count(), 0
        )
        call_command("inflate_templates", rollback=True, verbosity=0)
        remaining = Template.objects.filter(external_id__startswith="INFL-").count()
        self.assertEqual(remaining, 0)

    def test_rollback_dry_run_does_not_delete(self):
        call_command("inflate_templates", verbosity=0)
        count_before = Template.objects.filter(external_id__startswith="INFL-").count()
        call_command("inflate_templates", rollback=True, dry_run=True, verbosity=0)
        count_after = Template.objects.filter(external_id__startswith="INFL-").count()
        self.assertEqual(count_before, count_after)

    # ── Category filter ───────────────────────────────────────────────────────

    def test_category_filter_only_creates_matching_category(self):
        call_command("inflate_templates", category="typescript", verbosity=0)
        ts_count = Template.objects.filter(
            external_id__startswith="INFL-TS-"
        ).count()
        other_count = Template.objects.filter(
            external_id__startswith="INFL-"
        ).exclude(external_id__startswith="INFL-TS-").count()
        self.assertGreater(ts_count, 0)
        self.assertEqual(other_count, 0)

    def test_category_filter_invalid_slug_raises_error(self):
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command("inflate_templates", category="nonexistent-slug", verbosity=0)

    # ── Summary output ────────────────────────────────────────────────────────

    def test_completion_summary_in_output(self):
        stdout = StringIO()
        call_command("inflate_templates", stdout=stdout, verbosity=0)
        output = stdout.getvalue()
        self.assertIn("Inflation complete", output)
        self.assertIn("Created:", output)
        self.assertIn("Skipped", output)
        self.assertIn("Errors: 0", output)
