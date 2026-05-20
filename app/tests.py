from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Employee, Evaluation, ManagerAssignment
from .roles import ROLE_MANAGER, ROLE_VP


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

    def test_start_evaluation_creates_draft_and_opens_form(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        ManagerAssignment.objects.create(manager=manager, employee=employee)
        self.client.force_login(manager)

        response = self.client.post(
            reverse("start_evaluation", args=[employee.id])
        )

        evaluation = Evaluation.objects.get()
        self.assertRedirects(
            response,
            reverse("edit_evaluation", args=[evaluation.id]),
        )
        self.assertEqual(evaluation.manager, manager)
        self.assertEqual(evaluation.employee, employee)
        self.assertEqual(evaluation.state, Evaluation.State.DRAFT)

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
        evaluation = Evaluation.objects.create(
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
        evaluation = Evaluation.objects.create(
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
        evaluation = Evaluation.objects.create(
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

    def test_submit_for_review_requires_required_end_term_fields(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = Evaluation.objects.create(
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
        evaluation = Evaluation.objects.create(
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
        evaluation = Evaluation.objects.create(
            manager=other_manager,
            employee=employee,
        )
        self.client.force_login(manager)

        response = self.client.get(reverse("edit_evaluation", args=[evaluation.id]))

        self.assertEqual(response.status_code, 404)

    def test_edit_evaluation_rejects_non_draft(self):
        manager = self.create_manager()
        employee = Employee.objects.create(name="Assigned Employee")
        evaluation = Evaluation.objects.create(
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

    def test_evaluation_defaults_to_draft(self):
        evaluation = Evaluation.objects.create(
            manager=self.manager,
            employee=self.employee,
        )

        self.assertEqual(evaluation.state, Evaluation.State.DRAFT)
        self.assertTrue(evaluation.is_editable)
        self.assertEqual(evaluation.form_data, {})

    def test_evaluation_metadata_helpers_update_state(self):
        evaluation = Evaluation.objects.create(
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
