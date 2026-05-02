from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_media'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhotoAlbum',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Título do Álbum')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('cover', models.ImageField(blank=True, null=True, upload_to='gallery/covers/', verbose_name='Foto de Capa')),
                ('event_date', models.DateField(blank=True, null=True, verbose_name='Data do Evento')),
                ('published', models.BooleanField(default=True, verbose_name='Publicado')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Álbum de Fotos', 'verbose_name_plural': 'Álbuns de Fotos', 'ordering': ['-event_date', '-created_at']},
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='gallery/photos/', verbose_name='Foto')),
                ('caption', models.CharField(blank=True, max_length=300, verbose_name='Legenda')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('album', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='core.photoalbum', verbose_name='Álbum')),
            ],
            options={'verbose_name': 'Foto', 'verbose_name_plural': 'Fotos', 'ordering': ['order', 'created_at']},
        ),
    ]
