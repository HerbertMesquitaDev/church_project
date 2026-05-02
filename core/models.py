from django.db import models
from django.contrib.auth.models import User
from tenants.models import Igreja
from core.validators import validate_image, validate_audio, validate_document


class SiteSettings(models.Model):
    igreja = models.OneToOneField(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='settings'
    )
    church_name = models.CharField("Nome da Igreja", max_length=200, default="Igreja Assembléia de Deus no Brasil")
    tagline = models.CharField("Slogan", max_length=300, blank=True)
    about_text = models.TextField("Sobre a Igreja", blank=True)
    address = models.CharField("Endereço", max_length=300, blank=True)
    maps_url = models.URLField(
        "Link do Google Maps", blank=True,
        help_text="Cole aqui o link 'Compartilhar' do Google Maps (ex: https://maps.app.goo.gl/...)"
    )
    phone = models.CharField("Telefone", max_length=50, blank=True)
    email = models.EmailField("E-mail", blank=True)
    facebook_url = models.URLField("Facebook", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    youtube_url = models.URLField("YouTube", blank=True)
    logo = models.ImageField("Logo", upload_to='logos/', blank=True, null=True, validators=[validate_image])
    hero_image = models.ImageField("Imagem Principal (Hero)", upload_to='hero/', blank=True, null=True, validators=[validate_image])
    hero_title = models.CharField("Título do Hero", max_length=200, default="Bem-vindo à nossa Igreja")
    hero_subtitle = models.CharField("Subtítulo do Hero", max_length=300, blank=True)

    color_primary = models.CharField(
        "Cor Primária (Dourado)", max_length=7, default="#C9A84C",
        help_text="Cor principal do site. Ex: #C9A84C"
    )
    color_secondary = models.CharField(
        "Cor Secundária (Navy)", max_length=7, default="#1A2340",
        help_text="Cor de títulos e navbar. Ex: #1A2340"
    )
    color_accent = models.CharField(
        "Cor de Destaque (Dourado escuro)", max_length=7, default="#8B6914",
        help_text="Usada em hovers e destaques. Ex: #8B6914"
    )

    pix_key = models.CharField("Chave PIX", max_length=200, blank=True,
                                help_text="CPF, CNPJ, e-mail, telefone ou chave aleatória")
    pix_name = models.CharField("Nome do titular PIX", max_length=150, blank=True)
    bank_name = models.CharField("Banco", max_length=100, blank=True)
    bank_agency = models.CharField("Agência", max_length=20, blank=True)
    bank_account = models.CharField("Conta", max_length=40, blank=True)
    bank_holder = models.CharField("Titular da conta", max_length=150, blank=True)
    offering_text = models.TextField("Texto de apresentação das ofertas", blank=True,
                                      help_text="Mensagem exibida acima dos dados de pagamento")
    notification_email = models.EmailField("E-mail para notificações", blank=True,
                                            help_text="Recebe alertas de novos visitantes e pedidos de contato")

    class Meta:
        verbose_name = "Configurações do Site"
        verbose_name_plural = "Configurações do Site"

    def __str__(self):
        return f"{self.igreja.nome if self.igreja else 'Sem Igreja'} — Configurações"

    def save(self, *args, **kwargs):
        # Não é mais singleton — cada igreja tem suas próprias configurações
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls, igreja=None):
        if igreja:
            obj, _ = cls.objects.get_or_create(igreja=igreja)
            return obj
        return cls()


class HeroSlide(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='hero_slides'
    )
    title = models.CharField("Título", max_length=200)
    subtitle = models.CharField("Subtítulo", max_length=300, blank=True)
    image = models.ImageField("Imagem de Fundo", upload_to='hero/slides/', validators=[validate_image])
    button_text = models.CharField("Texto do Botão", max_length=80, blank=True,
                                   help_text="Ex: Ver Eventos")
    button_url = models.CharField("Link do Botão", max_length=200, blank=True,
                                  help_text="Ex: /eventos/ ou https://...")
    button_text_2 = models.CharField("Texto do 2º Botão", max_length=80, blank=True)
    button_url_2 = models.CharField("Link do 2º Botão", max_length=200, blank=True)
    order = models.PositiveIntegerField("Ordem", default=0)
    active = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Slide do Carrossel"
        verbose_name_plural = "Slides do Carrossel"
        ordering = ['order']

    def __str__(self):
        return self.title


