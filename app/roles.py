from functools import wraps

from django.core.exceptions import PermissionDenied


ROLE_VP = "VP"
ROLE_MANAGER = "Manager"
ROLE_EMPLOYEE = "Employee"
BUSINESS_ROLE_GROUPS = (ROLE_VP, ROLE_MANAGER, ROLE_EMPLOYEE)


def is_manager(user):
    return (
        user.is_authenticated
        and user.is_active
        and user.groups.filter(name=ROLE_MANAGER).exists()
    )


def is_vp(user):
    return (
        user.is_authenticated
        and user.is_active
        and user.groups.filter(name=ROLE_VP).exists()
    )


def manager_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not is_manager(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped


def vp_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not is_vp(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped
