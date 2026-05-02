from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Permite autenticação com e-mail além do username padrão.
    O campo 'username' do formulário de login aceita tanto
    o username quanto o endereço de e-mail do usuário.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            # Tenta encontrar pelo e-mail (case-insensitive)
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # Fallback: tenta pelo username normal
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                # Executa o hash para evitar timing attacks
                User().set_password(password)
                return None
        except User.MultipleObjectsReturned:
            # Se houver e-mails duplicados, tenta pelo username
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None
