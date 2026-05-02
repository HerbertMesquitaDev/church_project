from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Nome')),
                ('icon', models.CharField(default='fa-graduation-cap', max_length=80, verbose_name='Ícone FA')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
            ],
            options={'verbose_name': 'Categoria', 'verbose_name_plural': 'Categorias de Curso', 'ordering': ['order', 'name']},
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name='Título')),
                ('slug', models.SlugField(blank=True, unique=True, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Descrição')),
                ('cover', models.ImageField(blank=True, null=True, upload_to='courses/covers/', verbose_name='Capa')),
                ('level', models.CharField(choices=[('beginner','Iniciante'),('intermediate','Intermediário'),('advanced','Avançado')], default='beginner', max_length=15, verbose_name='Nível')),
                ('workload', models.PositiveIntegerField(default=0, verbose_name='Carga horária (min)')),
                ('published', models.BooleanField(default=False, verbose_name='Publicado')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses', to='courses.coursecategory', verbose_name='Categoria')),
                ('instructor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='courses_teaching', to=settings.AUTH_USER_MODEL, verbose_name='Professor')),
            ],
            options={'verbose_name': 'Curso', 'verbose_name_plural': 'Cursos', 'ordering': ['order', 'title']},
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name='Título do Módulo')),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modules', to='courses.course', verbose_name='Curso')),
            ],
            options={'verbose_name': 'Módulo', 'verbose_name_plural': 'Módulos', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200, verbose_name='Título da Aula')),
                ('description', models.TextField(blank=True, verbose_name='Resumo / Objetivo')),
                ('body', models.TextField(blank=True, verbose_name='Conteúdo (texto)')),
                ('video_url', models.URLField(blank=True, verbose_name='Vídeo (YouTube/Vimeo)')),
                ('audio_file', models.FileField(blank=True, null=True, upload_to='courses/audio/', verbose_name='Áudio')),
                ('pdf_file', models.FileField(blank=True, null=True, upload_to='courses/pdf/', verbose_name='PDF / Material')),
                ('duration', models.PositiveIntegerField(default=0, verbose_name='Duração estimada (min)')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Ordem')),
                ('published', models.BooleanField(default=True, verbose_name='Publicada')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('module', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lessons', to='courses.module', verbose_name='Módulo')),
            ],
            options={'verbose_name': 'Aula', 'verbose_name_plural': 'Aulas', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='Enrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('enrolled_at', models.DateTimeField(auto_now_add=True)),
                ('active', models.BooleanField(default=True, verbose_name='Ativa')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='courses.course', verbose_name='Curso')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to=settings.AUTH_USER_MODEL, verbose_name='Aluno')),
            ],
            options={'verbose_name': 'Inscrição', 'verbose_name_plural': 'Inscrições', 'ordering': ['-enrolled_at'], 'unique_together': {('course', 'user')}},
        ),
        migrations.CreateModel(
            name='LessonProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('completed', models.BooleanField(default=False, verbose_name='Concluída')),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress', to='courses.lesson', verbose_name='Aula')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lesson_progress', to=settings.AUTH_USER_MODEL, verbose_name='Aluno')),
            ],
            options={'verbose_name': 'Progresso', 'unique_together': {('user', 'lesson')}},
        ),
        migrations.CreateModel(
            name='LessonComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('body', models.TextField(max_length=1000, verbose_name='Comentário')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lesson', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='courses.lesson', verbose_name='Aula')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='courses.lessoncomment', verbose_name='Resposta a')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lesson_comments', to=settings.AUTH_USER_MODEL, verbose_name='Autor')),
            ],
            options={'verbose_name': 'Comentário', 'verbose_name_plural': 'Comentários', 'ordering': ['created_at']},
        ),
        migrations.CreateModel(
            name='LessonQuiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('passing_score', models.PositiveSmallIntegerField(default=70, verbose_name='Nota mínima (%)')),
                ('max_attempts', models.PositiveSmallIntegerField(default=3, verbose_name='Tentativas permitidas')),
                ('show_answers', models.BooleanField(default=True, verbose_name='Mostrar gabarito após tentativa')),
                ('lesson', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='quiz', to='courses.lesson', verbose_name='Aula')),
            ],
            options={'verbose_name': 'Quiz da Aula'},
        ),
        migrations.CreateModel(
            name='QuizQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('text', models.TextField(verbose_name='Pergunta')),
                ('explanation', models.TextField(blank=True, verbose_name='Explicação da resposta')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Ordem')),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='courses.lessonquiz', verbose_name='Quiz')),
            ],
            options={'verbose_name': 'Pergunta', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='QuizChoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('text', models.CharField(max_length=500, verbose_name='Alternativa')),
                ('is_correct', models.BooleanField(default=False, verbose_name='É a correta')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Ordem')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='choices', to='courses.quizquestion', verbose_name='Pergunta')),
            ],
            options={'verbose_name': 'Alternativa', 'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='QuizAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True)),
                ('score', models.PositiveSmallIntegerField(verbose_name='Pontuação (%)')),
                ('passed', models.BooleanField(verbose_name='Aprovado')),
                ('answers', models.JSONField(default=dict, verbose_name='Respostas')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('quiz', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='courses.lessonquiz', verbose_name='Quiz')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_quiz_attempts', to=settings.AUTH_USER_MODEL, verbose_name='Aluno')),
            ],
            options={'verbose_name': 'Tentativa de Quiz', 'ordering': ['-created_at']},
        ),
    ]
