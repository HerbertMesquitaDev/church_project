from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────
    path('auth/login/',  views.api_login,  name='api_login'),
    path('auth/logout/', views.api_logout, name='api_logout'),

    # ── Eventos ───────────────────────────────────────────
    path('eventos/',              views.EventListView.as_view(),         name='api_event_list'),
    path('eventos/inscricao/',    views.EventRegistrationView.as_view(), name='api_event_register'),
    path('eventos/<slug:slug>/',  views.EventDetailView.as_view(),       name='api_event_detail'),

    # ── Devocionais ───────────────────────────────────────
    path('devocionais/',        views.DevotionalListView.as_view(),  name='api_devotional_list'),
    path('devocionais/hoje/',   views.DevotionalTodayView.as_view(), name='api_devotional_today'),

    # ── Mídiateca ─────────────────────────────────────────
    path('midiateca/categorias/', views.MediaCategoryListView.as_view(), name='api_media_categories'),
    path('midiateca/',            views.MediaItemListView.as_view(),     name='api_media_list'),
    path('midiateca/<int:pk>/',   views.MediaItemDetailView.as_view(),   name='api_media_detail'),

    # ── Células ───────────────────────────────────────────
    path('celulas/', views.CellListView.as_view(), name='api_cell_list'),

    # ── Páginas dinâmicas ─────────────────────────────────
    path('paginas/',              views.PageListView.as_view(),   name='api_page_list'),
    path('paginas/<slug:slug>/',  views.PageDetailView.as_view(), name='api_page_detail'),

    # ── EBD ──────────────────────────────────────────────
    path('ebd/', views.EbdClassListView.as_view(), name='api_ebd_list'),

    # ── Cursos ────────────────────────────────────────────
    path('cursos/',                                  views.CourseListView.as_view(),    name='api_course_list'),
    path('cursos/inscricao/',                        views.EnrollView.as_view(),        name='api_enroll'),
    path('cursos/minhas-inscricoes/',                views.MyEnrollmentsView.as_view(), name='api_my_enrollments'),
    path('cursos/aulas/<int:lesson_id>/progresso/',  views.LessonProgressView.as_view(), name='api_lesson_progress'),
    path('cursos/<slug:slug>/',                      views.CourseDetailView.as_view(),  name='api_course_detail'),

    # ── Conteúdo exclusivo (requer login) ─────────────────
    path('conteudo/',          views.ExclusiveContentListView.as_view(),   name='api_content_list'),
    path('conteudo/<int:pk>/', views.ExclusiveContentDetailView.as_view(), name='api_content_detail'),

    # ── Avisos (requer login) ─────────────────────────────
    path('avisos/', views.NoticeListView.as_view(), name='api_notice_list'),

    # ── Perfil (requer login) ─────────────────────────────
    path('me/', views.MeView.as_view(), name='api_me'),

    # ── Pedidos de Oração (requer login) ──────────────────
    path('pedidos-oracao/',          views.PrayerRequestListCreateView.as_view(), name='api_prayer_list'),
    path('pedidos-oracao/<int:pk>/', views.PrayerRequestUpdateView.as_view(),     name='api_prayer_update'),

    # ── Testemunhos (requer login) ────────────────────────
    path('testemunhos/',     views.TestimonyListView.as_view(),   name='api_testimony_list'),
    path('testemunhos/novo/', views.TestimonyCreateView.as_view(), name='api_testimony_create'),

    # ── Células — detalhe e posts (requer login) ──────────
    path('celulas/<int:pk>/',        views.CellDetailView.as_view(),        name='api_cell_detail'),
    path('celulas/<int:pk>/posts/',  views.CellPostListCreateView.as_view(), name='api_cell_posts'),
    path('celulas/<int:pk>/entrar/', views.CellJoinView.as_view(),           name='api_cell_join'),
    path('celulas/<int:pk>/sair/',   views.CellLeaveView.as_view(),          name='api_cell_leave'),
]
