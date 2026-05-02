from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Configurações Gerais'

    def ready(self):
        from django.contrib import admin
        from core.admin_site import ChurchAdminSite
        # Troca a classe do admin.site existente preservando todos os models registrados
        admin.site.__class__ = ChurchAdminSite
