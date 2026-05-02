from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0005_memberprofile_lgpd_consent'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='memberprofile',
            name='role',
            field=models.CharField(
                choices=[
                    ('member', 'Membro'),
                    ('collaborator', 'Colaborador'),
                    ('admin', 'Administrador'),
                ],
                default='member',
                help_text='Define as permissões do usuário no portal',
                max_length=20,
                verbose_name='Grupo / Perfil',
            ),
        ),
        migrations.CreateModel(
            name='DeleteRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(
                    choices=[
                        ('media', 'Item de Mídia'),
                        ('content', 'Conteúdo Exclusivo'),
                        ('devotional', 'Devocional'),
                        ('heroslide', 'Banner da Página Principal'),
                        ('album', 'Álbum de Fotos'),
                        ('event', 'Evento'),
                        ('notice', 'Aviso Interno'),
                    ],
                    max_length=30,
                    verbose_name='Tipo de conteúdo',
                )),
                ('object_id', models.PositiveIntegerField(verbose_name='ID do objeto')),
                ('object_title', models.CharField(max_length=255, verbose_name='Título do item')),
                ('reason', models.TextField(blank=True, verbose_name='Motivo da exclusão')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'Aguardando'),
                        ('approved', 'Aprovado'),
                        ('rejected', 'Recusado'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Status',
                )),
                ('admin_note', models.TextField(blank=True, verbose_name='Resposta do admin')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('requested_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='delete_requests',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Solicitado por',
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_delete_requests',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Revisado por',
                )),
            ],
            options={
                'verbose_name': 'Solicitação de Exclusão',
                'verbose_name_plural': 'Solicitações de Exclusão',
                'ordering': ['-created_at'],
            },
        ),
    ]
