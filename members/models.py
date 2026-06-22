from django.db import models
from django.contrib.auth.models import User
from core.models import Ministry
from tenants.models import Igreja
from core.validators import validate_image, validate_audio, validate_document, validate_generic_file


class MemberMinistry(models.Model):
    """Intermediate table: member ↔ ministry with a role description."""
    profile = models.ForeignKey('MemberProfile', on_delete=models.CASCADE,
                                 related_name='member_ministries',
                                 verbose_name="Membro")
    ministry = models.ForeignKey(Ministry, on_delete=models.CASCADE,
                                  related_name='members',
                                  verbose_name="Ministério")
    role = models.CharField("Função no Ministério", max_length=150, blank=True,
                             help_text="Ex: Tecladista, Líder, Auxiliar")

    class Meta:
        verbose_name = "Membro do Ministério"
        verbose_name_plural = "Membros dos Ministérios"
        unique_together = ('profile', 'ministry')

    def __str__(self):
        return f"{self.profile} — {self.ministry} ({self.role or 'sem função'})"


class MemberProfile(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='members'
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                 related_name='profile', verbose_name="Usuário")
    photo = models.ImageField("Foto de Perfil", upload_to='members/photos/',
                               blank=True, null=True, validators=[validate_image])
    phone = models.CharField("Telefone", max_length=20, blank=True)
    birth_date = models.DateField("Data de Nascimento", null=True, blank=True)
    ministries = models.ManyToManyField(Ministry, through='MemberMinistry',
                                         blank=True, verbose_name="Ministérios",
                                         related_name='member_profiles')
    bio = models.TextField("Sobre mim", blank=True, max_length=500)
    baptized = models.BooleanField("Batizado(a)", default=False)
    member_since = models.DateField("Membro desde", null=True, blank=True)
    ROLE_CHOICES = [
        ('member',       'Membro'),
        ('collaborator', 'Colaborador'),
        ('teacher',      'Professor'),
        ('student',      'Aluno'),
        ('admin',        'Administrador'),
    ]
    approved = models.BooleanField("Cadastro Aprovado", default=False,
                                    help_text="Marque para liberar acesso à área de membros")
    role = models.CharField("Grupo / Perfil", max_length=20,
                             choices=ROLE_CHOICES, default='member',
                             help_text="Define as permissões do usuário no portal")

    # ── Consentimento LGPD — uso de imagem ────────────────────────────────
    image_consent = models.BooleanField(
        "Autorização de uso de imagem", default=False,
        help_text="O membro autorizou o uso de sua imagem conforme o Termo LGPD"
    )
    image_consent_date = models.DateTimeField(
        "Data/hora do consentimento", null=True, blank=True,
        help_text="Registrado automaticamente no momento do aceite"
    )
    image_consent_ip = models.GenericIPAddressField(
        "IP do consentimento", null=True, blank=True,
        help_text="IP do dispositivo no momento do aceite (auditoria LGPD)"
    )
    image_consent_revoked = models.BooleanField("Consentimento revogado", default=False)
    image_consent_revoked_date = models.DateTimeField(
        "Data/hora da revogação", null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Perfil de Membro"
        verbose_name_plural = "Perfis de Membros"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def is_teacher(self):
        return self.role == 'teacher'


class ContentCategory(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='content_categories'
    )
    name = models.CharField("Nome", max_length=100)
    icon = models.CharField("Ícone FA", max_length=80, default="fa-book",
                             help_text="Ex: fa-book, fa-video, fa-music")
    order = models.PositiveIntegerField("Ordem", default=0)

    class Meta:
        verbose_name = "Categoria de Conteúdo"
        verbose_name_plural = "Categorias de Conteúdo"
        ordering = ['order']

    def __str__(self):
        return self.name


class ExclusiveContent(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='exclusive_contents'
    )
    TYPE_CHOICES = [
        ('text',  'Texto / Estudo'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('file',  'Arquivo PDF'),
        ('link',  'Link Externo'),
    ]
    title = models.CharField("Título", max_length=200)
    category = models.ForeignKey(ContentCategory, on_delete=models.SET_NULL,
                                  null=True, blank=True, verbose_name="Categoria")
    content_type = models.CharField("Tipo", max_length=20,
                                     choices=TYPE_CHOICES, default='text')
    body = models.TextField("Conteúdo / Descrição", blank=True)
    video_url = models.URLField("URL do Vídeo (YouTube/Vimeo)", blank=True)
    file = models.FileField("Arquivo", upload_to='members/files/',
                             blank=True, null=True, validators=[validate_generic_file])
    external_link = models.URLField("Link Externo", blank=True)
    thumbnail = models.ImageField("Imagem de Capa", upload_to='members/thumbs/',
                                   blank=True, null=True, validators=[validate_image])
    published = models.BooleanField("Publicado", default=True)
    featured = models.BooleanField("Destaque", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                blank=True, verbose_name="Autor",
                                related_name='authored_content')

    class Meta:
        verbose_name = "Conteúdo Exclusivo"
        verbose_name_plural = "Conteúdos Exclusivos"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_embed_url(self):
        url = self.video_url
        if 'youtube.com/watch?v=' in url:
            vid = url.split('v=')[1].split('&')[0]
            return f'https://www.youtube.com/embed/{vid}'
        if 'youtu.be/' in url:
            vid = url.split('youtu.be/')[1].split('?')[0]
            return f'https://www.youtube.com/embed/{vid}'
        if 'vimeo.com/' in url:
            vid = url.split('vimeo.com/')[1]
            return f'https://player.vimeo.com/video/{vid}'
        return url


class Testimony(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Aguardando Aprovação'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
    ]
    profile = models.ForeignKey(MemberProfile, on_delete=models.CASCADE,
                                 related_name='testimonies', verbose_name="Membro")
    text = models.TextField("Testemunho", max_length=1500)
    status = models.CharField("Status", max_length=20,
                               choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField("Observação do Admin", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Testemunho de Membro"
        verbose_name_plural = "Testemunhos de Membros (Aprovação)"
        ordering = ['-created_at']

    def __str__(self):
        return f"Testemunho de {self.profile.full_name} ({self.get_status_display()})"


class Notice(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='notices'
    )
    PRIORITY_CHOICES = [
        ('normal',    'Normal'),
        ('important', 'Importante'),
        ('urgent',    'Urgente'),
    ]
    title = models.CharField("Título", max_length=200)
    body = models.TextField("Texto do Aviso")
    priority = models.CharField("Prioridade", max_length=20,
                                 choices=PRIORITY_CHOICES, default='normal')
    published = models.BooleanField("Publicado", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField("Expira em", null=True, blank=True)

    class Meta:
        verbose_name = "Aviso Interno"
        verbose_name_plural = "Avisos Internos"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class PrayerRequest(models.Model):
    VISIBILITY_CHOICES = [
        ('private', 'Privado — só a liderança vê'),
        ('members', 'Membros — visível na área de membros'),
    ]
    STATUS_CHOICES = [
        ('open',     'Aberto'),
        ('answered', 'Respondido'),
        ('closed',   'Encerrado'),
    ]
    profile = models.ForeignKey(MemberProfile, on_delete=models.CASCADE,
                                 related_name='prayer_requests', verbose_name="Membro")
    title = models.CharField("Título", max_length=150)
    description = models.TextField("Descrição", max_length=1000)
    visibility = models.CharField("Visibilidade", max_length=20,
                                   choices=VISIBILITY_CHOICES, default='private')
    status = models.CharField("Status", max_length=20,
                               choices=STATUS_CHOICES, default='open')
    admin_note = models.TextField("Resposta da liderança", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pedido de Oração"
        verbose_name_plural = "Pedidos de Oração"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.profile.full_name}"


class DeleteRequest(models.Model):
    """Colaborador solicita ao admin autorização para excluir um conteúdo."""
    CONTENT_TYPE_CHOICES = [
        ('media',      'Item de Mídia'),
        ('content',    'Conteúdo Exclusivo'),
        ('devotional', 'Devocional'),
        ('heroslide',  'Banner da Página Principal'),
        ('album',      'Álbum de Fotos'),
        ('event',      'Evento'),
        ('notice',     'Aviso Interno'),
    ]
    STATUS_CHOICES = [
        ('pending',  'Aguardando'),
        ('approved', 'Aprovado'),
        ('rejected', 'Recusado'),
    ]
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                      related_name='delete_requests',
                                      verbose_name='Solicitado por')
    content_type = models.CharField('Tipo de conteúdo', max_length=30,
                                     choices=CONTENT_TYPE_CHOICES)
    object_id = models.PositiveIntegerField('ID do objeto')
    object_title = models.CharField('Título do item', max_length=255)
    reason = models.TextField('Motivo da exclusão', blank=True)
    status = models.CharField('Status', max_length=20,
                               choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField('Resposta do admin', blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                     null=True, blank=True,
                                     related_name='reviewed_delete_requests',
                                     verbose_name='Revisado por')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Solicitação de Exclusão'
        verbose_name_plural = 'Solicitações de Exclusão'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_content_type_display()} "{self.object_title}" — {self.get_status_display()}'


class PasswordResetToken(models.Model):
    """Token de redefinição de senha — gerado ao solicitar reset."""
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='reset_tokens',
                              verbose_name='Usuário')
    token = models.CharField('Token', max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField('Usado', default=False)

    class Meta:
        verbose_name = 'Token de Reset de Senha'
        verbose_name_plural = 'Tokens de Reset de Senha'
        ordering = ['-created_at']

    def __str__(self):
        return f'Reset — {self.user.email} — {"usado" if self.used else "válido"}'

    def is_valid(self):
        """Token válido por 24 horas e não usado."""
        from django.utils import timezone
        from datetime import timedelta
        return (
            not self.used and
            self.created_at >= timezone.now() - timedelta(hours=24)
        )


# ══════════════════════════════════════════════════════════
# ── Controle de Presenças ─────────────────────────────────
# ══════════════════════════════════════════════════════════

class Culto(models.Model):
    """Registro de um culto ou reunião para controle de presença."""
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='cultos'
    )
    TYPE_CHOICES = [
        ('culto_domingo_manha', 'Culto Domingo Manhã'),
        ('culto_domingo_noite', 'Culto Domingo Noite'),
        ('culto_semana',        'Culto de Semana'),
        ('culto_oracao',        'Culto de Oração'),
        ('celula',              'Reunião de Célula'),
        ('conferencia',         'Conferência / Evento Especial'),
        ('outro',               'Outro'),
    ]
    title = models.CharField('Título', max_length=200, blank=True,
                              help_text='Deixe vazio para usar o tipo como título')
    culto_type = models.CharField('Tipo', max_length=30,
                                   choices=TYPE_CHOICES, default='culto_domingo_manha')
    date = models.DateField('Data')
    notes = models.TextField('Observações', blank=True)
    visitor_count = models.PositiveSmallIntegerField('Número de visitantes', default=0)
    visitor_names = models.TextField('Nomes dos visitantes', blank=True,
                                     help_text='Um nome por linha')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                    null=True, related_name='cultos_created',
                                    verbose_name='Criado por')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Culto / Reunião'
        verbose_name_plural = 'Cultos / Reuniões'
        ordering = ['-date', '-created_at']

    def __str__(self):
        label = self.title or self.get_culto_type_display()
        return f'{label} — {self.date.strftime("%d/%m/%Y")}'

    def presence_count(self):
        return self.presences.filter(present=True).count()

    def total_members(self):
        return self.presences.count()


class Presenca(models.Model):
    """Presença de um membro em um culto."""
    culto = models.ForeignKey(Culto, on_delete=models.CASCADE,
                               related_name='presences', verbose_name='Culto')
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE,
                                related_name='presences', verbose_name='Membro')
    present = models.BooleanField('Presente', default=False)
    noted_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='presences_noted',
                                  verbose_name='Registrado por')

    class Meta:
        verbose_name = 'Presença'
        verbose_name_plural = 'Presenças'
        unique_together = ('culto', 'member')
        ordering = ['member__user__first_name']

    def __str__(self):
        status = '✓' if self.present else '✗'
        return f'{status} {self.member.full_name} — {self.culto}'