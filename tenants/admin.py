from django.contrib import admin
from .models import Igreja
from core.admin_site import SuperAdminOnlyMixin


@admin.register(Igreja)
class IgrejaAdmin(SuperAdminOnlyMixin, admin.ModelAdmin):
    list_display = ('nome', 'slug', 'plano', 'ativo', 'criado_em')
    list_filter  = ('ativo', 'plano')
    search_fields = ('nome', 'slug', 'dominio_proprio')
    prepopulated_fields = {'slug': ('nome',)}