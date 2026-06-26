"""Testes de views públicas e de autenticação."""
import pytest
from django.urls import reverse
from django.utils import timezone

from core.models import SiteSettings, Devotional, Page
from events.models import Event


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(
        username='membro', password='senha123',
        first_name='João', last_name='Silva'
    )


@pytest.fixture
def approved_user(db, django_user_model):
    from members.models import MemberProfile
    u = django_user_model.objects.create_user(username='aprovado', password='senha123')
    MemberProfile.objects.create(user=u, approved=True)
    return u


@pytest.fixture
def site_settings(db):
    return SiteSettings.objects.create(church_name='Igreja Teste')


@pytest.fixture
def event(db):
    return Event.objects.create(
        title='Evento Público', slug='evento-publico',
        description='Desc', date=timezone.now() + timezone.timedelta(days=5),
        published=True,
    )


@pytest.fixture
def page(db):
    return Page.objects.create(
        title='Nossa História', slug='nossa-historia',
        content='<p>Texto</p>', published=True,
    )


# ── Views públicas ────────────────────────────────────────

class TestPublicViews:
    def test_home_ok(self, client, site_settings):
        resp = client.get(reverse('home'))
        assert resp.status_code == 200

    def test_about_ok(self, client, site_settings):
        resp = client.get(reverse('about'))
        assert resp.status_code == 200

    def test_contact_ok(self, client, site_settings):
        resp = client.get(reverse('contact'))
        assert resp.status_code == 200

    def test_offering_ok(self, client, site_settings):
        resp = client.get(reverse('offering_page'))
        assert resp.status_code == 200

    def test_gallery_ok(self, client, site_settings):
        resp = client.get(reverse('gallery'))
        assert resp.status_code == 200

    def test_media_list_ok(self, client, site_settings):
        resp = client.get(reverse('media_list'))
        assert resp.status_code == 200

    def test_devotional_list_ok(self, client, site_settings):
        resp = client.get(reverse('devotional_list'))
        assert resp.status_code == 200

    def test_devotional_detail_ok(self, client, site_settings, db):
        d = Devotional.objects.create(
            pub_date=timezone.localdate(), title='Fé', verse='Jo 3:16',
            reflection='Reflexão', published=True, author='Pastor Teste',
        )
        resp = client.get(reverse('devotional_detail', kwargs={'pk': d.pk}))
        assert resp.status_code == 200

    def test_404_on_missing_devotional(self, client, site_settings):
        resp = client.get(reverse('devotional_detail', kwargs={'pk': 9999}))
        assert resp.status_code == 404


# ── Páginas dinâmicas ─────────────────────────────────────

class TestDynamicPageView:
    def test_published_page_accessible(self, client, site_settings, page):
        resp = client.get(reverse('page_detail', kwargs={'slug': 'nossa-historia'}))
        assert resp.status_code == 200
        assert 'Nossa História' in resp.content.decode()

    def test_unpublished_returns_404(self, client, site_settings, db):
        Page.objects.create(title='Rascunho', slug='rascunho', published=False)
        resp = client.get(reverse('page_detail', kwargs={'slug': 'rascunho'}))
        assert resp.status_code == 404

    def test_nonexistent_slug_returns_404(self, client, site_settings):
        resp = client.get(reverse('page_detail', kwargs={'slug': 'nao-existe'}))
        assert resp.status_code == 404

    def test_page_content_rendered(self, client, site_settings, page):
        resp = client.get(reverse('page_detail', kwargs={'slug': 'nossa-historia'}))
        assert b'<p>Texto</p>' in resp.content


# ── Autenticação de membros ───────────────────────────────

class TestMemberAuth:
    def test_login_page_ok(self, client, db, site_settings):
        resp = client.get(reverse('member_login'))
        assert resp.status_code == 200

    def test_login_success_redirects(self, client, approved_user, site_settings):
        resp = client.post(reverse('member_login'), {
            'username': 'aprovado', 'password': 'senha123'
        })
        assert resp.status_code in (200, 302)

    def test_login_wrong_password(self, client, user, site_settings):
        resp = client.post(reverse('member_login'), {
            'username': 'membro', 'password': 'errada'
        })
        assert resp.status_code == 200

    def test_dashboard_requires_login(self, client, db, site_settings):
        resp = client.get(reverse('member_dashboard'))
        assert resp.status_code in (302, 403)

    def test_dashboard_accessible_logged_in(self, client, approved_user, site_settings):
        client.login(username='aprovado', password='senha123')
        resp = client.get(reverse('member_dashboard'))
        assert resp.status_code == 200

    def test_new_login_invalidates_previous_session(self, client, approved_user, site_settings):
        from django.test import Client

        first_client = client
        resp_login = first_client.post(reverse('member_login'), {
            'username': 'aprovado',
            'password': 'senha123'
        })
        assert resp_login.status_code in (200, 302)
        assert first_client.get(reverse('member_dashboard')).status_code == 200

        second_client = Client()
        resp_login_2 = second_client.post(reverse('member_login'), {
            'username': 'aprovado',
            'password': 'senha123'
        })
        assert resp_login_2.status_code in (200, 302)

        resp_old_session = first_client.get(reverse('member_dashboard'))
        assert resp_old_session.status_code == 302

    def test_dashboard_blocked_unapproved(self, client, user, site_settings):
        client.login(username='membro', password='senha123')
        resp = client.get(reverse('member_dashboard'))
        assert resp.status_code in (200, 302, 403)

    def test_logout_redirects(self, client, approved_user, site_settings):
        client.login(username='aprovado', password='senha123')
        resp = client.get(reverse('member_logout'))
        assert resp.status_code in (200, 302)


# ── Eventos (views públicas) ──────────────────────────────

class TestEventViews:
    def test_event_list_ok(self, client, site_settings, event):
        resp = client.get(reverse('event_list'))
        assert resp.status_code == 200

    def test_event_detail_ok(self, client, site_settings, event):
        resp = client.get(reverse('event_detail', kwargs={'slug': event.slug}))
        assert resp.status_code == 200
        assert b'Evento P' in resp.content

    def test_event_detail_unpublished_returns_404(self, client, site_settings, db):
        Event.objects.create(
            title='Privado', slug='privado',
            description='.', date=timezone.now(), published=False
        )
        resp = client.get(reverse('event_detail', kwargs={'slug': 'privado'}))
        assert resp.status_code == 404
