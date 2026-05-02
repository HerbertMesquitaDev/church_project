"""
Utilitários de e-mail para notificações da igreja.
Usa django.core.mail com templates HTML embutidos.
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils.html import strip_tags


def _base_html(title, body_html, church_name, church_email='', unsubscribe_url=''):
    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body {{ font-family: Arial, sans-serif; background:#f4f1eb; margin:0; padding:0; }}
  .wrap {{ max-width:560px; margin:32px auto; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,.08); }}
  .header {{ background:#1a2340; padding:28px 32px; text-align:center; }}
  .header h1 {{ color:#C9A84C; font-size:22px; margin:0; letter-spacing:.05em; }}
  .header p {{ color:rgba(255,255,255,.6); font-size:13px; margin:6px 0 0; }}
  .body {{ padding:32px; color:#444; line-height:1.7; }}
  .body h2 {{ color:#1a2340; font-size:18px; margin:0 0 12px; }}
  .body p {{ margin:0 0 14px; }}
  .btn {{ display:inline-block; background:#C9A84C; color:#1a2340 !important; text-decoration:none; padding:12px 28px; border-radius:6px; font-weight:bold; font-size:14px; margin:8px 0; }}
  .info-box {{ background:#f8f5ef; border-left:4px solid #C9A84C; border-radius:4px; padding:14px 18px; margin:16px 0; }}
  .info-box p {{ margin:4px 0; font-size:14px; color:#555; }}
  .info-box strong {{ color:#1a2340; }}
  .footer {{ background:#f4f1eb; padding:20px 32px; text-align:center; font-size:12px; color:#999; }}
  .footer a {{ color:#C9A84C; text-decoration:none; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <h1>{church_name}</h1>
    <p>Portal da Igreja</p>
  </div>
  <div class="body">
    {body_html}
  </div>
  <div class="footer">
    <p>Você está recebendo este e-mail porque é membro cadastrado em {church_name}.</p>
    {'<p><a href="' + unsubscribe_url + '">Gerenciar preferências de notificação</a></p>' if unsubscribe_url else ''}
    {'<p>' + church_email + '</p>' if church_email else ''}
  </div>
</div>
</body></html>"""


def send_notification(subject, body_html, recipient_list, church_name='Igreja', church_email='', unsubscribe_url=''):
    """Envia e-mail HTML com fallback texto simples."""
    if not recipient_list:
        return
    html = _base_html(subject, body_html, church_name, church_email, unsubscribe_url)
    text = strip_tags(body_html)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@igreja.com.br')
    for recipient in recipient_list:
        try:
            msg = EmailMultiAlternatives(subject, text, from_email, [recipient])
            msg.attach_alternative(html, 'text/html')
            msg.send()
        except Exception as e:
            print(f'[notify] Erro ao enviar para {recipient}: {e}')


def get_site():
    from core.models import SiteSettings
    return SiteSettings.get_settings()


def get_members_with_pref(pref_field):
    """Retorna lista de e-mails de membros aprovados com determinada preferência ativa."""
    from members.models import MemberProfile
    profiles = MemberProfile.objects.filter(
        approved=True, **{pref_field: True}
    ).select_related('user').exclude(user__email='')
    return [p.user.email for p in profiles if p.user.email]
