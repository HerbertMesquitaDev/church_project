"""Testes dos endpoints da API REST."""
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from core.models import Devotional, Page, MediaCategory, MediaItem
from events.models import Event, Category as EventCategory
from cells.models import Cell
from courses.models import Course, Module, Lesson, Enrollment
from members.models import ExclusiveContent, Notice
from ebd.models import EbdClass, EbdTrimester, EbdLesson


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(
        username='membro', password='senha123', email='membro@teste.com'
    )


@pytest.fixture
def staff_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username='pastor', password='senha123', is_staff=True
    )


@pytest.fixture
def token(db, user):
    t, _ = Token.objects.get_or_create(user=user)
    return t


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, token):
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    return api_client


@pytest.fixture
def event(db):
    cat = EventCategory.objects.create(name='Culto', color='#111')
    return Event.objects.create(
        title='Culto de Domingo', slug='culto-domingo',
        description='Desc', date=timezone.now() + timezone.timedelta(days=3),
        published=True, category=cat,
    )


@pytest.fixture
def past_event(db):
    return Event.objects.create(
        title='Evento Passado', slug='evento-passado',
        description='Desc', date=timezone.now() - timezone.timedelta(days=3),
        published=True,
    )


@pytest.fixture
def devotional_today(db):
    return Devotional.objects.create(
        pub_date=timezone.localdate(), title='Fé', verse='Jo 3:16',
        reflection='Reflexão', published=True, author='Pastor Teste',
    )


@pytest.fixture
def media_item(db):
    cat = MediaCategory.objects.create(name='Pregação', section='sermon', icon='fa-bible')
    return MediaItem.objects.create(
        title='Sermão da Montanha', category=cat,
        media_type='video', visibility='public',
        pub_date=timezone.localdate(), published=True,
    )


@pytest.fixture
def page(db):
    return Page.objects.create(
        title='Sobre', slug='sobre', content='<p>Conteúdo</p>', published=True
    )


@pytest.fixture
def cell(db):
    return Cell.objects.create(name='Célula Norte', cell_type='region', active=True)


@pytest.fixture
def course(db, staff_user):
    return Course.objects.create(
        title='Discipulado', description='Desc', instructor=staff_user, published=True
    )


@pytest.fixture
def ebd_data(db):
    cls = EbdClass.objects.create(name='Jovens', active=True)
    tri = EbdTrimester.objects.create(ebd_class=cls, year=2025, quarter=2, title='Graça')
    EbdLesson.objects.create(trimester=tri, number=1, title='O Dom da Graça', published=True)
    return cls


@pytest.fixture
def exclusive_content(db, staff_user):
    return ExclusiveContent.objects.create(
        title='Estudo Especial', body='Conteúdo exclusivo', published=True, author=staff_user
    )


@pytest.fixture
def notice(db):
    return Notice.objects.create(title='Aviso', body='Texto', published=True)


# ── Auth ──────────────────────────────────────────────────

class TestApiAuth:
    def test_login_success(self, api_client, user):
        resp = api_client.post('/api/v1/auth/login/', {'username': 'membro', 'password': 'senha123'})
        assert resp.status_code == 200
        assert 'token' in resp.data

    def test_login_wrong_password(self, api_client, user):
        resp = api_client.post('/api/v1/auth/login/', {'username': 'membro', 'password': 'errada'})
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, api_client, db):
        resp = api_client.post('/api/v1/auth/login/', {'username': 'nao_existe', 'password': '123'})
        assert resp.status_code == 401

    def test_logout_success(self, auth_client, token):
        resp = auth_client.post('/api/v1/auth/logout/')
        assert resp.status_code == 200
        assert not Token.objects.filter(key=token.key).exists()

    def test_logout_requires_auth(self, api_client, db):
        resp = api_client.post('/api/v1/auth/logout/')
        assert resp.status_code in (401, 403)


# ── Eventos ───────────────────────────────────────────────

