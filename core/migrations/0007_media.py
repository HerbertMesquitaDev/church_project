from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_visitor'),
    ]

    operations = [
        migrations.CreateModel(
            name='MediaCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome')),
                ('section', models.CharField(
                    choices=[('sermons','Pregações'),('worship','Louvores'),('studies','Estudos'),('live','Ao Vivo'),('other','Outros')],
                    default='sermons', max_length=20, verbose_name='Seção',
                )),
                ('icon', models.CharField(default='fa-play', help_text='Ex: fa-microphone, fa-music, fa-book-open', max_length=80, verbose_name='Ícone FA')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
            ],
            options={'verbose_name': 'Categoria de Mídia', 'verbose_name_plural': 'Categorias de Mídia', 'ordering': ['order', 'name']},
        ),
        migrations.CreateModel(
            name='MediaItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Título')),
                ('media_type', models.CharField(
                    choices=[('video','Vídeo (YouTube/Vimeo)'),('audio','Áudio'),('pdf','Estudo em PDF'),('live','Transmissão Ao Vivo')],
                    default='video', max_length=10, verbose_name='Tipo',
                )),
                ('visibility', models.CharField(
                    choices=[('public','Público'),('members','Só para membros')],
                    default='public', max_length=10, verbose_name='Visibilidade',
                )),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('video_url', models.URLField(blank=True, verbose_name='URL do Vídeo/Live (YouTube/Vimeo)')),
                ('audio_file', models.FileField(blank=True, null=True, upload_to='media/audio/', verbose_name='Arquivo de Áudio')),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='media/pdf/', verbose_name='Arquivo PDF')),
                ('thumbnail', models.ImageField(blank=True, null=True, upload_to='media/thumbs/', verbose_name='Capa')),
                ('speaker', models.CharField(blank=True, max_length=150, verbose_name='Pregador / Autor')),
                ('published', models.BooleanField(default=True, verbose_name='Publicado')),
                ('featured', models.BooleanField(default=False, verbose_name='Destaque')),
                ('pub_date', models.DateField(blank=True, null=True, verbose_name='Data')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='items', to='core.mediacategory', verbose_name='Categoria')),
            ],
            options={'verbose_name': 'Item de Mídia', 'verbose_name_plural': 'Midiateca', 'ordering': ['-pub_date', '-created_at']},
        ),
    ]
