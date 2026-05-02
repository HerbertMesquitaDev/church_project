import os

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Ministry, SiteSettings, HeroSlide, Devotional, Offering, Visitor, MediaCategory, MediaItem, Photo, PhotoAlbum, Page
from events.models import Event
from members.models import Testimony


def home(request):
    slides          = HeroSlide.objects.filter(active=True)
    upcoming_events = Event.objects.filter(
        date__gte=timezone.now(), published=True
    ).order_by('date')[:3]
    ministries  = Ministry.objects.filter(active=True)
    testimonies = Testimony.objects.filter(
        status='approved'
    ).select_related('profile__user', 'profile').order_by('-updated_at')[:6]
    today       = timezone.localdate()
    devotional  = Devotional.objects.filter(
        published=True, pub_date=today
    ).first()
    # Se não tem hoje, pega o mais recente
    if not devotional:
        devotional = Devotional.objects.filter(published=True).first()

    # Destaque da midiateca na home
    featured_media = MediaItem.objects.filter(
        published=True, featured=True, visibility='public'
    ).select_related('category')[:3]

    return render(request, 'core/home.html', {
        'slides':          slides,
        'upcoming_events': upcoming_events,
        'ministries':      ministries,
        'testimonies':     testimonies,
        'devotional':      devotional,
        'featured_media':  featured_media,
    })


def devotional_detail(request, pk):
    dev = get_object_or_404(Devotional, pk=pk, published=True)
    recent = Devotional.objects.filter(published=True).exclude(pk=pk)[:5]
    return render(request, 'core/devotional_detail.html', {
        'devotional': dev,
        'recent':     recent,
    })


def devotional_list(request):
    devos = Devotional.objects.filter(published=True)
    return render(request, 'core/devotional_list.html', {'devos': devos})


def ministries_page(request):
    ministries = Ministry.objects.filter(active=True).prefetch_related(
        'members__profile__user'
    )
    return render(request, 'core/ministries.html', {'ministries': ministries})


def about(request):
    return render(request, 'core/about.html')


def contact(request):
    return render(request, 'core/contact.html')


def offering_page(request):
    return render(request, 'core/offering.html')


def visitor_form(request):
    from django import forms as dj_forms

    class VisitorForm(dj_forms.ModelForm):
        class Meta:
            from .models import Visitor as V
            model  = V
            fields = ('name', 'email', 'phone', 'visit_date', 'how_found',
                      'how_found_other', 'wants_ministry', 'ministry_interest', 'message')
            widgets = {
                'name':             dj_forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Seu nome completo'}),
                'email':            dj_forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'seu@email.com'}),
                'phone':            dj_forms.TextInput(attrs={'class': 'form-input', 'placeholder': '(00) 00000-0000'}),
                'visit_date':       dj_forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
                'how_found':        dj_forms.Select(attrs={'class': 'form-input'}),
                'how_found_other':  dj_forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Como nos conheceu?'}),
                'ministry_interest':dj_forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Louvor, Jovens, Infantil...'}),
                'message':          dj_forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Deixe uma mensagem (opcional)'}),
            }

    success = False
    form = VisitorForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        visitor = form.save()
        success = True

        # Enviar e-mail de notificação
        site = SiteSettings.get_settings()
        if site.notification_email:
            try:
                from django.core.mail import send_mail
                from django.conf import settings as conf
                subject = f'Novo visitante: {visitor.name}'
                body = (
                    f'Nome: {visitor.name}\n'
                    f'E-mail: {visitor.email or "—"}\n'
                    f'Telefone: {visitor.phone or "—"}\n'
                    f'Visitou em: {visitor.visit_date.strftime("%d/%m/%Y")}\n'
                    f'Como conheceu: {visitor.get_how_found_display()}\n'
                    f'Quer participar de ministério: {"Sim" if visitor.wants_ministry else "Não"}\n'
                    f'Ministério: {visitor.ministry_interest or "—"}\n'
                    f'Mensagem: {visitor.message or "—"}\n'
                )
                send_mail(subject, body, conf.DEFAULT_FROM_EMAIL, [site.notification_email], fail_silently=True)
            except Exception:
                pass  # Não quebra se e-mail falhar

        return render(request, 'core/visitor_form.html', {'success': True})

    return render(request, 'core/visitor_form.html', {'form': form, 'success': False})