class TestEventApi:
    def test_list_events(self, api_client, event):
        resp = api_client.get('/api/v1/eventos/')
        assert resp.status_code == 200
        assert resp.data['count'] == 1

    def test_unpublished_not_listed(self, api_client, db):
        Event.objects.create(
            title='Rascunho', slug='rascunho', description='.',
            date=timezone.now(), published=False
        )
        resp = api_client.get('/api/v1/eventos/')
        assert resp.data['count'] == 0

    def test_filter_upcoming(self, api_client, event, past_event):
        resp = api_client.get('/api/v1/eventos/?upcoming=1')
        titles = [e['title'] for e in resp.data['results']]
        assert 'Culto de Domingo' in titles
        assert 'Evento Passado' not in titles

    def test_event_detail(self, api_client, event):
        resp = api_client.get(f'/api/v1/eventos/{event.slug}/')
        assert resp.status_code == 200
        assert resp.data['title'] == 'Culto de Domingo'
        assert 'description' in resp.data

    def test_event_detail_not_found(self, api_client, db):
        resp = api_client.get('/api/v1/eventos/nao-existe/')
        assert resp.status_code == 404

    def test_event_registration_requires_auth(self, api_client, event):
        resp = api_client.post('/api/v1/eventos/inscricao/', {'event': event.pk})
        assert resp.status_code in (401, 403)

    def test_event_registration_authenticated(self, auth_client, event):
        resp = auth_client.post('/api/v1/eventos/inscricao/', {'event': event.pk})
        assert resp.status_code in (200, 201)
        assert resp.data['status'] == 'confirmed'


# ── Devocionais ───────────────────────────────────────────

class TestDevotionalApi:
    def test_list(self, api_client, devotional_today):
        resp = api_client.get('/api/v1/devocionais/')
        assert resp.status_code == 200
        assert resp.data['count'] == 1

    def test_today(self, api_client, devotional_today):
        resp = api_client.get('/api/v1/devocionais/hoje/')
        assert resp.status_code == 200
        assert resp.data['title'] == 'Fé'

    def test_today_not_found(self, api_client, db):
        resp = api_client.get('/api/v1/devocionais/hoje/')
        assert resp.status_code == 404

    def test_unpublished_not_listed(self, api_client, devotional_today, db):
        devotional_today.published = False
        devotional_today.save()
        resp = api_client.get('/api/v1/devocionais/')
        assert resp.data['count'] == 0


# ── Mídiateca ─────────────────────────────────────────────

class TestMediaApi:
    def test_list(self, api_client, media_item):
        resp = api_client.get('/api/v1/midiateca/')
        assert resp.status_code == 200
        assert resp.data['count'] == 1

    def test_filter_by_tipo(self, api_client, media_item):
        resp = api_client.get('/api/v1/midiateca/?tipo=video')
        assert resp.data['count'] == 1
        resp2 = api_client.get('/api/v1/midiateca/?tipo=audio')
        assert resp2.data['count'] == 0

    def test_categories(self, api_client, media_item):
        resp = api_client.get('/api/v1/midiateca/categorias/')
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_member_only_not_listed(self, api_client, db):
        cat = MediaCategory.objects.create(name='Exclusivo', section='other', icon='fa-lock')
        MediaItem.objects.create(
            title='Só Membros', category=cat, media_type='video',
            visibility='members', pub_date=timezone.localdate(), published=True
        )
        resp = api_client.get('/api/v1/midiateca/')
        assert resp.data['count'] == 0


# ── Células ───────────────────────────────────────────────

class TestCellApi:
    def test_list(self, api_client, cell):
        resp = api_client.get('/api/v1/celulas/')
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_inactive_not_listed(self, api_client, db):
        Cell.objects.create(name='Inativa', cell_type='other', active=False)
        resp = api_client.get('/api/v1/celulas/')
        assert len(resp.data) == 0

    def test_member_count_in_response(self, api_client, cell):
        resp = api_client.get('/api/v1/celulas/')
        assert resp.data[0]['member_count'] == 0


# ── Páginas ───────────────────────────────────────────────

class TestPageApi:
    def test_list(self, api_client, page):
        resp = api_client.get('/api/v1/paginas/')
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_detail(self, api_client, page):
        resp = api_client.get(f'/api/v1/paginas/{page.slug}/')
        assert resp.status_code == 200
        assert resp.data['title'] == 'Sobre'
        assert '<p>Conteúdo</p>' in resp.data['content']

    def test_unpublished_not_accessible(self, api_client, db):
        Page.objects.create(title='Rascunho', slug='rascunho', published=False)
        resp = api_client.get('/api/v1/paginas/rascunho/')
        assert resp.status_code == 404


# ── EBD ──────────────────────────────────────────────────

