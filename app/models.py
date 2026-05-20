from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Employee(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    student_id = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "email", "id"]

    def __str__(self):
        return self.name


class ManagerAssignment(models.Model):
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="employee_assignments",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="manager_assignments",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee__name", "manager__username", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["manager", "employee"],
                condition=Q(is_active=True),
                name="unique_active_manager_employee_assignment",
            )
        ]

    def __str__(self):
        return f"{self.manager} -> {self.employee}"


class Evaluation(models.Model):
    class State(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_REVIEW = "in_review", "In Review"
        APPROVED = "approved", "Approved"

    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evaluations",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="evaluations",
    )
    state = models.CharField(
        max_length=32,
        choices=State.choices,
        default=State.DRAFT,
    )
    form_data = models.JSONField(default=dict, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_evaluations",
    )
    returned_at = models.DateTimeField(null=True, blank=True)
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="returned_evaluations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at", "id"]

    def __str__(self):
        return f"{self.employee} evaluation by {self.manager}"

    @property
    def is_editable(self):
        return self.state == self.State.DRAFT

    def mark_submitted(self):
        self.state = self.State.IN_REVIEW
        self.submitted_at = timezone.now()

    def mark_approved(self, reviewer):
        self.state = self.State.APPROVED
        self.approved_by = reviewer
        self.approved_at = timezone.now()

    def mark_returned(self, reviewer):
        self.state = self.State.DRAFT
        self.returned_by = reviewer
        self.returned_at = timezone.now()
