from django.apps import AppConfig

class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'members'
    verbose_name = 'Área de Membros'

    def ready(self):
        import members.signals  # noqa
