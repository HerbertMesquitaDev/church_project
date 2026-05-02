from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_socialconfig_socialpost'),
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialpost',
            name='source_type',
            field=models.CharField(
                choices=[('album', 'Álbum de Fotos'), ('event', 'Evento')],
                default='album',
                max_length=10,
                verbose_name='Origem',
            ),
        ),
        migrations.AddField(
            model_name='socialpost',
            name='event',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='social_posts',
                to='events.event',
                verbose_name='Evento',
            ),
        ),
        migrations.AlterField(
            model_name='socialpost',
            name='album',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='social_posts',
                to='core.photoalbum',
                verbose_name='Álbum',
            ),
        ),
    ]
