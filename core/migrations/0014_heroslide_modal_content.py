from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_alter_sitesettings_church_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='heroslide',
            name='button_modal_content',
            field=models.TextField(
                blank=True,
                help_text='Se preenchido, o botão abre uma modal com este texto em vez de navegar para o link.',
                verbose_name='Conteúdo da Modal (1º Botão)',
            ),
        ),
        migrations.AddField(
            model_name='heroslide',
            name='button_modal_content_2',
            field=models.TextField(
                blank=True,
                help_text='Se preenchido, o 2º botão abre uma modal com este texto.',
                verbose_name='Conteúdo da Modal (2º Botão)',
            ),
        ),
    ]
