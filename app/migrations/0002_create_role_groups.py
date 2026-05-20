from django.db import migrations


ROLE_GROUPS = ("VP", "Manager", "Employee")


def create_role_groups(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    for name in ROLE_GROUPS:
        group.objects.get_or_create(name=name)


def remove_role_groups(apps, schema_editor):
    group = apps.get_model("auth", "Group")
    group.objects.filter(name__in=ROLE_GROUPS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_role_groups, remove_role_groups),
    ]
