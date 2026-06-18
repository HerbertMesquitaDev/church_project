from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.text import slugify
import uuid

from core.models import Ministry
from events.models import Event, Category as EventCategory
from .models import MemberProfile, MemberMinistry, ExclusiveContent, ContentCategory, Notice, Testimony, PrayerRequest


# ── Auth forms ────────────────────────────────────────────
class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Nome", max_length=100,
                                  widget=forms.TextInput(attrs={'placeholder': 'Seu nome'}))
    last_name  = forms.CharField(label="Sobrenome", max_length=100,
                                  widget=forms.TextInput(attrs={'placeholder': 'Seu sobrenome'}))
    email      = forms.EmailField(label="E-mail",
                                   widget=forms.EmailInput(attrs={'placeholder': 'seu@email.com'}))

    # Consentimento LGPD
    image_consent = forms.BooleanField(
        required=False,
        label="Autorizo o uso da minha imagem",
        widget=forms.CheckboxInput(attrs={'id': 'id_image_consent', 'class': 'lgpd-checkbox'}),
    )

    class Meta:
        model  = User
        # username removido — gerado automaticamente a partir do e-mail
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs['placeholder'] = 'Senha'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirme a senha'
        for name, field in self.fields.items():
            if name != 'image_consent':
                field.widget.attrs['class'] = 'form-input'

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este e-mail já está cadastrado.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email'].strip().lower()
        user.email = email
        # Gera username único a partir do e-mail (parte antes do @)
        base = email.split('@')[0][:30]
        username = base
        counter  = 1
        while User.objects.filter(username=username).exists():
            suffix   = str(counter)
            username = f'{base[:30 - len(suffix)]}{suffix}'
            counter += 1
        user.username = username
        if commit:
            user.save()
        return user


