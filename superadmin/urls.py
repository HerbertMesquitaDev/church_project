from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.dashboard,      name='sa_dashboard'),
    path('igrejas/',                views.igreja_list,    name='sa_igreja_list'),
    path('igrejas/nova/',           views.igreja_create,  name='sa_igreja_create'),
    path('igrejas/<int:pk>/',       views.igreja_detail,  name='sa_igreja_detail'),
    path('igrejas/<int:pk>/edit/',  views.igreja_edit,    name='sa_igreja_edit'),
    path('igrejas/<int:pk>/toggle/',views.igreja_toggle,  name='sa_igreja_toggle'),
]