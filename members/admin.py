from django.contrib import admin
from django import forms
from tinymce.widgets import TinyMCE
from .models import (MemberProfile, MemberMinistry, ExclusiveContent, ContentCategory,
                     Notice, Testimony, PrayerRequest, DeleteRequest, Culto, Presenca)
from core.admin_site import TenantAdminMixin


class ExclusiveContentForm(forms.ModelForm):
    body = forms.CharField(widget=TinyMCE(), required=False)

    class Meta:
        model  = ExclusiveContent
        fields = '__all__'


class NoticeForm(forms.ModelForm):
    body = forms.CharField(widget=TinyMCE())

    class Meta:
        model  = Notice
        fields = '__all__'


class MemberMinistryInline(admin.TabularInline):
    model = MemberMinistry
    extra = 1
    verbose_name = "Ministério"
    verbose_name_plural = "Ministérios do Membro"


@admin.register(MemberProfile)
class MemberProfileAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('full_name', 'get_ministries', 'baptized', 'approved', 'image_consent', 'created_at')
    list_filter   = ('approved', 'baptized', 'ministries', 'image_consent', 'image_consent_revoked')
    list_editable = ('approved',)
    search_fields = ('user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('created_at', 'image_consent_date', 'image_consent_ip', 'image_consent_revoked_date')
    inlines = [MemberMinistryInline]
    fieldsets = (
        ('Dados Pessoais', {'fields': ('user', 'photo', 'phone', 'birth_date', 'bio', 'baptized', 'member_since')}),
        ('Acesso',         {'fields': ('approved', 'role')}),
        ('Consentimento LGPD — Uso de Imagem', {
            'fields': ('image_consent', 'image_consent_date', 'image_consent_ip',
                       'image_consent_revoked', 'image_consent_revoked_date'),
            'description': 'Campos registrados automaticamente. Não edite sem justificativa documentada.',
        }),
        ('Sistema', {'fields': ('created_at',)}),
    )

    @admin.display(description='Ministérios')
    def get_ministries(self, obj):
        return ', '.join(obj.ministries.values_list('name', flat=True)) or '—'



@admin.register(ContentCategory)
class ContentCategoryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'icon', 'order')
    list_editable = ('order',)


@admin.register(ExclusiveContent)
class ExclusiveContentAdmin(TenantAdminMixin, admin.ModelAdmin):
    form = ExclusiveContentForm
    list_display = ('title', 'category', 'content_type', 'published', 'featured', 'created_at')
    list_filter = ('published', 'featured', 'content_type', 'category')
    list_editable = ('published', 'featured')
    search_fields = ('title', 'body')
    fieldsets = (
        ('Conteúdo', {'fields': ('title', 'category', 'content_type', 'body', 'thumbnail')}),
        ('Mídia', {'fields': ('video_url', 'file', 'external_link')}),
        ('Publicação', {'fields': ('published', 'featured', 'author')}),
    )


@admin.register(Notice)
class NoticeAdmin(TenantAdminMixin, admin.ModelAdmin):
    form = NoticeForm
    list_display = ('title', 'priority', 'published', 'created_at', 'expires_at')
    list_filter = ('priority', 'published')
    list_editable = ('published',)


@admin.register(Testimony)
class TestimonyAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('profile', 'short_text', 'status', 'created_at')
    list_filter   = ('status',)
    list_editable = ('status',)
    search_fields = ('profile__user__first_name', 'profile__user__last_name', 'text')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Testemunho', {'fields': ('profile', 'text')}),
        ('Moderação',  {'fields': ('status', 'admin_note')}),
        ('Datas',      {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'profile__igreja')

    @admin.display(description='Texto')
    def short_text(self, obj):
        return obj.text[:80] + ('…' if len(obj.text) > 80 else '')


@admin.register(PrayerRequest)
class PrayerRequestAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('title', 'profile', 'visibility', 'status', 'created_at')
    list_filter   = ('status', 'visibility')
    list_editable = ('status',)
    search_fields = ('title', 'description', 'profile__user__first_name', 'profile__user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Pedido', {'fields': ('profile', 'title', 'description', 'visibility')}),
        ('Acompanhamento', {'fields': ('status', 'admin_note')}),
        ('Datas', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'profile__igreja')


@admin.register(DeleteRequest)
class DeleteRequestAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display    = ('object_title', 'content_type', 'requested_by', 'status', 'created_at')
    list_filter     = ('status', 'content_type')
    list_editable   = ('status',)
    search_fields   = ('object_title', 'reason', 'requested_by__first_name', 'requested_by__last_name')
    readonly_fields = ('requested_by', 'content_type', 'object_id', 'object_title', 'reason', 'created_at', 'reviewed_at')
    fieldsets = (
        ('Solicitação', {'fields': ('requested_by', 'content_type', 'object_id', 'object_title', 'reason', 'created_at')}),
        ('Decisão',     {'fields': ('status', 'admin_note', 'reviewed_by', 'reviewed_at')}),
    )

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'requested_by__profile__igreja')

    def save_model(self, request, obj, form, change):
        from django.utils import timezone
        if obj.status in ('approved', 'rejected') and not obj.reviewed_by:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


class PresencaInline(admin.TabularInline):
    model   = Presenca
    extra   = 0
    fields  = ('member', 'present', 'noted_by')
    raw_id_fields = ('member',)


@admin.register(Culto)
class CultoAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display    = ('title', 'culto_type', 'date', 'present_count', 'visitor_count', 'created_by')
    list_filter     = ('culto_type', 'date')
    search_fields   = ('title', 'notes')
    date_hierarchy  = 'date'
    readonly_fields = ('created_at', 'created_by')
    inlines         = [PresencaInline]
    fieldsets = (
        ('Culto',     {'fields': ('title', 'culto_type', 'date', 'notes')}),
        ('Visitantes', {'fields': ('visitor_count', 'visitor_names')}),
        ('Sistema',   {'fields': ('created_by', 'created_at'), 'classes': ('collapse',)}),
    )

    def present_count(self, obj):
        return obj.presences.filter(present=True).count()
    present_count.short_description = 'Presentes'

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


