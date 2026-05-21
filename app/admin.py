from django.contrib import admin

from .models import Employee, Evaluation, EvaluationTemplate, ManagerAssignment


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
    list_display = ("employee", "manager", "template", "state", "updated_at")
    list_filter = ("state", "template")
    search_fields = (
        "manager__username",
        "manager__email",
        "employee__name",
        "employee__email",
        "template__name",
    )


@admin.register(EvaluationTemplate)
class EvaluationTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "version", "is_active", "is_finalized", "updated_at")
    list_filter = ("is_active", "is_finalized")
    search_fields = ("name", "slug", "description")
    actions = ("clone_as_draft",)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ["created_at", "updated_at"]
        if obj and obj.is_finalized:
            readonly_fields.extend(
                [
                    "name",
                    "slug",
                    "description",
                    "version",
                    "is_finalized",
                    "schema",
                ]
            )
        return readonly_fields

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_finalized:
            return False
        return super().has_delete_permission(request, obj)

    def delete_queryset(self, request, queryset):
        queryset.filter(is_finalized=False).delete()

    @admin.action(description="Clone selected templates as editable drafts")
    def clone_as_draft(self, request, queryset):
        created_count = 0
        for template in queryset:
            template.clone_as_draft()
            created_count += 1
        self.message_user(request, f"Created {created_count} draft template clone(s).")
