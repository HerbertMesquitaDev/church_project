from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nome do Local')),
                ('address', models.CharField(blank=True, max_length=400, verbose_name='Endereço')),
                ('capacity', models.PositiveIntegerField(blank=True, null=True, verbose_name='Capacidade')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Local',
                'verbose_name_plural': 'Locais',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Título / Descrição')),
                ('ministry', models.CharField(blank=True, max_length=150, verbose_name='Ministério / Grupo')),
                ('date', models.DateField(verbose_name='Data')),
                ('start_time', models.TimeField(verbose_name='Horário de Início')),
                ('end_time', models.TimeField(verbose_name='Horário de Término')),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Aguardando Aprovação'),
                        ('approved', 'Aprovado'),
                        ('rejected', 'Recusado'),
                        ('cancelled', 'Cancelado'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Status',
                )),
                ('approved_at', models.DateTimeField(blank=True, null=True, verbose_name='Aprovado em')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('location', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='bookings',
                    to='agenda.location',
                    verbose_name='Local',
                )),
                ('responsible', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='bookings',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Responsável',
                )),
                ('approved_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='approved_bookings',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Aprovado por',
                )),
            ],
            options={
                'verbose_name': 'Agendamento',
                'verbose_name_plural': 'Agendamentos',
                'ordering': ['date', 'start_time'],
            },
        ),
    ]
