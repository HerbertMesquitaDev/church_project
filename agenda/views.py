from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Q
import json
from datetime import date, timedelta

from members.views import members_only, staff_only, superuser_only
from .models import Booking, Location
from .forms import BookingForm, BookingStatusForm, LocationForm


# ── Agenda principal (calendário mensal) ──────────────────
@members_only
def agenda_view(request):
    today = date.today()
    # mês exibido
    year  = int(request.GET.get('year',  today.year))
    month = int(request.GET.get('month', today.month))

    # navegação mês anterior / próximo
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    prev_month = first_day - timedelta(days=1)
    next_month = last_day + timedelta(days=1)

    # agendamentos do mês
    bookings = Booking.objects.filter(
        date__year=year,
        date__month=month,
    ).select_related('location', 'responsible')

    # não-admin vê só aprovados + os próprios
    if not (request.user.is_staff or request.user.is_superuser):
        bookings = bookings.filter(
            Q(status='approved') | Q(responsible=request.user)
        )

    bookings = bookings.order_by('date', 'start_time')

    # agrupar por dia para o calendário
    bookings_by_day = {}
    for b in bookings:
        bookings_by_day.setdefault(b.date.day, []).append(b)

    # montar semanas do mês
    calendar_weeks = []
    # dia da semana em que começa o mês (0=seg, 6=dom → ajustar para dom=0)
    start_weekday = first_day.weekday()  # 0=seg
    # usamos domingo como primeiro dia da semana
    start_weekday = (start_weekday + 1) % 7  # 0=dom

    day_cursor = 1
    week = [None] * start_weekday
    while day_cursor <= last_day.day:
        week.append(day_cursor)
        if len(week) == 7:
            calendar_weeks.append(week)
            week = []
        day_cursor += 1
    if week:
        week += [None] * (7 - len(week))
        calendar_weeks.append(week)

    locations = Location.objects.filter(active=True)

    context = {
        'year': year, 'month': month,
        'month_name': first_day.strftime('%B %Y'),
        'calendar_weeks': calendar_weeks,
        'bookings_by_day': bookings_by_day,
        'bookings': bookings,
        'today': today,
        'prev_year': prev_month.year, 'prev_month': prev_month.month,
        'next_year': next_month.year, 'next_month': next_month.month,
        'locations': locations,
        'selected_location': request.GET.get('location', ''),
        'selected_date': request.GET.get('date', ''),
    }
    return render(request, 'agenda/agenda.html', context)


# ── Lista de agendamentos ─────────────────────────────────
@members_only
def booking_list(request):
    bookings = Booking.objects.select_related('location', 'responsible').all()

    # filtros
    location_id = request.GET.get('location')
    status      = request.GET.get('status')
    date_from   = request.GET.get('date_from')
    date_to     = request.GET.get('date_to')

    if location_id:
        bookings = bookings.filter(location_id=location_id)
    if status:
        bookings = bookings.filter(status=status)
    if date_from:
        bookings = bookings.filter(date__gte=date_from)
    if date_to:
        bookings = bookings.filter(date__lte=date_to)

    # membros comuns veem apenas aprovados + os próprios
    if not (request.user.is_staff or request.user.is_superuser):
        bookings = bookings.filter(
            Q(status='approved') | Q(responsible=request.user)
        )

    bookings = bookings.order_by('date', 'start_time')

    locations = Location.objects.filter(active=True)
    context = {
        'bookings': bookings,
        'locations': locations,
        'status_choices': Booking.STATUS_CHOICES,
        'filter_location': location_id or '',
        'filter_status': status or '',
        'filter_date_from': date_from or '',
        'filter_date_to': date_to or '',
    }
    return render(request, 'agenda/booking_list.html', context)


# ── Criar agendamento ─────────────────────────────────────
@members_only
def booking_create(request):
    initial = {}
    if request.GET.get('date'):
        initial['date'] = request.GET.get('date')
    if request.GET.get('location'):
        initial['location'] = request.GET.get('location')

    form = BookingForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        booking = form.save(commit=False)
        booking.responsible = request.user
        # superuser/staff: auto-aprovado
        if request.user.is_staff or request.user.is_superuser:
            booking.status = 'approved'
            booking.approved_by = request.user
            booking.approved_at = timezone.now()
        booking.save()
        messages.success(request,
            f"Agendamento '{booking.title}' criado com sucesso!" +
            ("" if booking.status == 'approved' else " Aguardando aprovação da liderança.")
        )
        return redirect('agenda_view')

    locations = Location.objects.filter(active=True)
    context = {'form': form, 'locations': locations, 'title': 'Novo Agendamento'}
    return render(request, 'agenda/booking_form.html', context)


