from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_sitesettings_maps_url'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ig_user_id',       models.CharField(blank=True, max_length=50, verbose_name='Instagram User ID')),
                ('ig_access_token',  models.TextField(blank=True, verbose_name='Instagram Access Token')),
                ('fb_page_id',       models.CharField(blank=True, max_length=50, verbose_name='Facebook Page ID')),
                ('fb_access_token',  models.TextField(blank=True, verbose_name='Facebook Page Access Token')),
                ('site_base_url',    models.URLField(blank=True, help_text='Ex: https://meusite.com.br — sem barra no final', verbose_name='URL pública do site')),
                ('updated_at',       models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Configuração de Redes Sociais', 'verbose_name_plural': 'Configurações de Redes Sociais'},
        ),
        migrations.CreateModel(
            name='SocialPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('platform',      models.CharField(choices=[('instagram','Instagram'),('facebook','Facebook'),('both','Instagram + Facebook')], default='both', max_length=15, verbose_name='Plataforma')),
                ('post_format',   models.CharField(choices=[('single','Foto única'),('carousel','Carrossel'),('album_fb','Álbum Facebook')], default='carousel', max_length=15, verbose_name='Formato')),
                ('caption',       models.TextField(verbose_name='Legenda')),
                ('hashtags',      models.TextField(blank=True, help_text='Uma por linha, sem #', verbose_name='Hashtags')),
                ('status',        models.CharField(choices=[('draft','Rascunho'),('queued','Na fila'),('published','Publicado'),('failed','Falhou'),('partial','Publicado com erros')], default='draft', max_length=15, verbose_name='Status')),
                ('ig_post_id',    models.CharField(blank=True, max_length=100, verbose_name='ID post Instagram')),
                ('ig_permalink',  models.URLField(blank=True, verbose_name='Link Instagram')),
                ('ig_error',      models.TextField(blank=True, verbose_name='Erro Instagram')),
                ('fb_post_id',    models.CharField(blank=True, max_length=100, verbose_name='ID post Facebook')),
                ('fb_permalink',  models.URLField(blank=True, verbose_name='Link Facebook')),
                ('fb_error',      models.TextField(blank=True, verbose_name='Erro Facebook')),
                ('scheduled_for', models.DateTimeField(blank=True, null=True, verbose_name='Agendar para')),
                ('published_at',  models.DateTimeField(blank=True, null=True, verbose_name='Publicado em')),
                ('created_at',    models.DateTimeField(auto_now_add=True)),
                ('updated_at',    models.DateTimeField(auto_now=True)),
                ('album',         models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_posts', to='core.photoalbum', verbose_name='Álbum')),
                ('created_by',    models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='social_posts', to=settings.AUTH_USER_MODEL, verbose_name='Criado por')),
                ('photos',        models.ManyToManyField(blank=True, to='core.photo', verbose_name='Fotos selecionadas')),
            ],
            options={'verbose_name': 'Publicação Social', 'verbose_name_plural': 'Publicações Sociais', 'ordering': ['-created_at']},
        ),
    ]