# ── Profile form ──────────────────────────────────────────
class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(label="Nome", max_length=100,
                                  widget=forms.TextInput(attrs={'class': 'form-input'}))
    last_name  = forms.CharField(label="Sobrenome", max_length=100,
                                  widget=forms.TextInput(attrs={'class': 'form-input'}))
    email      = forms.EmailField(label="E-mail",
                                   widget=forms.EmailInput(attrs={'class': 'form-input'}))

    class Meta:
        model  = MemberProfile
        fields = ('photo', 'phone', 'birth_date', 'bio', 'baptized')
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'bio':        forms.Textarea(attrs={'rows': 4, 'class': 'form-input'}),
            'phone':      forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial  = user.last_name
            self.fields['email'].initial      = user.email

    def save_user(self, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name  = self.cleaned_data['last_name']
        user.email      = self.cleaned_data['email']
        user.save()


# ── Ministry formset ──────────────────────────────────────
class MemberMinistryForm(forms.ModelForm):
    class Meta:
        model  = MemberMinistry
        fields = ('ministry', 'role')
        widgets = {
            'ministry': forms.Select(attrs={'class': 'form-input'}),
            'role':     forms.TextInput(attrs={'class': 'form-input',
                                               'placeholder': 'Ex: Tecladista, Líder'}),
        }

MemberMinistryFormSet = forms.inlineformset_factory(
    MemberProfile, MemberMinistry,
    form=MemberMinistryForm, extra=1, can_delete=True, fields=('ministry', 'role'),
)


# ── Event form (admin/superuser only) ─────────────────────
class EventForm(forms.ModelForm):
    class Meta:
        model  = Event
        fields = ('title', 'slug', 'category', 'short_description', 'description',
                  'date', 'end_date', 'location', 'address', 'image',
                  'recurrence', 'published', 'featured', 'registration_link')
        widgets = {
            'title':             forms.TextInput(attrs={'class': 'form-input'}),
            'slug':              forms.TextInput(attrs={'class': 'form-input'}),
            'category':          forms.Select(attrs={'class': 'form-input'}),
            'short_description': forms.TextInput(attrs={'class': 'form-input'}),
            'description':       forms.Textarea(attrs={'class': 'form-input', 'rows': 6}),
            'date':              forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'end_date':          forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'location':          forms.TextInput(attrs={'class': 'form-input'}),
            'address':           forms.TextInput(attrs={'class': 'form-input'}),
            'recurrence':        forms.Select(attrs={'class': 'form-input'}),
            'registration_link': forms.URLInput(attrs={'class': 'form-input'}),
        }

    def clean_slug(self):
        slug = self.cleaned_data.get('slug', '').strip()
        if not slug:
            slug = slugify(self.cleaned_data.get('title', ''))
        # ensure uniqueness when editing
        qs = Event.objects.filter(slug=slug)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            slug = f"{slug}-{uuid.uuid4().hex[:6]}"
        return slug

    def clean(self):
        cleaned_data = super().clean()
        date     = cleaned_data.get('date')
        location = cleaned_data.get('location', '').strip()

        if date and location:
            # Verifica conflito: mesmo dia, mesma hora, mesmo local
            qs = Event.objects.filter(
                date=date,
                location__iexact=location,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                conflito = qs.first()
                raise forms.ValidationError(
                    f'Conflito de agenda: já existe o evento "{conflito.title}" '
                    f'em "{conflito.location}" no dia {conflito.date.strftime("%d/%m/%Y às %H:%M")}. '
                    f'Verifique a data, horário ou local antes de salvar.'
                )

        return cleaned_data


# ── Content form (staff) ──────────────────────────────────
class ContentForm(forms.ModelForm):
    class Meta:
        model  = ExclusiveContent
        fields = ('title', 'category', 'content_type', 'body',
                  'video_url', 'file', 'external_link', 'thumbnail',
                  'published', 'featured')
        widgets = {
            'title':        forms.TextInput(attrs={'class': 'form-input'}),
            'category':     forms.Select(attrs={'class': 'form-input'}),
            'content_type': forms.Select(attrs={'class': 'form-input'}),
            'body':         forms.Textarea(attrs={'class': 'form-input', 'rows': 8}),
            'video_url':    forms.URLInput(attrs={'class': 'form-input'}),
            'external_link':forms.URLInput(attrs={'class': 'form-input'}),
        }


# ── Notice form (staff) ───────────────────────────────────
class NoticeForm(forms.ModelForm):
    class Meta:
        model  = Notice
        fields = ('title', 'body', 'priority', 'published', 'expires_at')
        widgets = {
            'title':      forms.TextInput(attrs={'class': 'form-input'}),
            'body':       forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'priority':   forms.Select(attrs={'class': 'form-input'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }


# ── Testimony form ────────────────────────────────────────
class TestimonyForm(forms.ModelForm):
    class Meta:
        model  = Testimony
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 5,
                'placeholder': 'Compartilhe o que Deus tem feito em sua vida...',
                'maxlength': 1500,
            }),
        }
        labels = {'text': 'Seu Testemunho'}


# ── Prayer Request form ───────────────────────────────────
class PrayerRequestForm(forms.ModelForm):
    class Meta:
        model  = PrayerRequest
        fields = ('title', 'description', 'visibility')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Cura da minha mãe, Emprego, Relacionamento...',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 4,
                'placeholder': 'Descreva seu pedido com detalhes...',
                'maxlength': 1000,
            }),
            'visibility': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'title':       'Título do Pedido',
            'description': 'Descrição',
            'visibility':  'Quem pode ver este pedido?',
        }


# ── Offering form ─────────────────────────────────────────
from core.models import Offering