# ── Editar agendamento ────────────────────────────────────
@members_only
def booking_edit(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    # apenas responsável, staff ou superuser podem editar
    if not (request.user == booking.responsible or
            request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Você não tem permissão para editar este agendamento.')
        return redirect('booking_list')

    form = BookingForm(request.POST or None, instance=booking)
    if request.method == 'POST' and form.is_valid():
        updated = form.save(commit=False)
        # se editado por não-staff, volta para pendente
        if not (request.user.is_staff or request.user.is_superuser):
            updated.status = 'pending'
        updated.save()
        messages.success(request, f"Agendamento '{updated.title}' atualizado.")
        return redirect('booking_list')

    context = {'form': form, 'booking': booking, 'title': 'Editar Agendamento'}
    return render(request, 'agenda/booking_form.html', context)


# ── Detalhe do agendamento ────────────────────────────────
@members_only
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    # membros comuns só veem aprovados ou os próprios
    if not (request.user.is_staff or request.user.is_superuser):
        if booking.status != 'approved' and booking.responsible != request.user:
            messages.error(request, 'Acesso negado.')
            return redirect('booking_list')

    status_form = None
    if request.user.is_staff or request.user.is_superuser:
        status_form = BookingStatusForm(request.POST or None, instance=booking)
        if request.method == 'POST' and status_form.is_valid():
            b = status_form.save(commit=False)
            if b.status == 'approved':
                b.approved_by = request.user
                b.approved_at = timezone.now()
            b.save()
            messages.success(request, f"Status atualizado para: {b.get_status_display()}")
            return redirect('booking_detail', pk=pk)

    context = {'booking': booking, 'status_form': status_form}
    return render(request, 'agenda/booking_detail.html', context)


# ── Cancelar / Excluir agendamento ────────────────────────
@members_only
def booking_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if not (request.user == booking.responsible or
            request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Você não tem permissão.')
        return redirect('booking_list')

    if request.method == 'POST':
        title = booking.title
        # membros comuns: cancelar; staff/admin: excluir
        if request.user.is_staff or request.user.is_superuser:
            booking.delete()
            messages.success(request, f"Agendamento '{title}' excluído.")
        else:
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, f"Agendamento '{title}' cancelado.")
        return redirect('booking_list')

    return render(request, 'agenda/booking_confirm_delete.html', {'booking': booking})


# ── Gerenciar locais (superuser) ──────────────────────────
@superuser_only
def location_manage(request):
    locations = Location.objects.all().order_by('name')
    return render(request, 'agenda/location_manage.html', {'locations': locations})


@superuser_only
def location_create(request):
    form = LocationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Local criado com sucesso.")
        return redirect('location_manage')
    return render(request, 'agenda/location_form.html',
                  {'form': form, 'title': 'Novo Local'})


@superuser_only
def location_edit(request, pk):
    location = get_object_or_404(Location, pk=pk)
    form = LocationForm(request.POST or None, instance=location)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"Local '{location.name}' atualizado.")
        return redirect('location_manage')
    return render(request, 'agenda/location_form.html',
                  {'form': form, 'location': location, 'title': 'Editar Local'})


@superuser_only
def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == 'POST':
        name = location.name
        location.delete()
        messages.success(request, f"Local '{name}' excluído.")
        return redirect('location_manage')
    return render(request, 'agenda/location_confirm_delete.html',
                  {'location': location})


# ── API: verificar disponibilidade (AJAX) ─────────────────
@members_only
def check_availability(request):
    """Retorna JSON com conflitos para o local/data/horário informados."""
    location_id = request.GET.get('location')
    date_str    = request.GET.get('date')
    start       = request.GET.get('start')
    end         = request.GET.get('end')
    exclude_pk  = request.GET.get('exclude')

    if not all([location_id, date_str, start, end]):
        return JsonResponse({'available': True, 'conflicts': []})

    try:
        from datetime import time as dtime
        sh, sm = map(int, start.split(':'))
        eh, em = map(int, end.split(':'))
        start_t = dtime(sh, sm)
        end_t   = dtime(eh, em)
    except (ValueError, AttributeError):
        return JsonResponse({'available': True, 'conflicts': []})

    conflicts = Booking.objects.filter(
        location_id=location_id,
        date=date_str,
        status__in=['pending', 'approved'],
        start_time__lt=end_t,
        end_time__gt=start_t,
    )
    if exclude_pk:
        conflicts = conflicts.exclude(pk=exclude_pk)

    data = []
    for c in conflicts:
        data.append({
            'id': c.pk,
            'title': c.title,
            'start': c.start_time.strftime('%H:%M'),
            'end': c.end_time.strftime('%H:%M'),
            'status': c.get_status_display(),
        })

    return JsonResponse({'available': len(data) == 0, 'conflicts': data})
