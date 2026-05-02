from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_heroslide'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='color_primary',
            field=models.CharField(
                default='#C9A84C',
                help_text='Cor principal do site. Ex: #C9A84C',
                max_length=7,
                verbose_name='Cor Primária (Dourado)',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='color_secondary',
            field=models.CharField(
                default='#1A2340',
                help_text='Cor de títulos e navbar. Ex: #1A2340',
                max_length=7,
                verbose_name='Cor Secundária (Navy)',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='color_accent',
            field=models.CharField(
                default='#8B6914',
                help_text='Usada em hovers e destaques. Ex: #8B6914',
                max_length=7,
                verbose_name='Cor de Destaque (Dourado escuro)',
            ),
        ),
    ]
