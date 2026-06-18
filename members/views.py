from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models as db_models
from django.core.paginator import Paginator
from django.contrib.auth.models import User

from core.models import Ministry, Devotional, Offering, Visitor, SiteSettings
from .models import MemberProfile, ExclusiveContent, ContentCategory, Notice, MemberMinistry, Testimony, PrayerRequest, DeleteRequest, PasswordResetToken
from .emails import (
    send_password_reset, send_member_approved, send_member_rejected,
    notify_admin_new_member, notify_admin_new_prayer,
    notify_admin_new_testimony, notify_admin_delete_request,
    notify_collaborator_delete_reviewed,
)
from .forms import (RegisterForm, ProfileForm, MemberMinistryFormSet,
                    EventForm, ContentForm, NoticeForm, TestimonyForm, PrayerRequestForm,
                    OfferingForm, MinistryForm)
from events.models import Event, Category as EventCategory

PER_PAGE = 12


# ── Permission helpers ────────────────────────────────────
def get_or_create_profile(user):
    profile, _ = MemberProfile.objects.get_or_create(user=user)
    return profile

def timeout(request):
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    return redirect('member_login')


# ── Helpers de grupo ────────────────────────────────────
def is_admin(user):
    return user.is_authenticated and (user.is_superuser or
           getattr(getattr(user, 'profile', None), 'role', '') == 'admin')

def is_collaborator(user):
    return user.is_authenticated and (user.is_staff or is_admin(user))

def members_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('member_login')
        if is_collaborator(request.user):
            return view_func(request, *args, **kwargs)
        profile = get_or_create_profile(request.user)
        if not profile.approved:
            return render(request, 'members/pending.html')
        return view_func(request, *args, **kwargs)
    return wrapper

