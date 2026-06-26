"""
Signals:
- Notificações por e-mail (eventos, avisos urgentes, visitantes)
- Sincronização de is_staff com role='admin' + approved=True
"""
from django.contrib.auth import user_logged_in
from django.contrib.sessions.models import Session
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .role_utils import sync_user_flags


def _clear_other_sessions(user, current_session_key=None):
    """Remove outras sessões autenticadas do mesmo usuário."""
    if not user.is_authenticated:
        return

    user_id = str(user.pk)

    for session in Session.objects.all().iterator():
        if current_session_key and session.session_key == current_session_key:
            continue

        try:
            decoded = session.get_decoded()
        except Exception:
            continue

        if decoded.get('_auth_user_id') == user_id:
            session.delete()


@receiver(user_logged_in)
def enforce_single_session(sender, request, user, **kwargs):
    current_session_key = getattr(getattr(request, 'session', None), 'session_key', None)
    _clear_other_sessions(user, current_session_key=current_session_key)


@receiver(post_save, sender='members.MemberProfile')
def sync_staff_status(sender, instance, **kwargs):
    """
    Garante que is_staff reflita role='admin' + approved=True.
    Superusuários nunca são afetados.
    """
    if instance.user.is_superuser:
        return
    sync_user_flags(instance.user, instance.role, instance.approved)
    User.objects.filter(pk=instance.user_id).update(
        is_staff=instance.user.is_staff,
        is_superuser=instance.user.is_superuser,
    )


@receiver(post_save, sender='events.Event')
def notify_new_event(sender, instance, created, **kwargs):
    if not created:
        return
    if not instance.published:
        return
    try:
        from .email_utils import send_notification, get_members_with_pref, get_site
        from django.utils.formats import date_format

        site      = get_site()
        recipients = get_members_with_pref('notify_events')
        if not recipients:
            return

        date_str = date_format(instance.date, 'd/m/Y H:i')
        location = f'<br><strong>Local:</strong> {instance.location}' if getattr(instance, 'location', '') else ''
        btn_url  = f'http://seusite.com.br/eventos/{instance.slug}/' if instance.slug else ''
        btn      = f'<a href="{btn_url}" class="btn">Ver evento</a>' if btn_url else ''

        body = f"""
<h2>Novo evento: {instance.title}</h2>
<p>Um novo evento foi publicado e gostaríamos que você soubesse!</p>
<div class="info-box">
  <p><strong>Evento:</strong> {instance.title}</p>
  <p><strong>Data:</strong> {date_str}{location}</p>
  {'<p><strong>Descrição:</strong> ' + instance.description[:200] + '</p>' if getattr(instance, 'description', '') else ''}
</div>
{btn}
<p>Esperamos vê-lo(a) lá!</p>
"""
        send_notification(
            subject=f'Novo evento: {instance.title}',
            body_html=body,
            recipient_list=recipients,
            church_name=site.church_name,
            church_email=site.email,
        )
    except Exception as e:
        print(f'[signal] notify_new_event error: {e}')


@receiver(post_save, sender='members.Notice')
def notify_urgent_notice(sender, instance, created, **kwargs):
    if not created:
        return
    if not instance.published:
        return
    if instance.priority != 'urgent':
        return
    try:
        from .email_utils import send_notification, get_members_with_pref, get_site

        site       = get_site()
        recipients = get_members_with_pref('notify_notices')
        if not recipients:
            return

        body = f"""
<h2>⚠️ Aviso Urgente</h2>
<div class="info-box">
  <p><strong>{instance.title}</strong></p>
  <p>{instance.body}</p>
</div>
<p>Este é um aviso urgente de {site.church_name}. Por favor, fique atento(a).</p>
"""
        send_notification(
            subject=f'[URGENTE] {instance.title}',
            body_html=body,
            recipient_list=recipients,
            church_name=site.church_name,
            church_email=site.email,
        )
    except Exception as e:
        print(f'[signal] notify_urgent_notice error: {e}')


@receiver(post_save, sender='core.Visitor')
def notify_new_visitor(sender, instance, created, **kwargs):
    if not created:
        return
    try:
        from .email_utils import send_notification, get_site

        site = get_site()
        if not site.notification_email:
            return

        ministry = f'<p><strong>Ministério de interesse:</strong> {instance.ministry_interest}</p>' \
                   if instance.wants_ministry and instance.ministry_interest else \
                   ('<p><strong>Interesse em ministério:</strong> Sim</p>' if instance.wants_ministry else '')

        body = f"""
<h2>Novo visitante cadastrado</h2>
<p>Um novo visitante preencheu o formulário de visita no site.</p>
<div class="info-box">
  <p><strong>Nome:</strong> {instance.name}</p>
  {'<p><strong>E-mail:</strong> ' + instance.email + '</p>' if instance.email else ''}
  {'<p><strong>Telefone:</strong> ' + instance.phone + '</p>' if instance.phone else ''}
  <p><strong>Visitou em:</strong> {instance.visit_date.strftime('%d/%m/%Y')}</p>
  <p><strong>Como conheceu:</strong> {instance.get_how_found_display()}</p>
  {ministry}
  {'<p><strong>Mensagem:</strong> ' + instance.message + '</p>' if instance.message else ''}
</div>
<p>Acesse o painel para registrar o contato com este visitante.</p>
"""
        send_notification(
            subject=f'Novo visitante: {instance.name}',
            body_html=body,
            recipient_list=[site.notification_email],
            church_name=site.church_name,
            church_email=site.email,
        )
    except Exception as e:
        print(f'[signal] notify_new_visitor error: {e}')
