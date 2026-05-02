from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from tenants.models import Igreja


class Location(models.Model):
    """Locais disponíveis para agendamento (ex: SEDE, JD AEROPORTO, etc.)"""
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='locations'
    )
    name = models.CharField("Nome do Local", max_length=200)
    address = models.CharField("Endereço", max_length=400, blank=True)
    capacity = models.PositiveIntegerField("Capacidade", null=True, blank=True)
    description = models.TextField("Descrição", blank=True)
    active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Local"
        verbose_name_plural = "Locais"
        ordering = ['name']

    def __str__(self):
        return self.name


class Booking(models.Model):
    """Agendamento de um local para um evento/reunião em determinado dia e horário."""
    STATUS_CHOICES = [
        ('pending',   'Aguardando Aprovação'),
        ('approved',  'Aprovado'),
        ('rejected',  'Recusado'),
        ('cancelled', 'Cancelado'),
    ]
    title = models.CharField("Título / Descrição", max_length=200)
    location = models.ForeignKey(Location, on_delete=models.PROTECT,
                                  verbose_name="Local", related_name='bookings')
    responsible = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     verbose_name="Responsável", related_name='bookings')
    ministry = models.CharField("Ministério / Grupo", max_length=150, blank=True)
    date = models.DateField("Data")
    start_time = models.TimeField("Horário de Início")
    end_time = models.TimeField("Horário de Término")
    notes = models.TextField("Observações", blank=True)
    status = models.CharField("Status", max_length=20,
                               choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                     blank=True, verbose_name="Aprovado por",
                                     related_name='approved_bookings')
    approved_at = models.DateTimeField("Aprovado em", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.title} — {self.location} ({self.date} {self.start_time}–{self.end_time})"

    def clean(self):
        if not all([self.location_id, self.date, self.start_time, self.end_time]):
            return
        if self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': "O horário de término deve ser após o horário de início."
            })
        conflicts = Booking.objects.filter(
            location=self.location,
            date=self.date,
            status__in=['pending', 'approved'],
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        )
        if self.pk:
            conflicts = conflicts.exclude(pk=self.pk)
        if conflicts.exists():
            conflict = conflicts.first()
            raise ValidationError(
                f"Conflito de agendamento: '{conflict.title}' já está agendado em "
                f"{self.location} no dia {self.date.strftime('%d/%m/%Y')} "
                f"das {conflict.start_time.strftime('%H:%M')} às {conflict.end_time.strftime('%H:%M')}."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def duration_hours(self):
        from datetime import datetime, date
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        diff = (end - start).seconds // 60
        h, m = divmod(diff, 60)
        return f"{h}h{m:02d}" if m else f"{h}h"

    @property
    def status_color(self):
        return {
            'pending':   '#f39c12',
            'approved':  '#27ae60',
            'rejected':  '#e74c3c',
            'cancelled': '#95a5a6',
        }.get(self.status, '#999')

    @property
    def is_past(self):
        from datetime import datetime
        now = timezone.localtime(timezone.now())
        booking_end = timezone.make_aware(
            datetime.combine(self.date, self.end_time)
        )
        return booking_end < now