def staff_only(view_func):
    """Colaborador ou Admin: pode acessar o painel, criar e editar."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('member_login')
        if not is_collaborator(request.user):
            messages.error(request, 'Acesso restrito a colaboradores.')
            return redirect('member_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_only(view_func):
    """Somente Admin: exclusões, aprovações, gerenciamento de grupos."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('member_login')
        if not is_admin(request.user):
            messages.error(request, 'Acesso restrito ao administrador.')
            return redirect('member_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper

def superuser_only(view_func):
    """Compatibilidade — redireciona para admin_only."""
    return admin_only(view_func)


# ── Auth ──────────────────────────────────────────────────
def member_login(request):
    if request.user.is_authenticated:
        return redirect('member_dashboard')
    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password   = request.POST.get('password', '')
        # Tenta autenticar: EmailBackend tenta e-mail primeiro, depois username
        user = authenticate(request, username=identifier, password=password)
        if user:
            login(request, user)
            return redirect(request.GET.get('next', 'member_dashboard'))
        messages.error(request, 'E-mail/usuário ou senha incorretos.')
    return render(request, 'members/login.html')

def member_logout(request):
    logout(request)
    return redirect('home')

def member_register(request):
    if request.user.is_authenticated:
        return redirect('member_dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        # Captura dados de consentimento LGPD
        gave_consent = form.cleaned_data.get('image_consent', False)
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()

        from django.utils import timezone
        MemberProfile.objects.create(
            user=user,
            image_consent=gave_consent,
            image_consent_date=timezone.now() if gave_consent else None,
            image_consent_ip=ip if gave_consent else None,
        )
        messages.success(request, 'Cadastro realizado! Aguarde a aprovação da liderança.')
        # Notifica admins sobre novo cadastro
        try:
            profile = get_or_create_profile(user)
            notify_admin_new_member(profile)
        except Exception:
            pass
        return redirect('member_login')
    return render(request, 'members/register.html', {'form': form})


# ── Dashboard ─────────────────────────────────────────────
@members_only
def member_dashboard(request):
    profile         = get_or_create_profile(request.user)
    upcoming_events = Event.objects.filter(
        date__gte=timezone.now(), published=True).order_by('date')[:4]
    notices = Notice.objects.filter(published=True).filter(
        db_models.Q(expires_at__isnull=True) | db_models.Q(expires_at__gte=timezone.now())
    )[:5]

    from django.utils.timezone import localdate
    today      = localdate()
    devotional = Devotional.objects.filter(published=True, pub_date=today).first()
    if not devotional:
        devotional = Devotional.objects.filter(published=True).first()

    context = {'profile': profile, 'upcoming_events': upcoming_events, 'notices': notices, 'devotional': devotional}

    if request.user.is_staff or request.user.is_superuser:
        from datetime import date
        today = date.today()
        birthday_members = MemberProfile.objects.filter(
            approved=True,
            birth_date__month=today.month,
        ).select_related('user').order_by('birth_date__day')[:5]

        from django.utils.timezone import now as tz_now
        from datetime import timedelta
        thirty_days_ago = tz_now() - timedelta(days=30)
        new_members = MemberProfile.objects.filter(
            approved=True,
            created_at__gte=thirty_days_ago,
        ).select_related('user').order_by('-created_at')[:5]

        from django.db.models import Sum
        import json as _json
        from datetime import date as _date
        _now = timezone.now()
        _monthly = []
        for i in range(5, -1, -1):
            # Calcula mês sem dateutil
            _total_months = _now.month - 1 - i
            _year  = _now.year + _total_months // 12
            _month = _total_months % 12 + 1
            ref = _date(_year, _month, 1)
            amt = Offering.objects.filter(
                date__year=ref.year, date__month=ref.month
            ).aggregate(t=Sum('amount'))['t'] or 0
            _monthly.append({'label': ref.strftime('%b/%y'), 'value': float(amt)})
        total_month_offering = Offering.objects.filter(
            date__year=_now.year, date__month=_now.month
        ).aggregate(t=Sum('amount'))['t'] or 0

        from core.models import MediaItem, Visitor
        from members.models import Culto, Presenca

        # ── Gráfico 1: Novos membros por mês (últimos 6 meses) ──
        _members_monthly = []
        for i in range(5, -1, -1):
            _tm = _now.month - 1 - i
            _y  = _now.year + _tm // 12
            _m  = _tm % 12 + 1
            ref = _date(_y, _m, 1)
            cnt = MemberProfile.objects.filter(
                approved=True,
                created_at__year=ref.year,
                created_at__month=ref.month
            ).count()
            _members_monthly.append({'label': ref.strftime('%b/%y'), 'value': cnt})

        # ── Gráfico 2: Frequência média por mês (últimos 6 meses) ──
        _freq_monthly = []
        for i in range(5, -1, -1):
            _tm = _now.month - 1 - i
            _y  = _now.year + _tm // 12
            _m  = _tm % 12 + 1
            ref = _date(_y, _m, 1)
            cultos_mes = Culto.objects.filter(
                date__year=ref.year, date__month=ref.month
            )
            if cultos_mes.exists():
                total_pres  = Presenca.objects.filter(culto__in=cultos_mes, present=True).count()
                total_slots = Presenca.objects.filter(culto__in=cultos_mes).count()
                freq = round(total_pres / total_slots * 100) if total_slots else 0
            else:
                freq = 0
            _freq_monthly.append({'label': ref.strftime('%b/%y'), 'value': freq})

        # ── Gráfico 3: Visitantes por mês (últimos 6 meses) ──
        _visitors_monthly = []
        for i in range(5, -1, -1):
            _tm = _now.month - 1 - i
            _y  = _now.year + _tm // 12
            _m  = _tm % 12 + 1
            ref = _date(_y, _m, 1)
            # Visitantes registrados nos cultos
            vis_cultos = Culto.objects.filter(
                date__year=ref.year, date__month=ref.month
            ).aggregate(t=db_models.Sum('visitor_count'))['t'] or 0
            # Visitantes do formulário do site
            vis_form = Visitor.objects.filter(
                created_at__year=ref.year, created_at__month=ref.month
            ).count()
            _visitors_monthly.append({'label': ref.strftime('%b/%y'), 'value': vis_cultos + vis_form})

        # Stats de crescimento (comparação mês atual vs anterior)
        _cur_m  = _date(_now.year, _now.month, 1)
        if _now.month == 1:
            _prev_m = _date(_now.year - 1, 12, 1)
        else:
            _prev_m = _date(_now.year, _now.month - 1, 1)

        members_cur  = MemberProfile.objects.filter(approved=True, created_at__year=_cur_m.year, created_at__month=_cur_m.month).count()
        members_prev = MemberProfile.objects.filter(approved=True, created_at__year=_prev_m.year, created_at__month=_prev_m.month).count()
        members_growth = members_cur - members_prev

        offer_prev = Offering.objects.filter(date__year=_prev_m.year, date__month=_prev_m.month).aggregate(t=db_models.Sum('amount'))['t'] or 0
        offer_growth_pct = round((float(total_month_offering) - float(offer_prev)) / float(offer_prev) * 100) if offer_prev else 0

        context.update({
            'featured_content':    ExclusiveContent.objects.filter(published=True, featured=True)[:3],
            'total_media':         MediaItem.objects.filter(published=True).count(),
            'recent_media':        MediaItem.objects.select_related('category').order_by('-created_at')[:6],
            'total_visitors':      Visitor.objects.count(),
            'pending_visitors':    Visitor.objects.filter(contacted=False).count(),
            'offering_monthly_json':  _json.dumps(_monthly),
            'members_monthly_json':   _json.dumps(_members_monthly),
            'freq_monthly_json':      _json.dumps(_freq_monthly),
            'visitors_monthly_json':  _json.dumps(_visitors_monthly),
            'total_month_offering':   total_month_offering,
            'members_growth':         members_growth,
            'offer_growth_pct':       offer_growth_pct,
            'total_cultos':           Culto.objects.count(),
            'pending_members':     MemberProfile.objects.filter(approved=False).count(),
            'total_members':       MemberProfile.objects.filter(approved=True).count(),
            'total_contents':      ExclusiveContent.objects.filter(published=True).count(),
            'total_events':        Event.objects.filter(date__gte=timezone.now(), published=True).count(),
            'pending_testimonies': Testimony.objects.filter(status='pending').count(),
            'pending_prayers':     PrayerRequest.objects.filter(status='open').count(),
            'birthday_members':    birthday_members,
            'new_members':         new_members,
            'pending_delete_requests': DeleteRequest.objects.filter(status='pending').count(),
        })

    # Contexto extra para colaboradores (não-admin)
    if is_collaborator(request.user) and not is_admin(request.user):
        my_requests = DeleteRequest.objects.filter(
            requested_by=request.user
        ).order_by('-created_at')[:5]
        context['my_delete_requests'] = my_requests

    return render(request, 'members/dashboard.html', context)


# ── Profile ───────────────────────────────────────────────
@members_only
def member_profile(request):
    profile = get_or_create_profile(request.user)
    form    = ProfileForm(request.POST or None, request.FILES or None,
                          instance=profile, user=request.user)
    formset    = MemberMinistryFormSet(request.POST or None, instance=profile)
    testimony_form = TestimonyForm()
    user_testimony = Testimony.objects.filter(profile=profile).order_by('-created_at').first()

    if request.method == 'POST':
        if 'save_profile' in request.POST:
            if form.is_valid() and formset.is_valid():
                form.save_user(request.user)
                form.save()
                formset.save()
                messages.success(request, 'Perfil atualizado com sucesso!')
                return redirect('member_profile')
        elif 'save_testimony' in request.POST:
            testimony_form = TestimonyForm(request.POST)
            if testimony_form.is_valid():
                t = testimony_form.save(commit=False)
                t.profile = profile
                t.status = 'pending'
                t.save()
                try:
                    notify_admin_new_testimony(t)
                except Exception:
                    pass
                messages.success(request, 'Seu testemunho foi enviado e aguarda aprovação da liderança.')
                return redirect('member_profile')

    return render(request, 'members/profile.html', {
        'form': form,
        'formset': formset,
        'profile': profile,
        'testimony_form': testimony_form,
        'user_testimony': user_testimony,
    })


# ── Testimonies management (staff) ───────────────────────
@staff_only
def testimony_manage(request):
    pending  = Testimony.objects.filter(status='pending').select_related('profile__user')
    approved = Testimony.objects.filter(status='approved').select_related('profile__user')
    rejected = Testimony.objects.filter(status='rejected').select_related('profile__user')
    return render(request, 'members/testimony_manage.html', {
        'pending': pending, 'approved': approved, 'rejected': rejected,
        'pending_count': pending.count(),
    })

@staff_only
def testimony_approve(request, pk):
    t = get_object_or_404(Testimony, pk=pk)
    t.status = 'approved'
    t.save()
    messages.success(request, f'Testemunho de {t.profile.full_name} aprovado!')
    return redirect('testimony_manage')

@staff_only
def testimony_reject(request, pk):
    t = get_object_or_404(Testimony, pk=pk)
    if request.method == 'POST':
        t.status = 'rejected'
        t.admin_note = request.POST.get('admin_note', '')
        t.save()
        messages.success(request, 'Testemunho rejeitado.')
    return redirect('testimony_manage')


# ── Contents ──────────────────────────────────────────────
@members_only
def content_list(request):
    category_id = request.GET.get('categoria')
    qs = ExclusiveContent.objects.all() if (
        request.user.is_staff or request.user.is_superuser
    ) else ExclusiveContent.objects.filter(published=True)
    if category_id:
        qs = qs.filter(category_id=category_id)
    page_obj = Paginator(qs, PER_PAGE).get_page(request.GET.get('page'))
    return render(request, 'members/content_list.html', {
        'page_obj':          page_obj,
        'contents':          page_obj,
        'categories':        ContentCategory.objects.all(),
        'selected_category': category_id,
    })

@members_only
def content_detail(request, pk):
    content = get_object_or_404(ExclusiveContent, pk=pk)
    if not content.published and not (request.user.is_staff or request.user.is_superuser):
        return redirect('content_list')
    return render(request, 'members/content_detail.html', {'content': content})

@staff_only
def content_create(request):
    form = ContentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        c = form.save(commit=False)
        c.author = request.user
        c.save()
        messages.success(request, 'Conteúdo criado!')
        return redirect('content_list')
    return render(request, 'members/content_form.html', {'form': form, 'title': 'Novo Conteúdo'})

@staff_only
def content_edit(request, pk):
    content = get_object_or_404(ExclusiveContent, pk=pk)
    form    = ContentForm(request.POST or None, request.FILES or None, instance=content)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Conteúdo atualizado!')
        return redirect('content_list')
    return render(request, 'members/content_form.html',
                  {'form': form, 'title': 'Editar Conteúdo', 'content': content})

@admin_only
def content_delete(request, pk):
    content = get_object_or_404(ExclusiveContent, pk=pk)
    if request.method == 'POST':
        content.delete()
        messages.success(request, 'Conteúdo removido.')
        return redirect('content_list')
    return render(request, 'members/confirm_delete.html',
                  {'object': content, 'tipo': 'conteúdo'})


# ── Notices ───────────────────────────────────────────────
@staff_only
def notice_list(request):
    page_obj = Paginator(Notice.objects.all(), PER_PAGE).get_page(request.GET.get('page'))
    return render(request, 'members/notice_list.html',
                  {'page_obj': page_obj, 'notices': page_obj})

@staff_only
def notice_create(request):
    form = NoticeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Aviso criado!')
        return redirect('notice_list')
    return render(request, 'members/notice_form.html', {'form': form, 'title': 'Novo Aviso'})

@staff_only
def notice_edit(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    form   = NoticeForm(request.POST or None, instance=notice)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Aviso atualizado!')
        return redirect('notice_list')
    return render(request, 'members/notice_form.html',
                  {'form': form, 'title': 'Editar Aviso', 'notice': notice})

@admin_only
def notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == 'POST':
        notice.delete()
        messages.success(request, 'Aviso removido.')
        return redirect('notice_list')
    return render(request, 'members/confirm_delete.html',
                  {'object': notice, 'tipo': 'aviso'})


# ── Members management ────────────────────────────────────
@staff_only
def members_manage(request):
    pending  = MemberProfile.objects.filter(approved=False).select_related('user')

    # Filtros de busca e grupo
    q    = request.GET.get('q', '').strip()
    role = request.GET.get('role', '')
    qs   = MemberProfile.objects.filter(approved=True).select_related('user').prefetch_related('member_ministries__ministry')

    if q:
        from django.db.models import Q
        qs = qs.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q)  |
            Q(user__email__icontains=q)
        )
    if role:
        qs = qs.filter(role=role)

    qs = qs.order_by('user__first_name', 'user__last_name')
    approved = Paginator(qs, PER_PAGE).get_page(request.GET.get('page'))

    return render(request, 'members/members_manage.html', {
        'pending':  pending,
        'page_obj': approved,
        'approved': approved,
    })

@admin_only
def member_approve(request, pk):
    profile = get_object_or_404(MemberProfile, pk=pk)
    if request.method == 'POST':
        role = request.POST.get('role', 'member')
        profile.approved = True
        profile.role = role
        # Colaborador recebe is_staff; admin recebe is_staff + is_superuser
        if role == 'collaborator':
            profile.user.is_staff = True
            profile.user.is_superuser = False
        elif role == 'admin':
            profile.user.is_staff = True
            profile.user.is_superuser = True
        else:  # member
            profile.user.is_staff = False
            profile.user.is_superuser = False
        profile.user.save()
        profile.save()
        messages.success(request, f'{profile.full_name} aprovado(a) como {profile.get_role_display()}!')
        # E-mail de boas-vindas ao membro
        try:
            send_member_approved(profile.user, profile.get_role_display())
        except Exception:
            pass
    return redirect('members_manage')

@admin_only
def member_reject(request, pk):
    profile = get_object_or_404(MemberProfile, pk=pk)
    if request.method == 'POST':
        try:
            send_member_rejected(profile.user)
        except Exception:
            pass
        profile.user.delete()
        messages.success(request, 'Cadastro removido.')
    return redirect('members_manage')

@admin_only
def member_edit(request, pk):
    profile = get_object_or_404(MemberProfile, pk=pk)

    if request.method == 'POST':
        profile.user.first_name = request.POST.get('first_name', '').strip()
        profile.user.last_name  = request.POST.get('last_name', '').strip()
        profile.user.email      = request.POST.get('email', '').strip()
        profile.user.save()

        profile.phone    = request.POST.get('phone', '').strip()
        profile.baptized = 'baptized' in request.POST

        # Alterar role/grupo
        new_role = request.POST.get('role', profile.role)
        if new_role != profile.role:
            profile.role = new_role
            if new_role == 'collaborator':
                profile.user.is_staff = True
                profile.user.is_superuser = False
            elif new_role == 'admin':
                profile.user.is_staff = True
                profile.user.is_superuser = True
            else:
                profile.user.is_staff = False
                profile.user.is_superuser = False
            profile.user.save()

        birth_date_raw   = request.POST.get('birth_date', '').strip()
        member_since_raw = request.POST.get('member_since', '').strip()
        from datetime import date as _date
        try:
            profile.birth_date = _date.fromisoformat(birth_date_raw) if birth_date_raw else None
        except ValueError:
            profile.birth_date = None
        try:
            profile.member_since = _date.fromisoformat(member_since_raw) if member_since_raw else None
        except ValueError:
            profile.member_since = None

        profile.save()
        messages.success(request, 'Membro atualizado com sucesso!')
        return redirect('members_manage')

    return render(request, 'members/member_form.html', {
        'profile': profile,
        'role_choices': MemberProfile.ROLE_CHOICES,
    })


@admin_only
def member_delete(request, pk):
    profile = get_object_or_404(MemberProfile, pk=pk)

    if request.method == 'POST':
        profile.user.delete()  # já remove tudo junto
        messages.success(request, 'Membro excluído com sucesso!')
        return redirect('members_manage')

    return render(request, 'members/confirm_delete.html', {
        'object': profile,
        'tipo': 'membro'
    })

# ── Ministries ────────────────────────────────────────────
@staff_only
def ministry_manage(request):
    ministries = Ministry.objects.all().prefetch_related('members__profile__user')
    return render(request, 'members/ministry_manage.html', {'ministries': ministries})


# CRUD para Ministérios (painel)
@staff_only
def ministry_create(request):
    form = MinistryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ministério criado!')
        return redirect('ministry_manage')
    return render(request, 'members/ministry_form.html', {'form': form, 'title': 'Novo Ministério'})


@staff_only
def ministry_edit(request, pk):
    ministry = get_object_or_404(Ministry, pk=pk)
    form = MinistryForm(request.POST or None, instance=ministry)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ministério atualizado!')
        return redirect('ministry_manage')
    return render(request, 'members/ministry_form.html', {'form': form, 'title': 'Editar Ministério', 'ministry': ministry})


@admin_only
def ministry_delete(request, pk):
    ministry = get_object_or_404(Ministry, pk=pk)
    if request.method == 'POST':
        ministry.delete()
        messages.success(request, 'Ministério removido.')
        return redirect('ministry_manage')
    return render(request, 'members/confirm_delete.html', {'object': ministry, 'tipo': 'ministério'})


# ── Events (staff pode ver, superuser pode editar) ────────
@staff_only
def event_manage(request):
    from django.utils import timezone as tz
    q       = request.GET.get('q', '').strip()
    periodo = request.GET.get('periodo', 'upcoming')
    cat_id  = request.GET.get('categoria', '')

    qs = Event.objects.select_related('category').order_by('date')

    if q:
        qs = qs.filter(
            db_models.Q(title__icontains=q) |
            db_models.Q(location__icontains=q) |
            db_models.Q(description__icontains=q)
        )
    if cat_id:
        qs = qs.filter(category_id=cat_id)
    if periodo == 'past':
        qs = qs.filter(date__lt=tz.now()).order_by('-date')
    else:
        qs = qs.filter(date__gte=tz.now()).order_by('date')

    page_obj       = Paginator(qs, PER_PAGE).get_page(request.GET.get('page'))
    categories     = EventCategory.objects.all()
    total_upcoming = Event.objects.filter(date__gte=tz.now()).count()
    total_past     = Event.objects.filter(date__lt=tz.now()).count()
    total_all      = Event.objects.count()

    return render(request, 'members/event_manage.html', {
        'page_obj':       page_obj,
        'events':         page_obj,
        'categories':     categories,
        'q':              q,
        'periodo':        periodo,
        'cat_id':         cat_id,
        'total_upcoming': total_upcoming,
        'total_past':     total_past,
        'total_all':      total_all,
    })

@superuser_only
def event_create(request):
    form = EventForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Evento criado!')
        return redirect('event_manage')
    return render(request, 'members/event_form.html', {'form': form, 'title': 'Novo Evento'})

@superuser_only
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    form  = EventForm(request.POST or None, request.FILES or None, instance=event)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Evento atualizado!')
        return redirect('event_manage')
    return render(request, 'members/event_form.html',
                  {'form': form, 'title': 'Editar Evento', 'event': event})

@superuser_only
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Evento removido.')
        return redirect('event_manage')
    return render(request, 'members/confirm_delete.html',
                  {'object': event, 'tipo': 'evento'})

# ── Prayer Requests ───────────────────────────────────────
@members_only
def prayer_list(request):
    profile = get_or_create_profile(request.user)
    form    = PrayerRequestForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        pr = form.save(commit=False)
        pr.profile = profile
        pr.save()
        try:
            pr_obj = type('obj', (object,), {
                'user': request.user,
                'request': form.cleaned_data.get('request', '')
            })()
            notify_admin_new_prayer(pr_obj)
        except Exception:
            pass
        messages.success(request, 'Seu pedido de oração foi enviado!')
        return redirect('prayer_list')

    # Pedidos do próprio membro
    my_requests = PrayerRequest.objects.filter(profile=profile)

    # Pedidos de outros membros visíveis (apenas visibility=members)
    community_requests = PrayerRequest.objects.filter(
        visibility='members', status='open'
    ).exclude(profile=profile).select_related('profile__user')

    return render(request, 'members/prayer_list.html', {
        'form':                form,
        'my_requests':         my_requests,
        'community_requests':  community_requests,
    })

@members_only
def prayer_delete(request, pk):
    pr = get_object_or_404(PrayerRequest, pk=pk, profile__user=request.user)
    if request.method == 'POST':
        pr.delete()
        messages.success(request, 'Pedido removido.')
    return redirect('prayer_list')

@staff_only
def prayer_manage(request):
    open_private   = PrayerRequest.objects.filter(status='open', visibility='private').select_related('profile__user')
    open_members   = PrayerRequest.objects.filter(status='open', visibility='members').select_related('profile__user')
    answered       = PrayerRequest.objects.filter(status='answered').select_related('profile__user')
    return render(request, 'members/prayer_manage.html', {
        'open_private':  open_private,
        'open_members':  open_members,
        'answered':      answered,
        'pending_count': open_private.count() + open_members.count(),
    })

@staff_only
def prayer_respond(request, pk):
    pr = get_object_or_404(PrayerRequest, pk=pk)
    if request.method == 'POST':
        pr.status     = request.POST.get('status', pr.status)
        pr.admin_note = request.POST.get('admin_note', '')
        pr.save()
        messages.success(request, 'Pedido atualizado!')
    return redirect('prayer_manage')


# ── Offerings ─────────────────────────────────────────────
@members_only
def offering_list(request):
    profile = get_or_create_profile(request.user)
    form    = OfferingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        o = form.save(commit=False)
        o.profile = profile
        o.save()
        messages.success(request, 'Contribuição registrada com sucesso!')
        return redirect('offering_list')

    my_offerings = Offering.objects.filter(profile=profile)
    total        = sum(o.amount for o in my_offerings)

    # Totais por tipo
    from django.db.models import Sum
    by_type = my_offerings.values('type').annotate(total=Sum('amount')).order_by('-total')

    from core.models import SiteSettings
    return render(request, 'members/offering_list.html', {
        'form':          form,
        'my_offerings':  my_offerings[:20],
        'total':         total,
        'by_type':       by_type,
        'site_settings': SiteSettings.get_settings(),
    })

@staff_only
def offering_manage(request):
    from django.db.models import Sum, Count
    from django.utils.timezone import now
    import json

    # Totais gerais
    total_all   = Offering.objects.aggregate(t=Sum('amount'))['t'] or 0
    total_month = Offering.objects.filter(
        date__year=now().year, date__month=now().month
    ).aggregate(t=Sum('amount'))['t'] or 0

    # Por tipo
    by_type = Offering.objects.values('type').annotate(
        total=Sum('amount'), count=Count('id')
    ).order_by('-total')

    # Últimas 20 contribuições
    recent = Offering.objects.select_related('profile__user').order_by('-date', '-created_at')[:20]

    # Gráfico mensal — últimos 12 meses
    from datetime import date
    _n = now()
    monthly = []
    for i in range(11, -1, -1):
        _total_months = _n.month - 1 - i
        _year  = _n.year + _total_months // 12
        _month = _total_months % 12 + 1
        ref = date(_year, _month, 1)
        amt  = Offering.objects.filter(
            date__year=ref.year, date__month=ref.month
        ).aggregate(t=Sum('amount'))['t'] or 0
        monthly.append({'label': ref.strftime('%b/%y'), 'value': float(amt)})

    return render(request, 'members/offering_manage.html', {
        'total_all':   total_all,
        'total_month': total_month,
        'by_type':     by_type,
        'recent':      recent,
        'monthly_json': json.dumps(monthly),
    })


# ── Visitor management (staff) ────────────────────────────
@staff_only
def visitor_manage(request):
    from django.core.paginator import Paginator
    q         = request.GET.get('q', '').strip()
    contacted = request.GET.get('contacted', '')

    qs = Visitor.objects.all()
    if q:
        from django.db.models import Q as Qv
        qs = qs.filter(Qv(name__icontains=q) | Qv(phone__icontains=q) | Qv(email__icontains=q))
    if contacted == '0':
        qs = qs.filter(contacted=False)
    elif contacted == '1':
        qs = qs.filter(contacted=True)

    page_obj = Paginator(qs, 20).get_page(request.GET.get('page'))
    return render(request, 'members/visitor_manage.html', {
        'page_obj':  page_obj,
        'visitors':  page_obj,
        'q':         q,
        'contacted': contacted,
        'total_new': Visitor.objects.filter(contacted=False).count(),
    })

@staff_only
def visitor_contacted(request, pk):
    v = get_object_or_404(Visitor, pk=pk)
    v.contacted = not v.contacted
    v.save()
    return redirect(request.GET.get('next', 'visitor_manage'))


# ── Notification preferences ──────────────────────────────
@members_only
def notification_prefs(request):
    profile = get_or_create_profile(request.user)
    if request.method == 'POST':
        profile.notify_events     = 'notify_events'     in request.POST
        profile.notify_reminders  = 'notify_reminders'  in request.POST
        profile.notify_devotional = 'notify_devotional' in request.POST
        profile.notify_notices    = 'notify_notices'    in request.POST
        profile.save()
        messages.success(request, 'Preferências de notificação salvas!')
        return redirect('notification_prefs')
    return render(request, 'members/notification_prefs.html', {'profile': profile})


# ══════════════════════════════════════════════════════════
# ── Midiateca CRUD ────────────────────────────────────────
# ══════════════════════════════════════════════════════════
from core.models import MediaItem, MediaCategory, PhotoAlbum, Photo
from .forms import MediaItemForm, PhotoAlbumForm

@staff_only
def media_manage(request):
    from django.db.models import Q
    section = request.GET.get('secao', '')
    cat_id  = request.GET.get('categoria', '')
    tipo    = request.GET.get('tipo', '')
    pub     = request.GET.get('pub', '')
    q       = request.GET.get('q', '').strip()

    all_items = MediaItem.objects.select_related('category').order_by('-pub_date', '-created_at')

    # Stats globais (sem filtros)
    total_count     = all_items.count()
    published_count = all_items.filter(published=True).count()
    featured_count  = all_items.filter(featured=True).count()

    # Aplicar filtros
    qs = all_items
    if section:
        qs = qs.filter(category__section=section)
    if cat_id:
        qs = qs.filter(category_id=cat_id)
    if tipo:
        qs = qs.filter(media_type=tipo)
    if pub == '1':
        qs = qs.filter(published=True)
    elif pub == '0':
        qs = qs.filter(published=False)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(speaker__icontains=q))

    page_obj   = Paginator(qs, PER_PAGE).get_page(request.GET.get('page'))
    categories = MediaCategory.objects.all()
    sections   = MediaCategory.SECTION_CHOICES
    tipos      = MediaItem.TYPE_CHOICES

    return render(request, 'members/media_manage.html', {
        'page_obj':        page_obj,
        'items':           page_obj,
        'categories':      categories,
        'sections':        sections,
        'tipos':           tipos,
        'section':         section,
        'cat_id':          cat_id,
        'tipo':            tipo,
        'pub':             pub,
        'q':               q,
        'total_count':     total_count,
        'published_count': published_count,
        'featured_count':  featured_count,
    })


