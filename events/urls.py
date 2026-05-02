from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.event_list,               name='event_list'),
    path('<slug:slug>/',                  views.event_detail,             name='event_detail'),
    path('<slug:slug>/inscrever/',        views.event_register,           name='event_register'),
    path('<slug:slug>/cancelar/',         views.event_cancel_registration, name='event_cancel_registration'),
    path('<slug:slug>/inscritos/',        views.event_registrations_list,  name='event_registrations_list'),
]