def media_list(request):
    section  = request.GET.get('secao', '')
    cat_id   = request.GET.get('categoria', '')
    q        = request.GET.get('q', '').strip()

    # Visibilidade: público ou membro logado
    qs = MediaItem.objects.filter(published=True).select_related('category')
    if not (request.user.is_authenticated):
        qs = qs.filter(visibility='public')

    if section:
        qs = qs.filter(category__section=section)
    if cat_id:
        qs = qs.filter(category_id=cat_id)
    if q:
        from django.db.models import Q
        qs = qs.filter(Q(title__icontains=q) | Q(speaker__icontains=q) | Q(description__icontains=q))

    from django.core.paginator import Paginator
    page_obj   = Paginator(qs, 12).get_page(request.GET.get('page'))
    categories = MediaCategory.objects.all()
    sections   = MediaCategory.SECTION_CHOICES

    return render(request, 'core/media_list.html', {
        'page_obj':   page_obj,
        'items':      page_obj,
        'categories': categories,
        'sections':   sections,
        'section':    section,
        'cat_id':     cat_id,
        'q':          q,
    })


def media_detail(request, pk):
    item = MediaItem.objects.select_related('category').get(pk=pk, published=True)
    if item.visibility == 'members' and not request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect(f'/membros/login/?next=/midiateca/{pk}/')

    related = MediaItem.objects.filter(
        published=True, category=item.category, visibility='public'
    ).exclude(pk=pk)[:4]
    if request.user.is_authenticated:
        related = MediaItem.objects.filter(
            published=True, category=item.category
        ).exclude(pk=pk)[:4]

    return render(request, 'core/media_detail.html', {
        'item':    item,
        'related': related,
    })


def gallery(request):
    albums = PhotoAlbum.objects.filter(published=True).prefetch_related('photos')
    return render(request, 'core/gallery.html', {'albums': albums})


def gallery_album(request, pk):
    album  = get_object_or_404(PhotoAlbum, pk=pk, published=True)
    photos = album.photos.all()
    return render(request, 'core/gallery_album.html', {'album': album, 'photos': photos})


def privacy_policy(request):
    return render(request, 'core/privacy_policy.html')


def service_worker(request):
    """Serve o service worker na raiz para escopo correto."""
    from django.conf import settings
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'sw.js')
    try:
        with open(sw_path, 'r') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse('// sw not found', content_type='application/javascript')


def offline(request):
    """Página de fallback offline do PWA."""
    return render(request, 'pwa/offline.html')


# ── Handlers de erro customizados ────────────────────────
def error_404(request, exception=None):
    return render(request, '404.html', status=404)

def error_403(request, exception=None):
    return render(request, '403.html', status=403)

def error_400(request, exception=None):
    return render(request, '400.html', status=400)

def error_500(request):
    return render(request, '500.html', status=500)


def page_detail(request, slug):
    igreja = getattr(request, 'igreja', None)
    qs = Page.objects.filter(slug=slug, published=True)
    if igreja:
        qs = qs.filter(igreja=igreja)
    page = get_object_or_404(qs)
    return render(request, page.template_name, {'page': page})


def robots_txt(request):
    host = request.build_absolute_uri('/')
    content = (
        f"User-agent: *\n"
        f"Disallow: /membros/\n"
        f"Disallow: /admin/\n"
        f"Disallow: /api/\n"
        f"Disallow: /superadmin/\n"
        f"Allow: /\n\n"
        f"Sitemap: {host}sitemap.xml\n"
    )
    return HttpResponse(content, content_type='text/plain')
