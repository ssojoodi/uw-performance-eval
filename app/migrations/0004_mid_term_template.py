from django.db import migrations

from app.evaluation_templates import UW_MID_TERM_TEMPLATE_DEFINITION


def seed_mid_term_template(apps, schema_editor):
    EvaluationTemplate = apps.get_model("app", "EvaluationTemplate")
    EvaluationTemplate.objects.update_or_create(
        slug=UW_MID_TERM_TEMPLATE_DEFINITION["slug"],
        version=UW_MID_TERM_TEMPLATE_DEFINITION["version"],
        defaults={
            "name": UW_MID_TERM_TEMPLATE_DEFINITION["name"],
            "description": UW_MID_TERM_TEMPLATE_DEFINITION["description"],
            "is_active": UW_MID_TERM_TEMPLATE_DEFINITION["is_active"],
            "is_finalized": UW_MID_TERM_TEMPLATE_DEFINITION["is_finalized"],
            "schema": UW_MID_TERM_TEMPLATE_DEFINITION["schema"],
        },
    )


def unseed_mid_term_template(apps, schema_editor):
    EvaluationTemplate = apps.get_model("app", "EvaluationTemplate")
    EvaluationTemplate.objects.filter(
        slug=UW_MID_TERM_TEMPLATE_DEFINITION["slug"],
        version=UW_MID_TERM_TEMPLATE_DEFINITION["version"],
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0003_evaluation_templates"),
    ]

    operations = [
        migrations.RunPython(seed_mid_term_template, unseed_mid_term_template),
    ]
