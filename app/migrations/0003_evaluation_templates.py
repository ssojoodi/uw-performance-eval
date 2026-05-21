import django.db.models.deletion
from django.db import migrations, models

from app.evaluation_templates import UW_END_TERM_TEMPLATE_DEFINITION


def seed_initial_template(apps, schema_editor):
    EvaluationTemplate = apps.get_model("app", "EvaluationTemplate")
    Evaluation = apps.get_model("app", "Evaluation")

    template, _ = EvaluationTemplate.objects.update_or_create(
        slug=UW_END_TERM_TEMPLATE_DEFINITION["slug"],
        version=UW_END_TERM_TEMPLATE_DEFINITION["version"],
        defaults={
            "name": UW_END_TERM_TEMPLATE_DEFINITION["name"],
            "description": UW_END_TERM_TEMPLATE_DEFINITION["description"],
            "is_active": UW_END_TERM_TEMPLATE_DEFINITION["is_active"],
            "is_finalized": UW_END_TERM_TEMPLATE_DEFINITION["is_finalized"],
            "schema": UW_END_TERM_TEMPLATE_DEFINITION["schema"],
        },
    )
    Evaluation.objects.filter(template__isnull=True).update(template=template)


def unseed_initial_template(apps, schema_editor):
    EvaluationTemplate = apps.get_model("app", "EvaluationTemplate")
    Evaluation = apps.get_model("app", "Evaluation")

    template = EvaluationTemplate.objects.filter(
        slug=UW_END_TERM_TEMPLATE_DEFINITION["slug"],
        version=UW_END_TERM_TEMPLATE_DEFINITION["version"],
    ).first()
    if template:
        Evaluation.objects.filter(template=template).update(template=None)
        template.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0002_create_role_groups"),
    ]

    operations = [
        migrations.CreateModel(
            name="EvaluationTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("version", models.PositiveIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                ("is_finalized", models.BooleanField(default=False)),
                ("schema", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["slug", "-version"],
            },
        ),
        migrations.AddField(
            model_name="evaluation",
            name="template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="evaluations",
                to="app.evaluationtemplate",
            ),
        ),
        migrations.RunPython(seed_initial_template, unseed_initial_template),
        migrations.AlterField(
            model_name="evaluation",
            name="template",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="evaluations",
                to="app.evaluationtemplate",
            ),
        ),
        migrations.AddConstraint(
            model_name="evaluationtemplate",
            constraint=models.UniqueConstraint(
                fields=("slug", "version"),
                name="unique_evaluation_template_version",
            ),
        ),
    ]
