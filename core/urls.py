from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sobre/', views.about, name='about'),
    path('ministerios/', views.ministries_page, name='ministries'),
    path('contato/', views.contact, name='contact'),
    path('devocionais/', views.devotional_list, name='devotional_list'),
    path('devocionais/<int:pk>/', views.devotional_detail, name='devotional_detail'),
    path('dizimos-ofertas/', views.offering_page, name='offering_page'),
    path('visita/', views.visitor_form, name='visitor_form'),
    path('galeria/', views.gallery, name='gallery'),
    path('galeria/<int:pk>/', views.gallery_album, name='gallery_album'),
    path('politica-de-privacidade/', views.privacy_policy, name='privacy_policy'),
    path('midiateca/', views.media_list, name='media_list'),
    path('midiateca/<int:pk>/', views.media_detail, name='media_detail'),
    path('p/<slug:slug>/', views.page_detail, name='page_detail'),
]
