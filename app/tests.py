from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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

