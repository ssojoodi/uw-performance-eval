from django.contrib import admin

from .models import Employee, Evaluation, ManagerAssignment


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "student_id", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "email", "student_id")


@admin.register(ManagerAssignment)
class ManagerAssignmentAdmin(admin.ModelAdmin):
    list_display = ("manager", "employee", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = (
        "manager__username",
        "manager__email",
        "employee__name",
        "employee__email",
    )


@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ("employee", "manager", "state", "updated_at")
    list_filter = ("state",)
    search_fields = (
        "manager__username",
        "manager__email",
        "employee__name",
        "employee__email",
    )
