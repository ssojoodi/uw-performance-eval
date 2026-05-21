from django.db import migrations


FRAMEWORK_OPTIONS = [
    "Discipline and context specific skills",
    "Information and data literacy",
    "Technological agility",
    "Self-management",
    "Self-assessment",
    "Lifelong learning and career development",
    "Communication",
    "Collaboration",
    "Intercultural effectiveness",
    "Innovation mindset",
    "Critical thinking",
    "Implementation",
]


def text_question(question_id, label, *, max_length=None, multiline=False, rows=5):
    question = {"id": question_id, "label": label, "type": "text", "required": False}
    if max_length:
        question["max_length"] = max_length
    if multiline:
        question["widget"] = "textarea"
        question["rows"] = rows
    return question


def select_one_question(question_id, label, choices, *, required=False):
    return {
        "id": question_id,
        "label": label,
        "type": "select_one",
        "required": required,
        "choices": choices,
    }


def framework_hint():
    return "For more information on these 12 competencies, see the Future Ready Talent Framework."


UW_MID_TERM_TEMPLATE_DEFINITION = {
    "name": "UW Co-op Employer Mid-term Review",
    "slug": "uw-mid-term",
    "description": "University of Waterloo employer mid-term check-in review.",
    "version": 1,
    "is_active": True,
    "is_finalized": True,
    "schema": {
        "schema_version": 1,
        "sections": [
            {
                "title": "Placement Information",
                "layout": "grid",
                "questions": [
                    text_question("pi_student", "Student Name", max_length=255),
                ],
            },
            {
                "title": "Your Information (Who Is Completing This Form)",
                "layout": "grid",
                "questions": [
                    text_question("q_your_name", "Your full name", max_length=255),
                ],
            },
            {
                "title": "Your Feedback - Required",
                "questions": [
                    select_one_question(
                        "q_expectations",
                        "Overall, how is the student meeting your expectations with respect to their job performance and conduct at work?",
                        [
                            "Exceeding expectations",
                            "Meeting expectations",
                            "Not meeting expectations",
                        ],
                        required=True,
                    ),
                    select_one_question(
                        "q_eem_questions",
                        "Do you have any other questions or concerns that you would like to talk about with your Employer Experience Manager?",
                        ["Yes", "No"],
                        required=True,
                    ),
                ],
            },
            {
                "title": "Your Feedback - Optional",
                "questions": [
                    {
                        **select_one_question(
                            "q_strength",
                            "Based on the student's performance in the role to date, please select your student's top area of strength:",
                            FRAMEWORK_OPTIONS,
                        ),
                        "hint": framework_hint(),
                    },
                    text_question(
                        "q_strength_comments",
                        "Please provide any additional comments on your student's top area of strength:",
                        multiline=True,
                        rows=4,
                    ),
                    {
                        **select_one_question(
                            "q_development",
                            "Based on the student's performance in the role to date, please select an area for development:",
                            FRAMEWORK_OPTIONS,
                        ),
                        "hint": framework_hint(),
                    },
                    text_question(
                        "q_development_comments",
                        "Please provide any additional comments on your student's top area for development:",
                        multiline=True,
                        rows=4,
                    ),
                ],
            },
        ],
    },
}


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