class Ministry(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='ministries'
    )
    name = models.CharField("Nome", max_length=150)
    description = models.TextField("Descrição")
    icon = models.CharField("Ícone (Font Awesome class)", max_length=100, default="fa-church",
                            help_text="Ex: fa-music, fa-child, fa-users")
    order = models.PositiveIntegerField("Ordem", default=0)
    active = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Ministério"
        verbose_name_plural = "Ministérios"
        ordering = ['order']

    def __str__(self):
        return self.name


class Testimony(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='testimonies'
    )
    author_name = models.CharField("Nome", max_length=150)
    role = models.CharField("Função/Cargo", max_length=100, blank=True)
    text = models.TextField("Testemunho")
    photo = models.ImageField("Foto", upload_to='testimonies/', blank=True, null=True, validators=[validate_image])
    active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Testemunho do Site"
        verbose_name_plural = "Testemunhos do Site (Página Pública)"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author_name} - {self.created_at.strftime('%d/%m/%Y')}"


class Devotional(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='devotionals'
    )
    title = models.CharField("Título", max_length=200)
    verse = models.CharField("Versículo de Referência", max_length=200,
                              help_text="Ex: João 3:16, Salmos 23:1")
    verse_text = models.TextField("Texto do Versículo")
    reflection = models.TextField("Reflexão")
    prayer = models.TextField("Oração do Dia", blank=True)
    author = models.CharField("Autor / Pastor", max_length=150, blank=True)
    pub_date = models.DateField("Data de Publicação")
    published = models.BooleanField("Publicado", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Devocional"
        verbose_name_plural = "Devocionais"
        ordering = ["-pub_date"]
        unique_together = [('igreja', 'pub_date')]

    def __str__(self):
        return f"{self.pub_date.strftime('%d/%m/%Y')} — {self.title}"


class Offering(models.Model):
    TYPE_CHOICES = [
        ('tithe',    'Dízimo'),
        ('offering', 'Oferta'),
        ('mission',  'Missões'),
        ('building', 'Fundo de Obras'),
        ('other',    'Outro'),
    ]
    profile = models.ForeignKey(
        'members.MemberProfile', on_delete=models.CASCADE,
        related_name='offerings', verbose_name="Membro"
    )
    type = models.CharField("Tipo", max_length=20, choices=TYPE_CHOICES, default='tithe')
    amount = models.DecimalField("Valor (R$)", max_digits=10, decimal_places=2)
    date = models.DateField("Data")
    notes = models.TextField("Observações", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Contribuição"
        verbose_name_plural = "Contribuições"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.profile.full_name} — R$ {self.amount} ({self.get_type_display()}) {self.date}"


class Visitor(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='visitors'
    )
    HOW_CHOICES = [
        ('friend',     'Indicação de amigo/familiar'),
        ('social',     'Redes Sociais'),
        ('passing_by', 'Passando pela frente'),
        ('search',     'Pesquisa na internet'),
        ('event',      'Evento/Atividade'),
        ('other',      'Outro'),
    ]
    name = models.CharField("Nome completo", max_length=150)
    email = models.EmailField("E-mail", blank=True)
    phone = models.CharField("Telefone / WhatsApp", max_length=30, blank=True)
    visit_date = models.DateField("Data da Visita")
    how_found = models.CharField("Como conheceu a igreja", max_length=20,
                                  choices=HOW_CHOICES, default='friend')
    how_found_other = models.CharField("Outro (especifique)", max_length=150, blank=True)
    wants_ministry = models.BooleanField("Interesse em participar de ministério", default=False)
    ministry_interest = models.CharField("Qual ministério?", max_length=200, blank=True)
    message = models.TextField("Mensagem / Observações", blank=True)
    contacted = models.BooleanField("Já foi contatado", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Visitante"
        verbose_name_plural = "Visitantes"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} — {self.visit_date.strftime('%d/%m/%Y')}"


class MediaCategory(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='media_categories'
    )
    SECTION_CHOICES = [
        ('sermons', 'Pregações'),
        ('worship', 'Louvores'),
        ('studies', 'Estudos'),
        ('live',    'Ao Vivo'),
        ('other',   'Outros'),
    ]
    name = models.CharField("Nome", max_length=100)
    section = models.CharField("Seção", max_length=20, choices=SECTION_CHOICES, default='sermons')
    icon = models.CharField("Ícone FA", max_length=80, default="fa-play",
                             help_text="Ex: fa-microphone, fa-music, fa-book-open")
    order = models.PositiveIntegerField("Ordem", default=0)

    class Meta:
        verbose_name = "Categoria de Mídia"
        verbose_name_plural = "Categorias de Mídia"
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.get_section_display()} — {self.name}"


