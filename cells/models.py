from django.db import models
from django.contrib.auth.models import User
from tenants.models import Igreja
from core.validators import validate_image, validate_generic_file


class Cell(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='cells'
    )
    TYPE_CHOICES = [
        ('ministry', 'Por Ministério'),
        ('region',   'Por Região/Bairro'),
        ('other',    'Outro'),
    ]
    name = models.CharField("Nome do Grupo", max_length=150)
    cell_type = models.CharField("Tipo", max_length=20,
                                  choices=TYPE_CHOICES, default='ministry')
    description = models.TextField("Descrição", blank=True)
    cover = models.ImageField("Imagem de Capa", upload_to='cells/covers/',
                               blank=True, null=True, validators=[validate_image])
    region = models.CharField("Região/Bairro", max_length=150, blank=True)
    meeting_day = models.CharField("Dia de Reunião", max_length=100, blank=True,
                                    help_text="Ex: Quartas-feiras às 20h")
    meeting_place = models.CharField("Local de Reunião", max_length=200, blank=True)
    active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Célula"
        verbose_name_plural = "Células"
        ordering = ['cell_type', 'name']

    def __str__(self):
        return self.name

    def member_count(self):
        return self.memberships.filter(status='approved').count()


class CellMembership(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Aguardando Aprovação'),
        ('approved', 'Aprovado'),
        ('rejected', 'Rejeitado'),
        ('left',     'Saiu'),
    ]
    ROLE_CHOICES = [
        ('member', 'Membro'),
        ('leader', 'Líder'),
    ]
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE,
                              related_name='memberships', verbose_name="Célula")
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='cell_memberships', verbose_name="Membro")
    status = models.CharField("Status", max_length=15,
                               choices=STATUS_CHOICES, default='pending')
    role = models.CharField("Papel", max_length=15,
                             choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Membro da Célula"
        verbose_name_plural = "Membros das Células"
        unique_together = ('cell', 'user')
        ordering = ['role', 'joined_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.cell.name}"


class CellPost(models.Model):
    TYPE_CHOICES = [
        ('message', 'Mensagem'),
        ('prayer',  'Pedido de Oração'),
        ('file',    'Arquivo'),
        ('notice',  'Aviso do Líder'),
    ]
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE,
                              related_name='posts', verbose_name="Célula")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='cell_posts', verbose_name="Autor")
    post_type = models.CharField("Tipo", max_length=15,
                                  choices=TYPE_CHOICES, default='message')
    content = models.TextField("Mensagem")
    file = models.FileField("Arquivo", upload_to='cells/files/', blank=True, null=True, validators=[validate_generic_file])
    pinned = models.BooleanField("Fixado", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Post da Célula"
        verbose_name_plural = "Posts das Células"
        ordering = ['-pinned', '-created_at']

    def __str__(self):
        return f"{self.get_post_type_display()} — {self.cell.name}"


class CellPostReaction(models.Model):
    post = models.ForeignKey(CellPost, on_delete=models.CASCADE,
                              related_name='reactions', verbose_name="Post")
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name='cell_reactions', verbose_name="Membro")
    emoji = models.CharField("Emoji", max_length=10, default='🙏')

    class Meta:
        verbose_name = "Reação"
        verbose_name_plural = "Reações"
        unique_together = ('post', 'user', 'emoji')

    def __str__(self):
        return f"{self.emoji} por {self.user}"