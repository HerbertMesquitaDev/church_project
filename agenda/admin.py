from django.contrib import admin
from .models import Location, Booking


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'capacity', 'active')
    list_filter = ('active',)
    search_fields = ('name', 'address')
    list_editable = ('active',)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'date', 'start_time', 'end_time',
                    'responsible', 'status', 'ministry')
    list_filter = ('status', 'location', 'date')
    search_fields = ('title', 'ministry', 'responsible__first_name',
                     'responsible__last_name')
    ordering = ('date', 'start_time')
    readonly_fields = ('created_at', 'updated_at', 'approved_by', 'approved_at')
    fieldsets = (
        ('Informações', {
            'fields': ('title', 'location', 'responsible', 'ministry')
        }),
        ('Data e Horário', {
            'fields': ('date', 'start_time', 'end_time')
        }),
        ('Status', {
            'fields': ('status', 'approved_by', 'approved_at', 'notes')
        }),
        ('Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        from django.utils import timezone
        if obj.status == 'approved' and not obj.approved_by:
            obj.approved_by = request.user
            obj.approved_at = timezone.now()
        super().save_model(request, obj, form, change)
