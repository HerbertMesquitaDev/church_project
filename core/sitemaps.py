from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from core.models import Devotional, MediaItem, Page
from events.models import Event
from courses.models import Course
from ebd.models import EbdLesson


class StaticViewSitemap(Sitemap):
    priority   = 0.8
    changefreq = 'weekly'

    def items(self):
        return ['home', 'about', 'ministries', 'contact', 'offering_page',
                'gallery', 'media_list', 'devotional_list']

    def location(self, item):
        return reverse(item)


class EventSitemap(Sitemap):
    changefreq = 'weekly'
    priority   = 0.7

    def items(self):
        return Event.objects.filter(published=True, date__gte=timezone.now()).order_by('-date')

    def lastmod(self, obj):
        return obj.updated_at

    def priority(self, obj):
        return 0.9 if obj.featured else 0.7


class DevotionalSitemap(Sitemap):
    changefreq = 'daily'
    priority   = 0.6

    def items(self):
        return Devotional.objects.filter(published=True).order_by('-pub_date')[:90]

    def lastmod(self, obj):
        return obj.pub_date


class MediaSitemap(Sitemap):
    changefreq = 'weekly'
    priority   = 0.6

    def items(self):
        return MediaItem.objects.filter(published=True, visibility='public').order_by('-pub_date')

    def lastmod(self, obj):
        return obj.created_at


class PageSitemap(Sitemap):
    changefreq = 'monthly'
    priority   = 0.7

    def items(self):
        return Page.objects.filter(published=True)

    def lastmod(self, obj):
        return obj.updated_at


class CourseSitemap(Sitemap):
    changefreq = 'monthly'
    priority   = 0.6

    def items(self):
        return Course.objects.filter(published=True)

    def lastmod(self, obj):
        return obj.updated_at


# Mapa completo para registrar nas URLs
sitemaps = {
    'static':      StaticViewSitemap,
    'events':      EventSitemap,
    'devocionais': DevotionalSitemap,
    'midia':       MediaSitemap,
    'paginas':     PageSitemap,
    'cursos':      CourseSitemap,
}
