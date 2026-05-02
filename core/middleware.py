import hashlib
from django.core.cache import cache
from django.utils import timezone

SKIP_PREFIXES = ('/admin/', '/static/', '/media/', '/api/', '/tinymce/', '/superadmin/')
SKIP_EXACT    = {'/sw.js', '/robots.txt', '/sitemap.xml', '/offline/'}
ONLINE_TTL    = 300  # 5 minutos
GEO_TTL       = 60 * 60 * 24 * 7  # 7 dias
RATE_TTL      = 60 * 30  # 30 minutos por sessão+página

_BOTS = ('bot', 'crawler', 'spider', 'slurp', 'ia_archiver', 'facebookexternalhit', 'python-requests')


def _get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '') or None


def _is_private_ip(ip):
    return (not ip or ip in ('127.0.0.1', '::1')
            or ip.startswith('192.168.')
            or ip.startswith('10.')
            or ip.startswith('172.'))


def _is_bot(ua):
    ua = ua.lower()
    return any(b in ua for b in _BOTS)


def _get_geo(ip):
    if _is_private_ip(ip):
        return {'city': '', 'regionName': 'Local', 'countryCode': 'BR'}
    cache_key = f'geo:{ip}'
    geo = cache.get(cache_key)
    if geo is None:
        try:
            import requests as req
            resp = req.get(
                f'http://ip-api.com/json/{ip}?fields=status,city,regionName,countryCode&lang=pt-BR',
                timeout=2,
            )
            data = resp.json()
            geo = data if data.get('status') == 'success' else {}
        except Exception:
            geo = {}
        cache.set(cache_key, geo, GEO_TTL)
    return geo


def _update_online(session_key):
    try:
        from django_redis import get_redis_connection
        r   = get_redis_connection('default')
        now = int(timezone.now().timestamp())
        r.zadd('online_visitors', {session_key: now})
        r.zremrangebyscore('online_visitors', 0, now - ONLINE_TTL)
    except Exception:
        pass


class VisitTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method != 'GET' or response.status_code >= 400:
            return response
        path = request.path
        if path in SKIP_EXACT or any(path.startswith(p) for p in SKIP_PREFIXES):
            return response
        if _is_bot(request.META.get('HTTP_USER_AGENT', '')):
            return response

        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key

        _update_online(session_key)

        # Rate-limit: um registro por sessão+página a cada 30 min
        page_hash = hashlib.md5(path.encode()).hexdigest()[:8]
        rate_key  = f'visit_rl:{session_key}:{page_hash}'
        if cache.get(rate_key):
            return response
        cache.set(rate_key, 1, RATE_TTL)

        ip  = _get_ip(request)
        geo = _get_geo(ip)

        from core.models import SiteVisit
        SiteVisit.objects.create(
            igreja       = getattr(request, 'igreja', None),
            session_key  = session_key,
            ip           = ip,
            user         = request.user if request.user.is_authenticated else None,
            page         = path[:500],
            city         = geo.get('city', '')[:100],
            region       = geo.get('regionName', '')[:100],
            country_code = geo.get('countryCode', '')[:5],
        )

        return response
