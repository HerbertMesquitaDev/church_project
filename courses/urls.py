from django.urls import path
from . import views

urlpatterns = [
    # Rotas fixas primeiro (antes do slug genérico)
    path('',              views.course_list, name='course_list'),
    path('meus-cursos/', views.my_courses,   name='my_courses'),
    path('aula/<int:pk>/',          views.lesson_detail,  name='lesson_detail'),
    path('aula/<int:pk>/concluir/', views.lesson_complete, name='lesson_complete'),
    path('aula/<int:pk>/comentar/', views.lesson_comment,  name='lesson_comment'),
    path('aula/<int:pk>/quiz/',     views.lesson_quiz,     name='lesson_quiz'),

    # Gestão staff (antes do slug também)
    path('gestao/',                           views.manage_courses,       name='manage_courses'),
    path('gestao/novo/',                      views.manage_course_create, name='manage_course_create'),
    path('gestao/<int:pk>/edit/',             views.manage_course_edit,   name='manage_course_edit'),
    path('gestao/<int:pk>/del/',              views.manage_course_delete, name='manage_course_delete'),
    path('gestao/<int:pk>/modulos/',          views.manage_modules,       name='manage_modules'),
    path('gestao/modulo/<int:pk>/aulas/',     views.manage_lessons,       name='manage_lessons'),
    path('gestao/aula/nova/<int:module_pk>/', views.manage_lesson_create, name='manage_lesson_create'),
    path('gestao/aula/<int:pk>/edit/',        views.manage_lesson_edit,   name='manage_lesson_edit'),
    path('gestao/aula/<int:pk>/del/',         views.manage_lesson_delete, name='manage_lesson_delete'),
    path('gestao/<int:pk>/inscritos/',        views.manage_enrollments,   name='manage_enrollments'),

    # Gestão de quiz (staff)
    path('gestao/aula/<int:lesson_pk>/quiz/',              views.manage_quiz,                  name='manage_quiz'),
    path('gestao/aula/<int:lesson_pk>/quiz/pergunta/nova/',views.manage_quiz_question_create,   name='manage_quiz_question_create'),
    path('gestao/quiz/pergunta/<int:pk>/edit/',             views.manage_quiz_question_edit,     name='manage_quiz_question_edit'),
    path('gestao/quiz/pergunta/<int:pk>/del/',              views.manage_quiz_question_delete,   name='manage_quiz_question_delete'),
    path('gestao/quiz/alternativa/nova/<int:question_pk>/', views.manage_quiz_choice_create,     name='manage_quiz_choice_create'),
    path('gestao/quiz/alternativa/<int:pk>/edit/',          views.manage_quiz_choice_edit,       name='manage_quiz_choice_edit'),
    path('gestao/quiz/alternativa/<int:pk>/del/',           views.manage_quiz_choice_delete,     name='manage_quiz_choice_delete'),

    # Slug genérico por último
    path('<slug:slug>/',          views.course_detail,   name='course_detail'),
    path('<slug:slug>/inscrever/', views.course_enroll,  name='course_enroll'),
    path('<slug:slug>/cancelar/', views.course_unenroll, name='course_unenroll'),
]
