from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from core import views as core_views
from core.sitemaps import sitemaps
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "Painel da Igreja"
admin.site.site_title = "Igreja Admin"
admin.site.index_title = "Gerenciamento do Site"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', core_views.robots_txt, name='robots_txt'),
    path('api/v1/', include('api.urls')),
    path('sw.js',    core_views.service_worker, name='service_worker'),
    path('offline/', core_views.offline,         name='offline'),
    path('', include('core.urls')),
    path('membros/cursos/', include('courses.urls')),
    path('membros/', include('members.urls')),
    path('eventos/', include('events.urls')),
    path('membros/agenda/', include('agenda.urls')),
    path('ebd/', include('ebd.urls')),
    path('membros/celulas/', include('cells.urls')),
    path('aniversariantes/', include('birthdays.urls')),
    path('superadmin/', include('superadmin.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ── Handlers de erro personalizados ───────────────────────
handler400 = 'core.views.error_400'
handler403 = 'core.views.error_403'
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'
