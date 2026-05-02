from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='requires_registration',
            field=models.BooleanField(default=False, verbose_name='Requer Inscrição'),
        ),
        migrations.AddField(
            model_name='event',
            name='max_spots',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Vagas',
                help_text='Deixe em branco para vagas ilimitadas'),
        ),
        migrations.AddField(
            model_name='event',
            name='registration_deadline',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Prazo de Inscrição'),
        ),
        migrations.AlterField(
            model_name='event',
            name='registration_link',
            field=models.URLField(blank=True, verbose_name='Link de Inscrição Externo',
                help_text='Deixe em branco para usar o sistema interno'),
        ),
        migrations.CreateModel(
            name='EventRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[('confirmed','Confirmado'),('waitlist','Lista de Espera'),('cancelled','Cancelado')],
                    default='confirmed', max_length=15, verbose_name='Status',
                )),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='registrations', to='events.event', verbose_name='Evento')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                    related_name='event_registrations', to='auth.user', verbose_name='Membro')),
            ],
            options={
                'verbose_name': 'Inscrição',
                'verbose_name_plural': 'Inscrições',
                'ordering': ['created_at'],
                'unique_together': {('event', 'user')},
            },
        ),
    ]
