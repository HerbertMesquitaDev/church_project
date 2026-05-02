from django.db import models
from django.contrib.auth.models import User
from tenants.models import Igreja
from core.validators import validate_image, validate_audio, validate_document


class EbdClass(models.Model):
    """Turma da EBD: Adultos, Jovens, Infantil etc."""
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='ebd_classes'
    )
    name = models.CharField("Nome da Turma", max_length=100)
    description = models.TextField("Descrição", blank=True)
    order = models.PositiveIntegerField("Ordem", default=0)
    active = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name = "Turma"
        verbose_name_plural = "Turmas"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class EbdTrimester(models.Model):
    """Trimestre de estudo vinculado a uma turma."""
    QUARTER_CHOICES = [
        (1, '1º Trimestre'),
        (2, '2º Trimestre'),
        (3, '3º Trimestre'),
        (4, '4º Trimestre'),
    ]
    ebd_class = models.ForeignKey(EbdClass, on_delete=models.CASCADE,
                                   related_name='trimesters', verbose_name="Turma")
    year = models.PositiveIntegerField("Ano")
    quarter = models.PositiveSmallIntegerField("Trimestre", choices=QUARTER_CHOICES)
    title = models.CharField("Título do Trimestre", max_length=200)
    description = models.TextField("Descrição", blank=True)
    cover = models.ImageField("Capa", upload_to='ebd/covers/', blank=True, null=True, validators=[validate_image])
    active = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Trimestre"
        verbose_name_plural = "Trimestres"
        unique_together = ('ebd_class', 'year', 'quarter')
        ordering = ['-year', 'quarter']

    def __str__(self):
        return f"{self.ebd_class} — {self.get_quarter_display()} {self.year}"


class EbdLesson(models.Model):
    """Lição dentro de um trimestre."""
    trimester = models.ForeignKey(EbdTrimester, on_delete=models.CASCADE,
                                   related_name='lessons', verbose_name="Trimestre")
    number = models.PositiveSmallIntegerField("Número da Lição")
    title = models.CharField("Título", max_length=200)
    summary = models.TextField("Resumo público", blank=True,
                                help_text="Texto exibido na prévia pública")
    body = models.TextField("Conteúdo da aula (texto)", blank=True)
    video_url = models.URLField("Vídeo (YouTube/Vimeo)", blank=True)
    audio_file = models.FileField("Áudio", upload_to='ebd/audio/', blank=True, null=True, validators=[validate_audio])
    pdf_file = models.FileField("PDF", upload_to='ebd/pdf/', blank=True, null=True, validators=[validate_document])
    scripture = models.CharField("Texto Bíblico Base", max_length=200, blank=True,
                                  help_text="Ex: João 3:16-17")
    meta_description = models.CharField("Meta description (SEO)", max_length=160, blank=True,
                                         help_text="Resumo para o Google (max 160 caracteres). Se vazio, usa o Resumo público.")
    published = models.BooleanField("Publicada", default=False)
    order = models.PositiveSmallIntegerField("Ordem", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Lição"
        verbose_name_plural = "Lições"
        unique_together = ('trimester', 'number')
        ordering = ['order', 'number']

    def __str__(self):
        return f"Lição {self.number} — {self.title}"

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


class Quiz(models.Model):
    """Quiz vinculado a uma lição."""
    lesson = models.OneToOneField(EbdLesson, on_delete=models.CASCADE,
                                   related_name='quiz', verbose_name="Lição")
    passing_score = models.PositiveSmallIntegerField("Nota mínima para aprovação (%)", default=70)
    max_attempts = models.PositiveSmallIntegerField("Tentativas permitidas", default=3,
                                                     help_text="0 = ilimitado")
    show_answers = models.BooleanField("Mostrar gabarito após tentativa", default=True)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"

    def __str__(self):
        return f"Quiz — {self.lesson.title}"

    @property
    def question_count(self):
        return self.questions.count()


class Question(models.Model):
    """Pergunta de múltipla escolha de um quiz."""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE,
                              related_name='questions', verbose_name="Quiz")
    text = models.TextField("Enunciado")
    explanation = models.TextField("Explicação da resposta correta", blank=True)
    order = models.PositiveSmallIntegerField("Ordem", default=0)

    class Meta:
        verbose_name = "Pergunta"
        verbose_name_plural = "Perguntas"
        ordering = ['order']

    def __str__(self):
        return self.text[:80]


class Choice(models.Model):
    """Alternativa de uma pergunta."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE,
                                  related_name='choices', verbose_name="Pergunta")
    text = models.CharField("Texto da alternativa", max_length=500)
    is_correct = models.BooleanField("É a correta", default=False)
    order = models.PositiveSmallIntegerField("Ordem", default=0)

    class Meta:
        verbose_name = "Alternativa"
        verbose_name_plural = "Alternativas"
        ordering = ['order']

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:60]}"


class QuizAttempt(models.Model):
    """Registro de uma tentativa de quiz por um membro."""
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE,
                              related_name='attempts', verbose_name="Quiz")
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='quiz_attempts', verbose_name="Membro")
    score = models.PositiveSmallIntegerField("Pontuação (%)")
    passed = models.BooleanField("Aprovado")
    answers = models.JSONField("Respostas", default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tentativa de Quiz"
        verbose_name_plural = "Tentativas de Quiz"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} — {self.quiz} — {self.score}%"


class LessonCertificate(models.Model):
    """Certificado emitido ao membro que concluiu uma lição com aprovação."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='certificates', verbose_name="Membro")
    lesson = models.ForeignKey(EbdLesson, on_delete=models.CASCADE,
                                related_name='certificates', verbose_name="Lição")
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.SET_NULL,
                                 null=True, related_name='certificate',
                                 verbose_name="Tentativa")
    issued_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Certificado"
        verbose_name_plural = "Certificados"
        unique_together = ('user', 'lesson')
        ordering = ['-issued_at']

    def __str__(self):
        return f"Certificado de {self.user} — {self.lesson.title}"