@staff_only
def media_create(request):
    form = MediaItemForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Item adicionado à midiateca!')
        return redirect('media_manage')
    return render(request, 'members/media_form.html', {
        'form': form, 'title': 'Novo Item de Mídia'
    })


@staff_only
def media_edit(request, pk):
    item = get_object_or_404(MediaItem, pk=pk)
    form = MediaItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Item atualizado!')
        return redirect('media_manage')
    return render(request, 'members/media_form.html', {
        'form': form, 'title': 'Editar Item de Mídia', 'item': item
    })


@admin_only
def media_delete(request, pk):
    item = get_object_or_404(MediaItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item removido.')
        return redirect('media_manage')
    return render(request, 'members/confirm_delete.html',
                  {'object': item, 'tipo': 'item de mídia'})


# ══════════════════════════════════════════════════════════
# ── Galeria de Fotos CRUD ─────────────────────────────────
# ══════════════════════════════════════════════════════════

@staff_only
def album_manage(request):
    q  = request.GET.get('q', '').strip()
    qs = PhotoAlbum.objects.prefetch_related('photos').order_by('-event_date', '-created_at')
    if q:
        qs = qs.filter(title__icontains=q)
    page_obj = Paginator(qs, PER_PAGE).get_page(request.GET.get('page'))
    return render(request, 'members/album_manage.html', {
        'page_obj': page_obj,
        'albums':   page_obj,
        'q':        q,
    })


@staff_only
def album_create(request):
    form = PhotoAlbumForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        album = form.save()
        messages.success(request, 'Álbum criado! Agora adicione as fotos.')
        return redirect('album_photos', pk=album.pk)
    return render(request, 'members/album_form.html', {
        'form': form, 'title': 'Novo Álbum'
    })


@staff_only
def album_edit(request, pk):
    album = get_object_or_404(PhotoAlbum, pk=pk)
    form  = PhotoAlbumForm(request.POST or None, request.FILES or None, instance=album)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Álbum atualizado!')
        return redirect('album_manage')
    return render(request, 'members/album_form.html', {
        'form': form, 'title': 'Editar Álbum', 'album': album
    })


@admin_only
def album_delete(request, pk):
    album = get_object_or_404(PhotoAlbum, pk=pk)
    if request.method == 'POST':
        album.delete()
        messages.success(request, 'Álbum removido.')
        return redirect('album_manage')
    return render(request, 'members/confirm_delete.html',
                  {'object': album, 'tipo': 'álbum de fotos'})


@staff_only
def album_photos(request, pk):
    """Gerencia as fotos de um álbum: upload múltiplo + exclusão individual."""
    album = get_object_or_404(PhotoAlbum, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'upload':
            files = request.FILES.getlist('images')
            if not files:
                messages.error(request, 'Selecione ao menos uma foto.')
            else:
                count = album.photos.count()
                for f in files:
                    Photo.objects.create(album=album, image=f, order=count)
                    count += 1
                messages.success(request, f'{len(files)} foto(s) adicionada(s)!')

        elif action == 'delete_photo':
            photo_id = request.POST.get('photo_id')
            Photo.objects.filter(pk=photo_id, album=album).delete()
            messages.success(request, 'Foto removida.')

        elif action == 'set_cover':
            photo_id = request.POST.get('photo_id')
            photo = get_object_or_404(Photo, pk=photo_id, album=album)
            album.cover = photo.image
            album.save()
            messages.success(request, 'Capa do álbum atualizada!')

        return redirect('album_photos', pk=pk)

    photos = album.photos.all()
    return render(request, 'members/album_photos.html', {
        'album':  album,
        'photos': photos,
    })


# ══════════════════════════════════════════════════════════
# ── Conteúdos Exclusivos — Gestão para Staff/Admin ────────
# ══════════════════════════════════════════════════════════
from .models import ExclusiveContent, ContentCategory

@staff_only
def content_manage(request):
    q       = request.GET.get('q', '').strip()
    tipo    = request.GET.get('tipo', '')
    cat_id  = request.GET.get('categoria', '')

    qs = ExclusiveContent.objects.select_related('category', 'author').order_by('-created_at')
    if q:
        qs = qs.filter(title__icontains=q)
    if tipo:
        qs = qs.filter(content_type=tipo)
    if cat_id:
        qs = qs.filter(category_id=cat_id)

    page_obj   = Paginator(qs, PER_PAGE).get_page(request.GET.get('page'))
    categories = ContentCategory.objects.all()
    from .models import ExclusiveContent as EC
    tipos = EC.TYPE_CHOICES

    return render(request, 'members/content_manage.html', {
        'page_obj':   page_obj,
        'items':      page_obj,
        'categories': categories,
        'tipos':      tipos,
        'q':          q,
        'tipo':       tipo,
        'cat_id':     cat_id,
    })


@staff_only
def content_create_manage(request):
    form = ContentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        c = form.save(commit=False)
        c.author = request.user
        c.save()
        messages.success(request, 'Conteúdo criado com sucesso!')
        return redirect('content_manage')
    return render(request, 'members/content_manage_form.html', {
        'form': form, 'title': 'Novo Conteúdo'
    })


@staff_only
def content_edit_manage(request, pk):
    content = get_object_or_404(ExclusiveContent, pk=pk)
    form    = ContentForm(request.POST or None, request.FILES or None, instance=content)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Conteúdo atualizado!')
        return redirect('content_manage')
    return render(request, 'members/content_manage_form.html', {
        'form': form, 'title': 'Editar Conteúdo', 'content': content
    })


@admin_only
def content_delete_manage(request, pk):
    content = get_object_or_404(ExclusiveContent, pk=pk)
    if request.method == 'POST':
        content.delete()
        messages.success(request, 'Conteúdo removido.')
        return redirect('content_manage')
    return render(request, 'members/confirm_delete.html',
                  {'object': content, 'tipo': 'conteúdo exclusivo'})


# ── Consentimento LGPD ────────────────────────────────────
@members_only
def lgpd_consent(request):
    """Permite ao membro conceder ou revogar o consentimento de uso de imagem."""
    from django.utils import timezone
    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()

        if action == 'grant':
            profile.image_consent = True
            profile.image_consent_date = timezone.now()
            profile.image_consent_ip = ip
            profile.image_consent_revoked = False
            profile.image_consent_revoked_date = None
            profile.save()
            messages.success(request, 'Autorização de uso de imagem concedida. Obrigado!')

        elif action == 'revoke':
            profile.image_consent = False
            profile.image_consent_revoked = True
            profile.image_consent_revoked_date = timezone.now()
            profile.save()
            messages.success(request, 'Autorização de uso de imagem revogada com sucesso.')

        return redirect('lgpd_consent')

    return render(request, 'members/lgpd_consent.html', {'profile': profile})


# ══════════════════════════════════════════════════════════
# ── Devocionais — Gestão para Staff ───────────────────────
# ══════════════════════════════════════════════════════════
from .forms import DevotionalForm

@staff_only
def devotional_manage(request):
    q   = request.GET.get('q', '').strip()
    pub = request.GET.get('pub', '')

    qs = Devotional.objects.order_by('-pub_date')
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(title__icontains=q) | Q(verse__icontains=q) | Q(author__icontains=q))
    if pub == '1':
        qs = qs.filter(published=True)
    elif pub == '0':
        qs = qs.filter(published=False)

    page_obj = Paginator(qs, PER_PAGE).get_page(request.GET.get('page'))
    return render(request, 'members/devotional_manage.html', {
        'page_obj': page_obj,
        'devos':    page_obj,
        'q':        q,
        'pub':      pub,
    })


@staff_only
def devotional_create(request):
    form = DevotionalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Devocional criado com sucesso!')
        return redirect('devotional_manage')
    return render(request, 'members/devotional_form.html', {
        'form': form, 'title': 'Novo Devocional'
    })


@staff_only
def devotional_edit(request, pk):
    dev  = get_object_or_404(Devotional, pk=pk)
    form = DevotionalForm(request.POST or None, instance=dev)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Devocional atualizado!')
        return redirect('devotional_manage')
    return render(request, 'members/devotional_form.html', {
        'form': form, 'title': 'Editar Devocional', 'dev': dev
    })


@admin_only
def devotional_delete(request, pk):
    dev = get_object_or_404(Devotional, pk=pk)
    if request.method == 'POST':
        dev.delete()
        messages.success(request, 'Devocional removido.')
        return redirect('devotional_manage')
    return render(request, 'members/confirm_delete.html',
                  {'object': dev, 'tipo': 'devocional'})


# ══════════════════════════════════════════════════════════
# ── Página Principal (HeroSlide) — Gestão para Staff ──────
# ══════════════════════════════════════════════════════════
from core.models import HeroSlide
from .forms import HeroSlideForm

@staff_only
def heroslide_manage(request):
    slides = HeroSlide.objects.order_by('order')
    return render(request, 'members/heroslide_manage.html', {'slides': slides})


@staff_only
def heroslide_create(request):
    form = HeroSlideForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Banner criado com sucesso!')
        return redirect('heroslide_manage')
    return render(request, 'members/heroslide_form.html', {
        'form': form, 'title': 'Novo Banner — Página Principal'
    })


@staff_only
def heroslide_edit(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    form  = HeroSlideForm(request.POST or None, request.FILES or None, instance=slide)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        # Se há conteúdo de modal, limpa o URL (evita URL errada salva)
        if obj.button_modal_content.strip():
            obj.button_url = ''
        if obj.button_modal_content_2.strip():
            obj.button_url_2 = ''
        obj.save()
        messages.success(request, 'Banner atualizado!')
        return redirect('heroslide_manage')
    return render(request, 'members/heroslide_form.html', {
        'form': form, 'title': 'Editar Banner', 'slide': slide
    })


@admin_only
def heroslide_delete(request, pk):
    slide = get_object_or_404(HeroSlide, pk=pk)
    if request.method == 'POST':
        slide.delete()
        messages.success(request, 'Banner removido.')
        return redirect('heroslide_manage')
    return render(request, 'members/confirm_delete.html',
                  {'object': slide, 'tipo': 'banner da página principal'})


# ── Solicitações de exclusão (Colaborador → Admin) ────────

@staff_only
def delete_request_create(request):
    """Colaborador solicita a exclusão de um item ao admin."""
    if request.method == 'POST':
        content_type  = request.POST.get('content_type', '')
        object_id     = request.POST.get('object_id', '')
        object_title  = request.POST.get('object_title', '')
        reason        = request.POST.get('reason', '').strip()

        if not (content_type and object_id and object_title):
            messages.error(request, 'Dados inválidos.')
            return redirect('member_dashboard')

        # Evita duplicata pendente
        already = DeleteRequest.objects.filter(
            requested_by=request.user,
            content_type=content_type,
            object_id=object_id,
            status='pending'
        ).exists()
        if already:
            messages.warning(request, 'Já existe uma solicitação pendente para este item.')
        else:
            dr = DeleteRequest.objects.create(
                requested_by=request.user,
                content_type=content_type,
                object_id=int(object_id),
                object_title=object_title,
                reason=reason,
            )
            try:
                notify_admin_delete_request(dr)
            except Exception:
                pass
            messages.success(request, 'Solicitação de exclusão enviada ao administrador.')
    return redirect(request.POST.get('next', 'member_dashboard'))


@admin_only
def delete_request_manage(request):
    """Admin revisa todas as solicitações de exclusão."""
    pending  = DeleteRequest.objects.filter(status='pending').select_related('requested_by')
    reviewed = DeleteRequest.objects.exclude(status='pending').select_related('requested_by', 'reviewed_by')[:30]
    return render(request, 'members/delete_request_manage.html', {
        'pending': pending, 'reviewed': reviewed,
        'pending_count': pending.count(),
    })


@admin_only
def delete_request_approve(request, pk):
    """Admin aprova: executa a exclusão real e marca como aprovada."""
    from django.utils import timezone as tz
    dr = get_object_or_404(DeleteRequest, pk=pk)
    if request.method == 'POST':
        try:
            _execute_delete(dr)
            dr.status      = 'approved'
            dr.reviewed_by = request.user
            dr.reviewed_at = tz.now()
            dr.admin_note  = request.POST.get('admin_note', '')
            dr.save()
            try:
                notify_collaborator_delete_reviewed(dr)
            except Exception:
                pass
            messages.success(request, f'Item "{dr.object_title}" excluído com sucesso.')
        except Exception as e:
            messages.error(request, f'Erro ao excluir: {e}')
    return redirect('delete_request_manage')


@admin_only
def delete_request_reject(request, pk):
    """Admin rejeita a solicitação sem excluir nada."""
    from django.utils import timezone as tz
    dr = get_object_or_404(DeleteRequest, pk=pk)
    if request.method == 'POST':
        dr.status      = 'rejected'
        dr.reviewed_by = request.user
        dr.reviewed_at = tz.now()
        dr.admin_note  = request.POST.get('admin_note', '').strip()
        dr.save()
        try:
            notify_collaborator_delete_reviewed(dr)
        except Exception:
            pass
        messages.success(request, 'Solicitação recusada.')
    return redirect('delete_request_manage')


def _execute_delete(dr):
    """Executa a exclusão real conforme o tipo de conteúdo."""
    from core.models import MediaItem, Devotional
    from members.models import ExclusiveContent, Notice
    from core.models import HeroSlide
    MODEL_MAP = {
        'media':      ('core', 'MediaItem'),
        'content':    ('members', 'ExclusiveContent'),
        'devotional': ('core', 'Devotional'),
        'heroslide':  ('core', 'HeroSlide'),
        'notice':     ('members', 'Notice'),
    }
    ct = dr.content_type
    if ct == 'media':
        MediaItem.objects.filter(pk=dr.object_id).delete()
    elif ct == 'content':
        ExclusiveContent.objects.filter(pk=dr.object_id).delete()
    elif ct == 'devotional':
        Devotional.objects.filter(pk=dr.object_id).delete()
    elif ct == 'heroslide':
        HeroSlide.objects.filter(pk=dr.object_id).delete()
    elif ct == 'notice':
        Notice.objects.filter(pk=dr.object_id).delete()
    elif ct == 'album':
        from core.models import PhotoAlbum
        PhotoAlbum.objects.filter(pk=dr.object_id).delete()
    elif ct == 'event':
        from events.models import Event
        Event.objects.filter(pk=dr.object_id).delete()
    else:
        raise ValueError(f'Tipo desconhecido: {ct}')


# ── Perfil do aluno ────────────────────────────────────────

@members_only
def student_profile(request):
    """Página de progresso do aluno em cursos e EBD."""
    from courses.models import Enrollment, LessonProgress, Lesson, QuizAttempt as CQuizAttempt
    from ebd.models import QuizAttempt as EQuizAttempt, LessonCertificate

    user = request.user

    # Cursos — lessons ficam em Module, não direto em Course
    enrollments = Enrollment.objects.filter(user=user).select_related('course').order_by('-enrolled_at')
    course_data = []
    for enr in enrollments:
        # Suporta progress_percent tanto como método quanto como property
        _pp = enr.progress_percent
        pct = _pp() if callable(_pp) else _pp
        total = Lesson.objects.filter(module__course=enr.course, published=True).count()
        done  = LessonProgress.objects.filter(
            user=user, lesson__module__course=enr.course, completed=True
        ).count()
        best_quiz = CQuizAttempt.objects.filter(
            user=user, quiz__lesson__module__course=enr.course
        ).order_by('-score').first()
        course_data.append({
            'enrollment': enr,
            'pct':        pct,
            'done':       done,
            'total':      total,
            'best_quiz':  best_quiz,
        })

    # EBD — select_related ajustado ao caminho real do modelo
    ebd_attempts = (EQuizAttempt.objects
                    .filter(user=user)
                    .select_related('quiz__lesson')
                    .order_by('-created_at'))
    ebd_certs    = (LessonCertificate.objects
                    .filter(user=user)
                    .select_related('lesson__trimester__ebd_class')
                    .order_by('-issued_at'))

    # Conquistas automáticas
    achievements = []
    if enrollments.exists():
        achievements.append({'icon': 'fa-graduation-cap', 'label': 'Primeiro curso iniciado', 'color': '#3B8BD4'})
    if any(cd['pct'] == 100 for cd in course_data):
        achievements.append({'icon': 'fa-check-circle', 'label': 'Curso concluído', 'color': '#27ae60'})
    if ebd_certs.exists():
        achievements.append({'icon': 'fa-certificate', 'label': 'Certificado EBD', 'color': '#C9A84C'})
    if ebd_attempts.filter(score__gte=80).exists():
        achievements.append({'icon': 'fa-star', 'label': 'Nota acima de 80% no quiz', 'color': '#C9A84C'})
    if enrollments.count() >= 3:
        achievements.append({'icon': 'fa-fire', 'label': '3 cursos iniciados', 'color': '#e74c3c'})

    # Presenças
    total_cultos  = Culto.objects.count()
    pres_count    = Presenca.objects.filter(member__user=user, present=True).count()
    pres_total    = Presenca.objects.filter(member__user=user).count()
    pres_pct      = round(pres_count / pres_total * 100) if pres_total else 0

    # Streak de presenças
    recentes = Presenca.objects.filter(member__user=user).select_related('culto').order_by('-culto__date')
    pres_streak = 0
    for p in recentes:
        if p.present:
            pres_streak += 1
        else:
            break

    # Badges de presença
    if pres_pct >= 90 and pres_count >= 10:
        achievements.append({'icon': 'fa-medal', 'label': 'Presença Exemplar', 'color': '#C9A84C'})
    if pres_streak >= 10:
        achievements.append({'icon': 'fa-fire', 'label': f'{pres_streak} cultos seguidos', 'color': '#e74c3c'})
    if pres_count >= 50:
        achievements.append({'icon': 'fa-crown', 'label': '50+ presenças', 'color': '#6c3483'})

    # Nota 10: presença ≥ 85% + streak ≥ 4 + ao menos 1 curso iniciado ou quiz EBD
    is_nota10 = (pres_pct >= 85 and pres_streak >= 4 and
                 (enrollments.exists() or ebd_attempts.exists()))
    if is_nota10:
        achievements.append({'icon': 'fa-award', 'label': 'Aluno Nota 10', 'color': '#C9A84C'})

    return render(request, 'members/student_profile.html', {
        'course_data':   course_data,
        'ebd_attempts':  ebd_attempts[:10],
        'ebd_certs':     ebd_certs,
        'achievements':  achievements,
        'total_courses': enrollments.count(),
        'done_courses':  sum(1 for cd in course_data if cd['pct'] == 100),
        'total_ebd':     ebd_attempts.count(),
        'pres_count':    pres_count,
        'pres_pct':      pres_pct,
        'pres_streak':   pres_streak,
        'total_cultos':  total_cultos,
        'is_nota10':     is_nota10,
    })


# ══════════════════════════════════════════════════════════
# ── Redes Sociais — Instagram & Facebook ──────────────────
# ══════════════════════════════════════════════════════════
from core.models import SocialPost, SocialConfig
from core.social_publisher import publish_social_post, validate_ig_token, validate_fb_token


@staff_only
def social_post_create(request, album_pk):
    """Cria e opcionalmente publica um SocialPost para um álbum."""
    album  = get_object_or_404(PhotoAlbum, pk=album_pk)
    photos = album.photos.all()
    config = SocialConfig.get_config()

    if request.method == 'POST':
        # Fotos selecionadas
        photo_ids = request.POST.getlist('photo_ids')
        if not photo_ids:
            messages.error(request, 'Selecione ao menos uma foto.')
            return redirect('social_post_create', album_pk=album_pk)

        platform    = request.POST.get('platform', 'both')
        post_format = request.POST.get('post_format', 'carousel')
        caption     = request.POST.get('caption', '').strip()
        hashtags    = request.POST.get('hashtags', '').strip()
        action      = request.POST.get('submit_action', 'draft')  # 'draft' ou 'publish'
        schedule    = request.POST.get('scheduled_for', '').strip()

        if not caption:
            messages.error(request, 'A legenda não pode estar vazia.')
            return redirect('social_post_create', album_pk=album_pk)

        # Forçar 'single' se só uma foto
        selected_photos = Photo.objects.filter(pk__in=photo_ids, album=album)
        if selected_photos.count() == 1:
            post_format = 'single'

        scheduled_for = None
        if schedule:
            from datetime import datetime
            try:
                from django.utils.timezone import make_aware
                scheduled_for = make_aware(datetime.fromisoformat(schedule))
            except ValueError:
                pass

        sp = SocialPost.objects.create(
            album         = album,
            platform      = platform,
            post_format   = post_format,
            caption       = caption,
            hashtags      = hashtags,
            status        = 'draft',
            created_by    = request.user,
            scheduled_for = scheduled_for,
        )
        sp.photos.set(selected_photos)

        if action == 'publish':
            result = publish_social_post(sp)
            if sp.status == 'published':
                messages.success(request, '✅ Publicado com sucesso no(s) canal(is) selecionado(s)!')
            elif sp.status == 'partial':
                messages.warning(request, '⚠️ Publicado parcialmente — verifique os erros abaixo.')
            else:
                messages.error(request, f'❌ Falha ao publicar: verifique as configurações.')
        else:
            messages.success(request, 'Rascunho salvo! Publique quando estiver pronto.')

        return redirect('social_post_list', album_pk=album_pk)

    # GET — montar prévia
    return render(request, 'members/social_post_create.html', {
        'album':   album,
        'photos':  photos,
        'config':  config,
    })


@staff_only
def social_post_list(request, album_pk):
    """Lista publicações sociais de um álbum."""
    album = get_object_or_404(PhotoAlbum, pk=album_pk)
    posts = SocialPost.objects.filter(album=album).prefetch_related('photos')
    return render(request, 'members/social_post_list.html', {
        'album': album,
        'posts': posts,
    })


@staff_only
def social_post_publish(request, pk):
    """Publica um rascunho existente."""
    sp = get_object_or_404(SocialPost, pk=pk)
    if request.method == 'POST':
        if not sp.photos.exists():
            messages.error(request, 'Nenhuma foto selecionada nesta publicação.')
            return redirect('social_post_list', album_pk=sp.album_id)
        publish_social_post(sp)
        if sp.status == 'published':
            messages.success(request, '✅ Publicado com sucesso!')
        elif sp.status == 'partial':
            messages.warning(request, '⚠️ Publicado com erros em um dos canais.')
        else:
            messages.error(request, '❌ Falha ao publicar. Verifique as configurações.')
    return redirect('social_post_list', album_pk=sp.album_id)


@admin_only
def social_post_delete(request, pk):
    """Remove um SocialPost (não apaga o post nas redes, só o registro)."""
    sp = get_object_or_404(SocialPost, pk=pk)
    album_pk = sp.album_id
    if request.method == 'POST':
        sp.delete()
        messages.success(request, 'Registro removido.')
    return redirect('social_post_list', album_pk=album_pk)


@admin_only
def social_config(request):
    """Configurações de tokens Instagram/Facebook."""
    config = SocialConfig.get_config()
    ig_info = None
    fb_info = None

    if request.method == 'POST':
        action = request.POST.get('action', 'save')

        if action == 'save':
            config.ig_user_id      = request.POST.get('ig_user_id', '').strip()
            config.ig_access_token = request.POST.get('ig_access_token', '').strip()
            config.fb_page_id      = request.POST.get('fb_page_id', '').strip()
            config.fb_access_token = request.POST.get('fb_access_token', '').strip()
            config.site_base_url   = request.POST.get('site_base_url', '').strip().rstrip('/')
            config.save()
            messages.success(request, 'Configurações salvas!')

        elif action == 'test_ig':
            config.ig_user_id      = request.POST.get('ig_user_id', '').strip()
            config.ig_access_token = request.POST.get('ig_access_token', '').strip()
            config.save()
            ig_info = validate_ig_token(config.ig_user_id, config.ig_access_token)
            if ig_info['ok']:
                messages.success(request, f"✅ Instagram conectado: @{ig_info['data'].get('username', 'conta')}")
            else:
                messages.error(request, f"❌ Instagram: {ig_info['error']}")

        elif action == 'test_fb':
            config.fb_page_id      = request.POST.get('fb_page_id', '').strip()
            config.fb_access_token = request.POST.get('fb_access_token', '').strip()
            config.save()
            fb_info = validate_fb_token(config.fb_page_id, config.fb_access_token)
            if fb_info['ok']:
                messages.success(request, f"✅ Facebook conectado: {fb_info['data'].get('name', 'Página')}")
            else:
                messages.error(request, f"❌ Facebook: {fb_info['error']}")

        return redirect('social_config')

    return render(request, 'members/social_config.html', {
        'config':  config,
        'ig_info': ig_info,
        'fb_info': fb_info,
    })

# ══════════════════════════════════════════════════════════
# ── CMS — Configurações da Igreja ────────────────────────
# ══════════════════════════════════════════════════════════

@staff_only
@staff_only
def church_settings(request):
    """Configurações gerais da igreja (CMS)."""
    igreja = request.igreja
    settings = SiteSettings.get_settings(igreja)

    if request.method == 'POST':
        section = request.POST.get('section', 'basic')

        if section == 'basic':
            settings.church_name        = request.POST.get('church_name', '').strip()
            settings.tagline            = request.POST.get('tagline', '').strip()
            settings.about_text         = request.POST.get('about_text', '').strip()
            settings.address            = request.POST.get('address', '').strip()
            settings.maps_url           = request.POST.get('maps_url', '').strip()
            settings.phone              = request.POST.get('phone', '').strip()
            settings.email              = request.POST.get('email', '').strip()
            settings.notification_email = request.POST.get('notification_email', '').strip()

        elif section == 'visual':
            settings.color_primary   = request.POST.get('color_primary', '#C9A84C').strip()
            settings.color_secondary = request.POST.get('color_secondary', '#1A2340').strip()
            settings.color_accent    = request.POST.get('color_accent', '#8B6914').strip()
            settings.hero_title      = request.POST.get('hero_title', '').strip()
            settings.hero_subtitle   = request.POST.get('hero_subtitle', '').strip()
            if 'logo' in request.FILES:
                settings.logo = request.FILES['logo']
            if 'hero_image' in request.FILES:
                settings.hero_image = request.FILES['hero_image']

        elif section == 'social':
            settings.facebook_url  = request.POST.get('facebook_url', '').strip()
            settings.instagram_url = request.POST.get('instagram_url', '').strip()
            settings.youtube_url   = request.POST.get('youtube_url', '').strip()

        elif section == 'pix':
            settings.pix_key          = request.POST.get('pix_key', '').strip()
            settings.pix_name         = request.POST.get('pix_name', '').strip()
            settings.bank_name        = request.POST.get('bank_name', '').strip()
            settings.bank_agency      = request.POST.get('bank_agency', '').strip()
            settings.bank_account     = request.POST.get('bank_account', '').strip()
            settings.bank_holder      = request.POST.get('bank_holder', '').strip()
            settings.offering_text    = request.POST.get('offering_text', '').strip()

        settings.save()
        messages.success(request, '✅ Configurações salvas com sucesso!')
        return redirect('church_settings')

    return render(request, 'members/church_settings.html', {
        'settings': settings,
        'igreja':   igreja,
    })
# ══════════════════════════════════════════════════════════
# ── Redes Sociais — Eventos ───────────────────────────────
# ══════════════════════════════════════════════════════════
from events.models import Event as EventModel

@staff_only
def event_social_post_create(request, event_pk):
    """Cria e opcionalmente publica um SocialPost para um evento."""
    event  = get_object_or_404(EventModel, pk=event_pk)
    config = SocialConfig.get_config()

    # Gerar legenda padrão com dados do evento
    from django.utils.formats import date_format
    default_caption = event.short_description or event.description[:300]
    date_str  = date_format(event.date, 'd "de" F "de" Y "às" H:i')
    location_str = f'\n📍 {event.location}' if event.location else ''
    link_str  = f'\n🔗 {config.site_base_url}{event.get_absolute_url()}' if config.site_base_url else ''
    auto_caption = f'📅 {event.title}\n\n{default_caption}\n\n🗓 {date_str}{location_str}{link_str}'

    if request.method == 'POST':
        platform  = request.POST.get('platform', 'both')
        caption   = request.POST.get('caption', '').strip()
        hashtags  = request.POST.get('hashtags', '').strip()
        action    = request.POST.get('submit_action', 'draft')
        schedule  = request.POST.get('scheduled_for', '').strip()

        if not caption:
            messages.error(request, 'A legenda não pode estar vazia.')
            return redirect('event_social_post_create', event_pk=event_pk)

        scheduled_for = None
        if schedule:
            from datetime import datetime
            try:
                from django.utils.timezone import make_aware
                scheduled_for = make_aware(datetime.fromisoformat(schedule))
            except ValueError:
                pass

        sp = SocialPost.objects.create(
            source_type   = 'event',
            event         = event,
            platform      = platform,
            post_format   = 'single',
            caption       = caption,
            hashtags      = hashtags,
            status        = 'draft',
            created_by    = request.user,
            scheduled_for = scheduled_for,
        )

        if action == 'publish':
            publish_social_post(sp)
            if sp.status == 'published':
                messages.success(request, '✅ Evento publicado com sucesso nas redes sociais!')
            elif sp.status == 'partial':
                messages.warning(request, '⚠️ Publicado parcialmente — verifique os erros abaixo.')
            else:
                messages.error(request, '❌ Falha ao publicar. Verifique as configurações.')
        else:
            messages.success(request, 'Rascunho salvo! Publique quando estiver pronto.')

        return redirect('event_social_post_list', event_pk=event_pk)

    return render(request, 'members/event_social_post_create.html', {
        'event':          event,
        'config':         config,
        'auto_caption':   auto_caption,
    })


@staff_only
def event_social_post_list(request, event_pk):
    """Lista publicações sociais de um evento."""
    event = get_object_or_404(EventModel, pk=event_pk)
    posts = SocialPost.objects.filter(event=event).order_by('-created_at')
    return render(request, 'members/event_social_post_list.html', {
        'event': event,
        'posts': posts,
    })


@staff_only
def event_social_post_publish(request, pk):
    """Publica um rascunho de evento existente."""
    sp = get_object_or_404(SocialPost, pk=pk, source_type='event')
    if request.method == 'POST':
        publish_social_post(sp)
        if sp.status == 'published':
            messages.success(request, '✅ Publicado com sucesso!')
        elif sp.status == 'partial':
            messages.warning(request, '⚠️ Publicado com erros em um dos canais.')
        else:
            messages.error(request, '❌ Falha ao publicar.')
    return redirect('event_social_post_list', event_pk=sp.event_id)


@admin_only
def event_social_post_delete(request, pk):
    """Remove um SocialPost de evento."""
    sp = get_object_or_404(SocialPost, pk=pk, source_type='event')
    event_pk = sp.event_id
    if request.method == 'POST':
        sp.delete()
        messages.success(request, 'Registro removido.')
    return redirect('event_social_post_list', event_pk=event_pk)


# ══════════════════════════════════════════════════════════
# ── EBD — CRUD do Dashboard ───────────────────────────────
# ══════════════════════════════════════════════════════════
from ebd.models import (EbdClass, EbdTrimester, EbdLesson,
                         Quiz, Question, Choice, QuizAttempt as EbdQuizAttempt)


# ── Turmas ────────────────────────────────────────────────
@staff_only
def ebd_manage(request):
    """Lista de turmas da EBD com stats."""
    classes = EbdClass.objects.prefetch_related('trimesters').order_by('order', 'name')
    total_lessons = EbdLesson.objects.count()
    total_attempts = EbdQuizAttempt.objects.count()
    return render(request, 'members/ebd/ebd_manage.html', {
        'classes':       classes,
        'total_lessons': total_lessons,
        'total_attempts': total_attempts,
    })


@staff_only
def ebd_class_create(request):
    if request.method == 'POST':
        name  = request.POST.get('name', '').strip()
        desc  = request.POST.get('description', '').strip()
        order = request.POST.get('order', 0)
        if not name:
            messages.error(request, 'O nome da turma é obrigatório.')
        else:
            EbdClass.objects.create(name=name, description=desc, order=order)
            messages.success(request, f'Turma "{name}" criada!')
        return redirect('ebd_manage')
    return render(request, 'members/ebd/ebd_class_form.html', {'title': 'Nova Turma'})


@staff_only
def ebd_class_edit(request, pk):
    cls = get_object_or_404(EbdClass, pk=pk)
    if request.method == 'POST':
        cls.name        = request.POST.get('name', '').strip()
        cls.description = request.POST.get('description', '').strip()
        cls.order       = request.POST.get('order', 0)
        cls.active      = 'active' in request.POST
        cls.save()
        messages.success(request, 'Turma atualizada!')
        return redirect('ebd_manage')
    return render(request, 'members/ebd/ebd_class_form.html', {
        'title': 'Editar Turma', 'cls': cls
    })


@admin_only
def ebd_class_delete(request, pk):
    cls = get_object_or_404(EbdClass, pk=pk)
    if request.method == 'POST':
        cls.delete()
        messages.success(request, 'Turma removida.')
        return redirect('ebd_manage')
    return render(request, 'members/confirm_delete.html',
                  {'object': cls, 'tipo': 'turma da EBD',
                   'cancel_url': 'ebd_manage'})


# ── Trimestres ────────────────────────────────────────────
@staff_only
def ebd_trimester_manage(request, class_pk):
    cls        = get_object_or_404(EbdClass, pk=class_pk)
    trimesters = cls.trimesters.prefetch_related('lessons').all()
    return render(request, 'members/ebd/ebd_trimester_manage.html', {
        'cls': cls, 'trimesters': trimesters,
    })


@staff_only
def ebd_trimester_create(request, class_pk):
    cls = get_object_or_404(EbdClass, pk=class_pk)
    if request.method == 'POST':
        year    = request.POST.get('year', '').strip()
        quarter = request.POST.get('quarter', '').strip()
        title   = request.POST.get('title', '').strip()
        desc    = request.POST.get('description', '').strip()
        active  = 'active' in request.POST
        if not (year and quarter and title):
            messages.error(request, 'Ano, trimestre e título são obrigatórios.')
        else:
            t = EbdTrimester.objects.create(
                ebd_class=cls, year=int(year), quarter=int(quarter),
                title=title, description=desc, active=active,
            )
            messages.success(request, f'Trimestre "{t}" criado!')
        return redirect('ebd_trimester_manage', class_pk=class_pk)
    return render(request, 'members/ebd/ebd_trimester_form.html', {
        'cls': cls, 'title': 'Novo Trimestre',
        'quarters': EbdTrimester.QUARTER_CHOICES,
    })


@staff_only
def ebd_trimester_edit(request, pk):
    tri = get_object_or_404(EbdTrimester, pk=pk)
    if request.method == 'POST':
        tri.year        = int(request.POST.get('year', tri.year))
        tri.quarter     = int(request.POST.get('quarter', tri.quarter))
        tri.title       = request.POST.get('title', '').strip()
        tri.description = request.POST.get('description', '').strip()
        tri.active      = 'active' in request.POST
        tri.save()
        messages.success(request, 'Trimestre atualizado!')
        return redirect('ebd_trimester_manage', class_pk=tri.ebd_class_id)
    return render(request, 'members/ebd/ebd_trimester_form.html', {
        'cls': tri.ebd_class, 'tri': tri, 'title': 'Editar Trimestre',
        'quarters': EbdTrimester.QUARTER_CHOICES,
    })


@admin_only
def ebd_trimester_delete(request, pk):
    tri = get_object_or_404(EbdTrimester, pk=pk)
    class_pk = tri.ebd_class_id
    if request.method == 'POST':
        tri.delete()
        messages.success(request, 'Trimestre removido.')
        return redirect('ebd_trimester_manage', class_pk=class_pk)
    return render(request, 'members/confirm_delete.html',
                  {'object': tri, 'tipo': 'trimestre da EBD'})


# ── Lições ────────────────────────────────────────────────
@staff_only
def ebd_lesson_manage(request, trimester_pk):
    tri     = get_object_or_404(EbdTrimester, pk=trimester_pk)
    lessons = tri.lessons.select_related('trimester').all()
    return render(request, 'members/ebd/ebd_lesson_manage.html', {
        'tri': tri, 'lessons': lessons,
    })


@staff_only
def ebd_lesson_create(request, trimester_pk):
    tri = get_object_or_404(EbdTrimester, pk=trimester_pk)
    if request.method == 'POST':
        number    = request.POST.get('number', '').strip()
        title     = request.POST.get('title', '').strip()
        summary   = request.POST.get('summary', '').strip()
        body      = request.POST.get('body', '').strip()
        scripture = request.POST.get('scripture', '').strip()
        video_url = request.POST.get('video_url', '').strip()
        published = 'published' in request.POST
        order     = request.POST.get('order', 0)
        audio     = request.FILES.get('audio_file')
        pdf       = request.FILES.get('pdf_file')
        if not (number and title):
            messages.error(request, 'Número e título são obrigatórios.')
        else:
            lesson = EbdLesson.objects.create(
                trimester=tri, number=int(number), title=title,
                summary=summary, body=body, scripture=scripture,
                video_url=video_url, published=published,
                order=int(order) if order else 0,
                audio_file=audio, pdf_file=pdf,
            )
            messages.success(request, f'Lição {lesson.number} criada!')
            return redirect('ebd_lesson_manage', trimester_pk=trimester_pk)
        return redirect('ebd_lesson_manage', trimester_pk=trimester_pk)
    return render(request, 'members/ebd/ebd_lesson_form.html', {
        'tri': tri, 'title': 'Nova Lição',
    })


@staff_only
def ebd_lesson_edit(request, pk):
    lesson = get_object_or_404(EbdLesson, pk=pk)
    if request.method == 'POST':
        lesson.number    = int(request.POST.get('number', lesson.number))
        lesson.title     = request.POST.get('title', '').strip()
        lesson.summary   = request.POST.get('summary', '').strip()
        lesson.body      = request.POST.get('body', '').strip()
        lesson.scripture = request.POST.get('scripture', '').strip()
        lesson.video_url = request.POST.get('video_url', '').strip()
        lesson.published = 'published' in request.POST
        lesson.order     = int(request.POST.get('order', lesson.order) or 0)
        if request.FILES.get('audio_file'):
            lesson.audio_file = request.FILES['audio_file']
        if request.FILES.get('pdf_file'):
            lesson.pdf_file = request.FILES['pdf_file']
        lesson.save()
        messages.success(request, 'Lição atualizada!')
        return redirect('ebd_lesson_manage', trimester_pk=lesson.trimester_id)
    return render(request, 'members/ebd/ebd_lesson_form.html', {
        'tri': lesson.trimester, 'lesson': lesson, 'title': 'Editar Lição',
    })


@admin_only
def ebd_lesson_delete(request, pk):
    lesson = get_object_or_404(EbdLesson, pk=pk)
    tri_pk = lesson.trimester_id
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Lição removida.')
        return redirect('ebd_lesson_manage', trimester_pk=tri_pk)
    return render(request, 'members/confirm_delete.html',
                  {'object': lesson, 'tipo': 'lição da EBD'})


# ══════════════════════════════════════════════════════════
# ── Reset de Senha ────────────────────────────────────────
# ══════════════════════════════════════════════════════════

def password_reset_request(request):
    """Membro informa o e-mail para receber o link de reset."""
    if request.user.is_authenticated:
        return redirect('member_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        if email:
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                user = User.objects.get(email__iexact=email, is_active=True)

                # Invalida tokens antigos
                PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

                # Gera novo token
                import secrets
                token_str = secrets.token_urlsafe(48)
                PasswordResetToken.objects.create(user=user, token=token_str)

                # Envia e-mail
                send_password_reset(user, token_str)
            except Exception:
                pass  # Não revela se o e-mail existe ou não

        # Sempre mostra mensagem genérica (segurança)
        messages.success(request,
            'Se este e-mail estiver cadastrado, você receberá as instruções em breve.')
        return redirect('password_reset_request')

    return render(request, 'members/password_reset_request.html')


def password_reset_confirm(request, token):
    """Membro define a nova senha via link do e-mail."""
    if request.user.is_authenticated:
        return redirect('member_dashboard')

    try:
        reset = PasswordResetToken.objects.get(token=token)
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Link inválido ou expirado.')
        return redirect('password_reset_request')

    if not reset.is_valid():
        messages.error(request, 'Este link expirou. Solicite um novo.')
        return redirect('password_reset_request')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if len(password1) < 8:
            messages.error(request, 'A senha deve ter pelo menos 8 caracteres.')
        elif password1 != password2:
            messages.error(request, 'As senhas não coincidem.')
        else:
            user = reset.user
            user.set_password(password1)
            user.save()
            reset.used = True
            reset.save()
            # Invalida outros tokens pendentes
            PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
            messages.success(request, 'Senha redefinida com sucesso! Faça login.')
            return redirect('member_login')

    return render(request, 'members/password_reset_confirm.html', {'token': token})


# ══════════════════════════════════════════════════════════
# ── Células — CRUD do Dashboard ───────────────────────────
# ══════════════════════════════════════════════════════════
from cells.models import Cell, CellMembership, CellPost


@staff_only
def cell_manage(request):
    """Visão geral de todas as células com stats."""
    q     = request.GET.get('q', '').strip()
    tipo  = request.GET.get('tipo', '')
    ativo = request.GET.get('ativo', '')

    cells = Cell.objects.prefetch_related('memberships').order_by('cell_type', 'name')
    if q:
        cells = cells.filter(name__icontains=q)
    if tipo:
        cells = cells.filter(cell_type=tipo)
    if ativo == '1':
        cells = cells.filter(active=True)
    elif ativo == '0':
        cells = cells.filter(active=False)

    total_members = CellMembership.objects.filter(status='approved').count()
    pending_total = CellMembership.objects.filter(status='pending').count()

    return render(request, 'members/cells/cell_manage.html', {
        'cells':         cells,
        'q':             q,
        'tipo':          tipo,
        'ativo':         ativo,
        'type_choices':  Cell.TYPE_CHOICES,
        'total_members': total_members,
        'pending_total': pending_total,
        'total_cells':   Cell.objects.count(),
        'active_cells':  Cell.objects.filter(active=True).count(),
    })


@staff_only
def cell_create(request):
    if request.method == 'POST':
        name    = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'O nome é obrigatório.')
            return render(request, 'members/cells/cell_form.html', {
                'title': 'Nova Célula', 'type_choices': Cell.TYPE_CHOICES,
                'data': request.POST,
            })
        cell = Cell(
            name          = name,
            cell_type     = request.POST.get('cell_type', 'ministry'),
            description   = request.POST.get('description', '').strip(),
            region        = request.POST.get('region', '').strip(),
            meeting_day   = request.POST.get('meeting_day', '').strip(),
            meeting_place = request.POST.get('meeting_place', '').strip(),
            active        = 'active' in request.POST,
        )
        if request.FILES.get('cover'):
            cell.cover = request.FILES['cover']
        cell.save()
        messages.success(request, f'Célula "{cell.name}" criada!')
        return redirect('cell_manage_dashboard')
    return render(request, 'members/cells/cell_form.html', {
        'title': 'Nova Célula', 'type_choices': Cell.TYPE_CHOICES,
    })


@staff_only
def cell_edit(request, pk):
    cell = get_object_or_404(Cell, pk=pk)
    if request.method == 'POST':
        cell.name          = request.POST.get('name', '').strip()
        cell.cell_type     = request.POST.get('cell_type', 'ministry')
        cell.description   = request.POST.get('description', '').strip()
        cell.region        = request.POST.get('region', '').strip()
        cell.meeting_day   = request.POST.get('meeting_day', '').strip()
        cell.meeting_place = request.POST.get('meeting_place', '').strip()
        cell.active        = 'active' in request.POST
        if request.FILES.get('cover'):
            cell.cover = request.FILES['cover']
        cell.save()
        messages.success(request, 'Célula atualizada!')
        return redirect('cell_manage_dashboard')
    return render(request, 'members/cells/cell_form.html', {
        'title': 'Editar Célula', 'cell': cell, 'type_choices': Cell.TYPE_CHOICES,
    })


@admin_only
def cell_delete(request, pk):
    cell = get_object_or_404(Cell, pk=pk)
    if request.method == 'POST':
        cell.delete()
        messages.success(request, f'Célula "{cell.name}" removida.')
        return redirect('cell_manage_dashboard')
    return render(request, 'members/confirm_delete.html',
                  {'object': cell, 'tipo': 'célula'})


@staff_only
def cell_members_dashboard(request, pk):
    """Painel de gestão de membros de uma célula pelo admin/staff."""
    cell     = get_object_or_404(Cell, pk=pk)
    pending  = cell.memberships.filter(status='pending').select_related('user__profile')
    approved = cell.memberships.filter(status='approved').select_related('user__profile')
    others   = cell.memberships.filter(status__in=['rejected','left']).select_related('user__profile')

    if request.method == 'POST':
        action    = request.POST.get('action')
        member_id = request.POST.get('membership_id')
        try:
            m = CellMembership.objects.get(pk=member_id, cell=cell)
            actions = {
                'approve':     ('approved', f'{m.user.get_full_name() or m.user.username} aprovado(a)!'),
                'reject':      ('rejected', 'Pedido recusado.'),
                'remove':      ('left',     'Membro removido do grupo.'),
            }
            if action in actions:
                m.status = actions[action][0]
                m.save()
                messages.success(request, actions[action][1])
            elif action == 'make_leader':
                m.role = 'leader'; m.save()
                messages.success(request, 'Definido como líder.')
            elif action == 'make_member':
                m.role = 'member'; m.save()
                messages.success(request, 'Definido como membro.')
        except CellMembership.DoesNotExist:
            pass
        return redirect('cell_members_dashboard', pk=pk)

    return render(request, 'members/cells/cell_members.html', {
        'cell':    cell,
        'pending': pending,
        'approved': approved,
        'others':  others,
    })


# ══════════════════════════════════════════════════════════
# ── Controle de Presenças ─────────────────────────────────
# ══════════════════════════════════════════════════════════
from .models import Culto, Presenca


@staff_only
def culto_manage(request):
    """Lista de cultos com stats de presença."""
    cultos = Culto.objects.select_related('created_by').order_by('-date')[:60]
    total_members = MemberProfile.objects.filter(approved=True).count()
    return render(request, 'members/presenca/culto_manage.html', {
        'cultos':        cultos,
        'total_members': total_members,
        'type_choices':  Culto.TYPE_CHOICES,
    })


@staff_only
def culto_create(request):
    """Cria um culto e já abre a chamada."""
    if request.method == 'POST':
        culto_type = request.POST.get('culto_type', 'culto_domingo_manha')
        date_str   = request.POST.get('date', '').strip()
        title      = request.POST.get('title', '').strip()
        notes      = request.POST.get('notes', '').strip()

        if not date_str:
            messages.error(request, 'A data é obrigatória.')
            return render(request, 'members/presenca/culto_form.html', {
                'title': 'Novo Culto', 'type_choices': Culto.TYPE_CHOICES,
                'data': request.POST,
            })

        from datetime import date as _date
        try:
            date_obj = _date.fromisoformat(date_str)
        except ValueError:
            messages.error(request, 'Data inválida.')
            return render(request, 'members/presenca/culto_form.html', {
                'title': 'Novo Culto', 'type_choices': Culto.TYPE_CHOICES,
                'data': request.POST,
            })

        culto = Culto.objects.create(
            culto_type = culto_type,
            date       = date_obj,
            title      = title,
            notes      = notes,
            created_by = request.user,
        )

        # Já cria registros de presença para todos os membros aprovados
        members = MemberProfile.objects.filter(approved=True)
        Presenca.objects.bulk_create([
            Presenca(culto=culto, member=m, present=False, noted_by=request.user)
            for m in members
        ], ignore_conflicts=True)

        messages.success(request, f'Culto criado! Agora faça a chamada.')
        return redirect('culto_chamada', pk=culto.pk)

    return render(request, 'members/presenca/culto_form.html', {
        'title': 'Novo Culto', 'type_choices': Culto.TYPE_CHOICES,
    })


@staff_only
def culto_chamada(request, pk):
    """Tela de chamada — marca presenças rapidamente."""
    culto    = get_object_or_404(Culto, pk=pk)
    presencas = culto.presences.select_related(
        'member__user'
    ).order_by('member__user__first_name', 'member__user__last_name')

    # Garante que todos os membros aprovados estejam na chamada
    existing_ids = set(presencas.values_list('member_id', flat=True))
    new_members  = MemberProfile.objects.filter(approved=True).exclude(pk__in=existing_ids)
    if new_members.exists():
        Presenca.objects.bulk_create([
            Presenca(culto=culto, member=m, present=False, noted_by=request.user)
            for m in new_members
        ], ignore_conflicts=True)
        presencas = culto.presences.select_related('member__user').order_by(
            'member__user__first_name', 'member__user__last_name'
        )

    if request.method == 'POST':
        # IDs dos presentes enviados via checkbox
        present_ids = set(request.POST.getlist('present'))
        for p in presencas:
            p.present  = str(p.member_id) in present_ids
            p.noted_by = request.user
        Presenca.objects.bulk_update(presencas, ['present', 'noted_by'])

        # Visitantes
        visitor_count = int(request.POST.get('visitor_count', 0) or 0)
        visitor_names = request.POST.get('visitor_names', '').strip()
        culto.visitor_count = visitor_count
        culto.visitor_names = visitor_names
        culto.save(update_fields=['visitor_count', 'visitor_names'])

        count = presencas.filter(present=True).count()
        v_msg = f' + {visitor_count} visitante(s)' if visitor_count else ''
        messages.success(request, f'Chamada salva! {count} membro(s) presente(s){v_msg}.')
        return redirect('culto_chamada', pk=pk)

    presente_count = presencas.filter(present=True).count()
    total          = presencas.count()
    pct            = round(presente_count / total * 100) if total else 0

    return render(request, 'members/presenca/culto_chamada.html', {
        'culto':          culto,
        'presencas':      presencas,
        'presente_count': presente_count,
        'total':          total,
        'pct':            pct,
    })


@admin_only
def culto_delete(request, pk):
    culto = get_object_or_404(Culto, pk=pk)
    if request.method == 'POST':
        culto.delete()
        messages.success(request, 'Culto e presenças removidos.')
        return redirect('culto_manage')
    return render(request, 'members/confirm_delete.html',
                  {'object': culto, 'tipo': 'culto/reunião'})


@staff_only
def presenca_relatorio(request):
    """Relatório de frequência por membro com badges automáticos."""
    from django.db.models import Count, Q

    members = MemberProfile.objects.filter(approved=True).select_related('user')
    total_cultos = Culto.objects.count()

    relatorio = []
    for m in members:
        total_p    = Presenca.objects.filter(member=m).count()
        presentes  = Presenca.objects.filter(member=m, present=True).count()
        pct        = round(presentes / total_p * 100) if total_p else 0

        # Streak — cultos consecutivos mais recentes
        recentes = Presenca.objects.filter(member=m).select_related('culto').order_by('-culto__date')
        streak = 0
        for p in recentes:
            if p.present:
                streak += 1
            else:
                break

        # Badges de presença
        badges = []
        if pct >= 90 and presentes >= 10:
            badges.append({'icon': 'fa-medal', 'label': 'Presença Exemplar', 'color': '#C9A84C'})
        if streak >= 10:
            badges.append({'icon': 'fa-fire', 'label': f'{streak} seguidos', 'color': '#e74c3c'})
        if presentes >= 50:
            badges.append({'icon': 'fa-crown', 'label': '50+ presenças', 'color': '#6c3483'})
        if presentes >= 30:
            badges.append({'icon': 'fa-star', 'label': '30+ presenças', 'color': '#2475a8'})

        relatorio.append({
            'member':   m,
            'total':    total_p,
            'presentes': presentes,
            'pct':      pct,
            'streak':   streak,
            'badges':   badges,
            'nota10':   pct >= 85 and streak >= 4,
        })

    # Ordenar por % de presença (maior primeiro)
    relatorio.sort(key=lambda x: (-x['pct'], -x['presentes']))

    return render(request, 'members/presenca/presenca_relatorio.html', {
        'relatorio':    relatorio,
        'total_cultos': total_cultos,
    })


# ══════════════════════════════════════════════════════════
# ── Exportação de Dados ───────────────────────────────────
# ══════════════════════════════════════════════════════════
try:
    from .exports import (
        export_membros_xlsx, export_membros_csv,
        export_presencas_xlsx, export_presencas_csv,
        export_contribuicoes_xlsx, export_contribuicoes_csv,
        export_inscricoes_xlsx,
        export_visitantes_xlsx, export_visitantes_csv,
        export_aniversariantes_xlsx,
    )
    EXPORTS_AVAILABLE = True
except ImportError:
    EXPORTS_AVAILABLE = False


@admin_only
def exportar_centro(request):
    """Central de exportações — lista todas as opções disponíveis."""
    from core.models import Offering
    from events.models import EventRegistration
    from core.models import Visitor

    stats = {
        'membros':      MemberProfile.objects.filter(approved=True).count(),
        'cultos':       Culto.objects.count(),
        'contribuicoes': Offering.objects.count(),
        'eventos':      EventRegistration.objects.count(),
        'visitantes':   Visitor.objects.count(),
        'aniversariantes': MemberProfile.objects.filter(
            approved=True, birth_date__isnull=False).count(),
    }
    return render(request, 'members/exportar/centro.html', {'stats': stats})


@admin_only
def exportar_membros(request):
    fmt = request.GET.get('fmt', 'xlsx')
    qs  = MemberProfile.objects.filter(approved=True).select_related(
        'user').prefetch_related('member_ministries__ministry')

    # Filtros opcionais
    role = request.GET.get('role', '')
    bap  = request.GET.get('baptized', '')
    if role:
        qs = qs.filter(role=role)
    if bap == '1':
        qs = qs.filter(baptized=True)
    elif bap == '0':
        qs = qs.filter(baptized=False)

    if fmt == 'csv':
        return export_membros_csv(qs)
    return export_membros_xlsx(qs)


@admin_only
def exportar_presencas(request):
    fmt = request.GET.get('fmt', 'xlsx')
    from .models import Culto as CultoModel
    cultos  = CultoModel.objects.all()
    members = MemberProfile.objects.filter(approved=True)

    # Filtro por tipo de culto
    tipo = request.GET.get('tipo', '')
    if tipo:
        cultos = cultos.filter(culto_type=tipo)

    if fmt == 'csv':
        return export_presencas_csv(cultos, members)
    return export_presencas_xlsx(cultos, members)


@admin_only
def exportar_contribuicoes(request):
    from core.models import Offering
    fmt = request.GET.get('fmt', 'xlsx')
    qs  = Offering.objects.select_related('profile__user')

    tipo = request.GET.get('tipo', '')
    if tipo:
        qs = qs.filter(type=tipo)

    if fmt == 'csv':
        return export_contribuicoes_csv(qs)
    return export_contribuicoes_xlsx(qs)


@admin_only
def exportar_eventos(request):
    from events.models import EventRegistration
    qs = EventRegistration.objects.select_related('event', 'user')

    event_id = request.GET.get('event', '')
    if event_id:
        qs = qs.filter(event_id=event_id)

    return export_inscricoes_xlsx(qs)


@admin_only
def exportar_visitantes(request):
    from core.models import Visitor
    fmt = request.GET.get('fmt', 'xlsx')
    qs  = Visitor.objects.all()

    if fmt == 'csv':
        return export_visitantes_csv(qs)
    return export_visitantes_xlsx(qs)


@admin_only
def exportar_aniversariantes(request):
    from datetime import date

    qs = MemberProfile.objects.filter(
        approved=True, birth_date__isnull=False
    ).select_related('user')

    mes = request.GET.get('mes', '')
    if mes:
        qs = qs.filter(birth_date__month=int(mes))
    else:
        qs = qs.order_by('birth_date__month', 'birth_date__day')

    return export_aniversariantes_xlsx(qs)


# ══════════════════════════════════════════════════════════
# ── EBD — CRUD de Quiz ────────────────────────────────────
# ══════════════════════════════════════════════════════════
from ebd.models import Quiz, Question, Choice


@staff_only
def ebd_quiz_manage(request, lesson_pk):
    """Gerencia o quiz de uma lição — cria/edita perguntas e alternativas."""
    from ebd.models import EbdLesson as EbdLessonModel
    lesson = get_object_or_404(EbdLessonModel, pk=lesson_pk)

    # Cria o quiz se ainda não existir
    quiz, created = Quiz.objects.get_or_create(
        lesson=lesson,
        defaults={'passing_score': 70, 'max_attempts': 3, 'show_answers': True}
    )

    if request.method == 'POST':
        action = request.POST.get('action', '')

        # ── Salvar configurações do quiz ──
        if action == 'save_config':
            quiz.passing_score = int(request.POST.get('passing_score', 70))
            quiz.max_attempts  = int(request.POST.get('max_attempts', 3))
            quiz.show_answers  = 'show_answers' in request.POST
            quiz.save()
            messages.success(request, 'Configurações do quiz salvas!')

        # ── Adicionar pergunta ──
        elif action == 'add_question':
            text = request.POST.get('question_text', '').strip()
            explanation = request.POST.get('explanation', '').strip()
            if not text:
                messages.error(request, 'O enunciado da pergunta é obrigatório.')
            else:
                order = quiz.questions.count()
                q = Question.objects.create(
                    quiz=quiz, text=text,
                    explanation=explanation, order=order
                )
                # Criar 4 alternativas vazias por padrão
                for i in range(4):
                    Choice.objects.create(question=q, text='', order=i)
                messages.success(request, 'Pergunta adicionada!')

        # ── Salvar alternativas de uma pergunta ──
        elif action == 'save_question':
            q_id = request.POST.get('question_id')
            q    = get_object_or_404(Question, pk=q_id, quiz=quiz)
            q.text        = request.POST.get('question_text', '').strip()
            q.explanation = request.POST.get('explanation', '').strip()
            q.save()

            correct_id = request.POST.get('correct_choice')
            for choice in q.choices.all():
                choice.text       = request.POST.get(f'choice_text_{choice.pk}', '').strip()
                choice.is_correct = str(choice.pk) == correct_id
                choice.save()

            # Adicionar nova alternativa se solicitado
            new_choice = request.POST.get('new_choice_text', '').strip()
            if new_choice:
                Choice.objects.create(
                    question=q,
                    text=new_choice,
                    order=q.choices.count()
                )
            messages.success(request, 'Pergunta salva!')

        # ── Excluir alternativa ──
        elif action == 'delete_choice':
            c_id = request.POST.get('choice_id')
            Choice.objects.filter(pk=c_id, question__quiz=quiz).delete()

        # ── Excluir pergunta ──
        elif action == 'delete_question':
            q_id = request.POST.get('question_id')
            Question.objects.filter(pk=q_id, quiz=quiz).delete()
            messages.success(request, 'Pergunta removida.')

        # ── Reordenar perguntas ──
        elif action == 'reorder':
            order_ids = request.POST.getlist('order_ids')
            for idx, q_id in enumerate(order_ids):
                Question.objects.filter(pk=q_id, quiz=quiz).update(order=idx)

        return redirect('ebd_quiz_manage', lesson_pk=lesson_pk)

    questions = quiz.questions.prefetch_related('choices').order_by('order')
    return render(request, 'members/ebd/ebd_quiz_manage.html', {
        'lesson':    lesson,
        'quiz':      quiz,
        'questions': questions,
        'tri':       lesson.trimester,
    })


@admin_only
def ebd_quiz_delete(request, lesson_pk):
    """Remove o quiz inteiro de uma lição."""
    from ebd.models import EbdLesson as EbdLessonModel
    lesson = get_object_or_404(EbdLessonModel, pk=lesson_pk)
    if request.method == 'POST':
        Quiz.objects.filter(lesson=lesson).delete()
        messages.success(request, 'Quiz removido.')
        return redirect('ebd_lesson_manage', trimester_pk=lesson.trimester_id)
    return render(request, 'members/confirm_delete.html',
                  {'object': lesson, 'tipo': f'quiz da lição "{lesson.title}"'})


# ══════════════════════════════════════════════════════════
# ── Busca Global ──────────────────────────────────────────
# ══════════════════════════════════════════════════════════
import json as _json
from django.http import JsonResponse
from django.db.models import Q
from events.models import Event
from core.models import Devotional, MediaItem, PhotoAlbum

@login_required
def search(request):
    q = request.GET.get('q', '').strip()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    igreja = request.igreja

    if not q or len(q) < 2:
        if is_ajax:
            return JsonResponse({'results': []})
        return render(request, 'members/search.html', {'q': q, 'results': {}})

    results = {}

    # Membros (só staff vê)
    if request.user.is_staff or request.user.is_superuser:
        membros = MemberProfile.objects.filter(
            igreja=igreja
        ).filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q)
        ).select_related('user')[:5]
        if membros:
            results['Membros'] = [
                {'title': m.full_name, 'subtitle': m.user.email,
                 'icon': 'fa-user', 'url': f'/membros/gerenciar-membros/{m.pk}/editar/'}
                for m in membros
            ]

    # Eventos
    eventos = Event.objects.filter(
        igreja=igreja, published=True
    ).filter(
        Q(title__icontains=q) | Q(description__icontains=q)
    )[:5]
    if eventos:
        results['Eventos'] = [
            {'title': e.title, 'subtitle': e.display_date,
             'icon': 'fa-calendar', 'url': e.get_absolute_url()}
            for e in eventos
        ]

    # Conteúdos
    conteudos = ExclusiveContent.objects.filter(
        igreja=igreja, published=True
    ).filter(
        Q(title__icontains=q) | Q(body__icontains=q)
    )[:5]
    if conteudos:
        results['Conteúdos'] = [
            {'title': c.title, 'subtitle': c.get_content_type_display(),
             'icon': 'fa-book-open', 'url': f'/membros/conteudos/{c.pk}/'}
            for c in conteudos
        ]

    # Devocionais
    devocionais = Devotional.objects.filter(
        igreja=igreja, published=True
    ).filter(
        Q(title__icontains=q) | Q(verse__icontains=q)
    )[:5]
    if devocionais:
        results['Devocionais'] = [
            {'title': d.title, 'subtitle': d.verse,
             'icon': 'fa-sun', 'url': '#'}
            for d in devocionais
        ]

    # Mídia
    midias = MediaItem.objects.filter(
        igreja=igreja, published=True
    ).filter(
        Q(title__icontains=q) | Q(speaker__icontains=q)
    )[:5]
    if midias:
        results['Midiateca'] = [
            {'title': m.title, 'subtitle': m.speaker or m.get_media_type_display(),
             'icon': 'fa-photo-film', 'url': m.get_absolute_url()}
            for m in midias
        ]

    # Álbuns
    albuns = PhotoAlbum.objects.filter(
        igreja=igreja, published=True
    ).filter(
        Q(title__icontains=q) | Q(description__icontains=q)
    )[:5]
    if albuns:
        results['Galeria'] = [
            {'title': a.title, 'subtitle': a.event_date.strftime('%d/%m/%Y') if a.event_date else '',
             'icon': 'fa-images', 'url': '#'}
            for a in albuns
        ]

    if is_ajax:
        # Retorna só os 3 primeiros de cada categoria para o dropdown
        dropdown = []
        for categoria, items in results.items():
            for item in items[:3]:
                item['categoria'] = categoria
                dropdown.append(item)
        return JsonResponse({'results': dropdown[:12], 'q': q})

    return render(request, 'members/search.html', {'q': q, 'results': results})