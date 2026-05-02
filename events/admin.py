from django.contrib import admin
from .models import Event, Category, EventRegistration
from core.admin_site import TenantAdminMixin


class EventRegistrationInline(admin.TabularInline):
    model       = EventRegistration
    extra       = 0
    fields      = ('user', 'status', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Category)
class CategoryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'color')


@admin.register(Event)
class EventAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('title', 'date', 'requires_registration', 'max_spots', 'spots_taken', 'published')
    list_filter   = ('published', 'featured', 'requires_registration', 'category')
    list_editable = ('published',)
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines       = [EventRegistrationInline]
    fieldsets = (
        ('Evento',        {'fields': ('title', 'slug', 'category', 'description', 'short_description', 'image', 'featured', 'published')}),
        ('Data & Local',  {'fields': ('date', 'end_date', 'location', 'address', 'recurrence')}),
        ('Inscrições',    {'fields': ('requires_registration', 'max_spots', 'registration_deadline', 'registration_link')}),
        ('SEO',           {'fields': ('meta_description',), 'classes': ('collapse',)}),
    )


@admin.register(EventRegistration)
class EventRegistrationAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('user', 'event', 'status', 'created_at')
    list_filter   = ('status', 'event')
    list_editable = ('status',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'event__title')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'event__igreja')
