"""Testes de models: criação, __str__, propriedades e validações."""
import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError

from core.models import SiteSettings, Devotional, Page, Ministry, Testimony
from events.models import Event, Category as EventCategory, EventRegistration
from members.models import MemberProfile, Notice, ExclusiveContent
from courses.models import Course, Module, Lesson, Enrollment, LessonProgress
from ebd.models import EbdClass, EbdTrimester, EbdLesson
from cells.models import Cell, CellMembership


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(
        username='membro', password='senha123', email='membro@teste.com',
        first_name='João', last_name='Silva'
    )


@pytest.fixture
def staff_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username='pastor', password='senha123', is_staff=True
    )


@pytest.fixture
def site_settings(db):
    return SiteSettings.objects.create(church_name='Igreja Teste', tagline='Fé e Amor')


@pytest.fixture
def event_category(db):
    return EventCategory.objects.create(name='Culto', color='#8B6914')


@pytest.fixture
def event(db, event_category):
    return Event.objects.create(
        title='Culto de Domingo',
        slug='culto-domingo',
        category=event_category,
        description='Culto dominical',
        date=timezone.now() + timezone.timedelta(days=7),
        published=True,
    )


@pytest.fixture
def past_event(db, event_category):
    return Event.objects.create(
        title='Culto Passado',
        slug='culto-passado',
        description='Culto já realizado',
        date=timezone.now() - timezone.timedelta(days=7),
        published=True,
    )


@pytest.fixture
def devotional(db):
    return Devotional.objects.create(
        pub_date=timezone.localdate(),
        title='Deus é fiel',
        verse='Hebreus 11:1',
        reflection='Reflexão do dia...',
        published=True,
        author='Pastor Teste',
    )


@pytest.fixture
def page(db):
    return Page.objects.create(
        title='Nossa História',
        slug='nossa-historia',
        content='<p>Conteúdo da página.</p>',
        published=True,
    )


@pytest.fixture
def ebd_class(db):
    return EbdClass.objects.create(name='Adultos', order=1, active=True)


@pytest.fixture
def ebd_trimester(db, ebd_class):
    return EbdTrimester.objects.create(
        ebd_class=ebd_class, year=2025, quarter=1, title='A Fé Cristã'
    )


@pytest.fixture
def ebd_lesson(db, ebd_trimester):
    return EbdLesson.objects.create(
        trimester=ebd_trimester, number=1, title='O que é a fé',
        body='Corpo da lição', published=True,
    )


@pytest.fixture
def course(db, staff_user):
    return Course.objects.create(
        title='Curso de Liderança',
        description='Formação de líderes',
        instructor=staff_user,
        published=True,
    )


@pytest.fixture
def module(db, course):
    return Module.objects.create(course=course, title='Módulo 1 — Fundamentos', order=1)


@pytest.fixture
def lesson(db, module):
    return Lesson.objects.create(
        module=module, title='Aula 1 — Visão', order=1, published=True
    )


@pytest.fixture
def cell(db):
    return Cell.objects.create(name='Célula Centro', cell_type='region', active=True)


@pytest.fixture
def member_profile(db, user):
    return MemberProfile.objects.create(user=user, approved=True)


# ── SiteSettings ──────────────────────────────────────────

class TestSiteSettings:
    def test_str(self, site_settings):
        assert 'Configurações' in str(site_settings)

    def test_get_settings_returns_instance(self, site_settings, db):
        result = SiteSettings.get_settings()
        assert result is not None

    def test_only_one_allowed(self, site_settings, db):
        assert SiteSettings.objects.count() == 1


# ── Devotional ────────────────────────────────────────────

class TestDevotional:
    def test_str(self, devotional):
        assert 'Deus é fiel' in str(devotional)

    def test_published_filter(self, devotional, db):
        assert Devotional.objects.filter(published=True).count() == 1

    def test_unpublished_not_returned(self, devotional, db):
        devotional.published = False
        devotional.save()
        assert Devotional.objects.filter(published=True).count() == 0


# ── Page ──────────────────────────────────────────────────

class TestPage:
    def test_str(self, page):
        assert page.title in str(page)

    def test_get_absolute_url(self, page):
        url = page.get_absolute_url()
        assert '/p/nossa-historia/' in url

    def test_published_only(self, page, db):
        Page.objects.create(title='Rascunho', slug='rascunho', published=False)
        assert Page.objects.filter(published=True).count() == 1

    def test_nav_pages(self, db):
        Page.objects.create(title='No Menu', slug='no-menu', published=True, show_in_nav=True)
        Page.objects.create(title='Fora do Menu', slug='fora-menu', published=True, show_in_nav=False)
        assert Page.objects.filter(published=True, show_in_nav=True).count() == 1


# ── Event ─────────────────────────────────────────────────

