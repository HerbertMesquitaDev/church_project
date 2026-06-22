from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages

from .permissions import is_teacher


class TeacherRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not is_teacher(request.user):
            messages.error(request, 'Acesso restrito a professores.')
            return redirect('member_dashboard')
        return super().dispatch(request, *args, **kwargs)


class TeacherOrStaffMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not (is_teacher(request.user) or request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Acesso restrito.')
            return redirect('member_dashboard')
        return super().dispatch(request, *args, **kwargs)
