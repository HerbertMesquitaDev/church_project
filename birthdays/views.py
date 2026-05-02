from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from members.models import MemberProfile
import datetime

VERSICULOS = [
    ("Jeremias 29:11", "Porque eu sei os planos que tenho para vocês, diz o Senhor, planos de fazê-los prosperar e não de causar dano, planos de dar a vocês esperança e um futuro."),
    ("Salmos 23:1", "O Senhor é o meu pastor; nada me faltará."),
    ("Filipenses 4:13", "Tudo posso naquele que me fortalece."),
    ("Romanos 8:28", "Sabemos que Deus age em todas as coisas para o bem daqueles que o amam."),
    ("João 3:16", "Porque Deus amou o mundo de tal maneira que deu o seu Filho Unigênito, para que todo aquele que nele crê não pereça, mas tenha a vida eterna."),
    ("Isaías 40:31", "Mas os que esperam no Senhor renovarão as suas forças. Voarão alto como águias; correrão e não ficarão exaustos, andarão e não se cansarão."),
    ("Provérbios 3:5-6", "Confie no Senhor de todo o seu coração e não se apoie em seu próprio entendimento; reconheça o Senhor em todos os seus caminhos, e ele endireitará as suas veredas."),
    ("Salmos 37:4", "Deleite-se no Senhor, e ele atenderá aos desejos do seu coração."),
    ("Mateus 6:33", "Busquem, pois, em primeiro lugar o Reino de Deus e a sua justiça, e todas essas coisas lhes serão acrescentadas."),
    ("2 Timóteo 1:7", "Pois Deus não nos deu espírito de covardia, mas de poder, de amor e de equilíbrio."),
    ("Salmos 118:24", "Este é o dia que o Senhor fez; regozijemo-nos e alegremo-nos nele."),
    ("Números 6:24-26", "O Senhor te abençoe e te guarde; o Senhor faça resplandecer o seu rosto sobre ti e te conceda graça."),
]

# Temas de fundo disponíveis para o slideshow
SLIDE_THEMES = {
    'navy':     {'label': 'Azul Naval',   'gradients': ['135deg,#1A2340,#2D3A6B,#1a1a2e', '135deg,#0f1830,#1A2340,#0a0f20', '135deg,#1a1a2e,#2D3A6B,#1A2340']},
    'wine':     {'label': 'Vinho',        'gradients': ['135deg,#1a1010,#3d1a00,#1a0a0a', '135deg,#2a0a0a,#4a1010,#1a0505', '135deg,#1a0a0a,#3d1010,#2a0a0a']},
    'forest':   {'label': 'Verde Escuro', 'gradients': ['135deg,#0a1a0a,#1a3d1a,#0d1a0d', '135deg,#071407,#1a3d1a,#0a1a0a', '135deg,#0d1a0d,#1a4a1a,#0a1a0a']},
    'purple':   {'label': 'Roxo',         'gradients': ['135deg,#1a0a2e,#3d1a6b,#0f0520', '135deg,#120820,#2d1060,#1a0a2e', '135deg,#0f0520,#3d1a6b,#1a0a2e']},
    'charcoal': {'label': 'Carvão',       'gradients': ['135deg,#1a1a1a,#2d2d2d,#111111', '135deg,#111111,#333333,#1a1a1a', '135deg,#1a1a1a,#2a2a2a,#0f0f0f']},
    'teal':     {'label': 'Verde-Azul',   'gradients': ['135deg,#0a1a1a,#1a3d3d,#0d1a1a', '135deg,#071414,#1a4040,#0a1a1a', '135deg,#0d1a1a,#1a4a4a,#0a1a1a']},
}


def get_versiculo(profile_id):
    return VERSICULOS[profile_id % len(VERSICULOS)]


def buscar_aniversariantes(data_ini, data_fim):
    profiles = MemberProfile.objects.filter(
        birth_date__isnull=False,
        approved=True,
    ).select_related('user')

    today = timezone.now().date()
    aniversariantes = []

    dias_periodo = []
    delta = (data_fim - data_ini).days
    for i in range(delta + 1):
        d = data_ini + datetime.timedelta(days=i)
        dias_periodo.append((d.month, d.day, d))

    for profile in profiles:
        bd = profile.birth_date
        for (mes, dia, data_ref) in dias_periodo:
            if bd.month == mes and bd.day == dia:
                v = get_versiculo(profile.id)
                aniversariantes.append({
                    'profile': profile,
                    'data': data_ref,
                    'hoje': data_ref == today,
                    'versiculo_ref': v[0],
                    'versiculo_texto': v[1],
                })
                break

    aniversariantes.sort(key=lambda x: (not x['hoje'], x['data']))
    return aniversariantes


@login_required
def birthday_list(request):
    today = timezone.now().date()

    # Padrão: 1º ao 7º do mês atual
    default_ini = today.replace(day=1)
    try:
        default_fim = today.replace(day=7)
    except ValueError:
        default_fim = today

    try:
        data_ini = datetime.date.fromisoformat(request.GET.get('de', str(default_ini)))
    except ValueError:
        data_ini = default_ini

    try:
        data_fim = datetime.date.fromisoformat(request.GET.get('ate', str(default_fim)))
    except ValueError:
        data_fim = default_fim

    if data_ini > data_fim:
        data_ini, data_fim = data_fim, data_ini
    if (data_fim - data_ini).days > 365:
        data_fim = data_ini + datetime.timedelta(days=365)

    aniversariantes = buscar_aniversariantes(data_ini, data_fim)

    return render(request, 'birthdays/list.html', {
        'aniversariantes': aniversariantes,
        'data_ini': data_ini,
        'data_fim': data_fim,
        'total': len(aniversariantes),
        'today': today,
        'slide_themes': SLIDE_THEMES,
    })


def birthday_slide(request):
    today = timezone.now().date()

    # ── CORREÇÃO: usar getlist para receber TODOS os IDs marcados ──
    ids_list = request.GET.getlist('ids')
    ids = [int(i) for i in ids_list if i.strip().isdigit()]

    # Tema de fundo
    theme_key = request.GET.get('theme', 'navy')
    if theme_key not in SLIDE_THEMES:
        theme_key = 'navy'
    theme = SLIDE_THEMES[theme_key]

    if ids:
        profiles = MemberProfile.objects.filter(
            id__in=ids, birth_date__isnull=False
        ).select_related('user')

        id_order = {pid: idx for idx, pid in enumerate(ids)}
        aniversariantes = []
        for profile in profiles:
            v = get_versiculo(profile.id)
            date_key = f'date_{profile.id}'
            try:
                data_ref = datetime.date.fromisoformat(request.GET.get(date_key, ''))
            except ValueError:
                bd = profile.birth_date
                try:
                    data_ref = today.replace(month=bd.month, day=bd.day)
                except ValueError:
                    data_ref = today
            aniversariantes.append({
                'profile': profile,
                'data': data_ref,
                'hoje': data_ref == today,
                'versiculo_ref': v[0],
                'versiculo_texto': v[1],
                'order': id_order.get(profile.id, 999),
            })
        aniversariantes.sort(key=lambda x: (not x['hoje'], x['order']))
    else:
        monday = today - datetime.timedelta(days=today.weekday())
        sunday = monday + datetime.timedelta(days=6)
        aniversariantes = buscar_aniversariantes(monday, sunday)

    return render(request, 'birthdays/slide.html', {
        'aniversariantes': aniversariantes,
        'data_ini': request.GET.get('de', str(today)),
        'data_fim': request.GET.get('ate', str(today)),
        'theme': theme,
        'theme_key': theme_key,
    })
