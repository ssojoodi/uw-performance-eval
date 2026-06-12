from io import BytesIO
from xml.sax.saxutils import escape

from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def render_evaluation_markdown(evaluation):
    lines = [
        f"# {evaluation.employee.name} Evaluation",
        "",
        "## Summary",
        "",
    ]

    for label, value in _summary_rows(evaluation):
        lines.append(f"- **{label}:** {_markdown_value(value)}")

    for section in _export_sections(evaluation):
        lines.extend(["", f"## {section['title']}", ""])
        if section.get("intro"):
            lines.extend([section["intro"], ""])
        for item in section["items"]:
            if item["kind"] == "group":
                lines.extend([f"### {item['title']}", ""])
                continue
            lines.extend(
                [
                    f"### {item['label']}",
                    "",
                    _markdown_value(item["value"]),
                    "",
                ]
            )

    return "\n".join(lines).strip() + "\n"


def render_evaluation_pdf(evaluation):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=f"{evaluation.employee.name} Evaluation",
    )

    stylesheet = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ExportTitle",
            parent=stylesheet["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            spaceAfter=14,
            textColor=colors.HexColor("#111111"),
        ),
        "section": ParagraphStyle(
            "ExportSection",
            parent=stylesheet["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            spaceBefore=14,
            spaceAfter=8,
            textColor=colors.HexColor("#222222"),
        ),
        "group": ParagraphStyle(
            "ExportGroup",
            parent=stylesheet["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=5,
            textColor=colors.HexColor("#333333"),
        ),
        "label": ParagraphStyle(
            "ExportLabel",
            parent=stylesheet["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#333333"),
        ),
        "body": ParagraphStyle(
            "ExportBody",
            parent=stylesheet["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#111111"),
        ),
    }

    story = [
        Paragraph(_pdf_text(f"{evaluation.employee.name} Evaluation"), styles["title"]),
        _table_for_rows(_summary_rows(evaluation), styles),
        Spacer(1, 10),
    ]

    for section in _export_sections(evaluation):
        story.append(Paragraph(_pdf_text(section["title"]), styles["section"]))
        if section.get("intro"):
            story.append(Paragraph(_pdf_text(section["intro"]), styles["body"]))
            story.append(Spacer(1, 4))
        for item in section["items"]:
            if item["kind"] == "group":
                story.append(Paragraph(_pdf_text(item["title"]), styles["group"]))
                continue
            story.append(
                _table_for_rows([(item["label"], item["value"])], styles)
            )
            story.append(Spacer(1, 4))

    doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    return buffer.getvalue()


def _export_sections(evaluation):
    form_data = _form_data_with_defaults(evaluation)
    sections = []
    for section in evaluation.template.schema.get("sections", []):
        export_section = {
            "title": section["title"],
            "intro": section.get("intro", ""),
            "items": [],
        }
        if section.get("kind") == "ratings":
            for group in section.get("groups", []):
                export_section["items"].append(
                    {"kind": "group", "title": group["title"]}
                )
                for question in group.get("questions", []):
                    export_section["items"].append(_question_item(question, form_data))
        else:
            for question in section.get("questions", []):
                export_section["items"].append(_question_item(question, form_data))
        sections.append(export_section)
    return sections


def _question_item(question, form_data):
    return {
        "kind": "field",
        "label": question["label"],
        "value": _display_value(question, form_data.get(question["id"])),
    }


def _form_data_with_defaults(evaluation):
    form_data = dict(evaluation.form_data)
    form_data.setdefault("pi_student", evaluation.employee.name)
    form_data.setdefault("pi_student_id", evaluation.employee.student_id)
    return form_data


def _display_value(question, value):
    if value in (None, "", []):
        return ""
    if isinstance(value, list):
        return [_choice_label(question, item) for item in value]
    return _choice_label(question, value)


def _choice_label(question, value):
    for choice in question.get("choices", []):
        if isinstance(choice, dict):
            if choice.get("value") == value:
                return (
                    choice.get("label")
                    or _combined_choice_label(choice)
                    or choice.get("value")
                )
        elif choice == value:
            return choice
    return value


def _combined_choice_label(choice):
    short = choice.get("short")
    text = choice.get("text")
    if short and text and short != text:
        return f"{short} - {text}"
    return text


def _summary_rows(evaluation):
    return [
        ("Employee", evaluation.employee.name),
        ("Student ID", evaluation.employee.student_id),
        ("Manager", evaluation.manager.get_username()),
        ("Template", f"{evaluation.template.name} v{evaluation.template.version}"),
        ("Status", evaluation.get_state_display()),
        ("Created", _format_datetime(evaluation.created_at)),
        ("Updated", _format_datetime(evaluation.updated_at)),
        ("Submitted", _format_datetime(evaluation.submitted_at)),
        ("Approved", _format_datetime(evaluation.approved_at)),
        ("Approved By", _username_or_blank(evaluation.approved_by)),
        ("Returned", _format_datetime(evaluation.returned_at)),
        ("Returned By", _username_or_blank(evaluation.returned_by)),
    ]


def _format_datetime(value):
    if not value:
        return ""
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M %Z")


def _username_or_blank(user):
    return user.get_username() if user else ""


def _markdown_value(value):
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "-"
    return str(value) if value else "-"


def _table_for_rows(rows, styles):
    data = [
        [
            Paragraph(_pdf_text(label), styles["label"]),
            Paragraph(_pdf_text(_pdf_value(value)), styles["body"]),
        ]
        for label, value in rows
    ]
    table = Table(data, colWidths=[1.75 * inch, 5.0 * inch], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d7d7d7")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f3f3")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _pdf_value(value):
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "-"
    return str(value) if value else "-"


def _pdf_text(value):
    return escape(str(value)).replace("\n", "<br/>")


def _add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawRightString(
        letter[0] - doc.rightMargin,
        0.35 * inch,
        f"Page {doc.page}",
    )
    canvas.restoreState()
