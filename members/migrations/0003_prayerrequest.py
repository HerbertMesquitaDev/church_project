from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0002_testimony'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrayerRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=150, verbose_name='Título')),
                ('description', models.TextField(max_length=1000, verbose_name='Descrição')),
                ('visibility', models.CharField(
                    choices=[('private', 'Privado — só a liderança vê'), ('members', 'Membros — visível na área de membros')],
                    default='private', max_length=20, verbose_name='Visibilidade',
                )),
                ('status', models.CharField(
                    choices=[('open', 'Aberto'), ('answered', 'Respondido'), ('closed', 'Encerrado')],
                    default='open', max_length=20, verbose_name='Status',
                )),
                ('admin_note', models.TextField(blank=True, verbose_name='Resposta da liderança')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('profile', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='prayer_requests',
                    to='members.memberprofile',
                    verbose_name='Membro',
                )),
            ],
            options={
                'verbose_name': 'Pedido de Oração',
                'verbose_name_plural': 'Pedidos de Oração',
                'ordering': ['-created_at'],
            },
        ),
    ]
