from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_merge_0008_alter_testimony_options_0008_gallery'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='maps_url',
            field=models.URLField(
                blank=True,
                verbose_name='Link do Google Maps',
                help_text="Cole aqui o link 'Compartilhar' do Google Maps (ex: https://maps.app.goo.gl/...)"
            ),
        ),
    ]
