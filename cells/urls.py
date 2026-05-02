from django.urls import path
from . import views

urlpatterns = [
    path('',                                    views.cell_list,            name='cell_list'),
    path('<int:pk>/',                           views.cell_detail,          name='cell_detail'),
    path('<int:pk>/entrar/',                    views.cell_join,            name='cell_join'),
    path('<int:pk>/sair/',                      views.cell_leave,           name='cell_leave'),
    path('<int:pk>/membros/',                   views.cell_manage_members,  name='cell_manage_members'),
    path('<int:pk>/post/<int:post_pk>/excluir/', views.cell_delete_post,    name='cell_delete_post'),
    path('<int:pk>/post/<int:post_pk>/fixar/',   views.cell_pin_post,       name='cell_pin_post'),
    path('<int:pk>/post/<int:post_pk>/reagir/',  views.cell_react,          name='cell_react'),
]
