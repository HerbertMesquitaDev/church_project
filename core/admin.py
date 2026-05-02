from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django import forms
from tinymce.widgets import TinyMCE

from core.admin_site import TenantAdminMixin, SuperAdminOnlyMixin
from .models import (SiteSettings, Ministry, HeroSlide, Devotional, Offering,
                     Visitor, MediaCategory, MediaItem, PhotoAlbum, Photo, Page,
                     SocialPost, SocialConfig, SiteVisit)


# ── Protege User e Group para superadmin apenas ───────────────────────────────

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class ScopedUserAdmin(SuperAdminOnlyMixin, UserAdmin):
    pass


@admin.register(Group)
class ScopedGroupAdmin(SuperAdminOnlyMixin, GroupAdmin):
    pass


# ── Forms TinyMCE ─────────────────────────────────────────────────────────────

class SiteSettingsForm(forms.ModelForm):
    about_text    = forms.CharField(widget=TinyMCE())
    offering_text = forms.CharField(widget=TinyMCE(), required=False)

    class Meta:
        model  = SiteSettings
        fields = '__all__'


class DevotionalForm(forms.ModelForm):
    reflection = forms.CharField(widget=TinyMCE())
    prayer     = forms.CharField(widget=TinyMCE(), required=False)

    class Meta:
        model  = Devotional
        fields = '__all__'


class MediaItemForm(forms.ModelForm):
    description = forms.CharField(widget=TinyMCE(), required=False)

    class Meta:
        model  = MediaItem
        fields = '__all__'


class PageForm(forms.ModelForm):
    content = forms.CharField(widget=TinyMCE(), required=False)

    class Meta:
        model  = Page
        fields = '__all__'


# ── Admins ────────────────────────────────────────────────────────────────────

@admin.register(SiteSettings)
class SiteSettingsAdmin(TenantAdminMixin, admin.ModelAdmin):
    form = SiteSettingsForm
    fieldsets = (
        ('Identidade',        {'fields': ('church_name', 'tagline', 'logo')}),
        ('Hero (Capa)',        {'fields': ('hero_title', 'hero_subtitle', 'hero_image')}),
        ('Sobre',             {'fields': ('about_text',)}),
        ('Identidade Visual', {'fields': ('color_primary', 'color_secondary', 'color_accent')}),
        ('Dízimos & Ofertas', {'fields': ('offering_text', 'pix_key', 'pix_name', 'bank_name', 'bank_agency', 'bank_account', 'bank_holder')}),
        ('Notificações',      {'fields': ('notification_email',)}),
        ('Contato',           {'fields': ('address', 'maps_url', 'phone', 'email')}),
        ('Redes Sociais',     {'fields': ('facebook_url', 'instagram_url', 'youtube_url')}),
    )

    def has_add_permission(self, request):
        if not super().has_add_permission(request):
            return False
        igreja = getattr(request, 'igreja', None)
        if request.user.is_superuser:
            return True
        return not SiteSettings.objects.filter(igreja=igreja).exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Ministry)
class MinistryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('name', 'order', 'active')
    list_editable = ('order', 'active')
    list_filter   = ('active',)


@admin.register(HeroSlide)
class HeroSlideAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('title', 'order', 'active')
    list_editable = ('order', 'active')
    fieldsets = (
        ('Conteúdo',      {'fields': ('title', 'subtitle', 'image')}),
        ('Botões',        {'fields': ('button_text', 'button_url', 'button_text_2', 'button_url_2')}),
        ('Configurações', {'fields': ('order', 'active')}),
    )


@admin.register(Devotional)
class DevotionalAdmin(TenantAdminMixin, admin.ModelAdmin):
    form          = DevotionalForm
    list_display  = ('pub_date', 'title', 'verse', 'author', 'published')
    list_filter   = ('published',)
    list_editable = ('published',)
    search_fields = ('title', 'verse', 'reflection')
    date_hierarchy = 'pub_date'
    fieldsets = (
        ('Publicação', {'fields': ('pub_date', 'published', 'author')}),
        ('Conteúdo',   {'fields': ('title', 'verse', 'verse_text', 'reflection', 'prayer')}),
    )


@admin.register(Offering)
class OfferingAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('profile', 'type', 'amount_fmt', 'date', 'created_at')
    list_filter   = ('type', 'date')
    search_fields = ('profile__user__first_name', 'profile__user__last_name', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Contribuição', {'fields': ('profile', 'type', 'amount', 'date', 'notes')}),
    )

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'profile__igreja')

    @admin.display(description='Valor')
    def amount_fmt(self, obj):
        return f'R$ {obj.amount:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


@admin.register(Visitor)
class VisitorAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('name', 'phone', 'email', 'visit_date', 'how_found', 'wants_ministry', 'contacted', 'created_at')
    list_filter   = ('contacted', 'wants_ministry', 'how_found', 'visit_date')
    list_editable = ('contacted',)
    search_fields = ('name', 'email', 'phone', 'message')
    date_hierarchy = 'visit_date'
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Dados do Visitante', {'fields': ('name', 'email', 'phone', 'visit_date')}),
        ('Informações',        {'fields': ('how_found', 'how_found_other', 'wants_ministry', 'ministry_interest', 'message')}),
        ('Acompanhamento',     {'fields': ('contacted', 'created_at')}),
    )


