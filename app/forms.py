from django import forms

from .evaluation_templates import (
    QUESTION_SELECT_MANY,
    QUESTION_SELECT_ONE,
    QUESTION_TEXT,
)


class EvaluationForm(forms.Form):
    def __init__(
        self,
        *args,
        evaluation=None,
        require_complete=False,
        read_only=False,
        **kwargs,
    ):
        self.evaluation = evaluation
        self.require_complete = require_complete
        self.read_only = read_only
        self.schema = evaluation.template.schema if evaluation else {"sections": []}

        if evaluation and not args and "initial" not in kwargs:
            initial = dict(evaluation.form_data)
            initial.setdefault("pi_student", evaluation.employee.name)
            initial.setdefault("pi_student_id", evaluation.employee.student_id)
            kwargs["initial"] = initial

        super().__init__(*args, **kwargs)

        for question in self.questions:
            self.fields[question["id"]] = self._build_field(question)

        self.rating_section_title = self._rating_section_title()
        self.competency_sections = self._build_competency_sections()
        self.field_sections = self._build_field_sections()
        self.lead_field_sections, self.followup_field_sections = self._split_sections()

        if self.read_only:
            for field in self.fields.values():
                field.disabled = True

    @property
    def questions(self):
        questions = []
        for section in self.schema.get("sections", []):
            if section.get("kind") == "ratings":
                for group in section.get("groups", []):
                    questions.extend(group.get("questions", []))
            else:
                questions.extend(section.get("questions", []))
        return questions

    def clean(self):
        cleaned_data = super().clean()
        for question in self.questions:
            field_name = question["id"]
            value = cleaned_data.get(field_name)

            max_selections = question.get("max_selections")
            if max_selections and value and len(value) > max_selections:
                self.add_error(field_name, f"Select up to {max_selections} options.")

            if (
                self.require_complete
                and question.get("required")
                and self._is_empty(value)
            ):
                self.add_error(
                    field_name,
                    "This field is required before submitting for review.",
                )
        return cleaned_data

    def save(self):
        self.evaluation.form_data = {
            question["id"]: self.cleaned_data.get(question["id"])
            for question in self.questions
        }
        self.evaluation.save()
        return self.evaluation

    def _build_field(self, question):
        question_type = question.get("type")
        label = question.get("label", question["id"])

        if question_type == QUESTION_TEXT:
            widget = forms.TextInput
            widget_kwargs = {}
            if question.get("widget") == "textarea":
                widget = forms.Textarea
                widget_kwargs["attrs"] = {"rows": question.get("rows", 5)}
            return forms.CharField(
                label=label,
                required=False,
                max_length=question.get("max_length"),
                widget=widget(**widget_kwargs),
            )

        if question_type == QUESTION_SELECT_ONE:
            choices = self._choices_for_field(question)
            widget = (
                forms.RadioSelect
                if question.get("display") == "rating_cards"
                else forms.Select
            )
            return forms.ChoiceField(
                label=label,
                required=False,
                choices=choices,
                widget=widget,
            )

        if question_type == QUESTION_SELECT_MANY:
            return forms.MultipleChoiceField(
                label=label,
                required=False,
                choices=self._choices_for_field(question),
                widget=forms.CheckboxSelectMultiple,
            )

        raise ValueError(f"Unsupported evaluation question type: {question_type}")

    def _choices_for_field(self, question):
        choices = [self._choice_tuple(choice) for choice in question.get("choices", [])]
        if (
            question.get("type") == QUESTION_SELECT_ONE
            and question.get("display") != "rating_cards"
        ):
            return [("", "select"), *choices]
        return choices

    def _choice_tuple(self, choice):
        if isinstance(choice, dict):
            value = choice["value"]
            return value, choice.get("label") or choice.get("text") or value
        return choice, choice

    def _build_field_sections(self):
        sections = []
        for section in self.schema.get("sections", []):
            if section.get("kind") == "ratings":
                continue
            fields = []
            for question in section.get("questions", []):
                field_name = question["id"]
                fields.append(
                    {
                        "field": self[field_name],
                        "hint": question.get("hint"),
                    }
                )
            sections.append(
                {
                    "title": section["title"],
                    "fields": fields,
                    "class": "form-grid" if section.get("layout") == "grid" else "",
                }
            )
        return sections

    def _build_competency_sections(self):
        competency_sections = []
        for section in self.schema.get("sections", []):
            if section.get("kind") != "ratings":
                continue
            for group in section.get("groups", []):
                items = []
                for question in group.get("questions", []):
                    field_name = question["id"]
                    bound_field = self[field_name]
                    selected_value = bound_field.value()
                    items.append(
                        {
                            "label": question["label"],
                            "field": bound_field,
                            "options": [
                                {
                                    **choice,
                                    "name": bound_field.html_name,
                                    "id": f"id_{bound_field.html_name}_{option_index}",
                                    "checked": selected_value == choice["value"],
                                    "disabled": self.read_only,
                                }
                                for option_index, choice in enumerate(
                                    question.get("choices", [])
                                )
                            ],
                        }
                    )
                competency_sections.append(
                    {
                        "title": group["title"],
                        "intro": section.get("intro", ""),
                        "items": items,
                    }
                )
        return competency_sections

    def _split_sections(self):
        lead_count = 0
        for section in self.schema.get("sections", []):
            if section.get("kind") == "ratings":
                break
            lead_count += 1
        return self.field_sections[:lead_count], self.field_sections[lead_count:]

    def _rating_section_title(self):
        for section in self.schema.get("sections", []):
            if section.get("kind") == "ratings":
                return section.get("title", "Rating Details")
        return "Rating Details"

    def _is_empty(self, value):
        return value is None or value == "" or value == []
