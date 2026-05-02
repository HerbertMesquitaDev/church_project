from django.contrib import admin
from django import forms
from tinymce.widgets import TinyMCE
from .models import (CourseCategory, Course, Module, Lesson, Enrollment,
                     LessonProgress, LessonComment, LessonQuiz,
                     QuizQuestion, QuizChoice, QuizAttempt, PerfectStudentSeal)
from core.admin_site import TenantAdminMixin


class CourseForm(forms.ModelForm):
    description = forms.CharField(widget=TinyMCE())

    class Meta:
        model  = Course
        fields = '__all__'


class LessonForm(forms.ModelForm):
    description = forms.CharField(widget=TinyMCE(), required=False)
    body        = forms.CharField(widget=TinyMCE(), required=False)

    class Meta:
        model  = Lesson
        fields = '__all__'


@admin.register(CourseCategory)
class CourseCategoryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('name', 'icon', 'order')
    list_editable = ('order',)


class ModuleInline(admin.TabularInline):
    model  = Module
    extra  = 1
    fields = ('title', 'order')


class LessonInline(admin.TabularInline):
    model  = Lesson
    extra  = 1
    fields = ('title', 'order', 'published', 'duration')


@admin.register(Course)
class CourseAdmin(TenantAdminMixin, admin.ModelAdmin):
    form = CourseForm
    list_display  = ('title', 'category', 'instructor', 'level', 'published', 'enrolled_count', 'lesson_count')
    list_filter   = ('published', 'level', 'category')
    list_editable = ('published',)
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]
    fieldsets = (
        ('Curso',      {'fields': ('title', 'slug', 'category', 'description', 'cover', 'instructor', 'level', 'workload', 'published', 'order')}),
        ('SEO',        {'fields': ('meta_description',), 'classes': ('collapse',)}),
    )


@admin.register(Module)
class ModuleAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('title', 'course', 'order')
    list_editable = ('order',)
    inlines       = [LessonInline]

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'course__igreja')


class QuizChoiceInline(admin.TabularInline):
    model  = QuizChoice
    extra  = 4
    fields = ('text', 'is_correct', 'order')


class QuizQuestionInline(admin.StackedInline):
    model  = QuizQuestion
    extra  = 1
    fields = ('text', 'explanation', 'order')


@admin.register(Lesson)
class LessonAdmin(TenantAdminMixin, admin.ModelAdmin):
    form = LessonForm
    list_display  = ('title', 'module', 'order', 'duration', 'published')
    list_filter   = ('published', 'module__course')
    list_editable = ('published', 'order')
    search_fields = ('title',)

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'module__course__igreja')


@admin.register(Enrollment)
class EnrollmentAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('user', 'course', 'progress_percent', 'has_seal', 'enrolled_at', 'active')
    list_filter  = ('active', 'course')

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'course__igreja')

    @admin.display(description='Progresso')
    def progress_percent(self, obj):
        return f'{obj.progress_percent}%'

    @admin.display(description='Nota 10', boolean=True)
    def has_seal(self, obj):
        return hasattr(obj, 'perfect_seal')


@admin.register(LessonQuiz)
class LessonQuizAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('lesson', 'passing_score', 'max_attempts')
    inlines      = [QuizQuestionInline]

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'lesson__module__course__igreja')


@admin.register(PerfectStudentSeal)
class PerfectStudentSealAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display    = ('student_name', 'course_title', 'granted_at')
    list_filter     = ('enrollment__course',)
    search_fields   = ('enrollment__user__first_name', 'enrollment__user__last_name',
                       'enrollment__course__title')
    readonly_fields = ('enrollment', 'granted_at')
    date_hierarchy  = 'granted_at'

    @admin.display(description='Aluno')
    def student_name(self, obj):
        return obj.enrollment.user.get_full_name() or obj.enrollment.user.username

    @admin.display(description='Curso')
    def course_title(self, obj):
        return obj.enrollment.course.title

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'enrollment__course__igreja')

    def has_add_permission(self, request):
        return False


@admin.register(LessonComment)
class LessonCommentAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display  = ('short_body', 'user', 'lesson', 'parent', 'created_at')
    list_filter   = ('lesson__module__course',)
    search_fields = ('body', 'user__first_name', 'user__last_name', 'lesson__title')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'lesson__module__course__igreja')

    @admin.display(description='Comentário')
    def short_body(self, obj):
        return obj.body[:80] + ('…' if len(obj.body) > 80 else '')


@admin.register(QuizAttempt)
class CourseQuizAttemptAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display    = ('user', 'quiz', 'score', 'passed', 'created_at')
    list_filter     = ('passed', 'quiz__lesson__module__course')
    search_fields   = ('user__first_name', 'user__last_name')
    readonly_fields = ('user', 'quiz', 'score', 'passed', 'answers', 'created_at')

    def get_queryset(self, request):
        qs = super(TenantAdminMixin, self).get_queryset(request)
        return self._scoped(request, qs, 'quiz__lesson__module__course__igreja')
