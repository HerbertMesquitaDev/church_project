from django.urls import path
from . import views

urlpatterns = [
    path('', views.birthday_list, name='birthday_list'),
    path('slide/', views.birthday_slide, name='birthday_slide'),
]
