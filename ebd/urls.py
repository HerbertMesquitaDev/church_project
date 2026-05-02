from django.urls import path
from . import views

urlpatterns = [
    path('',                                 views.ebd_home,          name='ebd_home'),
    path('licao/<int:pk>/',                  views.ebd_lesson_preview, name='ebd_lesson_preview'),
    path('licao/<int:pk>/estudo/',           views.ebd_lesson_detail,  name='ebd_lesson_detail'),
    path('licao/<int:lesson_pk>/quiz/',      views.ebd_quiz,           name='ebd_quiz'),
    path('resultado/<int:attempt_pk>/',      views.ebd_quiz_result,    name='ebd_quiz_result'),
    path('meu-progresso/',                   views.ebd_my_progress,    name='ebd_my_progress'),
]
