from django.urls import path
from . import views 

urlpatterns = [
    # auth
    path('login/',    views.member_login,    name='member_login'),
    path('logout/',   views.member_logout,   name='member_logout'),
    path('cadastro/', views.member_register, name='member_register'),
    path('timeout/',  views.timeout, name='session_timeout'),

    # Reset de senha
    path('esqueci-senha/',                       views.password_reset_request, name='password_reset_request'),
    path('redefinir-senha/<str:token>/',          views.password_reset_confirm, name='password_reset_confirm'),

    # member
    path('dashboard/', views.member_dashboard, name='member_dashboard'),
    path('perfil/',    views.member_profile,   name='member_profile'),
    path('professor/', views.teacher_dashboard, name='teacher_dashboard'),

    # contents
    path('conteudos/',              views.content_list,   name='content_list'),
    path('conteudos/novo/',         views.content_create, name='content_create'),
    path('conteudos/<int:pk>/',     views.content_detail, name='content_detail'),
    path('conteudos/<int:pk>/edit/',views.content_edit,   name='content_edit'),
    path('conteudos/<int:pk>/del/', views.content_delete, name='content_delete'),

    # notices
    path('avisos/',              views.notice_list,   name='notice_list'),
    path('avisos/novo/',         views.notice_create, name='notice_create'),
    path('avisos/<int:pk>/edit/',views.notice_edit,   name='notice_edit'),
    path('avisos/<int:pk>/del/', views.notice_delete, name='notice_delete'),

    # members management
    path('gerenciar-membros/',          views.members_manage,  name='members_manage'),
    path('gerenciar-membros/<int:pk>/aprovar/', views.member_approve, name='member_approve'),
    path('gerenciar-membros/<int:pk>/rejeitar/',views.member_reject,  name='member_reject'),

    # testimonies
    path('testemunhos/',                    views.testimony_manage,  name='testimony_manage'),
    path('testemunhos/<int:pk>/aprovar/',   views.testimony_approve, name='testimony_approve'),
    path('testemunhos/<int:pk>/rejeitar/',  views.testimony_reject,  name='testimony_reject'),

    # offerings
    path('dizimos/',         views.offering_list,   name='offering_list'),
    path('dizimos-gestao/',  views.offering_manage, name='offering_manage'),

    path('notificacoes/', views.notification_prefs, name='notification_prefs'),

    # visitors
    path('visitantes/',                       views.visitor_manage,    name='visitor_manage'),
    path('visitantes/<int:pk>/contato/',      views.visitor_contacted, name='visitor_contacted'),

    # prayer requests
    path('oracao/',                      views.prayer_list,    name='prayer_list'),
    path('oracao/<int:pk>/remover/',     views.prayer_delete,  name='prayer_delete'),
    path('oracao-gestao/',               views.prayer_manage,  name='prayer_manage'),
    path('oracao-gestao/<int:pk>/resp/', views.prayer_respond, name='prayer_respond'),

    # ministries
    path('ministerios-gestao/', views.ministry_manage, name='ministry_manage'),
    path('ministerios-gestao/novo/', views.ministry_create, name='ministry_create'),
    path('ministerios-gestao/<int:pk>/edit/', views.ministry_edit, name='ministry_edit'),
    path('ministerios-gestao/<int:pk>/del/', views.ministry_delete, name='ministry_delete'),

    # events (superuser)
    path('eventos-gestao/',              views.event_manage, name='event_manage'),
    path('eventos-gestao/novo/',         views.event_create, name='event_create'),
    path('eventos-gestao/<int:pk>/edit/',views.event_edit,   name='event_edit'),
    path('eventos-gestao/<int:pk>/del/', views.event_delete, name='event_delete'),

    #members
    path('gerenciar-membros/<int:pk>/editar/', views.member_edit, name='member_edit'),
    path('gerenciar-membros/<int:pk>/excluir/', views.member_delete, name='member_delete'),

    # midiateca
    path('midiateca-gestao/',                views.media_manage, name='media_manage'),
    path('midiateca-gestao/novo/',           views.media_create, name='media_create'),
    path('midiateca-gestao/<int:pk>/edit/',  views.media_edit,   name='media_edit'),
    path('midiateca-gestao/<int:pk>/del/',   views.media_delete, name='media_delete'),

    # galeria de fotos
    path('galeria-gestao/',                      views.album_manage, name='album_manage'),
    path('galeria-gestao/novo/',                 views.album_create, name='album_create'),
    path('galeria-gestao/<int:pk>/edit/',        views.album_edit,   name='album_edit'),
    path('galeria-gestao/<int:pk>/del/',         views.album_delete, name='album_delete'),
    path('galeria-gestao/<int:pk>/fotos/',       views.album_photos, name='album_photos'),

    # conteúdos — gestão staff
    path('conteudos-gestao/',                views.content_manage,        name='content_manage'),
    path('conteudos-gestao/novo/',           views.content_create_manage, name='content_create_manage'),
    path('conteudos-gestao/<int:pk>/edit/',  views.content_edit_manage,   name='content_edit_manage'),
    path('conteudos-gestao/<int:pk>/del/',   views.content_delete_manage, name='content_delete_manage'),

    # devocionais
    path('devocionais-gestao/',                views.devotional_manage, name='devotional_manage'),
    path('devocionais-gestao/novo/',           views.devotional_create, name='devotional_create'),
    path('devocionais-gestao/<int:pk>/edit/',  views.devotional_edit,   name='devotional_edit'),
    path('devocionais-gestao/<int:pk>/del/',   views.devotional_delete, name='devotional_delete'),

    # página principal (hero slides)
    path('pagina-principal/',                views.heroslide_manage, name='heroslide_manage'),
    path('pagina-principal/novo/',           views.heroslide_create, name='heroslide_create'),
    path('pagina-principal/<int:pk>/edit/',  views.heroslide_edit,   name='heroslide_edit'),
    path('pagina-principal/<int:pk>/del/',   views.heroslide_delete, name='heroslide_delete'),

    # LGPD
    path('privacidade/', views.lgpd_consent, name='lgpd_consent'),

    # Solicitações de exclusão (Colaborador → Admin)
    path('solicitar-exclusao/',                    views.delete_request_create,  name='delete_request_create'),
    path('solicitacoes-exclusao/',                 views.delete_request_manage,  name='delete_request_manage'),
    path('solicitacoes-exclusao/<int:pk>/aprovar/',views.delete_request_approve, name='delete_request_approve'),
    path('solicitacoes-exclusao/<int:pk>/recusar/',views.delete_request_reject,  name='delete_request_reject'),

    # Perfil do aluno
    path('minha-jornada/', views.student_profile, name='student_profile'),

    # Redes Sociais
    path('galeria-gestao/<int:album_pk>/publicar/',          views.social_post_create,  name='social_post_create'),
    path('galeria-gestao/<int:album_pk>/publicacoes/',       views.social_post_list,    name='social_post_list'),
    path('publicacoes-sociais/<int:pk>/publicar/',           views.social_post_publish, name='social_post_publish'),
    path('publicacoes-sociais/<int:pk>/del/',                views.social_post_delete,  name='social_post_delete'),
    path('configuracoes/redes-sociais/',                     views.social_config,       name='social_config'),

    # Exportação de dados
    path('exportar/',                views.exportar_centro,         name='exportar_centro'),
    path('exportar/membros/',        views.exportar_membros,        name='exportar_membros'),
    path('exportar/presencas/',      views.exportar_presencas,      name='exportar_presencas'),
    path('exportar/contribuicoes/',  views.exportar_contribuicoes,  name='exportar_contribuicoes'),
    path('exportar/eventos/',        views.exportar_eventos,        name='exportar_eventos'),
    path('exportar/visitantes/',     views.exportar_visitantes,     name='exportar_visitantes'),
    path('exportar/aniversariantes/',views.exportar_aniversariantes,name='exportar_aniversariantes'),

    # Presenças
    path('presencas/',                       views.culto_manage,       name='culto_manage'),
    path('presencas/novo/',                  views.culto_create,       name='culto_create'),
    path('presencas/<int:pk>/chamada/',      views.culto_chamada,      name='culto_chamada'),
    path('presencas/<int:pk>/del/',          views.culto_delete,       name='culto_delete'),
    path('presencas/relatorio/',             views.presenca_relatorio,  name='presenca_relatorio'),

    # Células — CRUD do Dashboard
    path('celulas-gestao/',                        views.cell_manage,           name='cell_manage_dashboard'),
    path('celulas-gestao/nova/',                   views.cell_create,            name='cell_create_dashboard'),
    path('celulas-gestao/<int:pk>/edit/',          views.cell_edit,              name='cell_edit_dashboard'),
    path('celulas-gestao/<int:pk>/del/',           views.cell_delete,            name='cell_delete_dashboard'),
    path('celulas-gestao/<int:pk>/membros/',       views.cell_members_dashboard, name='cell_members_dashboard'),

    # EBD — CRUD do Dashboard
    path('ebd-gestao/',                                    views.ebd_manage,             name='ebd_manage'),
    path('ebd-gestao/turma/nova/',                         views.ebd_class_create,        name='ebd_class_create'),
    path('ebd-gestao/turma/<int:pk>/edit/',                views.ebd_class_edit,          name='ebd_class_edit'),
    path('ebd-gestao/turma/<int:pk>/del/',                 views.ebd_class_delete,        name='ebd_class_delete'),
    path('ebd-gestao/turma/<int:class_pk>/trimestres/',    views.ebd_trimester_manage,    name='ebd_trimester_manage'),
    path('ebd-gestao/turma/<int:class_pk>/trimestre/novo/',views.ebd_trimester_create,    name='ebd_trimester_create'),
    path('ebd-gestao/trimestre/<int:pk>/edit/',            views.ebd_trimester_edit,      name='ebd_trimester_edit'),
    path('ebd-gestao/trimestre/<int:pk>/del/',             views.ebd_trimester_delete,    name='ebd_trimester_delete'),
    path('ebd-gestao/trimestre/<int:trimester_pk>/licoes/',views.ebd_lesson_manage,       name='ebd_lesson_manage'),
    path('ebd-gestao/trimestre/<int:trimester_pk>/licao/nova/', views.ebd_lesson_create,  name='ebd_lesson_create'),
    path('ebd-gestao/licao/<int:pk>/edit/',                views.ebd_lesson_edit,         name='ebd_lesson_edit'),
    path('ebd-gestao/licao/<int:pk>/del/',                 views.ebd_lesson_delete,       name='ebd_lesson_delete'),
    path('ebd-gestao/licao/<int:lesson_pk>/quiz/',         views.ebd_quiz_manage,         name='ebd_quiz_manage'),
    path('ebd-gestao/licao/<int:lesson_pk>/quiz/del/',     views.ebd_quiz_delete,         name='ebd_quiz_delete'),

    # Redes Sociais — Eventos
    path('eventos-gestao/<int:event_pk>/publicar/',          views.event_social_post_create,  name='event_social_post_create'),
    path('eventos-gestao/<int:event_pk>/publicacoes/',       views.event_social_post_list,    name='event_social_post_list'),
    path('eventos-social/<int:pk>/publicar/',                views.event_social_post_publish, name='event_social_post_publish'),
    path('eventos-social/<int:pk>/del/',                     views.event_social_post_delete,  name='event_social_post_delete'),


    # Configurações da Igreja (CMS)
    path('configuracoes/igreja/', views.church_settings, name='church_settings'),
    path('busca/', views.search, name='search'),
    #path('login/verificar/', views.login_verify_2fa, name='login_verify_2fa'),
    #path('login/reenviar/', views.login_resend_2fa,  name='login_resend_2fa'),
]