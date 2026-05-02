from django.contrib import admin
from django import forms
from tinymce.widgets import TinyMCE
from .models import EbdClass, EbdTrimester, EbdLesson, Quiz, Question, Choice, QuizAttempt, LessonCertificate
from core.admin_site import TenantAdminMixin


class EbdLessonForm(forms.ModelForm):
    summary = forms.CharField(widget=TinyMCE(), required=False)
    body    = forms.CharField(widget=TinyMCE(), required=False)

    class Meta:
        model  = EbdLesson
        fields = '__all__'


class ChoiceInline(admin.TabularInline):
    model   = Choice
    extra   = 4
    fields  = ('text', 'is_correct', 'order')


class QuestionInline(admin.StackedInline):
    model   = Question
    extra   = 2
    fields  = ('text', 'explanation', 'order')
    show_change_link = True


@admin.register(EbdClass)
class EbdClassAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('name', 'order', 'active')
    list_editable = ('order', 'active')


@admin.register(EbdTrimester)
class EbdTrimesterAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('__str__', 'ebd_class', 'year', 'quarter', 'active')
    list_filter   = ('ebd_class', 'year', 'active')
    list_editable = ('active',)

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'ebd_class__igreja')


class QuizInline(admin.StackedInline):
    model           = Quiz
    extra           = 0
    can_delete      = False
    show_change_link = True
    fields          = ('passing_score', 'max_attempts', 'show_answers')


@admin.register(EbdLesson)
class EbdLessonAdmin(TenantAdminMixin, admin.ModelAdmin):
    form = EbdLessonForm
    list_display   = ('number', 'title', 'trimester', 'published', 'created_at')
    list_filter    = ('trimester__ebd_class', 'trimester', 'published')
    list_editable  = ('published',)
    search_fields  = ('title', 'body', 'scripture')
    inlines        = [QuizInline]
    fieldsets = (
        ('Identificação',  {'fields': ('trimester', 'number', 'order', 'title', 'scripture', 'published')}),
        ('Prévia pública', {'fields': ('summary',)}),
        ('Conteúdo',       {'fields': ('body',)}),
        ('Mídia',          {'fields': ('video_url', 'audio_file', 'pdf_file')}),
        ('SEO',            {'fields': ('meta_description',), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'trimester__ebd_class__igreja')


@admin.register(Quiz)
class QuizAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('lesson', 'question_count', 'passing_score', 'max_attempts')
    inlines      = [QuestionInline]

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'lesson__trimester__ebd_class__igreja')


@admin.register(Question)
class QuestionAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('__str__', 'quiz')
    inlines      = [ChoiceInline]
    search_fields = ('text',)

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'quiz__lesson__trimester__ebd_class__igreja')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display   = ('user', 'quiz', 'score', 'passed', 'created_at')
    list_filter    = ('passed',)
    readonly_fields = ('user', 'quiz', 'score', 'passed', 'answers', 'created_at')

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'quiz__lesson__trimester__ebd_class__igreja')


@admin.register(LessonCertificate)
class LessonCertificateAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('user', 'lesson', 'issued_at')
    list_filter   = ('lesson__trimester__ebd_class',)
    readonly_fields = ('user', 'lesson', 'attempt', 'issued_at')

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'lesson__trimester__ebd_class__igreja')
