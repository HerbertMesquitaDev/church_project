from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0008_culto_presenca'),
    ]

    operations = [
        migrations.AddField(
            model_name='culto',
            name='visitor_count',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Número de visitantes'),
        ),
        migrations.AddField(
            model_name='culto',
            name='visitor_names',
            field=models.TextField(blank=True, help_text='Um nome por linha', verbose_name='Nomes dos visitantes'),
        ),
    ]
