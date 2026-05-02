from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from events.models import Event, EventRegistration
from core.models import Devotional, MediaItem, MediaCategory, Page
from cells.models import Cell, CellMembership, CellPost
from courses.models import Course, Enrollment, LessonProgress, Lesson
from members.models import ExclusiveContent, Notice, PrayerRequest, Testimony
from ebd.models import EbdClass

from .serializers import (
    EventListSerializer, EventDetailSerializer, EventRegistrationSerializer,
    DevotionalSerializer, MediaItemSerializer, MediaCategorySerializer,
    CellSerializer, CellDetailSerializer, CellPostSerializer, PageSerializer, EbdClassSerializer,
    CourseListSerializer, CourseDetailSerializer, EnrollmentSerializer,
    LessonProgressSerializer,
    ExclusiveContentSerializer, NoticeSerializer,
    MemberProfileSerializer, PrayerRequestSerializer, TestimonySerializer,
)


def get_igreja(request):
    return getattr(request, 'igreja', None)


# ── Auth ──────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    from django.contrib.auth import authenticate
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if not user:
        return Response({'detail': 'Credenciais inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({
        'token': token.key,
        'user_id': user.pk,
        'username': user.username,
        'full_name': user.get_full_name(),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    request.user.auth_token.delete()
    return Response({'detail': 'Logout realizado com sucesso.'})


# ── Eventos ───────────────────────────────────────────────

class EventListView(generics.ListAPIView):
    serializer_class   = EventListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = Event.objects.filter(published=True).order_by('date')
        if igreja:
            qs = qs.filter(igreja=igreja)
        if self.request.query_params.get('upcoming'):
            qs = qs.filter(date__gte=timezone.now())
        if self.request.query_params.get('destaque'):
            qs = qs.filter(featured=True)
        return qs


class EventDetailView(generics.RetrieveAPIView):
    serializer_class   = EventDetailSerializer
    permission_classes = [AllowAny]
    lookup_field       = 'slug'

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = Event.objects.filter(published=True)
        if igreja:
            qs = qs.filter(igreja=igreja)
        return qs


class EventRegistrationView(generics.CreateAPIView):
    serializer_class   = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        event = serializer.validated_data['event']
        s = 'waitlist' if event.is_full else 'confirmed'
        serializer.save(user=self.request.user, status=s)


# ── Devocionais ───────────────────────────────────────────

class DevotionalTodayView(generics.RetrieveAPIView):
    serializer_class   = DevotionalSerializer
    permission_classes = [AllowAny]

    def get_object(self):
        today = timezone.localdate()
        return generics.get_object_or_404(Devotional, published=True, pub_date=today)


class DevotionalListView(generics.ListAPIView):
    serializer_class   = DevotionalSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Devotional.objects.filter(published=True).order_by('-pub_date')


# ── Mídiateca ─────────────────────────────────────────────

class MediaCategoryListView(generics.ListAPIView):
    serializer_class   = MediaCategorySerializer
    permission_classes = [AllowAny]
    pagination_class   = None

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = MediaCategory.objects.all()
        if igreja:
            qs = qs.filter(igreja=igreja)
        return qs


class MediaItemListView(generics.ListAPIView):
    serializer_class   = MediaItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = MediaItem.objects.filter(published=True, visibility='public').order_by('-pub_date')
        if igreja:
            qs = qs.filter(igreja=igreja)
        if tipo := self.request.query_params.get('tipo'):
            qs = qs.filter(media_type=tipo)
        if cat := self.request.query_params.get('categoria'):
            qs = qs.filter(category_id=cat)
        return qs


class MediaItemDetailView(generics.RetrieveAPIView):
    serializer_class   = MediaItemSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return MediaItem.objects.filter(published=True, visibility='public')


# ── Células ───────────────────────────────────────────────

class CellListView(generics.ListAPIView):
    serializer_class   = CellSerializer
    permission_classes = [AllowAny]
    pagination_class   = None

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = Cell.objects.filter(active=True)
        if igreja:
            qs = qs.filter(igreja=igreja)
        return qs


# ── Páginas dinâmicas ─────────────────────────────────────

class PageListView(generics.ListAPIView):
    serializer_class   = PageSerializer
    permission_classes = [AllowAny]
    pagination_class   = None

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = Page.objects.filter(published=True)
        if igreja:
            qs = qs.filter(igreja=igreja)
        return qs


class PageDetailView(generics.RetrieveAPIView):
    serializer_class   = PageSerializer
    permission_classes = [AllowAny]
    lookup_field       = 'slug'

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = Page.objects.filter(published=True)
        if igreja:
            qs = qs.filter(igreja=igreja)
        return qs


# ── EBD ──────────────────────────────────────────────────

class EbdClassListView(generics.ListAPIView):
    serializer_class   = EbdClassSerializer
    permission_classes = [AllowAny]
    pagination_class   = None

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = EbdClass.objects.filter(active=True).prefetch_related('trimesters__lessons')
        if igreja:
            qs = qs.filter(igreja=igreja)
        return qs


# ── Cursos ────────────────────────────────────────────────

class CourseListView(generics.ListAPIView):
    serializer_class   = CourseListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = Course.objects.filter(published=True)
        if igreja:
            qs = qs.filter(igreja=igreja)
        return qs


class CourseDetailView(generics.RetrieveAPIView):
    serializer_class   = CourseDetailSerializer
    permission_classes = [AllowAny]
    lookup_field       = 'slug'

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = Course.objects.filter(published=True).prefetch_related('modules__lessons')
        if igreja:
            qs = qs.filter(igreja=igreja)
        return qs


class MyEnrollmentsView(generics.ListAPIView):
    serializer_class   = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user, active=True)


class EnrollView(generics.CreateAPIView):
    serializer_class   = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        course_id  = request.data.get('course')
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user, course_id=course_id,
            defaults={'active': True}
        )
        if not created and not enrollment.active:
            enrollment.active = True
            enrollment.save()
        serializer = self.get_serializer(enrollment)
        code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=code)