class MediaItem(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='media_items'
    )
    TYPE_CHOICES = [
        ('video', 'Vídeo (YouTube/Vimeo)'),
        ('audio', 'Áudio'),
        ('pdf',   'Estudo em PDF'),
        ('live',  'Transmissão Ao Vivo'),
    ]
    VISIBILITY_CHOICES = [
        ('public',  'Público'),
        ('members', 'Só para membros'),
    ]
    title = models.CharField("Título", max_length=200)
    category = models.ForeignKey(MediaCategory, on_delete=models.SET_NULL,
                                  null=True, blank=True, verbose_name="Categoria",
                                  related_name='items')
    media_type = models.CharField("Tipo", max_length=10, choices=TYPE_CHOICES, default='video')
    visibility = models.CharField("Visibilidade", max_length=10,
                                   choices=VISIBILITY_CHOICES, default='public')
    description = models.TextField("Descrição", blank=True)
    video_url = models.URLField("URL do Vídeo/Live (YouTube/Vimeo)", blank=True)
    audio_file = models.FileField("Arquivo de Áudio", upload_to='media/audio/', blank=True, null=True, validators=[validate_audio])
    pdf_file = models.FileField("Arquivo PDF", upload_to='media/pdf/', blank=True, null=True, validators=[validate_document])
    thumbnail = models.ImageField("Capa", upload_to='media/thumbs/', blank=True, null=True, validators=[validate_image])
    speaker = models.CharField("Pregador / Autor", max_length=150, blank=True)
    meta_description = models.CharField("Meta description (SEO)", max_length=160, blank=True,
                                         help_text="Resumo para o Google (max 160 caracteres).")
    published = models.BooleanField("Publicado", default=True)
    featured = models.BooleanField("Destaque", default=False)
    pub_date = models.DateField("Data", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Item de Mídia"
        verbose_name_plural = "Midiateca"
        ordering = ['-pub_date', '-created_at']

    def __str__(self):
        return self.title

    def get_embed_url(self):
        url = self.video_url
        if not url:
            return ''
        if 'youtube.com/watch?v=' in url:
            vid = url.split('v=')[1].split('&')[0]
            return f'https://www.youtube.com/embed/{vid}'
        if 'youtu.be/' in url:
            vid = url.split('youtu.be/')[1].split('?')[0]
            return f'https://www.youtube.com/embed/{vid}'
        if 'vimeo.com/' in url:
            vid = url.split('vimeo.com/')[1].split('?')[0]
            return f'https://player.vimeo.com/video/{vid}'
        return url

    @property
    def is_live(self):
        return self.media_type == 'live'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('media_detail', args=[self.pk])


class PhotoAlbum(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='photo_albums'
    )
    title = models.CharField("Título do Álbum", max_length=200)
    description = models.TextField("Descrição", blank=True)
    cover = models.ImageField("Foto de Capa", upload_to='gallery/covers/', blank=True, null=True, validators=[validate_image])
    event_date = models.DateField("Data do Evento", null=True, blank=True)
    published = models.BooleanField("Publicado", default=True)
    order = models.PositiveIntegerField("Ordem", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Álbum de Fotos"
        verbose_name_plural = "Álbuns de Fotos"
        ordering = ['-event_date', '-created_at']

    def __str__(self):
        return self.title

    def photo_count(self):
        return self.photos.count()


class Photo(models.Model):
    album = models.ForeignKey(PhotoAlbum, on_delete=models.CASCADE,
                               related_name='photos', verbose_name="Álbum")
    image = models.ImageField("Foto", upload_to='gallery/photos/', validators=[validate_image])
    caption = models.CharField("Legenda", max_length=300, blank=True)
    order = models.PositiveIntegerField("Ordem", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foto"
        verbose_name_plural = "Fotos"
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.album.title} — foto {self.pk}"


class SocialPost(models.Model):
    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='social_posts'
    )
    STATUS_CHOICES = [
        ('draft',     'Rascunho'),
        ('queued',    'Na fila'),
        ('published', 'Publicado'),
        ('failed',    'Falhou'),
        ('partial',   'Publicado com erros'),
    ]
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('facebook',  'Facebook'),
        ('both',      'Instagram + Facebook'),
    ]
    FORMAT_CHOICES = [
        ('single',   'Foto única'),
        ('carousel', 'Carrossel'),
        ('album_fb', 'Álbum Facebook'),
    ]
    SOURCE_CHOICES = [
        ('album', 'Álbum de Fotos'),
        ('event', 'Evento'),
    ]
    source_type = models.CharField('Origem', max_length=10,
                                    choices=SOURCE_CHOICES, default='album')
    album = models.ForeignKey('PhotoAlbum', on_delete=models.CASCADE,
                               related_name='social_posts_core',
                               verbose_name='Álbum', null=True, blank=True)
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE,
                               related_name='social_posts',
                               verbose_name='Evento', null=True, blank=True)
    photos = models.ManyToManyField('Photo', verbose_name='Fotos selecionadas', blank=True)
    platform = models.CharField('Plataforma', max_length=15,
                                 choices=PLATFORM_CHOICES, default='both')
    post_format = models.CharField('Formato', max_length=15,
                                    choices=FORMAT_CHOICES, default='carousel')
    caption = models.TextField('Legenda')
    hashtags = models.TextField('Hashtags', blank=True, help_text='Uma por linha, sem #')
    status = models.CharField('Status', max_length=15,
                               choices=STATUS_CHOICES, default='draft')
    ig_post_id = models.CharField('ID post Instagram', max_length=100, blank=True)
    ig_permalink = models.URLField('Link Instagram', blank=True)
    ig_error = models.TextField('Erro Instagram', blank=True)
    fb_post_id = models.CharField('ID post Facebook', max_length=100, blank=True)
    fb_permalink = models.URLField('Link Facebook', blank=True)
    fb_error = models.TextField('Erro Facebook', blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL,
                                    null=True, related_name='social_posts_created',
                                    verbose_name='Criado por')
    scheduled_for = models.DateTimeField('Agendar para', null=True, blank=True,
                                          help_text='Deixe vazio para publicar agora')
    published_at = models.DateTimeField('Publicado em', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Publicação Social'
        verbose_name_plural = 'Publicações Sociais'
        ordering = ['-created_at']

    def __str__(self):
        src = self.album.title if self.album else (self.event.title if self.event else '?')
        return f'{src} → {self.get_platform_display()} ({self.get_status_display()})'

    def full_caption(self):
        tags = '\n'.join(f'#{t.strip()}' for t in self.hashtags.splitlines() if t.strip())
        return f'{self.caption}\n\n{tags}' if tags else self.caption


class SocialConfig(models.Model):
    igreja = models.OneToOneField(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='social_config'
    )
    ig_user_id = models.CharField('Instagram User ID', max_length=50, blank=True)
    ig_access_token = models.TextField('Instagram Access Token', blank=True)
    fb_page_id = models.CharField('Facebook Page ID', max_length=50, blank=True)
    fb_access_token = models.TextField('Facebook Page Access Token', blank=True)
    site_base_url = models.URLField('URL pública do site', blank=True,
                                     help_text='Ex: https://meusite.com.br — sem barra no final')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração de Redes Sociais'
        verbose_name_plural = 'Configurações de Redes Sociais'

    def __str__(self):
        return f"{self.igreja.nome if self.igreja else 'Sem Igreja'} — Redes Sociais"

    @classmethod
    def get_config(cls, igreja=None):
        if igreja:
            obj, _ = cls.objects.get_or_create(igreja=igreja)
            return obj
        return cls()

    def ig_configured(self):
        return bool(self.ig_user_id and self.ig_access_token)

    def fb_configured(self):
        return bool(self.fb_page_id and self.fb_access_token)


class Page(models.Model):
    """Página dinâmica criada pelo painel sem necessidade de código."""

    TEMPLATE_CHOICES = [
        ('core/page.html',         'Página padrão'),
        ('core/page_wide.html',    'Página largura total'),
        ('core/page_landing.html', 'Landing page (sem menu/rodapé)'),
    ]

    igreja = models.ForeignKey(
        Igreja, on_delete=models.CASCADE,
        verbose_name="Igreja", null=True, blank=True,
        related_name='pages'
    )
    title            = models.CharField("Título", max_length=200)
    slug             = models.SlugField("Slug (URL)", unique=True,
                                        help_text="Ex: 'nossa-historia' → /p/nossa-historia/")
    cover            = models.ImageField("Imagem de capa", upload_to='pages/covers/',
                                          blank=True, null=True, validators=[validate_image])
    content          = models.TextField("Conteúdo", blank=True)
    template_name    = models.CharField("Template", max_length=60,
                                         choices=TEMPLATE_CHOICES, default='core/page.html')
    meta_description = models.CharField("Meta description (SEO)", max_length=160, blank=True,
                                         help_text="Resumo exibido nos resultados do Google (max 160 caracteres)")
    meta_keywords    = models.CharField("Meta keywords", max_length=255, blank=True)
    published        = models.BooleanField("Publicada", default=False)
    show_in_nav      = models.BooleanField("Exibir no menu", default=False,
                                            help_text="Adiciona esta página ao menu de navegação público")
    nav_order        = models.PositiveSmallIntegerField("Posição no menu", default=0)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name         = "Página"
        verbose_name_plural  = "Páginas"
        ordering             = ['nav_order', 'title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('page_detail', kwargs={'slug': self.slug})


class SiteVisit(models.Model):
    igreja       = models.ForeignKey(Igreja, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='visits', verbose_name="Igreja")
    session_key  = models.CharField("Sessão", max_length=40, db_index=True)
    ip           = models.GenericIPAddressField("IP", null=True, blank=True)
    user         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='site_visits', verbose_name="Usuário")
    page         = models.CharField("Página", max_length=500)
    city         = models.CharField("Cidade", max_length=100, blank=True)
    region       = models.CharField("Estado", max_length=100, blank=True)
    country_code = models.CharField("País", max_length=5, blank=True)
    visited_at   = models.DateTimeField("Data/Hora", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name         = "Visita"
        verbose_name_plural  = "Visitas"
        ordering             = ['-visited_at']
        indexes = [
            models.Index(fields=['visited_at', 'session_key']),
        ]

    def __str__(self):
        return f"{self.city or self.ip or '?'} — {self.page} ({self.visited_at:%d/%m/%Y %H:%M})"

    def fb_configured(self):
        return bool(self.fb_page_id and self.fb_access_token)