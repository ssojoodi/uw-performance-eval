from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Employee, Evaluation, EvaluationTemplate, ManagerAssignment
from .roles import ROLE_MANAGER, ROLE_VP


UW_END_TERM_TEMPLATE_SLUG = "uw-end-term"
UW_END_TERM_TEMPLATE_VERSION = 1
UW_MID_TERM_TEMPLATE_SLUG = "uw-mid-term"
UW_MID_TERM_TEMPLATE_VERSION = 1


class BaseAppTests(TestCase):
    def create_manager(self, username="manager"):
        user = get_user_model().objects.create_user(username=username)
        manager_group, _ = Group.objects.get_or_create(name=ROLE_MANAGER)
        user.groups.add(manager_group)
        return user

    def create_vp(self, username="vp"):
        user = get_user_model().objects.create_user(username=username)
        vp_group, _ = Group.objects.get_or_create(name=ROLE_VP)
        user.groups.add(vp_group)
        return user

    def get_template(self):
        return EvaluationTemplate.objects.get(
            slug=UW_END_TERM_TEMPLATE_SLUG,
            version=UW_END_TERM_TEMPLATE_VERSION,
        )

    def get_mid_term_template(self):
        return EvaluationTemplate.objects.get(
            slug=UW_MID_TERM_TEMPLATE_SLUG,
            version=UW_MID_TERM_TEMPLATE_VERSION,
        )

    def create_evaluation(self, **kwargs):
        kwargs.setdefault("template", self.get_template())
        return Evaluation.objects.create(**kwargs)

    def minimal_template_schema(self):
        return {
            "sections": [
                {
                    "title": "Minimal",
                    "questions": [
                        {
                            "id": "q_minimal",
                            "label": "Minimal question",
                            "type": "text",
                            "required": False,
                        }
                    ],
                }
            ]
        }

    def test_health_check_is_public(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_authenticated_pages_show_logout_button(self):
        user = self.create_manager()
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Log out")

    def test_logout_ends_session(self):
        user = self.create_manager()
        self.client.force_login(user)

        response = self.client.post(reverse("logout"))

        self.assertRedirects(response, reverse("login"))
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_dashboard_renders_for_authenticated_user(self):
        user = self.create_manager(username="manager@example.com")
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)

    def test_dashboard_renders_for_vp_user(self):
        user = self.create_vp()
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VP workspace")

    def test_vp_dashboard_lists_in_review_and_approved_evaluations(self):
        vp = self.create_vp()
        manager = self.create_manager()
        in_review_employee = Employee.objects.create(name="Review Student")
        approved_employee = Employee.objects.create(name="Approved Student")
        draft_employee = Employee.objects.create(name="Draft Student")
        self.create_evaluation(
            manager=manager,
            employee=in_review_employee,
            state=Evaluation.State.IN_REVIEW,
        )
        self.create_evaluation(
            manager=manager,
            employee=approved_employee,
            state=Evaluation.State.APPROVED,
        )
        self.create_evaluation(
            manager=manager,
            employee=draft_employee,
            state=Evaluation.State.DRAFT,
        )
        self.client.force_login(vp)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Review Student")
        self.assertContains(response, "Approved Student")
        self.assertContains(response, "Review eval")
        self.assertContains(response, "View eval")
        self.assertNotContains(response, "Draft Student")

    def test_vp_dashboard_is_paginated(self):
        vp = self.create_vp()
        manager = self.create_manager()
        for index in range(11):
            employee = Employee.objects.create(name=f"Review Student {index:02d}")
            self.create_evaluation(
                manager=manager,
                employee=employee,
                state=Evaluation.State.IN_REVIEW,
            )
        self.client.force_login(vp)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Page 1 of 2")
        self.assertContains(response, "Next")

    def test_vp_can_preview_evaluation_in_review(self):
        vp = self.create_vp()
        manager = self.create_manager()
        employee = Employee.objects.create(name="Review Student")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
            state=Evaluation.State.IN_REVIEW,
            form_data={"q_supervisor_comments": "Ready for review."},
        )
        self.client.force_login(vp)

        response = self.client.get(reverse("vp_preview_evaluation", args=[evaluation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ready for review.")
        self.assertContains(response, "Approve")
        self.assertContains(response, "Return to draft")

    def test_vp_can_preview_approved_evaluation_read_only(self):
        vp = self.create_vp()
        manager = self.create_manager()
        employee = Employee.objects.create(name="Approved Student")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
            state=Evaluation.State.APPROVED,
            form_data={"q_supervisor_comments": "Final comments."},
        )
        self.client.force_login(vp)

        response = self.client.get(reverse("vp_preview_evaluation", args=[evaluation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Final comments.")
        self.assertContains(response, "approved and finalized")
        self.assertNotContains(response, ">Approve</button>")
        self.assertNotContains(response, "Return to draft")

    def test_vp_can_approve_evaluation(self):
        vp = self.create_vp()
        manager = self.create_manager()
        employee = Employee.objects.create(name="Review Student")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
            state=Evaluation.State.IN_REVIEW,
        )
        self.client.force_login(vp)

        response = self.client.post(reverse("approve_evaluation", args=[evaluation.id]))

        self.assertRedirects(response, reverse("dashboard"))
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.state, Evaluation.State.APPROVED)
        self.assertEqual(evaluation.approved_by, vp)
        self.assertIsNotNone(evaluation.approved_at)

    def test_vp_can_return_evaluation_to_draft(self):
        vp = self.create_vp()
        manager = self.create_manager()
        employee = Employee.objects.create(name="Review Student")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
            state=Evaluation.State.IN_REVIEW,
        )
        self.client.force_login(vp)

        response = self.client.post(reverse("return_evaluation", args=[evaluation.id]))

        self.assertRedirects(response, reverse("dashboard"))
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.state, Evaluation.State.DRAFT)
        self.assertEqual(evaluation.returned_by, vp)
        self.assertIsNotNone(evaluation.returned_at)

    def test_manager_cannot_use_vp_review_actions(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Review Student")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
            state=Evaluation.State.IN_REVIEW,
        )
        self.client.force_login(manager)

        response = self.client.post(reverse("approve_evaluation", args=[evaluation.id]))

        self.assertEqual(response.status_code, 403)
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.state, Evaluation.State.IN_REVIEW)

    def test_dashboard_rejects_authenticated_user_without_role(self):
        user = get_user_model().objects.create_user(username="employee")
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 403)

    def test_start_evaluation_rejects_vp_user(self):
        vp = self.create_vp()
        employee = Employee.objects.create(name="Assigned Employee")
        self.client.force_login(vp)

        response = self.client.post(
            reverse("start_evaluation", args=[employee.id])
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Evaluation.objects.exists())

    def test_dashboard_lists_only_active_assignments_for_user(self):
        manager = self.create_manager()
        other_manager = self.create_manager(username="other")
        assigned_employee = Employee.objects.create(name="Assigned Employee")
        inactive_employee = Employee.objects.create(
            name="Inactive Employee",
            is_active=False,
        )
        other_employee = Employee.objects.create(name="Other Employee")
        ManagerAssignment.objects.create(
            manager=manager,
            employee=assigned_employee,
        )
        ManagerAssignment.objects.create(
            manager=manager,
            employee=inactive_employee,
        )
        ManagerAssignment.objects.create(
            manager=other_manager,
            employee=other_employee,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Assigned Employee")
        self.assertNotContains(response, "Inactive Employee")
        self.assertNotContains(response, "Other Employee")

    def test_manager_dashboard_lists_all_owned_evaluations(self):
        manager = self.create_manager()
        other_manager = self.create_manager(username="other")
        draft_employee = Employee.objects.create(name="Draft Employee")
        in_review_employee = Employee.objects.create(name="Review Employee")
        approved_employee = Employee.objects.create(name="Approved Employee")
        other_employee = Employee.objects.create(name="Other Employee")
        self.create_evaluation(
            manager=manager,
            employee=draft_employee,
            state=Evaluation.State.DRAFT,
        )
        self.create_evaluation(
            manager=manager,
            employee=in_review_employee,
            state=Evaluation.State.IN_REVIEW,
        )
        self.create_evaluation(
            manager=manager,
            employee=approved_employee,
            state=Evaluation.State.APPROVED,
        )
        self.create_evaluation(
            manager=other_manager,
            employee=other_employee,
            state=Evaluation.State.APPROVED,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Draft Employee")
        self.assertContains(response, "Review Employee")
        self.assertContains(response, "Approved Employee")
        self.assertNotContains(response, "Other Employee")

    def test_manager_dashboard_is_paginated(self):
        manager = self.create_manager()
        for index in range(11):
            employee = Employee.objects.create(name=f"Eval Student {index:02d}")
            self.create_evaluation(
                manager=manager,
                employee=employee,
                state=Evaluation.State.DRAFT,
            )
        self.client.force_login(manager)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Page 1 of 2")
        self.assertContains(response, "Next")

    def test_start_evaluation_shows_active_finalized_templates(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        ManagerAssignment.objects.create(manager=manager, employee=employee)
        draft_template = EvaluationTemplate.objects.create(
            name="Draft Template",
            slug="draft-template",
            version=1,
            is_active=True,
            is_finalized=False,
            schema=self.minimal_template_schema(),
        )
        inactive_template = EvaluationTemplate.objects.create(
            name="Inactive Template",
            slug="inactive-template",
            version=1,
            is_active=False,
            is_finalized=True,
            schema=self.minimal_template_schema(),
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("start_evaluation", args=[employee.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.get_template().name)
        self.assertContains(response, self.get_mid_term_template().name)
        self.assertNotContains(response, draft_template.name)
        self.assertNotContains(response, inactive_template.name)

    def test_start_evaluation_creates_draft_and_opens_form(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        ManagerAssignment.objects.create(manager=manager, employee=employee)
        self.client.force_login(manager)

        response = self.client.post(
            reverse("start_evaluation", args=[employee.id]),
            {"template": self.get_template().id},
        )

        evaluation = Evaluation.objects.get()
        self.assertRedirects(
            response,
            reverse("edit_evaluation", args=[evaluation.id]),
        )
        self.assertEqual(evaluation.manager, manager)
        self.assertEqual(evaluation.employee, employee)
        self.assertEqual(evaluation.template, self.get_template())
        self.assertEqual(evaluation.state, Evaluation.State.DRAFT)

    def test_start_evaluation_can_create_mid_term_review(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        template = self.get_mid_term_template()
        ManagerAssignment.objects.create(manager=manager, employee=employee)
        self.client.force_login(manager)

        response = self.client.post(
            reverse("start_evaluation", args=[employee.id]),
            {"template": template.id},
        )

        evaluation = Evaluation.objects.get()
        self.assertRedirects(response, reverse("edit_evaluation", args=[evaluation.id]))
        self.assertEqual(evaluation.template, template)

    def test_mid_term_review_form_saves_and_validates_required_fields(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
            template=self.get_mid_term_template(),
        )
        self.client.force_login(manager)

        response = self.client.post(
            reverse("edit_evaluation", args=[evaluation.id]),
            {
                "pi_student": "Assigned Employee",
                "q_your_name": "Manager Person",
                "q_expectations": "Meeting expectations",
                "q_eem_questions": "No",
                "q_strength": "Communication",
                "q_strength_comments": "Clear updates.",
                "q_development": "Implementation",
                "q_development_comments": "More independent delivery.",
                "action": "submit_for_review",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.state, Evaluation.State.IN_REVIEW)
        self.assertEqual(evaluation.form_data["q_expectations"], "Meeting expectations")
        self.assertEqual(evaluation.form_data["q_eem_questions"], "No")

    def test_start_evaluation_rejects_unassigned_employee(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Unassigned Employee")
        self.client.force_login(manager)

        response = self.client.post(
            reverse("start_evaluation", args=[employee.id])
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Evaluation.objects.exists())

    def test_edit_evaluation_renders_form_for_own_draft(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("edit_evaluation", args=[evaluation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Assigned Employee")
        self.assertContains(response, "Save as draft")
        self.assertContains(response, "Submit for review")

    def test_save_as_draft_persists_form_data(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
        )
        self.client.force_login(manager)

        response = self.client.post(
            reverse("edit_evaluation", args=[evaluation.id]),
            {
                "pi_student": "Assigned Employee",
                "pi_term": "Winter 2026",
                "pi_job_title": "Software Developer",
                "q_your_name": "Manager Person",
                "q_strengths": ["Communication", "Collaboration"],
                "q_strength_comments": "Communication and ownership.",
                "q_developments": ["Critical thinking"],
                "q_development_comments": "More production debugging reps.",
                "q_overall_rating": "EXCELLENT",
                "q_supervisor_comments": "Strong delivery.",
                "q_supervisor_recommendations": "Ready for larger tasks.",
                "q_reviewed_with_student": "Yes",
                "q_return_next_term": "Yes",
                "action": "save_draft",
            },
        )

        self.assertRedirects(
            response,
            reverse("edit_evaluation", args=[evaluation.id]),
        )
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.state, Evaluation.State.DRAFT)
        self.assertEqual(evaluation.form_data["pi_term"], "Winter 2026")
        self.assertEqual(evaluation.form_data["q_overall_rating"], "EXCELLENT")
        self.assertEqual(
            evaluation.form_data["q_strengths"],
            ["Communication", "Collaboration"],
        )

    def test_submit_for_review_saves_data_and_transitions_state(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
        )
        self.client.force_login(manager)

        response = self.client.post(
            reverse("edit_evaluation", args=[evaluation.id]),
            {
                "pi_student": "Assigned Employee",
                "pi_term": "Winter 2026",
                "pi_job_title": "Software Developer",
                "q_strengths": ["Collaboration"],
                "q_strength_comments": "Reliability.",
                "q_developments": ["Critical thinking"],
                "q_development_comments": "Testing depth.",
                "q_overall_rating": "GOOD",
                "q_supervisor_comments": "Consistent progress.",
                "q_supervisor_recommendations": "Submitted for review.",
                "q_reviewed_with_student": "Yes",
                "q_return_next_term": "Undecided",
                "action": "submit_for_review",
            },
        )

        self.assertRedirects(response, reverse("dashboard"))
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.state, Evaluation.State.IN_REVIEW)
        self.assertIsNotNone(evaluation.submitted_at)
        self.assertEqual(
            evaluation.form_data["q_supervisor_recommendations"],
            "Submitted for review.",
        )

    def test_submitted_evaluation_is_not_editable_from_dashboard(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        self.create_evaluation(
            manager=manager,
            employee=employee,
            state=Evaluation.State.IN_REVIEW,
        )
        ManagerAssignment.objects.create(manager=manager, employee=employee)
        self.client.force_login(manager)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "In Review")
        self.assertContains(response, "View eval")
        self.assertNotContains(response, "Continue eval")

    def test_manager_can_preview_submitted_evaluation(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
            state=Evaluation.State.IN_REVIEW,
            form_data={
                "pi_student": "Assigned Employee",
                "q_supervisor_comments": "Submitted comments.",
            },
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("preview_evaluation", args=[evaluation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Submitted evaluation")
        self.assertContains(response, "Submitted comments.")
        self.assertContains(response, "Unlock for editing")

    def test_manager_can_preview_approved_evaluation_read_only(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
            state=Evaluation.State.APPROVED,
            form_data={"q_supervisor_comments": "Final comments."},
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("preview_evaluation", args=[evaluation.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Final comments.")
        self.assertContains(response, "approved and finalized")
        self.assertNotContains(response, "Unlock for editing")

    def test_manager_can_unlock_submitted_evaluation_for_editing(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
            state=Evaluation.State.IN_REVIEW,
        )
        self.client.force_login(manager)

        response = self.client.post(reverse("unlock_evaluation", args=[evaluation.id]))

        self.assertRedirects(response, reverse("edit_evaluation", args=[evaluation.id]))
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.state, Evaluation.State.DRAFT)

    def test_unlock_rejects_other_manager_evaluation(self):
        manager = self.create_manager()
        other_manager = self.create_manager(username="other")
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=other_manager,
            employee=employee,
            state=Evaluation.State.IN_REVIEW,
        )
        self.client.force_login(manager)

        response = self.client.post(reverse("unlock_evaluation", args=[evaluation.id]))

        self.assertEqual(response.status_code, 404)
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.state, Evaluation.State.IN_REVIEW)

    def test_submit_for_review_requires_required_end_term_fields(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
        )
        self.client.force_login(manager)

        response = self.client.post(
            reverse("edit_evaluation", args=[evaluation.id]),
            {
                "pi_student": "Assigned Employee",
                "action": "submit_for_review",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required before submitting for review.")
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.state, Evaluation.State.DRAFT)

    def test_save_as_draft_limits_strengths_to_three(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
        )
        self.client.force_login(manager)

        response = self.client.post(
            reverse("edit_evaluation", args=[evaluation.id]),
            {
                "q_strengths": [
                    "Communication",
                    "Collaboration",
                    "Critical thinking",
                    "Implementation",
                ],
                "action": "save_draft",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select up to 3 options.")
        evaluation.refresh_from_db()
        self.assertEqual(evaluation.form_data, {})

    def test_edit_evaluation_rejects_other_manager(self):
        manager = self.create_manager()
        other_manager = self.create_manager(username="other")
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=other_manager,
            employee=employee,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("edit_evaluation", args=[evaluation.id]))

        self.assertEqual(response.status_code, 404)

    def test_edit_evaluation_rejects_non_draft(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = self.create_evaluation(
            manager=manager,
            employee=employee,
            state=Evaluation.State.IN_REVIEW,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("edit_evaluation", args=[evaluation.id]))

        self.assertEqual(response.status_code, 404)


class DataModelTests(TestCase):
    def setUp(self):
        self.manager = get_user_model().objects.create_user(
            username="manager",
            email="manager@example.com",
            password="password",
        )
        self.reviewer = get_user_model().objects.create_user(
            username="vp",
            email="vp@example.com",
            password="password",
        )
        self.employee = Employee.objects.create(
            name="Taylor Student",
            email="taylor@example.com",
            student_id="12345678",
        )
        self.template = EvaluationTemplate.objects.get(
            slug=UW_END_TERM_TEMPLATE_SLUG,
            version=UW_END_TERM_TEMPLATE_VERSION,
        )
        self.mid_term_template = EvaluationTemplate.objects.get(
            slug=UW_MID_TERM_TEMPLATE_SLUG,
            version=UW_MID_TERM_TEMPLATE_VERSION,
        )

    def create_evaluation(self, **kwargs):
        kwargs.setdefault("template", self.template)
        return Evaluation.objects.create(**kwargs)

    def minimal_template_schema(self):
        return {
            "sections": [
                {
                    "title": "Minimal",
                    "questions": [
                        {
                            "id": "q_minimal",
                            "label": "Minimal question",
                            "type": "text",
                            "required": False,
                        }
                    ],
                }
            ]
        }

    def test_manager_assignment_allows_only_one_active_pair(self):
        ManagerAssignment.objects.create(
            manager=self.manager,
            employee=self.employee,
        )

        with self.assertRaises(IntegrityError):
            ManagerAssignment.objects.create(
                manager=self.manager,
                employee=self.employee,
            )

    def test_inactive_assignment_can_be_recreated(self):
        ManagerAssignment.objects.create(
            manager=self.manager,
            employee=self.employee,
            is_active=False,
        )

        assignment = ManagerAssignment.objects.create(
            manager=self.manager,
            employee=self.employee,
        )

        self.assertTrue(assignment.is_active)

    def test_seeded_uw_end_term_template_is_finalized(self):
        self.assertEqual(self.template.name, "UW Co-op Employer End-of-Term Evaluation")
        self.assertTrue(self.template.is_active)
        self.assertTrue(self.template.is_finalized)
        self.assertIn("sections", self.template.schema)

    def test_seeded_mid_term_template_is_finalized(self):
        self.assertEqual(
            self.mid_term_template.name,
            "UW Co-op Employer Mid-term Review",
        )
        self.assertTrue(self.mid_term_template.is_active)
        self.assertTrue(self.mid_term_template.is_finalized)
        self.assertIn("sections", self.mid_term_template.schema)

    def test_template_schema_must_be_valid_json_form_schema(self):
        template = EvaluationTemplate(
            name="Invalid",
            slug="invalid",
            version=1,
            schema={"sections": []},
        )

        with self.assertRaises(ValidationError):
            template.save()

    def test_new_valid_template_can_be_created_without_code_definition(self):
        template = EvaluationTemplate.objects.create(
            name="Custom Template",
            slug="custom-template",
            version=1,
            is_active=True,
            is_finalized=True,
            schema=self.minimal_template_schema(),
        )

        self.assertEqual(template.schema["sections"][0]["questions"][0]["id"], "q_minimal")

    def test_finalized_template_allows_only_active_flag_changes(self):
        self.template.is_active = False
        self.template.save()
        self.template.refresh_from_db()
        self.assertFalse(self.template.is_active)

        self.template.name = "Changed"
        with self.assertRaises(ValidationError):
            self.template.save()

    def test_finalized_template_can_be_cloned_as_draft(self):
        clone = self.template.clone_as_draft()

        self.assertEqual(clone.slug, self.template.slug)
        self.assertEqual(clone.version, self.template.version + 1)
        self.assertFalse(clone.is_active)
        self.assertFalse(clone.is_finalized)
        self.assertEqual(clone.schema, self.template.schema)

    def test_evaluation_defaults_to_draft(self):
        evaluation = self.create_evaluation(
            manager=self.manager,
            employee=self.employee,
        )

        self.assertEqual(evaluation.state, Evaluation.State.DRAFT)
        self.assertEqual(evaluation.template, self.template)
        self.assertTrue(evaluation.is_editable)
        self.assertEqual(evaluation.form_data, {})

    def test_evaluation_metadata_helpers_update_state(self):
        evaluation = self.create_evaluation(
            manager=self.manager,
            employee=self.employee,
        )

        evaluation.mark_submitted()
        self.assertEqual(evaluation.state, Evaluation.State.IN_REVIEW)
        self.assertIsNotNone(evaluation.submitted_at)

        evaluation.mark_approved(self.reviewer)
        self.assertEqual(evaluation.state, Evaluation.State.APPROVED)
        self.assertEqual(evaluation.approved_by, self.reviewer)
        self.assertIsNotNone(evaluation.approved_at)

        evaluation.mark_returned(self.reviewer)
        self.assertEqual(evaluation.state, Evaluation.State.DRAFT)
        self.assertEqual(evaluation.returned_by, self.reviewer)
        self.assertIsNotNone(evaluation.returned_at)
