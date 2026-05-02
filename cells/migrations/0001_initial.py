from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cell',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, verbose_name='Nome do Grupo')),
                ('cell_type', models.CharField(choices=[('ministry','Por Ministério'),('region','Por Região/Bairro'),('other','Outro')], default='ministry', max_length=20, verbose_name='Tipo')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('cover', models.ImageField(blank=True, null=True, upload_to='cells/covers/', verbose_name='Imagem de Capa')),
                ('region', models.CharField(blank=True, max_length=150, verbose_name='Região/Bairro')),
                ('meeting_day', models.CharField(blank=True, help_text='Ex: Quartas-feiras às 20h', max_length=100, verbose_name='Dia de Reunião')),
                ('meeting_place', models.CharField(blank=True, max_length=200, verbose_name='Local de Reunião')),
                ('active', models.BooleanField(default=True, verbose_name='Ativo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Célula', 'verbose_name_plural': 'Células', 'ordering': ['cell_type', 'name']},
        ),
        migrations.CreateModel(
            name='CellMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending','Aguardando Aprovação'),('approved','Aprovado'),('rejected','Rejeitado'),('left','Saiu')], default='pending', max_length=15, verbose_name='Status')),
                ('role', models.CharField(choices=[('member','Membro'),('leader','Líder')], default='member', max_length=15, verbose_name='Papel')),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('cell', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='cells.cell', verbose_name='Célula')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cell_memberships', to='auth.user', verbose_name='Membro')),
            ],
            options={'verbose_name': 'Membro da Célula', 'verbose_name_plural': 'Membros das Células', 'ordering': ['role', 'joined_at'], 'unique_together': {('cell', 'user')}},
        ),
        migrations.CreateModel(
            name='CellPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('post_type', models.CharField(choices=[('message','Mensagem'),('prayer','Pedido de Oração'),('file','Arquivo'),('notice','Aviso do Líder')], default='message', max_length=15, verbose_name='Tipo')),
                ('content', models.TextField(verbose_name='Mensagem')),
                ('file', models.FileField(blank=True, null=True, upload_to='cells/files/', verbose_name='Arquivo')),
                ('pinned', models.BooleanField(default=False, verbose_name='Fixado')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cell_posts', to='auth.user', verbose_name='Autor')),
                ('cell', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='cells.cell', verbose_name='Célula')),
            ],
            options={'verbose_name': 'Post da Célula', 'verbose_name_plural': 'Posts das Células', 'ordering': ['-pinned', '-created_at']},
        ),
        migrations.CreateModel(
            name='CellPostReaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('emoji', models.CharField(default='🙏', max_length=10, verbose_name='Emoji')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reactions', to='cells.cellpost', verbose_name='Post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cell_reactions', to='auth.user', verbose_name='Membro')),
            ],
            options={'verbose_name': 'Reação', 'verbose_name_plural': 'Reações', 'unique_together': {('post', 'user', 'emoji')}},
        ),
    ]
