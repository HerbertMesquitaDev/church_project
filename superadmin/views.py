from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone

from tenants.models import Igreja
from members.models import MemberProfile


def superadmin_only(view_func):
    """Decorator — apenas superusuários Django."""
    @login_required(login_url='/membros/login/')
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Acesso restrito.')
            return redirect('member_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def _online_count():
    try:
        from django_redis import get_redis_connection
        r   = get_redis_connection('default')
        now = int(timezone.now().timestamp())
        r.zremrangebyscore('online_visitors', 0, now - 300)
        return r.zcard('online_visitors')
    except Exception:
        return 0


def _visit_stats():
    from core.models import SiteVisit
    today    = timezone.localdate()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    base = SiteVisit.objects
    return {
        'today':       base.filter(visited_at__date=today).count(),
        'week':        base.filter(visited_at__date__gte=week_ago).count(),
        'top_regions': (
            base.filter(visited_at__date__gte=month_ago)
                .exclude(region='').exclude(region='Local')
                .values('region')
                .annotate(total=Count('id'))
                .order_by('-total')[:6]
        ),
    }


@superadmin_only
def dashboard(request):
    igrejas       = Igreja.objects.annotate(total_membros=Count('members'))
    total_igrejas = igrejas.count()
    total_ativas  = igrejas.filter(ativo=True).count()
    total_membros = MemberProfile.objects.count()

    from courses.models import PerfectStudentSeal
    visit_stats = _visit_stats()

    context = {
        'igrejas':        igrejas.order_by('-criado_em')[:5],
        'total_igrejas':  total_igrejas,
        'total_ativas':   total_ativas,
        'total_inativas': total_igrejas - total_ativas,
        'total_membros':  total_membros,
        # stats de visitas
        'online_count':   _online_count(),
        'visits_today':   visit_stats['today'],
        'visits_week':    visit_stats['week'],
        'top_regions':    visit_stats['top_regions'],
        'max_region':     visit_stats['top_regions'][0]['total'] if visit_stats['top_regions'] else 1,
        # selos
        'total_seals':    PerfectStudentSeal.objects.count(),
    }
    return render(request, 'superadmin/dashboard.html', context)


@superadmin_only
def igreja_list(request):
    q       = request.GET.get('q', '')
    plano   = request.GET.get('plano', '')
    status  = request.GET.get('status', '')

    igrejas = Igreja.objects.annotate(total_membros=Count('members'))

    if q:
        igrejas = igrejas.filter(nome__icontains=q)
    if plano:
        igrejas = igrejas.filter(plano=plano)
    if status == 'ativa':
        igrejas = igrejas.filter(ativo=True)
    elif status == 'inativa':
        igrejas = igrejas.filter(ativo=False)

    return render(request, 'superadmin/igreja_list.html', {
        'igrejas': igrejas.order_by('-criado_em'),
        'q': q, 'plano': plano, 'status': status,
    })


@superadmin_only
def igreja_create(request):
    if request.method == 'POST':
        igreja = Igreja()
        igreja.nome            = request.POST.get('nome', '').strip()
        igreja.slug            = request.POST.get('slug', '').strip()
        igreja.dominio_proprio = request.POST.get('dominio_proprio', '').strip()
        igreja.plano           = request.POST.get('plano', 'trial')
        igreja.trial_ate       = request.POST.get('trial_ate') or None
        igreja.ativo           = 'ativo' in request.POST
        igreja.save()
        messages.success(request, f'Igreja "{igreja.nome}" criada com sucesso!')
        return redirect('sa_igreja_detail', pk=igreja.pk)

    return render(request, 'superadmin/igreja_form.html', {
        'title': 'Nova Igreja',
        'igreja': None,
    })


@superadmin_only
def igreja_detail(request, pk):
    igreja  = get_object_or_404(Igreja, pk=pk)
    membros = MemberProfile.objects.filter(igreja=igreja).select_related('user')

    return render(request, 'superadmin/igreja_detail.html', {
        'igreja':  igreja,
        'membros': membros,
        'total_membros': membros.count(),
        'admins': membros.filter(role='admin'),
    })


@superadmin_only
def igreja_edit(request, pk):
    igreja = get_object_or_404(Igreja, pk=pk)

    if request.method == 'POST':
        igreja.nome            = request.POST.get('nome', '').strip()
        igreja.slug            = request.POST.get('slug', '').strip()
        igreja.dominio_proprio = request.POST.get('dominio_proprio', '').strip()
        igreja.plano           = request.POST.get('plano', 'trial')
        igreja.trial_ate       = request.POST.get('trial_ate') or None
        igreja.ativo           = 'ativo' in request.POST
        igreja.save()
        messages.success(request, 'Igreja atualizada com sucesso!')
        return redirect('sa_igreja_detail', pk=igreja.pk)

    return render(request, 'superadmin/igreja_form.html', {
        'title': f'Editar — {igreja.nome}',
        'igreja': igreja,
    })


@superadmin_only
def igreja_toggle(request, pk):
    """Ativa ou desativa uma igreja rapidamente."""
    igreja = get_object_or_404(Igreja, pk=pk)
    igreja.ativo = not igreja.ativo
    igreja.save()
    status = 'ativada' if igreja.ativo else 'desativada'
    messages.success(request, f'Igreja "{igreja.nome}" {status}!')
    return redirect('sa_igreja_list')