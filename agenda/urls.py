from django.urls import path
from . import views

urlpatterns = [
    # Calendário principal
    path('', views.agenda_view, name='agenda_view'),

    # Agendamentos
    path('lista/',             views.booking_list,   name='booking_list'),
    path('novo/',              views.booking_create, name='booking_create'),
    path('<int:pk>/',          views.booking_detail, name='booking_detail'),
    path('<int:pk>/editar/',   views.booking_edit,   name='booking_edit'),
    path('<int:pk>/excluir/',  views.booking_delete, name='booking_delete'),

    # Locais (superuser)
    path('locais/',                    views.location_manage, name='location_manage'),
    path('locais/novo/',               views.location_create, name='location_create'),
    path('locais/<int:pk>/editar/',    views.location_edit,   name='location_edit'),
    path('locais/<int:pk>/excluir/',   views.location_delete, name='location_delete'),

    # API AJAX
    path('api/disponibilidade/', views.check_availability, name='check_availability'),
]
