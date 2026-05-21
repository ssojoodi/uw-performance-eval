from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import EvaluationForm
from .models import Evaluation, EvaluationTemplate, ManagerAssignment
from .roles import is_manager, is_vp, manager_required, vp_required


PAGE_SIZE = 10


def health(request):
    return JsonResponse({"status": "ok"})


def paginate(request, queryset):
    return Paginator(queryset, PAGE_SIZE).get_page(request.GET.get("page"))


@login_required
def dashboard(request):
    if is_vp(request.user):
        evaluations = Evaluation.objects.filter(
            state__in=[Evaluation.State.IN_REVIEW, Evaluation.State.APPROVED]
        ).select_related("employee", "manager", "template")
        return render(
            request,
            "app/vp_dashboard.html",
            {
                "empty_message": "No evaluations are waiting for review or finalized.",
                "is_vp_list": True,
                "page_obj": paginate(request, evaluations),
            },
        )

    if not is_manager(request.user):
        return render(request, "app/no_role.html", status=403)

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
        todo_items.append(
            {
                "employee": assignment.employee,
            }
        )

    evaluations = Evaluation.objects.filter(manager=request.user).select_related(
        "employee", "template"
    )
    return render(
        request,
        "app/dashboard.html",
        {
            "empty_message": "No evaluations yet.",
            "is_vp_list": False,
            "todo_items": todo_items,
            "page_obj": paginate(request, evaluations),
        },
    )


@login_required
@manager_required
def start_evaluation(request, employee_id):
    assignment = get_object_or_404(
        ManagerAssignment.objects.select_related("employee"),
        manager=request.user,
        employee_id=employee_id,
        employee__is_active=True,
        is_active=True,
    )

    templates = EvaluationTemplate.objects.filter(
        is_active=True,
        is_finalized=True,
    )

    if request.method == "POST":
        template = get_object_or_404(templates, id=request.POST.get("template"))
        evaluation = Evaluation.objects.create(
            manager=request.user,
            employee=assignment.employee,
            template=template,
        )
        return redirect("edit_evaluation", evaluation_id=evaluation.id)

    return render(
        request,
        "app/template_select.html",
        {
            "employee": assignment.employee,
            "templates": templates,
        },
    )


@login_required
@manager_required
def edit_evaluation(request, evaluation_id):
    evaluation = get_object_or_404(
        Evaluation.objects.select_related("employee", "manager", "template"),
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


@login_required
@manager_required
def preview_evaluation(request, evaluation_id):
    evaluation = get_object_or_404(
        Evaluation.objects.select_related("employee", "manager", "template"),
        id=evaluation_id,
        manager=request.user,
        state__in=[Evaluation.State.IN_REVIEW, Evaluation.State.APPROVED],
    )
    form = EvaluationForm(evaluation=evaluation, read_only=True)

    return render(
        request,
        "app/evaluation_preview.html",
        {
            "evaluation": evaluation,
            "form": form,
        },
    )


@login_required
@manager_required
def unlock_evaluation(request, evaluation_id):
    if request.method != "POST":
        return redirect("dashboard")

    evaluation = get_object_or_404(
        Evaluation,
        id=evaluation_id,
        manager=request.user,
        state=Evaluation.State.IN_REVIEW,
    )
    evaluation.mark_unlocked()
    evaluation.save()

    return redirect("edit_evaluation", evaluation_id=evaluation.id)


@login_required
@vp_required
def vp_preview_evaluation(request, evaluation_id):
    evaluation = get_object_or_404(
        Evaluation.objects.select_related("employee", "manager", "template"),
        id=evaluation_id,
        state__in=[Evaluation.State.IN_REVIEW, Evaluation.State.APPROVED],
    )
    form = EvaluationForm(evaluation=evaluation, read_only=True)

    return render(
        request,
        "app/evaluation_preview.html",
        {
            "evaluation": evaluation,
            "form": form,
            "is_vp_review": True,
        },
    )


@login_required
@vp_required
def approve_evaluation(request, evaluation_id):
    if request.method != "POST":
        return redirect("dashboard")

    evaluation = get_object_or_404(
        Evaluation,
        id=evaluation_id,
        state=Evaluation.State.IN_REVIEW,
    )
    evaluation.mark_approved(request.user)
    evaluation.save()

    return redirect("dashboard")


@login_required
@vp_required
def return_evaluation(request, evaluation_id):
    if request.method != "POST":
        return redirect("dashboard")

    evaluation = get_object_or_404(
        Evaluation,
        id=evaluation_id,
        state=Evaluation.State.IN_REVIEW,
    )
    evaluation.mark_returned(request.user)
    evaluation.save()

    return redirect("dashboard")
