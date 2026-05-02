"""
social_publisher.py — Integração com Meta Graph API
Instagram Business + Facebook Pages

Documentação:
  Instagram: https://developers.facebook.com/docs/instagram-api/guides/content-publishing
  Facebook:  https://developers.facebook.com/docs/pages/publishing
"""
import json
import urllib.request
import urllib.parse
import urllib.error
from django.utils import timezone

GRAPH_URL = 'https://graph.facebook.com/v19.0'


# ── Helpers HTTP ──────────────────────────────────────────────────────────────

def _get(url, params=None):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read())


def _post(url, data):
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def _post_json(url, data):
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


# ── Validação de token ────────────────────────────────────────────────────────

def validate_ig_token(user_id, token):
    """Verifica se o token do Instagram está válido e retorna info da conta."""
    try:
        data = _get(f'{GRAPH_URL}/{user_id}', {
            'fields': 'id,name,username,account_type',
            'access_token': token,
        })
        return {'ok': True, 'data': data}
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        return {'ok': False, 'error': body.get('error', {}).get('message', str(e))}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def validate_fb_token(page_id, token):
    """Verifica se o token da Página do Facebook está válido."""
    try:
        data = _get(f'{GRAPH_URL}/{page_id}', {
            'fields': 'id,name,link',
            'access_token': token,
        })
        return {'ok': True, 'data': data}
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        return {'ok': False, 'error': body.get('error', {}).get('message', str(e))}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# ── Instagram Publishing ──────────────────────────────────────────────────────

def _ig_upload_single(user_id, token, image_url, caption):
    """Cria container de mídia única no Instagram."""
    data = _post(f'{GRAPH_URL}/{user_id}/media', {
        'image_url':   image_url,
        'caption':     caption,
        'access_token': token,
    })
    return data['id']


def _ig_upload_carousel_item(user_id, token, image_url):
    """Cria item de carrossel (sem legenda individual)."""
    data = _post(f'{GRAPH_URL}/{user_id}/media', {
        'image_url':    image_url,
        'is_carousel_item': True,
        'access_token': token,
    })
    return data['id']


def _ig_create_carousel(user_id, token, children_ids, caption):
    """Cria container de carrossel com os filhos."""
    data = _post(f'{GRAPH_URL}/{user_id}/media', {
        'media_type':   'CAROUSEL',
        'children':     ','.join(children_ids),
        'caption':      caption,
        'access_token': token,
    })
    return data['id']


def _ig_publish(user_id, token, creation_id):
    """Publica o container criado."""
    data = _post(f'{GRAPH_URL}/{user_id}/media_publish', {
        'creation_id':  creation_id,
        'access_token': token,
    })
    return data['id']


def _ig_get_permalink(post_id, token):
    try:
        data = _get(f'{GRAPH_URL}/{post_id}', {
            'fields': 'permalink',
            'access_token': token,
        })
        return data.get('permalink', '')
    except Exception:
        return ''


def publish_to_instagram(social_post, config, request=None):
    """
    Publica SocialPost no Instagram.
    Retorna dict com ok, post_id, permalink, error.
    """
    from core.models import SocialPost  # evita import circular

    user_id = config.ig_user_id
    token   = config.ig_access_token
    caption = social_post.full_caption()
    photos  = list(social_post.photos.all())
    base_url = (config.site_base_url or '').rstrip('/')

    if not base_url:
        return {'ok': False, 'error': 'URL pública do site não configurada.'}

    try:
        if social_post.post_format == 'single' or len(photos) == 1:
            img_url = f"{base_url}{photos[0].image.url}"
            container_id = _ig_upload_single(user_id, token, img_url, caption)
            post_id      = _ig_publish(user_id, token, container_id)

        else:  # carousel — máximo 10 fotos
            items = photos[:10]
            children = []
            for p in items:
                img_url = f"{base_url}{p.image.url}"
                cid = _ig_upload_carousel_item(user_id, token, img_url)
                children.append(cid)
            carousel_id = _ig_create_carousel(user_id, token, children, caption)
            post_id     = _ig_publish(user_id, token, carousel_id)

        permalink = _ig_get_permalink(post_id, token)
        return {'ok': True, 'post_id': post_id, 'permalink': permalink}

    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        msg  = body.get('error', {}).get('message', str(e))
        return {'ok': False, 'error': msg}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# ── Facebook Publishing ───────────────────────────────────────────────────────

def _fb_upload_photo(page_id, token, image_url, published=False):
    """Faz upload de foto para a Página (não publica ainda)."""
    data = _post(f'{GRAPH_URL}/{page_id}/photos', {
        'url':          image_url,
        'published':    'false' if not published else 'true',
        'access_token': token,
    })
    return data['id']


def _fb_create_post_with_photos(page_id, token, photo_ids, caption):
    """Cria post com múltiplas fotos anexadas."""
    params = {
        'message':      caption,
        'access_token': token,
    }
    for i, pid in enumerate(photo_ids):
        params[f'attached_media[{i}]'] = json.dumps({'media_fbid': pid})

    data = _post(f'{GRAPH_URL}/{page_id}/feed', params)
    return data['id']


def _fb_get_permalink(post_id, token):
    try:
        data = _get(f'{GRAPH_URL}/{post_id}', {
            'fields': 'permalink_url',
            'access_token': token,
        })
        return data.get('permalink_url', '')
    except Exception:
        return ''


