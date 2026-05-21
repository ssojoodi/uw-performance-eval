QUESTION_TEXT = "text"
QUESTION_SELECT_ONE = "select_one"
QUESTION_SELECT_MANY = "select_many"

UW_END_TERM_TEMPLATE_SLUG = "uw-end-term"
UW_END_TERM_TEMPLATE_VERSION = 1

RATING_OPTIONS = [
    {"value": "Not observed", "short": "N.O.", "text": "Not observed"},
    {"value": "1 - Poor performance", "short": "1", "text": "Poor performance"},
    {
        "value": "2 - Developing performance",
        "short": "2",
        "text": "Developing performance",
    },
    {"value": "3 - Good performance", "short": "3", "text": "Good performance"},
    {"value": "4 - Strong performance", "short": "4", "text": "Strong performance"},
]

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

COMPETENCY_GROUPS = [
    (
        "expand_transfer_expertise",
        "Expand and Transfer Expertise",
        [
            "learn job duties and work processes",
            "locate, evaluate, and use information effectively",
            "draw reasoned conclusions from multiple sources of information",
            "learn and employ technical skills necessary for the role",
            "apply skills and prior knowledge from academic program and/or previous work experience",
        ],
    ),
    (
        "design_deliver_solutions",
        "Design and Deliver Solutions",
        [
            "deliver quality work",
            "meet deadlines and cope with workplace pressures",
            "analyze problems and evaluate alternative solutions",
            "engage in work with curiosity; ask questions to understand more than the work assigned",
            "identify opportunities for improvement within the team and/or organization",
        ],
    ),
    (
        "develop_self",
        "Develop Self",
        [
            "adapt to changing priorities and circumstances",
            "recognize limits of knowledge, skills and abilities",
            "respond well to direction and incorporate feedback on performance",
            "seek new tasks and responsibilities",
            "seek opportunities to learn",
        ],
    ),
    (
        "build_relationships",
        "Build Relationships",
        [
            "write clearly and effectively",
            "orally convey ideas and information clearly and effectively",
            "collaborate well with others; both co-workers and supervisor/senior leaders",
            "demonstrate ethical conduct in the workplace",
            "show understanding and sensitivity to the needs and differences of others in the workplace (e.g. ethnicity, religion, language, etc.)",
        ],
    ),
]


def text_question(question_id, label, *, max_length=None, multiline=False, rows=5):
    question = {
        "id": question_id,
        "label": label,
        "type": QUESTION_TEXT,
        "required": False,
    }
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
        "type": QUESTION_SELECT_ONE,
        "required": required,
        "choices": choices,
    }


def select_many_question(question_id, label, choices, *, required=False, max_selections=None):
    question = {
        "id": question_id,
        "label": label,
        "type": QUESTION_SELECT_MANY,
        "required": required,
        "choices": choices,
    }
    if max_selections:
        question["max_selections"] = max_selections
        question["hint"] = f"Select up to {max_selections}."
    return question


UW_END_TERM_SCHEMA = {
    "schema_version": 1,
    "sections": [
        {
            "title": "Placement Information",
            "layout": "grid",
            "questions": [
                text_question("pi_student", "Student Name", max_length=255),
                text_question("pi_student_id", "Student ID", max_length=64),
                text_question("pi_org", "Organization", max_length=255),
                text_question("pi_division", "Division / Department", max_length=255),
                text_question("pi_job_title", "Job Title", max_length=255),
                text_question("pi_term", "Work Term", max_length=120),
                text_question("pi_supervisor", "Supervisor", max_length=255),
                text_question("pi_supervisor_email", "Supervisor Email", max_length=255),
            ],
        },
        {
            "title": "Your Information",
            "layout": "grid",
            "questions": [
                text_question("q_your_name", "Your full name", max_length=255),
                text_question("q_your_title", "Your title", max_length=255),
                text_question("q_your_phone", "Your phone", max_length=80),
            ],
        },
        {
            "title": "Rating Details",
            "kind": "ratings",
            "intro": "Student demonstrates the ability to:",
            "groups": [
                {
                    "id": group_id,
                    "title": title,
                    "questions": [
                        {
                            "id": f"{group_id}_{index}",
                            "label": label,
                            "type": QUESTION_SELECT_ONE,
                            "required": False,
                            "display": "rating_cards",
                            "choices": RATING_OPTIONS,
                        }
                        for index, label in enumerate(items)
                    ],
                }
                for group_id, title, items in COMPETENCY_GROUPS
            ],
        },
        {
            "title": "Strengths",
            "questions": [
                select_many_question(
                    "q_strengths",
                    "Top 3 areas of strength",
                    FRAMEWORK_OPTIONS,
                    required=True,
                    max_selections=3,
                ),
                text_question(
                    "q_strength_comments",
                    "Additional comments on the student's top 3 areas of strength",
                    multiline=True,
                ),
            ],
        },
        {
            "title": "Development",
            "questions": [
                select_many_question(
                    "q_developments",
                    "Top 3 areas for development",
                    FRAMEWORK_OPTIONS,
                    required=True,
                    max_selections=3,
                ),
                text_question(
                    "q_development_comments",
                    "Additional comments on the student's top 3 areas for development",
                    multiline=True,
                ),
            ],
        },
        {
            "title": "Overall Evaluation",
            "questions": [
                select_one_question(
                    "q_overall_rating",
                    "Overall performance rating",
                    [
                        "OUTSTANDING",
                        "EXCELLENT",
                        "VERY GOOD",
                        "GOOD",
                        "SATISFACTORY",
                        "MARGINAL",
                        "UNSATISFACTORY",
                    ],
                    required=True,
                ),
                text_question(
                    "q_supervisor_comments",
                    "Supervisor's comments",
                    multiline=True,
                    rows=6,
                ),
                text_question(
                    "q_supervisor_recommendations",
                    "Supervisor's recommendations",
                    multiline=True,
                    rows=6,
                ),
                select_one_question(
                    "q_reviewed_with_student",
                    "Did you review the completed evaluation form with the student?",
                    ["No", "Yes"],
                    required=True,
                ),
            ],
        },
        {
            "title": "Student Comments",
            "questions": [
                text_question("q_student_comments", "Student comments", multiline=True, rows=6)
            ],
        },
        {
            "title": "Future Employment Potential",
            "questions": [
                select_one_question(
                    "q_return_next_term",
                    "Do you wish to have the student return for the next work term?",
                    ["N/A", "No", "Undecided", "Yes"],
                    required=True,
                ),
            ],
        },
    ],
}

UW_END_TERM_TEMPLATE_DEFINITION = {
    "name": "UW Co-op Employer End-of-Term Evaluation",
    "slug": UW_END_TERM_TEMPLATE_SLUG,
    "description": "University of Waterloo employer end-of-term performance evaluation.",
    "version": UW_END_TERM_TEMPLATE_VERSION,
    "is_active": True,
    "is_finalized": True,
    "schema": UW_END_TERM_SCHEMA,
}
