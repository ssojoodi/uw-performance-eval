from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import Employee, Evaluation, ManagerAssignment


class BaseAppTests(TestCase):
    def test_health_check_is_public(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_dashboard_renders_for_authenticated_user(self):
        user = get_user_model().objects.create_user(
            username="manager@example.com",
            email="manager@example.com",
            password="password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)

    def test_dashboard_lists_only_active_assignments_for_user(self):
        manager = get_user_model().objects.create_user(username="manager")
        other_manager = get_user_model().objects.create_user(username="other")
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

    def test_start_evaluation_creates_draft_for_assigned_employee(self):
        manager = get_user_model().objects.create_user(username="manager")
        employee = Employee.objects.create(name="Assigned Employee")
        ManagerAssignment.objects.create(manager=manager, employee=employee)
        self.client.force_login(manager)

        response = self.client.post(
            reverse("start_evaluation", args=[employee.id])
        )

        self.assertRedirects(response, reverse("dashboard"))
        evaluation = Evaluation.objects.get()
        self.assertEqual(evaluation.manager, manager)
        self.assertEqual(evaluation.employee, employee)
        self.assertEqual(evaluation.state, Evaluation.State.DRAFT)

    def test_start_evaluation_rejects_unassigned_employee(self):
        manager = get_user_model().objects.create_user(username="manager")
        employee = Employee.objects.create(name="Unassigned Employee")
        self.client.force_login(manager)

        response = self.client.post(
            reverse("start_evaluation", args=[employee.id])
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(Evaluation.objects.exists())


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
