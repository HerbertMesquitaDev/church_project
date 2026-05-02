from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_offering'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='notification_email',
            field=models.EmailField(blank=True, help_text='Recebe alertas de novos visitantes e pedidos de contato', max_length=254, verbose_name='E-mail para notificações'),
        ),
        migrations.CreateModel(
            name='Visitor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Nome completo')),
                ('email', models.EmailField(blank=True, verbose_name='E-mail')),
                ('phone', models.CharField(blank=True, max_length=30, verbose_name='Telefone / WhatsApp')),
                ('visit_date', models.DateField(verbose_name='Data da Visita')),
                ('how_found', models.CharField(
                    choices=[('friend','Indicação de amigo/familiar'),('social','Redes Sociais'),('passing_by','Passando pela frente'),('search','Pesquisa na internet'),('event','Evento/Atividade'),('other','Outro')],
                    default='friend', max_length=20, verbose_name='Como conheceu a igreja',
                )),
                ('how_found_other', models.CharField(blank=True, max_length=150, verbose_name='Outro (especifique)')),
                ('wants_ministry', models.BooleanField(default=False, verbose_name='Interesse em participar de ministério')),
                ('ministry_interest', models.CharField(blank=True, max_length=200, verbose_name='Qual ministério?')),
                ('message', models.TextField(blank=True, verbose_name='Mensagem / Observações')),
                ('contacted', models.BooleanField(default=False, verbose_name='Já foi contatado')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Visitante', 'verbose_name_plural': 'Visitantes', 'ordering': ['-created_at']},
        ),
    ]
