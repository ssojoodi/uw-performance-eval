from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render


def health(request):
    return JsonResponse({"status": "ok"})


@login_required
def dashboard(request):
    return render(request, "app/dashboard.html")
