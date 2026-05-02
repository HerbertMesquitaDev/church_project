from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0007_passwordresettoken'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Culto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, help_text='Deixe vazio para usar o tipo como título', max_length=200, verbose_name='Título')),
                ('culto_type', models.CharField(
                    choices=[
                        ('culto_domingo_manha', 'Culto Domingo Manhã'),
                        ('culto_domingo_noite', 'Culto Domingo Noite'),
                        ('culto_semana', 'Culto de Semana'),
                        ('culto_oracao', 'Culto de Oração'),
                        ('celula', 'Reunião de Célula'),
                        ('conferencia', 'Conferência / Evento Especial'),
                        ('outro', 'Outro'),
                    ],
                    default='culto_domingo_manha',
                    max_length=30,
                    verbose_name='Tipo',
                )),
                ('date', models.DateField(verbose_name='Data')),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='cultos_created',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Criado por',
                )),
            ],
            options={
                'verbose_name': 'Culto / Reunião',
                'verbose_name_plural': 'Cultos / Reuniões',
                'ordering': ['-date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Presenca',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('present', models.BooleanField(default=False, verbose_name='Presente')),
                ('culto', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='presences',
                    to='members.culto',
                    verbose_name='Culto',
                )),
                ('member', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='presences',
                    to='members.memberprofile',
                    verbose_name='Membro',
                )),
                ('noted_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='presences_noted',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Registrado por',
                )),
            ],
            options={
                'verbose_name': 'Presença',
                'verbose_name_plural': 'Presenças',
                'ordering': ['member__user__first_name'],
                'unique_together': {('culto', 'member')},
            },
        ),
    ]
