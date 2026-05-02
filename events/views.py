from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Event, Category, EventRegistration

PER_PAGE = 9


def event_list(request):
    category_id = request.GET.get('categoria')
    period      = request.GET.get('periodo', 'upcoming')

    events = Event.objects.filter(published=True)
    if category_id:
        events = events.filter(category_id=category_id)
    if period == 'past':
        events = events.filter(date__lt=timezone.now()).order_by('-date')
    else:
        events = events.filter(date__gte=timezone.now()).order_by('date')

    paginator  = Paginator(events, PER_PAGE)
    page_obj   = paginator.get_page(request.GET.get('page'))
    categories = Category.objects.all()
    featured   = Event.objects.filter(
        featured=True, published=True, date__gte=timezone.now()).first()

    return render(request, 'events/event_list.html', {
        'page_obj':          page_obj,
        'events':            page_obj,
        'categories':        categories,
        'selected_category': category_id,
        'period':            period,
        'featured':          featured,
    })


def event_detail(request, slug):
    event   = get_object_or_404(Event, slug=slug, published=True)
    related = Event.objects.filter(
        published=True, date__gte=timezone.now()
    ).exclude(pk=event.pk).order_by('date')[:3]

    user_registration = None
    if request.user.is_authenticated:
        user_registration = EventRegistration.objects.filter(
            event=event, user=request.user
        ).first()

    confirmed_count = event.registrations.filter(status='confirmed').count()
    waitlist_count  = event.registrations.filter(status='waitlist').count()

    return render(request, 'events/event_detail.html', {
        'event':             event,
        'related':           related,
        'user_registration': user_registration,
        'confirmed_count':   confirmed_count,
        'waitlist_count':    waitlist_count,
    })


@login_required
def event_register(request, slug):
    event = get_object_or_404(Event, slug=slug, published=True)

    if not event.requires_registration:
        messages.warning(request, 'Este evento não requer inscrição.')
        return redirect('event_detail', slug=slug)

    if event.is_past:
        messages.warning(request, 'Este evento já passou.')
        return redirect('event_detail', slug=slug)

    if event.registration_deadline and timezone.now() > event.registration_deadline:
        messages.warning(request, 'O prazo de inscrição para este evento encerrou.')
        return redirect('event_detail', slug=slug)

    # Check existing
    existing = EventRegistration.objects.filter(event=event, user=request.user).first()
    if existing:
        if existing.status == 'cancelled':
            # Reactivate
            if event.is_full:
                existing.status = 'waitlist'
                existing.save()
                messages.info(request, 'Evento lotado. Você foi adicionado à lista de espera.')
            else:
                existing.status = 'confirmed'
                existing.save()
                messages.success(request, 'Inscrição reativada com sucesso!')
        else:
            messages.info(request, 'Você já está inscrito neste evento.')
        return redirect('event_detail', slug=slug)

    # New registration
    if event.is_full:
        status = 'waitlist'
        msg = 'Evento lotado. Você foi adicionado à lista de espera!'
    else:
        status = 'confirmed'
        msg = 'Inscrição realizada com sucesso!'

    EventRegistration.objects.create(event=event, user=request.user, status=status)
    messages.success(request, msg)

    # Email confirmation
    try:
        from members.email_utils import send_notification, get_site
        site = get_site()
        body = f"""
<h2>{'Inscrição confirmada' if status == 'confirmed' else 'Lista de espera'}: {event.title}</h2>
<p>{'Sua inscrição foi confirmada!' if status == 'confirmed' else 'Você entrou na lista de espera.'}</p>
<div class="info-box">
  <p><strong>Evento:</strong> {event.title}</p>
  <p><strong>Data:</strong> {event.display_date}</p>
  {'<p><strong>Local:</strong> ' + event.location + '</p>' if event.location else ''}
</div>
<p>Nos vemos lá!</p>
"""
        send_notification(
            subject=f'Inscrição: {event.title}',
            body_html=body,
            recipient_list=[request.user.email],
            church_name=site.church_name,
        )
    except Exception:
        pass

    return redirect('event_detail', slug=slug)


@login_required
def event_cancel_registration(request, slug):
    event = get_object_or_404(Event, slug=slug, published=True)
    reg   = get_object_or_404(EventRegistration, event=event, user=request.user)

    if request.method == 'POST':
        was_confirmed = reg.status == 'confirmed'
        reg.status = 'cancelled'
        reg.save()
        messages.success(request, 'Inscrição cancelada.')

        # Promote first waitlist person
        if was_confirmed:
            next_reg = EventRegistration.objects.filter(
                event=event, status='waitlist'
            ).order_by('created_at').first()
            if next_reg:
                next_reg.status = 'confirmed'
                next_reg.save()
                try:
                    from members.email_utils import send_notification, get_site
                    site = get_site()
                    body = f"""
<h2>Vaga disponível: {event.title}</h2>
<p>Boas notícias! Uma vaga foi liberada e sua inscrição foi confirmada.</p>
<div class="info-box">
  <p><strong>Evento:</strong> {event.title}</p>
  <p><strong>Data:</strong> {event.display_date}</p>
  {'<p><strong>Local:</strong> ' + event.location + '</p>' if event.location else ''}
</div>
"""
                    send_notification(
                        subject=f'Vaga confirmada: {event.title}',
                        body_html=body,
                        recipient_list=[next_reg.user.email],
                        church_name=site.church_name,
                    )
                except Exception:
                    pass
        return redirect('event_detail', slug=slug)

    return render(request, 'events/event_cancel.html', {'event': event, 'reg': reg})


# ── Staff: list all registrations for an event ────────────
@login_required
def event_registrations_list(request, slug):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('event_detail', slug=slug)
    event         = get_object_or_404(Event, slug=slug)
    confirmed     = event.registrations.filter(status='confirmed').select_related('user')
    waitlist      = event.registrations.filter(status='waitlist').select_related('user')
    cancelled     = event.registrations.filter(status='cancelled').select_related('user')
    return render(request, 'events/event_registrations.html', {
        'event':     event,
        'confirmed': confirmed,
        'waitlist':  waitlist,
        'cancelled': cancelled,
    })
