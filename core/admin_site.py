"""
Scoped admin por tenant.

TenantAdminMixin  — aplicar a todo ModelAdmin com dados de uma igreja
SuperAdminOnlyMixin — aplicar a modelos globais (Igreja, User, Group)
ChurchAdminSite   — AdminSite com has_permission que aceita admins de igreja
"""

from django.contrib import admin
from django.contrib.admin import AdminSite


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_igreja(request):
    return getattr(request, 'igreja', None)


def _is_church_admin(request):
    """True se o usuário é admin aprovado da igreja detectada pelo middleware."""
    if request.user.is_superuser:
        return False
    try:
        profile = request.user.profile
        igreja  = _get_igreja(request)
        return (
            profile.role     == 'admin'
            and profile.approved
            and profile.igreja == igreja
        )
    except Exception:
        return False


# ── Mixin principal ───────────────────────────────────────────────────────────

class TenantAdminMixin:
    """
    Aplique a qualquer ModelAdmin que tenha campo `igreja` (direto ou via FK aninhada).

    Para modelos sem FK `igreja` direta, sobrescreva `get_queryset` na subclasse
    usando o helper `_scoped(request, qs, 'campo__igreja')`.
    """

    # ── Visibilidade do app no menu ───────────────────────

    def has_module_perms(self, request):
        if request.user.is_superuser:
            return True
        return _is_church_admin(request)

    # ── Permissões por objeto ─────────────────────────────

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not _is_church_admin(request):
            return False
        return obj is None or self._obj_ok(request, obj)

    def has_add_permission(self, request):
        return request.user.is_superuser or _is_church_admin(request)

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not _is_church_admin(request):
            return False
        return obj is None or self._obj_ok(request, obj)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if not _is_church_admin(request):
            return False
        return obj is None or self._obj_ok(request, obj)

    def _obj_ok(self, request, obj):
        """Verifica se o objeto pertence à igreja da requisição."""
        igreja = _get_igreja(request)
        if not igreja:
            return False
        if hasattr(obj, 'igreja_id'):
            return obj.igreja_id == igreja.pk
        return True  # modelos sem FK direta já são filtrados no queryset

    # ── Queryset ──────────────────────────────────────────

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        igreja = _get_igreja(request)
        if not igreja:
            return qs.none()
        if hasattr(self.model, 'igreja'):
            return qs.filter(igreja=igreja)
        # Modelos sem FK direta: sobrescreva get_queryset e chame _scoped()
        return qs

    @staticmethod
    def _scoped(request, qs, lookup):
        """Filtra queryset por igreja usando um lookup arbitrário (ex: 'event__igreja')."""
        if request.user.is_superuser:
            return qs
        igreja = _get_igreja(request)
        if not igreja:
            return qs.none()
        return qs.filter(**{lookup: igreja})

    # ── Auto-assign igreja ao salvar ──────────────────────

    def save_model(self, request, obj, form, change):
        if not change and not request.user.is_superuser:
            igreja = _get_igreja(request)
            if igreja and hasattr(obj, 'igreja') and not obj.igreja_id:
                obj.igreja = igreja
        super().save_model(request, obj, form, change)

    # ── Choices de FK e M2M filtradas por tenant ──────────

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            igreja = _get_igreja(request)
            if igreja and hasattr(db_field.related_model, 'igreja'):
                kwargs['queryset'] = db_field.related_model.objects.filter(
                    igreja=igreja
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            igreja = _get_igreja(request)
            if igreja and hasattr(db_field.related_model, 'igreja'):
                kwargs['queryset'] = db_field.related_model.objects.filter(
                    igreja=igreja
                )
        return super().formfield_for_manytomany(db_field, request, **kwargs)


# ── Mixin superadmin ──────────────────────────────────────────────────────────

class SuperAdminOnlyMixin:
    """Aplique a modelos globais: Igreja, User, Group."""

    def has_module_perms(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ── AdminSite customizado ─────────────────────────────────────────────────────

class ChurchAdminSite(AdminSite):
    site_header = "Gestão da Igreja"
    site_title  = "Igreja CMS"
    index_title = "Painel de Administração"

    def has_permission(self, request):
        if not request.user.is_active:
            return False
        if request.user.is_superuser:
            return True
        # Admins de igreja precisam de is_staff=True (setado via signal)
        if not request.user.is_staff:
            return False
        return _is_church_admin(request)
