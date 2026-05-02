from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0004_alter_testimony_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberprofile',
            name='image_consent',
            field=models.BooleanField(
                default=False,
                verbose_name='Autorização de uso de imagem',
                help_text='O membro autorizou o uso de sua imagem conforme o Termo LGPD'
            ),
        ),
        migrations.AddField(
            model_name='memberprofile',
            name='image_consent_date',
            field=models.DateTimeField(
                null=True, blank=True,
                verbose_name='Data/hora do consentimento'
            ),
        ),
        migrations.AddField(
            model_name='memberprofile',
            name='image_consent_ip',
            field=models.GenericIPAddressField(
                null=True, blank=True,
                verbose_name='IP do consentimento'
            ),
        ),
        migrations.AddField(
            model_name='memberprofile',
            name='image_consent_revoked',
            field=models.BooleanField(
                default=False,
                verbose_name='Consentimento revogado'
            ),
        ),
        migrations.AddField(
            model_name='memberprofile',
            name='image_consent_revoked_date',
            field=models.DateTimeField(
                null=True, blank=True,
                verbose_name='Data/hora da revogação'
            ),
        ),
    ]