class OfferingForm(forms.ModelForm):
    class Meta:
        model  = Offering
        fields = ('type', 'amount', 'date', 'notes')
        widgets = {
            'type':   forms.Select(attrs={'class': 'form-input'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0,00', 'step': '0.01', 'min': '0'}),
            'date':   forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'notes':  forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Observações opcionais...'}),
        }
        labels = {
            'type':   'Tipo de Contribuição',
            'amount': 'Valor (R$)',
            'date':   'Data',
            'notes':  'Observações',
        }


# ── MediaItem form (staff) ────────────────────────────────
from core.models import MediaItem, MediaCategory

class MediaItemForm(forms.ModelForm):
    class Meta:
        model  = MediaItem
        fields = ('title', 'category', 'media_type', 'visibility', 'description',
                  'video_url', 'audio_file', 'pdf_file', 'thumbnail',
                  'speaker', 'pub_date', 'published', 'featured')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-input'}),
            'category':    forms.Select(attrs={'class': 'form-input'}),
            'media_type':  forms.Select(attrs={'class': 'form-input'}),
            'visibility':  forms.Select(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'video_url':   forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://youtube.com/watch?v=...'}),
            'speaker':     forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Pregador ou autor'}),
            'pub_date':    forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }
        labels = {
            'title':      'Título',
            'category':   'Categoria',
            'media_type': 'Tipo de Mídia',
            'visibility': 'Visibilidade',
            'description':'Descrição',
            'video_url':  'URL do Vídeo (YouTube/Vimeo)',
            'audio_file': 'Arquivo de Áudio',
            'pdf_file':   'Arquivo PDF',
            'thumbnail':  'Imagem de Capa',
            'speaker':    'Pregador / Autor',
            'pub_date':   'Data',
            'published':  'Publicado',
            'featured':   'Destaque na Home',
        }


# ── PhotoAlbum form (staff) ───────────────────────────────
from core.models import PhotoAlbum, Photo

class PhotoAlbumForm(forms.ModelForm):
    class Meta:
        model  = PhotoAlbum
        fields = ('title', 'description', 'cover', 'event_date', 'published', 'order')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'event_date':  forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'order':       forms.NumberInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'title':       'Título do Álbum',
            'description': 'Descrição',
            'cover':       'Foto de Capa',
            'event_date':  'Data do Evento',
            'published':   'Publicado',
            'order':       'Ordem de exibição',
        }


# ── Devotional form (staff) ───────────────────────────────
from core.models import Devotional

class DevotionalForm(forms.ModelForm):
    class Meta:
        model  = Devotional
        fields = ('title', 'verse', 'verse_text', 'reflection',
                  'prayer', 'author', 'pub_date', 'published')
        widgets = {
            'title':       forms.TextInput(attrs={'class': 'form-input'}),
            'verse':       forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: João 3:16'}),
            'verse_text':  forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'reflection':  forms.Textarea(attrs={'class': 'form-input', 'rows': 8}),
            'prayer':      forms.Textarea(attrs={'class': 'form-input', 'rows': 4,
                                                  'placeholder': 'Opcional — oração para o dia'}),
            'author':      forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nome do pastor ou autor'}),
            'pub_date':    forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }
        labels = {
            'title':      'Título',
            'verse':      'Versículo de Referência',
            'verse_text': 'Texto do Versículo',
            'reflection': 'Reflexão',
            'prayer':     'Oração do Dia',
            'author':     'Autor / Pastor',
            'pub_date':   'Data de Publicação',
            'published':  'Publicado',
        }


# ── Ministry form (CMS dashboard) ───────────────────────
class MinistryForm(forms.ModelForm):
    class Meta:
        model = Ministry
        fields = ('name', 'description', 'icon', 'order', 'active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'fa-church'}),
            'order': forms.NumberInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'name': 'Nome',
            'description': 'Descrição',
            'icon': 'Ícone (Font Awesome class)',
            'order': 'Ordem',
            'active': 'Ativo',
        }


# ── HeroSlide form (staff) ────────────────────────────────
from core.models import HeroSlide

class HeroSlideForm(forms.ModelForm):
    class Meta:
        model  = HeroSlide
        fields = ('title', 'subtitle', 'image', 'button_text', 'button_url',
                  'button_text_2', 'button_url_2', 'order', 'active')
        widgets = {
            'title':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Título de destaque'}),
            'subtitle':     forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Frase complementar (opcional)'}),
            'button_text':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Ver Eventos'}),
            'button_url':   forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: /eventos/'}),
            'button_text_2':forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Conheça-nos'}),
            'button_url_2': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: /sobre/'}),
            'order':        forms.NumberInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'title':         'Título',
            'subtitle':      'Subtítulo',
            'image':         'Imagem de Fundo',
            'button_text':   'Texto do 1º Botão',
            'button_url':    'Link do 1º Botão',
            'button_text_2': 'Texto do 2º Botão',
            'button_url_2':  'Link do 2º Botão',
            'order':         'Ordem',
            'active':        'Ativo',
        }
