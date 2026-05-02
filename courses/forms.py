from django import forms
from .models import Course, Module, Lesson


class CourseForm(forms.ModelForm):
    class Meta:
        model  = Course
        fields = ('title', 'category', 'description', 'cover', 'instructor',
                  'level', 'workload', 'order', 'published')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-input'}),
            'category':    forms.Select(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'instructor':  forms.Select(attrs={'class': 'form-input'}),
            'level':       forms.Select(attrs={'class': 'form-input'}),
            'workload':    forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Ex: 120'}),
            'order':       forms.NumberInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'title':      'Título do Curso',
            'category':   'Categoria',
            'description':'Descrição',
            'cover':      'Imagem de Capa',
            'instructor': 'Professor',
            'level':      'Nível',
            'workload':   'Carga horária (minutos)',
            'order':      'Ordem de exibição',
            'published':  'Publicado',
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model  = Module
        fields = ('title', 'description', 'order')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Módulo 1 — Fundamentos'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
            'order':       forms.NumberInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'title':       'Título do Módulo',
            'description': 'Descrição (opcional)',
            'order':       'Ordem',
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model  = Lesson
        fields = ('title', 'description', 'body', 'video_url',
                  'audio_file', 'pdf_file', 'duration', 'order', 'published')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 2,
                                                  'placeholder': 'Resumo ou objetivo da aula'}),
            'body':        forms.Textarea(attrs={'class': 'form-input', 'rows': 10}),
            'video_url':   forms.URLInput(attrs={'class': 'form-input',
                                                  'placeholder': 'https://youtube.com/watch?v=...'}),
            'duration':    forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0'}),
            'order':       forms.NumberInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'title':       'Título da Aula',
            'description': 'Resumo / Objetivo',
            'body':        'Conteúdo (texto)',
            'video_url':   'URL do Vídeo (YouTube/Vimeo)',
            'audio_file':  'Arquivo de Áudio',
            'pdf_file':    'Material em PDF',
            'duration':    'Duração estimada (min)',
            'order':       'Ordem',
            'published':   'Aula publicada',
        }


# ── Quiz forms (staff) ────────────────────────────────────
from .models import LessonQuiz, QuizQuestion, QuizChoice

class LessonQuizForm(forms.ModelForm):
    class Meta:
        model  = LessonQuiz
        fields = ('passing_score', 'max_attempts', 'show_answers')
        widgets = {
            'passing_score': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 100}),
            'max_attempts':  forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
        }
        labels = {
            'passing_score': 'Nota mínima para aprovação (%)',
            'max_attempts':  'Máximo de tentativas (0 = ilimitado)',
            'show_answers':  'Mostrar gabarito após a tentativa',
        }


class QuizQuestionForm(forms.ModelForm):
    class Meta:
        model  = QuizQuestion
        fields = ('text', 'explanation', 'order')
        widgets = {
            'text':        forms.Textarea(attrs={'class': 'form-input', 'rows': 3,
                                                  'placeholder': 'Digite a pergunta...'}),
            'explanation': forms.Textarea(attrs={'class': 'form-input', 'rows': 2,
                                                  'placeholder': 'Explicação exibida após a resposta (opcional)'}),
            'order':       forms.NumberInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'text':        'Pergunta',
            'explanation': 'Explicação da resposta correta',
            'order':       'Ordem',
        }


class QuizChoiceForm(forms.ModelForm):
    class Meta:
        model  = QuizChoice
        fields = ('text', 'is_correct', 'order')
        widgets = {
            'text':  forms.TextInput(attrs={'class': 'form-input',
                                             'placeholder': 'Texto da alternativa'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'text':       'Alternativa',
            'is_correct': 'Esta é a resposta correta',
            'order':      'Ordem',
        }