@admin.register(MediaCategory)
class MediaCategoryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('name', 'section', 'icon', 'order')
    list_editable = ('order',)
    list_filter   = ('section',)


@admin.register(MediaItem)
class MediaItemAdmin(TenantAdminMixin, admin.ModelAdmin):
    form          = MediaItemForm
    list_display  = ('title', 'category', 'media_type', 'visibility', 'speaker', 'pub_date', 'published', 'featured')
    list_filter   = ('media_type', 'visibility', 'published', 'featured', 'category')
    list_editable = ('published', 'featured', 'visibility')
    search_fields = ('title', 'speaker', 'description')
    date_hierarchy = 'pub_date'
    fieldsets = (
        ('Conteúdo',   {'fields': ('title', 'category', 'media_type', 'visibility', 'description', 'speaker', 'pub_date', 'thumbnail')}),
        ('Mídia',      {'fields': ('video_url', 'audio_file', 'pdf_file')}),
        ('Publicação', {'fields': ('published', 'featured')}),
        ('SEO',        {'fields': ('meta_description',), 'classes': ('collapse',)}),
    )


class PhotoInline(admin.TabularInline):
    model  = Photo
    extra  = 3
    fields = ('image', 'caption', 'order')


@admin.register(PhotoAlbum)
class PhotoAlbumAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('title', 'event_date', 'photo_count', 'published', 'order')
    list_editable = ('published', 'order')
    list_filter   = ('published',)
    search_fields = ('title', 'description')
    inlines       = [PhotoInline]
    fieldsets = (
        ('Álbum',      {'fields': ('title', 'description', 'cover', 'event_date')}),
        ('Publicação', {'fields': ('published', 'order')}),
    )


@admin.register(SiteVisit)
class SiteVisitAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display    = ('visited_at', 'page', 'city', 'region', 'country_code', 'user', 'ip')
    list_filter     = ('country_code', 'region', 'visited_at')
    search_fields   = ('page', 'city', 'region', 'ip')
    date_hierarchy  = 'visited_at'
    readonly_fields = ('igreja', 'session_key', 'ip', 'user', 'page',
                       'city', 'region', 'country_code', 'visited_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SocialConfig)
class SocialConfigAdmin(TenantAdminMixin, admin.ModelAdmin):
    fieldsets = (
        ('Instagram', {'fields': ('ig_user_id', 'ig_access_token')}),
        ('Facebook',  {'fields': ('fb_page_id', 'fb_access_token')}),
        ('Geral',     {'fields': ('site_base_url',)}),
    )

    def has_add_permission(self, request):
        if not super().has_add_permission(request):
            return False
        igreja = getattr(request, 'igreja', None)
        if request.user.is_superuser:
            return True
        return not SocialConfig.objects.filter(igreja=igreja).exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SocialPost)
class SocialPostAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display    = ('caption_short', 'platform', 'post_format', 'status', 'scheduled_for', 'created_at')
    list_filter     = ('status', 'platform', 'post_format', 'source_type')
    search_fields   = ('caption',)
    readonly_fields = ('created_at', 'published_at', 'ig_post_id', 'ig_permalink', 'ig_error',
                       'fb_post_id', 'fb_permalink', 'fb_error', 'created_by')
    date_hierarchy  = 'created_at'
    fieldsets = (
        ('Origem',     {'fields': ('source_type', 'album', 'event', 'photos')}),
        ('Conteúdo',   {'fields': ('platform', 'post_format', 'caption', 'hashtags')}),
        ('Publicação', {'fields': ('status', 'scheduled_for', 'published_at')}),
        ('Instagram',  {'fields': ('ig_post_id', 'ig_permalink', 'ig_error'), 'classes': ('collapse',)}),
        ('Facebook',   {'fields': ('fb_post_id', 'fb_permalink', 'fb_error'),  'classes': ('collapse',)}),
        ('Sistema',    {'fields': ('created_by', 'created_at'), 'classes': ('collapse',)}),
    )

    @admin.display(description='Legenda')
    def caption_short(self, obj):
        return obj.caption[:60] + ('…' if len(obj.caption) > 60 else '')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Page)
class PageAdmin(TenantAdminMixin, admin.ModelAdmin):
    form                = PageForm
    list_display        = ('title', 'slug', 'template_name', 'show_in_nav', 'published', 'updated_at')
    list_filter         = ('published', 'show_in_nav', 'template_name')
    list_editable       = ('published', 'show_in_nav')
    search_fields       = ('title', 'slug', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields     = ('created_at', 'updated_at')
    fieldsets = (
        ('Conteúdo',   {'fields': ('title', 'slug', 'cover', 'content')}),
        ('SEO',        {'fields': ('meta_description', 'meta_keywords'), 'classes': ('collapse',)}),
        ('Publicação', {'fields': ('template_name', 'published', 'show_in_nav', 'nav_order')}),
        ('Sistema',    {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
