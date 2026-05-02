from datetime import timedelta
from django import template
from django.db.models import Count
from django.utils import timezone

register = template.Library()


@register.simple_tag
def get_online_count():
    try:
        from django_redis import get_redis_connection
        r   = get_redis_connection('default')
        now = int(timezone.now().timestamp())
        r.zremrangebyscore('online_visitors', 0, now - 300)
        return r.zcard('online_visitors')
    except Exception:
        return 0


@register.simple_tag
def get_visit_stats():
    try:
        from core.models import SiteVisit
        today = timezone.localdate()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        base = SiteVisit.objects
        return {
            'today':       base.filter(visited_at__date=today).count(),
            'week':        base.filter(visited_at__date__gte=week_ago).count(),
            'top_regions': (
                base.filter(visited_at__date__gte=month_ago)
                    .exclude(region='')
                    .exclude(region='Local')
                    .values('region')
                    .annotate(total=Count('id'))
                    .order_by('-total')[:6]
            ),
        }
    except Exception:
        return {'today': 0, 'week': 0, 'top_regions': []}


@register.simple_tag
def get_seal_count():
    try:
        from courses.models import PerfectStudentSeal
        return PerfectStudentSeal.objects.count()
    except Exception:
        return 0
