"""
emails.py — Envio de e-mails transacionais do portal da igreja.
Todas as funções usam fail_silently=True para não derrubar a requisição
em caso de falha no servidor SMTP.
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def _from():
    return getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@adbrsede.com.br')


def _site_name():
    try:
        from core.models import SiteSettings
        return SiteSettings.get_settings().church_name or 'Portal da Igreja Assembleia de Deus no Brasil- Sede'
    except Exception:
        return 'Portal da Igreja Assembleia de Deus no Brasil- Sede'


def _base_url():
    try:
        from core.models import SocialConfig
        url = SocialConfig.get_config().site_base_url or ''
        return url.rstrip('/')
    except Exception:
        return ''


# ── Reset de senha ────────────────────────────────────────────────────────────

def send_password_reset(user, token):
    """Envia link de redefinição de senha ao membro."""
    base   = _base_url()
    link   = f"{base}/membros/redefinir-senha/{token}/"
    name   = user.first_name or user.username
    church = _site_name()

    subject = f"[{church}] Redefinição de senha"
    body = (
        f"Olá, {name}!\n\n"
        f"Recebemos uma solicitação de redefinição de senha para sua conta no {church}.\n\n"
        f"Clique no link abaixo para criar uma nova senha:\n"
        f"{link}\n\n"
        f"Este link é válido por 24 horas.\n\n"
        f"Se você não solicitou a redefinição, ignore este e-mail. Sua senha não será alterada.\n\n"
        f"— {church}"
    )
    send_mail(subject, body, _from(), [user.email], fail_silently=True)


# ── Aprovação de membro ───────────────────────────────────────────────────────

def send_member_approved(user, role_display):
    """Avisa o membro que seu cadastro foi aprovado."""
    name   = user.first_name or user.username
    church = _site_name()
    base   = _base_url()

    subject = f"[{church}] Cadastro aprovado!"
    body = (
        f"Olá, {name}! Bem-vindo(a) à família! 🎉\n\n"
        f"Seu cadastro no portal {church} foi aprovado.\n"
        f"Seu perfil: {role_display}\n\n"
        f"Acesse agora:\n"
        f"{base}/membros/login/\n\n"
        f"— {church}"
    )
    send_mail(subject, body, _from(), [user.email], fail_silently=True)


def send_member_rejected(user):
    """Avisa o membro que seu cadastro foi rejeitado."""
    name   = user.first_name or user.username
    church = _site_name()

    subject = f"[{church}] Atualização sobre seu cadastro"
    body = (
        f"Olá, {name}.\n\n"
        f"Infelizmente seu cadastro no portal {church} não foi aprovado no momento.\n"
        f"Entre em contato com a secretaria da igreja para mais informações.\n\n"
        f"— {church}"
    )
    send_mail(subject, body, _from(), [user.email], fail_silently=True)


# ── Notificações para o admin ─────────────────────────────────────────────────

def _admin_emails():
    """Retorna lista de e-mails dos admins cadastrados."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    emails = list(
        User.objects.filter(is_superuser=True, is_active=True)
        .exclude(email='')
        .values_list('email', flat=True)
    )
    # Fallback para o e-mail configurado no settings
    admin_email = getattr(settings, 'SERVER_EMAIL', '')
    if admin_email and admin_email not in emails:
        emails.append(admin_email)
    return emails


def notify_admin_new_member(profile):
    """Notifica admins quando um novo membro aguarda aprovação."""
    admins = _admin_emails()
    if not admins:
        return
    church = _site_name()
    base   = _base_url()
    name   = profile.full_name or profile.user.username

    subject = f"[{church}] Novo cadastro aguardando aprovação"
    body = (
        f"Um novo membro se cadastrou no portal e aguarda aprovação:\n\n"
        f"Nome: {name}\n"
        f"E-mail: {profile.user.email}\n"
        f"Usuário: {profile.user.username}\n\n"
        f"Acesse o painel para aprovar ou rejeitar:\n"
        f"{base}/membros/gerenciar-membros/\n\n"
        f"— Sistema {church}"
    )
    send_mail(subject, body, _from(), admins, fail_silently=True)


def notify_admin_new_prayer(prayer_request):
    """Notifica admins sobre novo pedido de oração."""
    admins = _admin_emails()
    if not admins:
        return
    church = _site_name()
    base   = _base_url()
    user   = prayer_request.user
    name   = user.get_full_name() or user.username

    subject = f"[{church}] Novo pedido de oração"
    body = (
        f"Um membro enviou um pedido de oração:\n\n"
        f"De: {name}\n"
        f"Pedido: {prayer_request.request[:300]}{'...' if len(prayer_request.request) > 300 else ''}\n\n"
        f"Acesse o painel para responder:\n"
        f"{base}/membros/oracao-gestao/\n\n"
        f"— Sistema {church}"
    )
    send_mail(subject, body, _from(), admins, fail_silently=True)


def notify_admin_new_testimony(testimony):
    """Notifica admins sobre novo testemunho aguardando aprovação."""
    admins = _admin_emails()
    if not admins:
        return
    church = _site_name()
    base   = _base_url()

    subject = f"[{church}] Novo testemunho aguardando aprovação"
    body = (
        f"Um membro enviou um testemunho para aprovação:\n\n"
        f"De: {testimony.author_name or 'Anônimo'}\n"
        f"Testemunho: {testimony.content[:300]}{'...' if len(testimony.content) > 300 else ''}\n\n"
        f"Acesse o painel para aprovar ou rejeitar:\n"
        f"{base}/membros/testemunhos/\n\n"
        f"— Sistema {church}"
    )
    send_mail(subject, body, _from(), admins, fail_silently=True)


def notify_admin_delete_request(delete_request):
    """Notifica admins sobre nova solicitação de exclusão de conteúdo."""
    admins = _admin_emails()
    if not admins:
        return
    church = _site_name()
    base   = _base_url()
    req_by = delete_request.requested_by

    subject = f"[{church}] Solicitação de exclusão de conteúdo"
    body = (
        f"Um colaborador solicitou exclusão de conteúdo:\n\n"
        f"Solicitante: {req_by.get_full_name() or req_by.username}\n"
        f"Tipo: {delete_request.get_content_type_display()}\n"
        f"Item: {delete_request.object_title}\n"
        f"Motivo: {delete_request.reason or 'Não informado'}\n\n"
        f"Acesse o painel para aprovar ou recusar:\n"
        f"{base}/membros/solicitacoes-exclusao/\n\n"
        f"— Sistema {church}"
    )
    send_mail(subject, body, _from(), admins, fail_silently=True)


# ── Notificações para o colaborador ──────────────────────────────────────────

def notify_collaborator_delete_reviewed(delete_request):
    """Avisa o colaborador sobre o resultado da solicitação de exclusão."""
    user   = delete_request.requested_by
    church = _site_name()
    status = delete_request.get_status_display()
    note   = delete_request.admin_note or 'Nenhuma observação.'

    subject = f"[{church}] Solicitação de exclusão: {status}"
    body = (
        f"Olá, {user.first_name or user.username}!\n\n"
        f"Sua solicitação de exclusão foi revisada:\n\n"
        f"Item: {delete_request.object_title}\n"
        f"Resultado: {status}\n"
        f"Observação do admin: {note}\n\n"
        f"— {church}"
    )
    send_mail(subject, body, _from(), [user.email], fail_silently=True)