def publish_to_facebook(social_post, config):
    """
    Publica SocialPost no Facebook.
    Retorna dict com ok, post_id, permalink, error.
    """
    page_id  = config.fb_page_id
    token    = config.fb_access_token
    caption  = social_post.full_caption()
    photos   = list(social_post.photos.all())
    base_url = (config.site_base_url or '').rstrip('/')

    if not base_url:
        return {'ok': False, 'error': 'URL pública do site não configurada.'}

    try:
        if len(photos) == 1:
            # Post simples com uma foto
            post_id = _fb_upload_photo(page_id, token, f"{base_url}{photos[0].image.url}", published=True)
            # Para foto única publicada, já tem um post_id direto
            permalink = _fb_get_permalink(post_id, token)
            return {'ok': True, 'post_id': post_id, 'permalink': permalink}
        else:
            # Upload das fotos como não-publicadas
            photo_ids = []
            for p in photos:
                img_url = f"{base_url}{p.image.url}"
                pid = _fb_upload_photo(page_id, token, img_url, published=False)
                photo_ids.append(pid)
            # Criar o post multi-foto
            post_id   = _fb_create_post_with_photos(page_id, token, photo_ids, caption)
            permalink = _fb_get_permalink(post_id, token)
            return {'ok': True, 'post_id': post_id, 'permalink': permalink}

    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        msg  = body.get('error', {}).get('message', str(e))
        return {'ok': False, 'error': msg}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# ── Evento: publicação com imagem única ──────────────────────────────────────

def publish_event_to_instagram(social_post, config):
    """Publica evento no Instagram como post de imagem única."""
    user_id  = config.ig_user_id
    token    = config.ig_access_token
    caption  = social_post.full_caption()
    base_url = (config.site_base_url or '').rstrip('/')
    event    = social_post.event

    if not base_url:
        return {'ok': False, 'error': 'URL pública do site não configurada.'}
    if not event.image:
        return {'ok': False, 'error': 'O evento não tem imagem cadastrada.'}

    try:
        img_url      = f"{base_url}{event.image.url}"
        container_id = _ig_upload_single(user_id, token, img_url, caption)
        post_id      = _ig_publish(user_id, token, container_id)
        permalink    = _ig_get_permalink(post_id, token)
        return {'ok': True, 'post_id': post_id, 'permalink': permalink}
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        return {'ok': False, 'error': body.get('error', {}).get('message', str(e))}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def publish_event_to_facebook(social_post, config):
    """Publica evento no Facebook como post com imagem e link do evento."""
    page_id  = config.fb_page_id
    token    = config.fb_access_token
    caption  = social_post.full_caption()
    base_url = (config.site_base_url or '').rstrip('/')
    event    = social_post.event

    if not base_url:
        return {'ok': False, 'error': 'URL pública do site não configurada.'}

    try:
        if event.image:
            # Post com imagem
            img_url = f"{base_url}{event.image.url}"
            post_id = _fb_upload_photo(page_id, token, img_url, published=True)
            permalink = _fb_get_permalink(post_id, token)
        else:
            # Post só com texto + link
            link = f"{base_url}{event.get_absolute_url()}"
            data = _post(f'{GRAPH_URL}/{page_id}/feed', {
                'message':      caption,
                'link':         link,
                'access_token': token,
            })
            post_id   = data['id']
            permalink = _fb_get_permalink(post_id, token)
        return {'ok': True, 'post_id': post_id, 'permalink': permalink}
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        return {'ok': False, 'error': body.get('error', {}).get('message', str(e))}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


# ── Orquestrador principal ────────────────────────────────────────────────────

def publish_social_post(social_post):
    """
    Publica um SocialPost nas plataformas configuradas.
    Suporta origem álbum (fotos) e evento (imagem única).
    Atualiza o objeto no banco com resultado.
    """
    from core.models import SocialConfig
    config = SocialConfig.get_config()

    platform    = social_post.platform
    is_event    = social_post.source_type == 'event'
    ig_result   = None
    fb_result   = None
    any_success = False
    any_failure = False

    if platform in ('instagram', 'both'):
        if config.ig_configured():
            if is_event:
                ig_result = publish_event_to_instagram(social_post, config)
            else:
                ig_result = publish_to_instagram(social_post, config)
            if ig_result['ok']:
                social_post.ig_post_id   = ig_result.get('post_id', '')
                social_post.ig_permalink = ig_result.get('permalink', '')
                social_post.ig_error     = ''
                any_success = True
            else:
                social_post.ig_error = ig_result.get('error', 'Erro desconhecido')
                any_failure = True
        else:
            social_post.ig_error = 'Instagram não configurado. Acesse Configurações > Redes Sociais.'
            any_failure = True

    if platform in ('facebook', 'both'):
        if config.fb_configured():
            if is_event:
                fb_result = publish_event_to_facebook(social_post, config)
            else:
                fb_result = publish_to_facebook(social_post, config)
            if fb_result['ok']:
                social_post.fb_post_id   = fb_result.get('post_id', '')
                social_post.fb_permalink = fb_result.get('permalink', '')
                social_post.fb_error     = ''
                any_success = True
            else:
                social_post.fb_error = fb_result.get('error', 'Erro desconhecido')
                any_failure = True
        else:
            social_post.fb_error = 'Facebook não configurado. Acesse Configurações > Redes Sociais.'
            any_failure = True

    # Determinar status final
    if any_success and any_failure:
        social_post.status = 'partial'
    elif any_success:
        social_post.status       = 'published'
        social_post.published_at = timezone.now()
    else:
        social_post.status = 'failed'

    social_post.save()
    return {'ig': ig_result, 'fb': fb_result}