class TestEvent:
    def test_str(self, event):
        assert 'Culto de Domingo' in str(event)

    def test_is_upcoming(self, event):
        assert event.is_upcoming is True

    def test_is_past(self, past_event):
        assert past_event.is_past is True

    def test_get_absolute_url(self, event):
        assert '/eventos/' in event.get_absolute_url() or 'culto-domingo' in event.get_absolute_url()

    def test_spots_available_unlimited(self, event):
        assert event.spots_available is None

    def test_spots_available_with_limit(self, event, user):
        event.max_spots = 10
        event.requires_registration = True
        event.save()
        EventRegistration.objects.create(event=event, user=user, status='confirmed')
        assert event.spots_available == 9

    def test_is_full(self, event, user):
        event.max_spots = 1
        event.save()
        EventRegistration.objects.create(event=event, user=user, status='confirmed')
        assert event.is_full is True

    def test_registration_closed_for_past_event(self, past_event):
        past_event.requires_registration = True
        past_event.save()
        assert past_event.registration_open is False


# ── EBD ──────────────────────────────────────────────────

class TestEbd:
    def test_class_str(self, ebd_class):
        assert 'Adultos' in str(ebd_class)

    def test_trimester_str(self, ebd_trimester):
        s = str(ebd_trimester)
        assert 'Adultos' in s and '2025' in s

    def test_lesson_str(self, ebd_lesson):
        assert 'O que é a fé' in str(ebd_lesson)

    def test_lesson_unique_number_per_trimester(self, ebd_trimester, db):
        EbdLesson.objects.create(trimester=ebd_trimester, number=2, title='Lição 2')
        with pytest.raises(Exception):
            EbdLesson.objects.create(trimester=ebd_trimester, number=2, title='Duplicada')

    def test_trimester_unique_per_class_year_quarter(self, ebd_trimester, db):
        with pytest.raises(Exception):
            EbdTrimester.objects.create(
                ebd_class=ebd_trimester.ebd_class, year=2025, quarter=1, title='Duplicado'
            )


# ── Courses ───────────────────────────────────────────────

class TestCourse:
    def test_slug_auto_generated(self, course):
        assert course.slug == 'curso-de-lideranca'

    def test_lesson_count(self, course, lesson):
        assert course.lesson_count == 1

    def test_enrolled_count(self, course, user):
        Enrollment.objects.create(course=course, user=user, active=True)
        assert course.enrolled_count == 1

    def test_progress_percent_zero(self, course, user, lesson):
        enrollment = Enrollment.objects.create(course=course, user=user)
        assert enrollment.progress_percent == 0

    def test_progress_percent_complete(self, course, user, lesson):
        enrollment = Enrollment.objects.create(course=course, user=user)
        LessonProgress.objects.create(
            user=user, lesson=lesson, completed=True,
            completed_at=timezone.now()
        )
        assert enrollment.progress_percent == 100

    def test_module_str(self, module):
        assert 'Módulo 1' in str(module)

    def test_lesson_embed_youtube(self, lesson):
        lesson.video_url = 'https://www.youtube.com/watch?v=abc123'
        assert 'youtube.com/embed/abc123' in lesson.get_embed_url()

    def test_lesson_embed_youtu_be(self, lesson):
        lesson.video_url = 'https://youtu.be/xyz789'
        assert 'youtube.com/embed/xyz789' in lesson.get_embed_url()

    def test_lesson_embed_vimeo(self, lesson):
        lesson.video_url = 'https://vimeo.com/12345678'
        assert 'player.vimeo.com/video/12345678' in lesson.get_embed_url()


# ── Cell ──────────────────────────────────────────────────

class TestCell:
    def test_str(self, cell):
        assert 'Célula Centro' in str(cell)

    def test_member_count_zero(self, cell):
        assert cell.member_count() == 0

    def test_member_count_approved(self, cell, user):
        CellMembership.objects.create(cell=cell, user=user, status='approved')
        assert cell.member_count() == 1

    def test_member_count_excludes_pending(self, cell, user):
        CellMembership.objects.create(cell=cell, user=user, status='pending')
        assert cell.member_count() == 0

    def test_unique_membership(self, cell, user):
        CellMembership.objects.create(cell=cell, user=user, status='approved')
        with pytest.raises(Exception):
            CellMembership.objects.create(cell=cell, user=user, status='approved')


# ── Notice ────────────────────────────────────────────────

class TestNotice:
    def test_str(self, db):
        notice = Notice.objects.create(title='Aviso Importante', body='Texto do aviso.')
        assert 'Aviso Importante' in str(notice)

    def test_expired_not_shown(self, db):
        Notice.objects.create(
            title='Expirado', body='.',
            published=True,
            expires_at=timezone.now() - timezone.timedelta(hours=1)
        )
        active = Notice.objects.filter(
            published=True, expires_at__gt=timezone.now()
        )
        assert active.count() == 0


# ── MemberProfile ─────────────────────────────────────────

class TestMemberProfile:
    def test_str(self, member_profile):
        assert 'João' in str(member_profile) or 'membro' in str(member_profile)

    def test_approved_default(self, db, django_user_model):
        u = django_user_model.objects.create_user(username='novo', password='123')
        profile = MemberProfile.objects.create(user=u)
        assert profile.approved is False
