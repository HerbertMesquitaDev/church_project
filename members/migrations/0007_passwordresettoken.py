from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_memberprofile_role_deleterequest'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=64, unique=True, verbose_name='Token')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('used', models.BooleanField(default=False, verbose_name='Usado')),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='reset_tokens',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuário',
                )),
            ],
            options={
                'verbose_name': 'Token de Reset de Senha',
                'verbose_name_plural': 'Tokens de Reset de Senha',
                'ordering': ['-created_at'],
            },
        ),
    ]
