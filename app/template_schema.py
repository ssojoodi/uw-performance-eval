from django.core.exceptions import ValidationError


QUESTION_TEXT = "text"
QUESTION_SELECT_ONE = "select_one"
QUESTION_SELECT_MANY = "select_many"
QUESTION_TYPES = {QUESTION_TEXT, QUESTION_SELECT_ONE, QUESTION_SELECT_MANY}


def iter_schema_questions(schema):
    for section in schema.get("sections", []):
        if section.get("kind") == "ratings":
            for group in section.get("groups", []):
                yield from group.get("questions", [])
        else:
            yield from section.get("questions", [])


def validate_template_schema(schema):
    if not isinstance(schema, dict):
        raise ValidationError("Template schema must be a JSON object.")

    sections = schema.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ValidationError("Template schema must include at least one section.")

    seen_question_ids = set()
    for section in sections:
        _validate_section(section, seen_question_ids)


def _validate_section(section, seen_question_ids):
    if not isinstance(section, dict):
        raise ValidationError("Each template section must be an object.")
    if not section.get("title"):
        raise ValidationError("Each template section must have a title.")

    if section.get("kind") == "ratings":
        groups = section.get("groups")
        if not isinstance(groups, list) or not groups:
            raise ValidationError("Rating sections must include at least one group.")
        for group in groups:
            if not isinstance(group, dict) or not group.get("title"):
                raise ValidationError("Each rating group must have a title.")
            _validate_questions(group.get("questions"), seen_question_ids)
        return

    _validate_questions(section.get("questions"), seen_question_ids)


def _validate_questions(questions, seen_question_ids):
    if not isinstance(questions, list) or not questions:
        raise ValidationError("Each template section must include at least one question.")

    for question in questions:
        if not isinstance(question, dict):
            raise ValidationError("Each template question must be an object.")

        question_id = question.get("id")
        if not question_id:
            raise ValidationError("Each template question must have an id.")
        if question_id in seen_question_ids:
            raise ValidationError(f"Duplicate template question id: {question_id}.")
        seen_question_ids.add(question_id)

        question_type = question.get("type")
        if question_type not in QUESTION_TYPES:
            raise ValidationError(f"Unsupported template question type: {question_type}.")
        if not question.get("label"):
            raise ValidationError(f"Template question {question_id} must have a label.")

        if question_type in {QUESTION_SELECT_ONE, QUESTION_SELECT_MANY}:
            choices = question.get("choices")
            if not isinstance(choices, list) or not choices:
                raise ValidationError(
                    f"Template question {question_id} must include choices."
                )
            for choice in choices:
                if isinstance(choice, dict):
                    if not choice.get("value"):
                        raise ValidationError(
                            f"Template question {question_id} has a choice without a value."
                        )
                elif not isinstance(choice, str):
                    raise ValidationError(
                        f"Template question {question_id} choices must be strings or objects."
                    )

        max_selections = question.get("max_selections")
        if max_selections is not None and (
            not isinstance(max_selections, int) or max_selections < 1
        ):
            raise ValidationError(
                f"Template question {question_id} max_selections must be a positive integer."
            )