class LessonProgressView(generics.UpdateAPIView):
    serializer_class   = LessonProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        lesson = generics.get_object_or_404(Lesson, pk=self.kwargs['lesson_id'])
        obj, _ = LessonProgress.objects.get_or_create(user=self.request.user, lesson=lesson)
        return obj

    def update(self, request, *args, **kwargs):
        obj       = self.get_object()
        completed = request.data.get('completed', True)
        obj.completed = completed
        if completed and not obj.completed_at:
            obj.completed_at = timezone.now()
        obj.save()
        return Response(LessonProgressSerializer(obj).data)


# ── Conteúdo exclusivo ────────────────────────────────────

class ExclusiveContentListView(generics.ListAPIView):
    serializer_class   = ExclusiveContentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs = ExclusiveContent.objects.filter(published=True).order_by('-created_at')
        if igreja:
            qs = qs.filter(igreja=igreja)
        if tipo := self.request.query_params.get('tipo'):
            qs = qs.filter(content_type=tipo)
        return qs


class ExclusiveContentDetailView(generics.RetrieveAPIView):
    serializer_class   = ExclusiveContentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ExclusiveContent.objects.filter(published=True)


# ── Avisos ────────────────────────────────────────────────

class NoticeListView(generics.ListAPIView):
    serializer_class   = NoticeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class   = None

    def get_queryset(self):
        now = timezone.now()
        return Notice.objects.filter(published=True).filter(
            expires_at__isnull=True
        ) | Notice.objects.filter(
            published=True, expires_at__gt=now
        )


# ── Perfil do usuário logado ──────────────────────────────

class MeView(generics.RetrieveUpdateAPIView):
    serializer_class   = MemberProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return generics.get_object_or_404(
            self.request.user.__class__,
            pk=self.request.user.pk
        ).profile


# ── Pedidos de Oração ─────────────────────────────────────

class PrayerRequestListCreateView(generics.ListCreateAPIView):
    serializer_class   = PrayerRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        profile = self.request.user.profile
        return PrayerRequest.objects.filter(profile=profile).order_by('-created_at')


class PrayerRequestUpdateView(generics.UpdateAPIView):
    serializer_class   = PrayerRequestSerializer
    permission_classes = [IsAuthenticated]
    http_method_names  = ['patch']

    def get_queryset(self):
        return PrayerRequest.objects.filter(profile=self.request.user.profile)

    def perform_update(self, serializer):
        allowed = {'status', 'title', 'description', 'visibility'}
        data    = {k: v for k, v in self.request.data.items() if k in allowed}
        serializer.save(**{k: v for k, v in data.items() if k not in serializer.validated_data})


# ── Testemunhos ───────────────────────────────────────────

class TestimonyListView(generics.ListAPIView):
    serializer_class   = TestimonySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs     = Testimony.objects.filter(status='approved').order_by('-created_at')
        if igreja:
            qs = qs.filter(profile__igreja=igreja)
        return qs


class TestimonyCreateView(generics.CreateAPIView):
    serializer_class   = TestimonySerializer
    permission_classes = [IsAuthenticated]


# ── Detalhe da Célula + Posts ─────────────────────────────

class CellDetailView(generics.RetrieveAPIView):
    serializer_class   = CellDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        igreja = get_igreja(self.request)
        qs     = Cell.objects.filter(active=True)
        if igreja:
            qs = qs.filter(igreja=igreja)
        return qs


class CellPostListCreateView(generics.ListCreateAPIView):
    serializer_class   = CellPostSerializer
    permission_classes = [IsAuthenticated]

    def _get_cell(self):
        return generics.get_object_or_404(Cell, pk=self.kwargs['pk'], active=True)

    def get_queryset(self):
        cell = self._get_cell()
        membership = CellMembership.objects.filter(
            cell=cell, user=self.request.user, status='approved'
        ).first()
        if not membership:
            return CellPost.objects.none()
        return cell.posts.order_by('-pinned', '-created_at')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['cell'] = self._get_cell()
        return ctx

    def perform_create(self, serializer):
        cell = self._get_cell()
        membership = CellMembership.objects.filter(
            cell=cell, user=self.request.user, status='approved'
        ).first()
        if not membership:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Você não é membro aprovado desta célula.')
        serializer.save()


class CellJoinView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        cell = generics.get_object_or_404(Cell, pk=kwargs['pk'], active=True)
        membership, created = CellMembership.objects.get_or_create(
            cell=cell, user=request.user,
            defaults={'status': 'pending', 'role': 'member'}
        )
        if not created and membership.status == 'left':
            membership.status = 'pending'
            membership.save()
        return Response(
            {'status': membership.status},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


class CellLeaveView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        cell = generics.get_object_or_404(Cell, pk=kwargs['pk'])
        CellMembership.objects.filter(cell=cell, user=request.user).update(status='left')
        return Response(status=status.HTTP_204_NO_CONTENT)
