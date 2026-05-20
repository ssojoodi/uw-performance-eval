from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EvaluationForm
from .models import Evaluation, ManagerAssignment


def health(request):
    return JsonResponse({"status": "ok"})


@login_required
def dashboard(request):
    assignments = (
        ManagerAssignment.objects.filter(
            manager=request.user,
            is_active=True,
            employee__is_active=True,
        )
        .select_related("employee")
        .prefetch_related("employee__evaluations")
    )
    todo_items = []

    for assignment in assignments:
        latest_evaluation = assignment.employee.evaluations.filter(
            manager=request.user
        ).first()
        todo_items.append(
            {
                "employee": assignment.employee,
                "latest_evaluation": latest_evaluation,
            }
        )

    return render(request, "app/dashboard.html", {"todo_items": todo_items})


@login_required
def start_evaluation(request, employee_id):
    if request.method != "POST":
        return redirect("dashboard")

    assignment = get_object_or_404(
        ManagerAssignment.objects.select_related("employee"),
        manager=request.user,
        employee_id=employee_id,
        employee__is_active=True,
        is_active=True,
    )
    evaluation = Evaluation.objects.create(
        manager=request.user,
        employee=assignment.employee,
    )

    return redirect("edit_evaluation", evaluation_id=evaluation.id)


@login_required
def edit_evaluation(request, evaluation_id):
    evaluation = get_object_or_404(
        Evaluation.objects.select_related("employee", "manager"),
        id=evaluation_id,
        manager=request.user,
        state=Evaluation.State.DRAFT,
    )

    if request.method == "POST":
        action = request.POST.get("action")
        form = EvaluationForm(
            request.POST,
            evaluation=evaluation,
            require_complete=action == "submit_for_review",
        )
        if form.is_valid():
            form.save()
            if action == "submit_for_review":
                evaluation.mark_submitted()
                evaluation.save()
                return redirect("dashboard")
            return redirect("edit_evaluation", evaluation_id=evaluation.id)
    else:
        form = EvaluationForm(evaluation=evaluation)

    return render(
        request,
        "app/evaluation_form.html",
        {
            "evaluation": evaluation,
            "form": form,
        },
    )
