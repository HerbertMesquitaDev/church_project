from django.db import models
from django.contrib.auth.models import User

from tenants.models import Igreja
from core.validators import validate_image, validate_audio, validate_document


class CourseCategory(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='course_categories'
    )
    name  = models.CharField("Nome", max_length=100)
    icon  = models.CharField("Ícone FA", max_length=80, default="fa-graduation-cap",
                              help_text="Ex: fa-bible, fa-music, fa-users")
    order = models.PositiveIntegerField("Ordem", default=0)

    class Meta:
        verbose_name         = "Categoria"
        verbose_name_plural  = "Categorias de Curso"
        ordering             = ['order', 'name']

    def __str__(self):
        return self.name


class Course(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='courses'
    )
    LEVEL_CHOICES = [
        ('beginner',     'Iniciante'),
        ('intermediate', 'Intermediário'),
        ('advanced',     'Avançado'),
    ]

    title       = models.CharField("Título", max_length=200)
    slug        = models.SlugField("Slug", unique=True, blank=True)
    category    = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL,
                                     null=True, blank=True, verbose_name="Categoria",
                                     related_name='courses')
    description = models.TextField("Descrição")
    cover       = models.ImageField("Capa", upload_to='courses/covers/', blank=True, null=True, validators=[validate_image])
    instructor  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     related_name='courses_teaching', verbose_name="Professor")
    level       = models.CharField("Nível", max_length=15,
                                    choices=LEVEL_CHOICES, default='beginner')
    workload    = models.PositiveIntegerField("Carga horária (min)", default=0,
                                              help_text="Duração total estimada em minutos")
    meta_description = models.CharField("Meta description (SEO)", max_length=160, blank=True,
                                         help_text="Resumo para o Google (max 160 caracteres). Se vazio, usa a Descrição.")
    published   = models.BooleanField("Publicado", default=False)
    order       = models.PositiveIntegerField("Ordem", default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name         = "Curso"
        verbose_name_plural  = "Cursos"
        ordering             = ['order', 'title']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            base = slugify(self.title)
            self.slug = base if not Course.objects.filter(slug=base).exists() \
                else f"{base}-{uuid.uuid4().hex[:6]}"
        super().save(*args, **kwargs)

    @property
    def lesson_count(self):
        return Lesson.objects.filter(module__course=self).count()

    @property
    def enrolled_count(self):
        return self.enrollments.filter(active=True).count()


class Module(models.Model):
    course      = models.ForeignKey(Course, on_delete=models.CASCADE,
                                     related_name='modules', verbose_name="Curso")
    title       = models.CharField("Título do Módulo", max_length=200)
    description = models.TextField("Descrição", blank=True)
    order       = models.PositiveIntegerField("Ordem", default=0)

    class Meta:
        verbose_name         = "Módulo"
        verbose_name_plural  = "Módulos"
        ordering             = ['order']

    def __str__(self):
        return f"{self.course.title} › {self.title}"


class Lesson(models.Model):
    module      = models.ForeignKey(Module, on_delete=models.CASCADE,
                                     related_name='lessons', verbose_name="Módulo")
    title       = models.CharField("Título da Aula", max_length=200)
    description = models.TextField("Resumo / Objetivo", blank=True)
    body        = models.TextField("Conteúdo (texto)", blank=True)
    video_url   = models.URLField("Vídeo (YouTube/Vimeo)", blank=True)
    audio_file  = models.FileField("Áudio", upload_to='courses/audio/', blank=True, null=True, validators=[validate_audio])
    pdf_file    = models.FileField("PDF / Material", upload_to='courses/pdf/', blank=True, null=True, validators=[validate_document])
    duration    = models.PositiveIntegerField("Duração estimada (min)", default=0)
    order       = models.PositiveIntegerField("Ordem", default=0)
    published   = models.BooleanField("Publicada", default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name         = "Aula"
        verbose_name_plural  = "Aulas"
        ordering             = ['order']

    def __str__(self):
        return f"{self.module.title} › {self.title}"

    def get_embed_url(self):
        url = self.video_url
        if not url:
            return ''
        if 'youtube.com/watch?v=' in url:
            return f'https://www.youtube.com/embed/{url.split("v=")[1].split("&")[0]}'
        if 'youtu.be/' in url:
            return f'https://www.youtube.com/embed/{url.split("youtu.be/")[1].split("?")[0]}'
        if 'vimeo.com/' in url:
            return f'https://player.vimeo.com/video/{url.split("vimeo.com/")[1].split("?")[0]}'
        return url


class Enrollment(models.Model):
    """Inscrição de um membro em um curso."""
    course     = models.ForeignKey(Course, on_delete=models.CASCADE,
                                    related_name='enrollments', verbose_name="Curso")
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='enrollments', verbose_name="Aluno")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    active     = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name         = "Inscrição"
        verbose_name_plural  = "Inscrições"
        unique_together      = ('course', 'user')
        ordering             = ['-enrolled_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.course.title}"

    @property
    def progress_percent(self):
        total = Lesson.objects.filter(module__course=self.course, published=True).count()
        if not total:
            return 0
        done = LessonProgress.objects.filter(
            user=self.user, lesson__module__course=self.course, completed=True
        ).count()
        return int((done / total) * 100)


class LessonProgress(models.Model):
    """Progresso individual por aula."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='lesson_progress', verbose_name="Aluno")
    lesson     = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                                    related_name='progress', verbose_name="Aula")
    completed  = models.BooleanField("Concluída", default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name    = "Progresso"
        unique_together = ('user', 'lesson')

    def __str__(self):
        status = "✓" if self.completed else "○"
        return f"{status} {self.user} — {self.lesson.title}"


class LessonComment(models.Model):
    """Comentário de um aluno em uma aula."""
    lesson     = models.ForeignKey(Lesson, on_delete=models.CASCADE,
                                    related_name='comments', verbose_name="Aula")
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='lesson_comments', verbose_name="Autor")
    parent     = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='replies', verbose_name="Resposta a")
    body       = models.TextField("Comentário", max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name         = "Comentário"
        verbose_name_plural  = "Comentários"
        ordering             = ['created_at']

    def __str__(self):
        return f"{self.user} em {self.lesson.title}"


# ── Quiz ──────────────────────────────────────────────────

class LessonQuiz(models.Model):
    lesson        = models.OneToOneField(Lesson, on_delete=models.CASCADE,
                                          related_name='quiz', verbose_name="Aula")
    passing_score = models.PositiveSmallIntegerField("Nota mínima (%)", default=70)
    max_attempts  = models.PositiveSmallIntegerField("Tentativas permitidas", default=3,
                                                      help_text="0 = ilimitado")
    show_answers  = models.BooleanField("Mostrar gabarito após tentativa", default=True)

    class Meta:
        verbose_name = "Quiz da Aula"

    def __str__(self):
        return f"Quiz — {self.lesson.title}"


class QuizQuestion(models.Model):
    quiz        = models.ForeignKey(LessonQuiz, on_delete=models.CASCADE,
                                     related_name='questions', verbose_name="Quiz")
    text        = models.TextField("Pergunta")
    explanation = models.TextField("Explicação da resposta", blank=True)
    order       = models.PositiveSmallIntegerField("Ordem", default=0)

    class Meta:
        verbose_name = "Pergunta"
        ordering     = ['order']

    def __str__(self):
        return self.text[:80]


class QuizChoice(models.Model):
    question   = models.ForeignKey(QuizQuestion, on_delete=models.CASCADE,
                                    related_name='choices', verbose_name="Pergunta")
    text       = models.CharField("Alternativa", max_length=500)
    is_correct = models.BooleanField("É a correta", default=False)
    order      = models.PositiveSmallIntegerField("Ordem", default=0)

    class Meta:
        verbose_name = "Alternativa"
        ordering     = ['order']

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:60]}"


class QuizAttempt(models.Model):
    quiz       = models.ForeignKey(LessonQuiz, on_delete=models.CASCADE,
                                    related_name='attempts', verbose_name="Quiz")
    user       = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='course_quiz_attempts', verbose_name="Aluno")
    score      = models.PositiveSmallIntegerField("Pontuação (%)")
    passed     = models.BooleanField("Aprovado")
    answers    = models.JSONField("Respostas", default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tentativa de Quiz"
        ordering     = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.quiz} — {self.score}%"


class PerfectStudentSeal(models.Model):
    """Concedido automaticamente ao aluno que conclui 100% das aulas de um curso."""
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE,
                                       related_name='perfect_seal', verbose_name="Matrícula")
    granted_at = models.DateTimeField("Concedido em", auto_now_add=True)

    class Meta:
        verbose_name         = "Selo Nota 10"
        verbose_name_plural  = "Selos Nota 10"
        ordering             = ['-granted_at']

    def __str__(self):
        return f"★ {self.enrollment.user.get_full_name() or self.enrollment.user.username} — {self.enrollment.course.title}"
