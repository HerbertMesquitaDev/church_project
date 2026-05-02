from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Testimony',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField('Testemunho', max_length=1500)),
                ('status', models.CharField(
                    'Status',
                    max_length=20,
                    choices=[
                        ('pending', 'Aguardando Aprovação'),
                        ('approved', 'Aprovado'),
                        ('rejected', 'Rejeitado'),
                    ],
                    default='pending',
                )),
                ('admin_note', models.TextField('Observação do Admin', blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('profile', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='testimonies',
                    to='members.memberprofile',
                    verbose_name='Membro',
                )),
            ],
            options={
                'verbose_name': 'Testemunho',
                'verbose_name_plural': 'Testemunhos',
                'ordering': ['-created_at'],
            },
        ),
    ]
