from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from app import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("health/", views.health, name="health"),
    path(
        "employees/<int:employee_id>/evaluations/start/",
        views.start_evaluation,
        name="start_evaluation",
    ),
    path(
        "evaluations/<int:evaluation_id>/edit/",
        views.edit_evaluation,
        name="edit_evaluation",
    ),
    path("", views.dashboard, name="dashboard"),
]
