from .models import SiteSettings, Page


def site_info(request):
    igreja = getattr(request, 'igreja', None)
    nav_pages = Page.objects.filter(published=True, show_in_nav=True).order_by('nav_order', 'title')
    if igreja:
        nav_pages = nav_pages.filter(igreja=igreja)
    return {
        'site_settings': SiteSettings.get_settings(igreja),
        'nav_pages': nav_pages,
    }


def pending_prayer_count(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        from members.models import PrayerRequest
        igreja = getattr(request, 'igreja', None)
        qs = PrayerRequest.objects.filter(status='open')
        if igreja:
            qs = qs.filter(profile__igreja=igreja)
        return {'pending_prayer_count': qs.count()}
    return {'pending_prayer_count': 0}


def pending_testimony_count(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        from members.models import Testimony
        return {'pending_testimony_count': Testimony.objects.filter(status='pending').count()}
    return {'pending_testimony_count': 0}


def pending_visitor_count(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        from core.models import Visitor
        igreja = getattr(request, 'igreja', None)
        qs = Visitor.objects.filter(contacted=False)
        if igreja:
            qs = qs.filter(igreja=igreja)
        return {'pending_visitor_count': qs.count()}
    return {'pending_visitor_count': 0}


def pending_cell_count(request):
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        from cells.models import CellMembership
        return {'pending_cell_count': CellMembership.objects.filter(status='pending').count()}
    return {'pending_cell_count': 0}


def pending_delete_count(request):
    if request.user.is_authenticated and request.user.is_superuser:
        from members.models import DeleteRequest
        return {'pending_delete_count': DeleteRequest.objects.filter(status='pending').count()}
    return {'pending_delete_count': 0}