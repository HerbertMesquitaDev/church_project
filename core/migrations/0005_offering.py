from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_devotional'),
        ('members', '0003_prayerrequest'),
    ]

    operations = [
        migrations.AddField(model_name='sitesettings', name='pix_key',
            field=models.CharField(blank=True, help_text='CPF, CNPJ, e-mail, telefone ou chave aleatória', max_length=200, verbose_name='Chave PIX')),
        migrations.AddField(model_name='sitesettings', name='pix_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='Nome do titular PIX')),
        migrations.AddField(model_name='sitesettings', name='bank_name',
            field=models.CharField(blank=True, max_length=100, verbose_name='Banco')),
        migrations.AddField(model_name='sitesettings', name='bank_agency',
            field=models.CharField(blank=True, max_length=20, verbose_name='Agência')),
        migrations.AddField(model_name='sitesettings', name='bank_account',
            field=models.CharField(blank=True, max_length=40, verbose_name='Conta')),
        migrations.AddField(model_name='sitesettings', name='bank_holder',
            field=models.CharField(blank=True, max_length=150, verbose_name='Titular da conta')),
        migrations.AddField(model_name='sitesettings', name='offering_text',
            field=models.TextField(blank=True, help_text='Mensagem exibida acima dos dados de pagamento', verbose_name='Texto de apresentação das ofertas')),
        migrations.CreateModel(
            name='Offering',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('tithe','Dízimo'),('offering','Oferta'),('mission','Missões'),('building','Fundo de Obras'),('other','Outro')], default='tithe', max_length=20, verbose_name='Tipo')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valor (R$)')),
                ('date', models.DateField(verbose_name='Data')),
                ('notes', models.TextField(blank=True, verbose_name='Observações')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offerings', to='members.memberprofile', verbose_name='Membro')),
            ],
            options={'verbose_name': 'Contribuição', 'verbose_name_plural': 'Contribuições', 'ordering': ['-date', '-created_at']},
        ),
    ]
