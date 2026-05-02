from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_sitesettings_colors'),
    ]

    operations = [
        migrations.CreateModel(
            name='Devotional',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Título')),
                ('verse', models.CharField(help_text='Ex: João 3:16, Salmos 23:1', max_length=200, verbose_name='Versículo de Referência')),
                ('verse_text', models.TextField(verbose_name='Texto do Versículo')),
                ('reflection', models.TextField(verbose_name='Reflexão')),
                ('prayer', models.TextField(blank=True, verbose_name='Oração do Dia')),
                ('author', models.CharField(blank=True, max_length=150, verbose_name='Autor / Pastor')),
                ('pub_date', models.DateField(unique=True, verbose_name='Data de Publicação')),
                ('published', models.BooleanField(default=True, verbose_name='Publicado')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Devocional',
                'verbose_name_plural': 'Devocionais',
                'ordering': ['-pub_date'],
            },
        ),
    ]
