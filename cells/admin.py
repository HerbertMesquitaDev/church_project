from django.contrib import admin
from .models import Cell, CellMembership, CellPost, CellPostReaction
from core.admin_site import TenantAdminMixin


class CellMembershipInline(admin.TabularInline):
    model   = CellMembership
    extra   = 0
    fields  = ('user', 'role', 'status', 'joined_at')
    readonly_fields = ('joined_at',)


@admin.register(Cell)
class CellAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('name', 'cell_type', 'region', 'member_count', 'active')
    list_filter   = ('cell_type', 'active')
    list_editable = ('active',)
    search_fields = ('name', 'region', 'description')
    inlines       = [CellMembershipInline]
    fieldsets = (
        ('Grupo',    {'fields': ('name', 'cell_type', 'region', 'description', 'cover', 'active')}),
        ('Reunião',  {'fields': ('meeting_day', 'meeting_place')}),
    )


@admin.register(CellMembership)
class CellMembershipAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('user', 'cell', 'role', 'status', 'joined_at')
    list_filter   = ('status', 'role', 'cell')
    list_editable = ('status', 'role')
    search_fields = ('user__first_name', 'user__last_name', 'cell__name')

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'cell__igreja')


@admin.register(CellPost)
class CellPostAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('__str__', 'author', 'post_type', 'pinned', 'created_at')
    list_filter   = ('post_type', 'pinned', 'cell')
    list_editable = ('pinned',)
    search_fields = ('content', 'author__username')

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'cell__igreja')
