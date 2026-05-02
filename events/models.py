from django.db import models
from django.urls import reverse
from tenants.models import Igreja
from django.utils import timezone
from core.validators import validate_image


class Category(models.Model):
    igreja = models.ForeignKey(Igreja, on_delete=models.CASCADE, verbose_name="Igreja", null=True, blank=True, related_name="event_categories")
    name = models.CharField("Nome", max_length=100)
    color = models.CharField("Cor (hex)", max_length=7, default="#8B6914",
                              help_text="Ex: #8B6914")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.name


class Event(models.Model):
    igreja = models.ForeignKey(Igreja, on_delete=models.CASCADE, verbose_name="Igreja", null=True, blank=True, related_name="events")
    RECURRENCE_CHOICES = [
        ('none', 'Sem Recorrência'),
        ('weekly', 'Semanal'),
        ('biweekly', 'Quinzenal'),
        ('monthly', 'Mensal'),
    ]

    title = models.CharField("Título", max_length=200)
    slug = models.SlugField("Slug (URL)", unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="Categoria")
    description = models.TextField("Descrição")
    short_description = models.CharField("Descrição Curta", max_length=300, blank=True)
    date = models.DateTimeField("Data e Hora")
    end_date = models.DateTimeField("Data/Hora Final", null=True, blank=True)
    location = models.CharField("Local", max_length=300, blank=True)
    address = models.CharField("Endereço Completo", max_length=500, blank=True)
    image = models.ImageField("Imagem", upload_to='events/', blank=True, null=True, validators=[validate_image])
    recurrence = models.CharField("Recorrência", max_length=20,
                                   choices=RECURRENCE_CHOICES, default='none')
    meta_description = models.CharField("Meta description (SEO)", max_length=160, blank=True,
                                         help_text="Resumo para o Google (max 160 caracteres). Se vazio, usa a Descrição Curta.")
    published = models.BooleanField("Publicado", default=True)
    featured = models.BooleanField("Destaque", default=False)
    registration_link      = models.URLField("Link de Inscrição Externo", blank=True,
                                              help_text="Deixe em branco para usar o sistema interno")
    requires_registration  = models.BooleanField("Requer Inscrição", default=False)
    max_spots              = models.PositiveIntegerField("Vagas", null=True, blank=True,
                                                          help_text="Deixe em branco para vagas ilimitadas")
    registration_deadline  = models.DateTimeField("Prazo de Inscrição", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['date']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'slug': self.slug})

    @property
    def is_upcoming(self):
        return self.date >= timezone.now()

    @property
    def is_past(self):
        return self.date < timezone.now()

    @property
    def spots_taken(self):
        return self.registrations.filter(status='confirmed').count()

    @property
    def spots_available(self):
        if self.max_spots is None:
            return None
        return max(0, self.max_spots - self.spots_taken)

    @property
    def is_full(self):
        if self.max_spots is None:
            return False
        return self.spots_taken >= self.max_spots

    @property
    def waitlist_count(self):
        return self.registrations.filter(status='waitlist').count()

    @property
    def registration_open(self):
        from django.utils import timezone as tz
        if not self.requires_registration:
            return False
        if self.is_past:
            return False
        if self.registration_deadline and tz.now() > self.registration_deadline:
            return False
        return True

    @property
    def display_date(self):
        return self.date.strftime("%d/%m/%Y às %H:%M")


class EventRegistration(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmado'),
        ('waitlist',  'Lista de Espera'),
        ('cancelled', 'Cancelado'),
    ]

    event      = models.ForeignKey(Event, on_delete=models.CASCADE,
                                    related_name='registrations', verbose_name="Evento")
    user       = models.ForeignKey('auth.User', on_delete=models.CASCADE,
                                    related_name='event_registrations', verbose_name="Membro")
    status     = models.CharField("Status", max_length=15,
                                   choices=STATUS_CHOICES, default='confirmed')
    notes      = models.TextField("Observações", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name         = "Inscrição"
        verbose_name_plural  = "Inscrições"
        unique_together      = ('event', 'user')
        ordering             = ['created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.event.title}"