class TestEbdApi:
    def test_list_classes(self, api_client, ebd_data):
        resp = api_client.get('/api/v1/ebd/')
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]['name'] == 'Jovens'

    def test_trimesters_nested(self, api_client, ebd_data):
        resp = api_client.get('/api/v1/ebd/')
        trimesters = resp.data[0]['trimesters']
        assert len(trimesters) == 1
        assert trimesters[0]['title'] == 'Graça'

    def test_lessons_nested(self, api_client, ebd_data):
        resp = api_client.get('/api/v1/ebd/')
        lessons = resp.data[0]['trimesters'][0]['lessons']
        assert len(lessons) == 1
        assert lessons[0]['title'] == 'O Dom da Graça'


# ── Cursos ────────────────────────────────────────────────

class TestCourseApi:
    def test_list(self, api_client, course):
        resp = api_client.get('/api/v1/cursos/')
        assert resp.status_code == 200
        assert resp.data['count'] == 1

    def test_detail_with_modules(self, api_client, course, db):
        mod = Module.objects.create(course=course, title='Módulo 1', order=1)
        Lesson.objects.create(module=mod, title='Aula 1', order=1, published=True)
        resp = api_client.get(f'/api/v1/cursos/{course.slug}/')
        assert resp.status_code == 200
        assert len(resp.data['modules']) == 1
        assert len(resp.data['modules'][0]['lessons']) == 1

    def test_enroll_requires_auth(self, api_client, course):
        resp = api_client.post('/api/v1/cursos/inscricao/', {'course': course.pk})
        assert resp.status_code in (401, 403)

    def test_enroll_authenticated(self, auth_client, course):
        resp = auth_client.post('/api/v1/cursos/inscricao/', {'course': course.pk})
        assert resp.status_code in (200, 201)
        assert Enrollment.objects.filter(course=course).count() == 1

    def test_enroll_idempotent(self, auth_client, course):
        auth_client.post('/api/v1/cursos/inscricao/', {'course': course.pk})
        resp = auth_client.post('/api/v1/cursos/inscricao/', {'course': course.pk})
        assert resp.status_code == 200
        assert Enrollment.objects.filter(course=course).count() == 1

    def test_my_enrollments(self, auth_client, course, user):
        before = Enrollment.objects.filter(user=user, active=True).count()
        Enrollment.objects.get_or_create(course=course, user=user, defaults={'active': True})
        resp = auth_client.get('/api/v1/cursos/minhas-inscricoes/')
        assert resp.status_code == 200
        assert len(resp.data) >= before + 1 or len(resp.data) >= 1

    def test_my_enrollments_requires_auth(self, api_client, db):
        resp = api_client.get('/api/v1/cursos/minhas-inscricoes/')
        assert resp.status_code in (401, 403)


# ── Conteúdo exclusivo ────────────────────────────────────

class TestExclusiveContentApi:
    def test_requires_auth(self, api_client, exclusive_content):
        resp = api_client.get('/api/v1/conteudo/')
        assert resp.status_code == 401

    def test_list_authenticated(self, auth_client, exclusive_content):
        resp = auth_client.get('/api/v1/conteudo/')
        assert resp.status_code == 200
        assert resp.data['count'] == 1

    def test_detail_authenticated(self, auth_client, exclusive_content):
        resp = auth_client.get(f'/api/v1/conteudo/{exclusive_content.pk}/')
        assert resp.status_code == 200
        assert resp.data['title'] == 'Estudo Especial'

    def test_filter_by_tipo(self, auth_client, exclusive_content):
        resp = auth_client.get('/api/v1/conteudo/?tipo=text')
        assert resp.data['count'] == 1
        resp2 = auth_client.get('/api/v1/conteudo/?tipo=video')
        assert resp2.data['count'] == 0


# ── Avisos ────────────────────────────────────────────────

class TestNoticeApi:
    def test_requires_auth(self, api_client, notice):
        resp = api_client.get('/api/v1/avisos/')
        assert resp.status_code == 401

    def test_list_authenticated(self, auth_client, notice):
        resp = auth_client.get('/api/v1/avisos/')
        assert resp.status_code == 200
        assert len(resp.data) == 1

    def test_expired_not_shown(self, auth_client, db):
        Notice.objects.create(
            title='Expirado', body='.',
            published=True,
            expires_at=timezone.now() - timezone.timedelta(hours=1)
        )
        resp = auth_client.get('/api/v1/avisos/')
        assert len(resp.data) == 0
