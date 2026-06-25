from django.shortcuts import redirect
from django.contrib import messages


def is_teacher(user):
    profile = getattr(user, 'profile', None)
    return bool(user.is_authenticated and profile and profile.approved and profile.role == 'teacher')


def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('member_login')
        if not is_teacher(request.user):
            messages.error(request, 'Acesso restrito a professores.')
            return redirect('member_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def teacher_or_staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('member_login')
        if not (is_teacher(request.user) or request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Acesso restrito.')
            return redirect('member_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
