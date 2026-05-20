from django import forms


RATING_OPTIONS = [
    {
        "value": "Not observed",
        "short": "N.O.",
        "text": "Not observed",
    },
    {
        "value": "1 - Poor performance",
        "short": "1",
        "text": "Poor performance",
    },
    {
        "value": "2 - Developing performance",
        "short": "2",
        "text": "Developing performance",
    },
    {
        "value": "3 - Good performance",
        "short": "3",
        "text": "Good performance",
    },
    {
        "value": "4 - Strong performance",
        "short": "4",
        "text": "Strong performance",
    },
]
RATING_CHOICES = [(option["value"], option["text"]) for option in RATING_OPTIONS]

COMPETENCY_SECTIONS = [
    {
        "id": "expand_transfer_expertise",
        "title": "Expand and Transfer Expertise",
        "items": [
            "learn job duties and work processes",
            "locate, evaluate, and use information effectively",
            "draw reasoned conclusions from multiple sources of information",
            "learn and employ technical skills necessary for the role",
            "apply skills and prior knowledge from academic program and/or previous work experience",
        ],
    },
    {
        "id": "design_deliver_solutions",
        "title": "Design and Deliver Solutions",
        "items": [
            "deliver quality work",
            "meet deadlines and cope with workplace pressures",
            "analyze problems and evaluate alternative solutions",
            "engage in work with curiosity; ask questions to understand more than the work assigned",
            "identify opportunities for improvement within the team and/or organization",
        ],
    },
    {
        "id": "develop_self",
        "title": "Develop Self",
        "items": [
            "adapt to changing priorities and circumstances",
            "recognize limits of knowledge, skills and abilities",
            "respond well to direction and incorporate feedback on performance",
            "seek new tasks and responsibilities",
            "seek opportunities to learn",
        ],
    },
    {
        "id": "build_relationships",
        "title": "Build Relationships",
        "items": [
            "write clearly and effectively",
            "orally convey ideas and information clearly and effectively",
            "collaborate well with others; both co-workers and supervisor/senior leaders",
            "demonstrate ethical conduct in the workplace",
            "show understanding and sensitivity to the needs and differences of others in the workplace (e.g. ethnicity, religion, language, etc.)",
        ],
    },
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

FIELD_SECTIONS = [
    (
        "Placement Information",
        [
            "pi_student",
            "pi_student_id",
            "pi_org",
            "pi_division",
            "pi_job_title",
            "pi_term",
            "pi_supervisor",
            "pi_supervisor_email",
        ],
        "form-grid",
    ),
    (
        "Your Information",
        ["q_your_name", "q_your_title", "q_your_phone"],
        "form-grid",
    ),
    (
        "Strengths",
        ["q_strengths", "q_strength_comments"],
        "",
    ),
    (
        "Development",
        ["q_developments", "q_development_comments"],
        "",
    ),
    (
        "Overall Evaluation",
        [
            "q_overall_rating",
            "q_supervisor_comments",
            "q_supervisor_recommendations",
            "q_reviewed_with_student",
        ],
        "",
    ),
    (
        "Student Comments",
        ["q_student_comments"],
        "",
    ),
    (
        "Future Employment Potential",
        ["q_return_next_term"],
        "",
    ),
]

FIELD_HINTS = {
    "q_strengths": "Select up to 3.",
    "q_developments": "Select up to 3.",
}


class EvaluationForm(forms.Form):
    pi_student = forms.CharField(label="Student Name", required=False, max_length=255)
    pi_student_id = forms.CharField(label="Student ID", required=False, max_length=64)
    pi_org = forms.CharField(label="Organization", required=False, max_length=255)
    pi_division = forms.CharField(
        label="Division / Department",
        required=False,
        max_length=255,
    )
    pi_job_title = forms.CharField(label="Job Title", required=False, max_length=255)
    pi_term = forms.CharField(label="Work Term", required=False, max_length=120)
    pi_supervisor = forms.CharField(label="Supervisor", required=False, max_length=255)
    pi_supervisor_email = forms.EmailField(label="Supervisor Email", required=False)

    q_your_name = forms.CharField(label="Your full name", required=False, max_length=255)
    q_your_title = forms.CharField(label="Your title", required=False, max_length=255)
    q_your_phone = forms.CharField(label="Your phone", required=False, max_length=80)

    q_strengths = forms.MultipleChoiceField(
        label="Top 3 areas of strength",
        required=False,
        choices=[(option, option) for option in FRAMEWORK_OPTIONS],
        widget=forms.CheckboxSelectMultiple,
    )
    q_strength_comments = forms.CharField(
        label="Additional comments on the student's top 3 areas of strength",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
    )
    q_developments = forms.MultipleChoiceField(
        label="Top 3 areas for development",
        required=False,
        choices=[(option, option) for option in FRAMEWORK_OPTIONS],
        widget=forms.CheckboxSelectMultiple,
    )
    q_development_comments = forms.CharField(
        label="Additional comments on the student's top 3 areas for development",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5}),
    )

    q_overall_rating = forms.ChoiceField(
        label="Overall performance rating",
        required=False,
        choices=[
            ("", "select"),
            ("OUTSTANDING", "OUTSTANDING"),
            ("EXCELLENT", "EXCELLENT"),
            ("VERY GOOD", "VERY GOOD"),
            ("GOOD", "GOOD"),
            ("SATISFACTORY", "SATISFACTORY"),
            ("MARGINAL", "MARGINAL"),
            ("UNSATISFACTORY", "UNSATISFACTORY"),
        ],
    )
    q_supervisor_comments = forms.CharField(
        label="Supervisor's comments",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
    )
    q_supervisor_recommendations = forms.CharField(
        label="Supervisor's recommendations",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
    )
    q_reviewed_with_student = forms.ChoiceField(
        label="Did you review the completed evaluation form with the student?",
        required=False,
        choices=[("", "select"), ("No", "No"), ("Yes", "Yes")],
    )
    q_student_comments = forms.CharField(
        label="Student comments",
        required=False,
        widget=forms.Textarea(attrs={"rows": 6}),
    )
    q_return_next_term = forms.ChoiceField(
        label="Do you wish to have the student return for the next work term?",
        required=False,
        choices=[
            ("", "select"),
            ("N/A", "N/A"),
            ("No", "No"),
            ("Undecided", "Undecided"),
            ("Yes", "Yes"),
        ],
    )

    def __init__(self, *args, evaluation=None, require_complete=False, **kwargs):
        self.evaluation = evaluation
        self.require_complete = require_complete
        if evaluation and not args and "initial" not in kwargs:
            initial = dict(evaluation.form_data)
            initial.setdefault("pi_student", evaluation.employee.name)
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)
        self.competency_sections = self._build_competency_sections()
        self.field_sections = self._build_field_sections()
        self.lead_field_sections = self.field_sections[:2]
        self.followup_field_sections = self.field_sections[2:]

    def clean_q_strengths(self):
        return self._clean_limited_choices("q_strengths")

    def clean_q_developments(self):
        return self._clean_limited_choices("q_developments")

    def clean(self):
        cleaned_data = super().clean()
        if not self.require_complete:
            return cleaned_data

        required_fields = [
            "q_strengths",
            "q_developments",
            "q_overall_rating",
            "q_reviewed_with_student",
            "q_return_next_term",
        ]
        for field_name in required_fields:
            if not cleaned_data.get(field_name):
                self.add_error(
                    field_name,
                    "This field is required before submitting for review.",
                )

        return cleaned_data

    def save(self):
        self.evaluation.form_data = {
            field_name: self.cleaned_data[field_name]
            for field_name in self.fields
        }
        self.evaluation.save()
        return self.evaluation

    def _clean_limited_choices(self, field_name):
        values = self.cleaned_data[field_name]
        if len(values) > 3:
            raise forms.ValidationError("Select up to 3 options.")
        return values

    def _build_field_sections(self):
        return [
            {
                "title": title,
                "fields": [
                    {
                        "field": self[field_name],
                        "hint": FIELD_HINTS.get(field_name),
                    }
                    for field_name in field_names
                ],
                "class": section_class,
            }
            for title, field_names, section_class in FIELD_SECTIONS
        ]

    def _build_competency_sections(self):
        sections = []
        for section in COMPETENCY_SECTIONS:
            items = []
            for index, label in enumerate(section["items"]):
                field_name = f"{section['id']}_{index}"
                self.fields[field_name] = forms.ChoiceField(
                    label=label,
                    required=False,
                    choices=RATING_CHOICES,
                    widget=forms.RadioSelect,
                )
                bound_field = self[field_name]
                items.append(
                    {
                        "label": label,
                        "field": bound_field,
                        "options": [
                            {
                                **option,
                                "name": bound_field.html_name,
                                "id": f"id_{bound_field.html_name}_{option_index}",
                                "checked": bound_field.value() == option["value"],
                            }
                            for option_index, option in enumerate(RATING_OPTIONS)
                        ],
                    }
                )
            sections.append(
                {
                    "title": section["title"],
                    "items": items,
                }
            )
        return sections
