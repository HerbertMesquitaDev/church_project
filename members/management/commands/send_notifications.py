"""
Comando agendado para notificações periódicas.
Configure no cron para rodar todo dia às 8h:
  0 8 * * * cd /caminho/projeto && .venv/bin/python manage.py send_notifications

Envia:
  - Lembrete de eventos amanhã      → membros com notify_reminders=True
  - Parabéns de aniversário do dia   → aniversariante + admin
  - Devocional do dia                → membros com notify_devotional=True
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Envia notificações periódicas por e-mail'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando envio de notificações...')
        sent = 0
        sent += self._send_event_reminders()
        sent += self._send_birthdays()
        sent += self._send_devotional()
        self.stdout.write(self.style.SUCCESS(f'Concluído. {sent} e-mail(s) enviado(s).'))

    def _send_event_reminders(self):
        from datetime import date, timedelta
        from events.models import Event
        from members.email_utils import send_notification, get_members_with_pref, get_site

        tomorrow  = date.today() + timedelta(days=1)
        events    = Event.objects.filter(date__date=tomorrow, published=True)
        if not events.exists():
            return 0

        site       = get_site()
        recipients = get_members_with_pref('notify_reminders')
        if not recipients:
            return 0

        count = 0
        for event in events:
            location = f'<p><strong>Local:</strong> {event.location}</p>' if getattr(event, 'location', '') else ''
            body = f"""
<h2>Lembrete: {event.title} é amanhã!</h2>
<p>Não esqueça — você tem um evento amanhã.</p>
<div class="info-box">
  <p><strong>Evento:</strong> {event.title}</p>
  <p><strong>Data:</strong> {event.date.strftime('%d/%m/%Y às %H:%M')}</p>
  {location}
</div>
<p>Esperamos vê-lo(a) lá!</p>
"""
            send_notification(
                subject=f'Lembrete: {event.title} é amanhã!',
                body_html=body,
                recipient_list=recipients,
                church_name=site.church_name,
                church_email=site.email,
            )
            count += len(recipients)
            self.stdout.write(f'  Lembrete "{event.title}": {len(recipients)} destinatário(s)')
        return count

    def _send_birthdays(self):
        from datetime import date
        from members.models import MemberProfile
        from members.email_utils import send_notification, get_site

        site  = get_site()
        today = date.today()

        birthdays = MemberProfile.objects.filter(
            approved=True,
            birth_date__month=today.month,
            birth_date__day=today.day,
        ).select_related('user').exclude(user__email='')

        count = 0
        for profile in birthdays:
            body = f"""
<h2>Parabéns, {profile.full_name}!</h2>
<p>Toda a família de {site.church_name} deseja a você um feliz aniversário!</p>
<div class="info-box">
  <p>Que Deus continue abençoando sua vida abundantemente.</p>
  <p><em>"O Senhor te abençoe e te guarde."</em> — Números 6:24</p>
</div>
<p>Com carinho,<br><strong>{site.church_name}</strong></p>
"""
            send_notification(
                subject=f'Feliz Aniversário, {profile.first_name or profile.full_name}!',
                body_html=body,
                recipient_list=[profile.user.email],
                church_name=site.church_name,
                church_email=site.email,
            )
            count += 1
            self.stdout.write(f'  Aniversário: {profile.full_name}')

        if birthdays.exists() and site.notification_email:
            names = ', '.join(p.full_name for p in birthdays)
            body_admin = f"""
<h2>Aniversariantes de hoje</h2>
<p>Os seguintes membros fazem aniversário hoje ({today.strftime('%d/%m')}):</p>
<div class="info-box"><p>{names}</p></div>
<p>Não esqueça de parabenizá-los pessoalmente!</p>
"""
            send_notification(
                subject=f'Aniversariantes do dia: {today.strftime("%d/%m")}',
                body_html=body_admin,
                recipient_list=[site.notification_email],
                church_name=site.church_name,
            )
        return count

    def _send_devotional(self):
        from datetime import date
        from core.models import Devotional
        from members.email_utils import send_notification, get_members_with_pref, get_site

        site       = get_site()
        today      = date.today()
        devotional = Devotional.objects.filter(published=True, pub_date=today).first()
        if not devotional:
            return 0

        recipients = get_members_with_pref('notify_devotional')
        if not recipients:
            return 0

        body = f"""
<h2>{devotional.title}</h2>
<div class="info-box">
  <p><strong>{devotional.verse}</strong></p>
  <p><em>"{devotional.verse_text}"</em></p>
</div>
<p>{devotional.body[:400]}{'...' if len(devotional.body) > 400 else ''}</p>
"""
        send_notification(
            subject=f'Devocional do dia: {devotional.title}',
            body_html=body,
            recipient_list=recipients,
            church_name=site.church_name,
            church_email=site.email,
        )
        self.stdout.write(f'  Devocional "{devotional.title}": {len(recipients)} destinatário(s)')
        return len(recipients)
