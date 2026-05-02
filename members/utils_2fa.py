import random
from django.core.cache import cache
from django.conf import settings


def gerar_codigo(telefone):
    """Gera e armazena um código de 6 dígitos válido por 5 minutos."""
    codigo = str(random.randint(100000, 999999))
    cache.set(f'2fa_{telefone}', codigo, timeout=300)
    return codigo


def verificar_codigo(telefone, codigo_digitado):
    """Verifica se o código digitado é válido."""
    codigo_salvo = cache.get(f'2fa_{telefone}')
    if not codigo_salvo:
        return False, 'Código expirado. Solicite um novo.'
    if codigo_salvo != codigo_digitado.strip():
        return False, 'Código incorreto.'
    cache.delete(f'2fa_{telefone}')
    return True, 'OK'


def enviar_sms(telefone, codigo):
    """Envia o código via SMS usando Twilio."""
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f'Seu código de acesso é: {codigo}. Válido por 5 minutos.',
            from_=settings.TWILIO_PHONE_NUMBER,
            to=telefone
        )
        return True, 'SMS enviado.'
    except Exception as e:
        return False, str(e)


def enviar_codigo_2fa(telefone):
    """Gera e envia o código 2FA."""
    codigo = gerar_codigo(telefone)
    return enviar_sms(telefone, codigo)