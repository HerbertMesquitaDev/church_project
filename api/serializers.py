from rest_framework import serializers
from django.contrib.auth.models import User

from events.models import Event, EventRegistration
from core.models import Devotional, MediaItem, MediaCategory, Page
from cells.models import Cell, CellPost, CellMembership
from courses.models import Course, Module, Lesson, Enrollment, LessonProgress
from members.models import ExclusiveContent, Notice, MemberProfile, PrayerRequest, Testimony
from ebd.models import EbdClass, EbdTrimester, EbdLesson


# ── Auth ──────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ('id', 'username', 'full_name', 'email')

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


# ── Eventos ───────────────────────────────────────────────

class EventListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', default=None)
    image_url     = serializers.SerializerMethodField()
    url           = serializers.CharField(source='get_absolute_url')

    class Meta:
        model  = Event
        fields = (
            'id', 'title', 'slug', 'category_name', 'short_description',
            'date', 'end_date', 'location', 'image_url', 'recurrence',
            'featured', 'requires_registration', 'spots_available', 'is_full',
            'registration_open', 'url',
        )

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class EventDetailSerializer(EventListSerializer):
    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + (
            'description', 'address', 'max_spots', 'spots_taken',
            'waitlist_count', 'registration_deadline', 'registration_link',
        )


class EventRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EventRegistration
        fields = ('id', 'event', 'status', 'notes', 'created_at')
        read_only_fields = ('status', 'created_at')


# ── Devocionais ───────────────────────────────────────────

class DevotionalSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Devotional
        fields = (
            'id', 'pub_date', 'title', 'verse', 'verse_text',
            'reflection', 'prayer', 'author',
        )


# ── Mídiateca ─────────────────────────────────────────────

class MediaCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = MediaCategory
        fields = ('id', 'name', 'section', 'icon')


class MediaItemSerializer(serializers.ModelSerializer):
    category      = MediaCategorySerializer(read_only=True)
    thumbnail_url = serializers.SerializerMethodField()
    audio_url     = serializers.SerializerMethodField()
    pdf_url       = serializers.SerializerMethodField()
    embed_url     = serializers.CharField(source='get_embed_url')

    class Meta:
        model  = MediaItem
        fields = (
            'id', 'title', 'category', 'media_type', 'description',
            'speaker', 'pub_date', 'video_url', 'embed_url',
            'audio_url', 'pdf_url', 'thumbnail_url', 'featured',
        )

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

    def get_audio_url(self, obj):
        request = self.context.get('request')
        if obj.audio_file and request:
            return request.build_absolute_uri(obj.audio_file.url)
        return None

    def get_pdf_url(self, obj):
        request = self.context.get('request')
        if obj.pdf_file and request:
            return request.build_absolute_uri(obj.pdf_file.url)
        return None


# ── Células ───────────────────────────────────────────────

class CellSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    cover_url    = serializers.SerializerMethodField()

    class Meta:
        model  = Cell
        fields = (
            'id', 'name', 'cell_type', 'description', 'region',
            'meeting_day', 'meeting_place', 'cover_url', 'member_count',
        )

    def get_member_count(self, obj):
        return obj.member_count()

    def get_cover_url(self, obj):
        request = self.context.get('request')
        if obj.cover and request:
            return request.build_absolute_uri(obj.cover.url)
        return None


# ── Páginas dinâmicas ─────────────────────────────────────

class PageSerializer(serializers.ModelSerializer):
    cover_url = serializers.SerializerMethodField()
    url       = serializers.CharField(source='get_absolute_url')

    class Meta:
        model  = Page
        fields = ('id', 'title', 'slug', 'cover_url', 'content',
                  'meta_description', 'url', 'updated_at')

    def get_cover_url(self, obj):
        request = self.context.get('request')
        if obj.cover and request:
            return request.build_absolute_uri(obj.cover.url)
        return None


# ── EBD ──────────────────────────────────────────────────

class EbdLessonListSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EbdLesson
        fields = ('id', 'number', 'title', 'scripture', 'summary', 'order')


class EbdTrimesterSerializer(serializers.ModelSerializer):
    lessons = EbdLessonListSerializer(many=True, read_only=True)

    class Meta:
        model  = EbdTrimester
        fields = ('id', 'year', 'quarter', 'get_quarter_display', 'title',
                  'description', 'lessons')

    get_quarter_display = serializers.SerializerMethodField()

    def get_get_quarter_display(self, obj):
        return obj.get_quarter_display()


class EbdClassSerializer(serializers.ModelSerializer):
    trimesters = EbdTrimesterSerializer(many=True, read_only=True)

    class Meta:
        model  = EbdClass
        fields = ('id', 'name', 'description', 'order', 'trimesters')


# ── Cursos ────────────────────────────────────────────────

class LessonSerializer(serializers.ModelSerializer):
    embed_url   = serializers.CharField(source='get_embed_url')
    audio_url   = serializers.SerializerMethodField()
    pdf_url     = serializers.SerializerMethodField()

    class Meta:
        model  = Lesson
        fields = ('id', 'title', 'description', 'body', 'video_url',
                  'embed_url', 'audio_url', 'pdf_url', 'duration', 'order')

    def get_audio_url(self, obj):
        request = self.context.get('request')
        if obj.audio_file and request:
            return request.build_absolute_uri(obj.audio_file.url)
        return None

    def get_pdf_url(self, obj):
        request = self.context.get('request')
        if obj.pdf_file and request:
            return request.build_absolute_uri(obj.pdf_file.url)
        return None


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model  = Module
        fields = ('id', 'title', 'description', 'order', 'lessons')


class CourseListSerializer(serializers.ModelSerializer):
    category_name    = serializers.CharField(source='category.name', default=None)
    instructor_name  = serializers.SerializerMethodField()
    cover_url        = serializers.SerializerMethodField()

    class Meta:
        model  = Course
        fields = (
            'id', 'title', 'slug', 'category_name', 'description',
            'cover_url', 'instructor_name', 'level', 'workload',
            'lesson_count', 'enrolled_count',
        )

    def get_instructor_name(self, obj):
        if obj.instructor:
            return obj.instructor.get_full_name() or obj.instructor.username
        return None

    def get_cover_url(self, obj):
        request = self.context.get('request')
        if obj.cover and request:
            return request.build_absolute_uri(obj.cover.url)
        return None


class CourseDetailSerializer(CourseListSerializer):
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ('modules',)


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title    = serializers.CharField(source='course.title', read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Enrollment
        fields = ('id', 'course', 'course_title', 'enrolled_at',
                  'active', 'progress_percent')
        read_only_fields = ('enrolled_at',)


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LessonProgress
        fields = ('id', 'lesson', 'completed', 'completed_at')


# ── Conteúdo exclusivo ────────────────────────────────────

class ExclusiveContentSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', default=None)
    thumbnail_url = serializers.SerializerMethodField()
    file_url      = serializers.SerializerMethodField()

    class Meta:
        model  = ExclusiveContent
        fields = (
            'id', 'title', 'category_name', 'content_type', 'body',
            'video_url', 'external_link', 'thumbnail_url', 'file_url',
            'featured', 'created_at',
        )

    def get_thumbnail_url(self, obj):
        request = self.context.get('request')
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return None

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


# ── Avisos ────────────────────────────────────────────────

class NoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Notice
        fields = ('id', 'title', 'body', 'priority', 'created_at', 'expires_at')


# ── Perfil ────────────────────────────────────────────────

class MemberProfileSerializer(serializers.ModelSerializer):
    username   = serializers.CharField(source='user.username', read_only=True)
    email      = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name  = serializers.CharField(source='user.last_name')
    photo_url  = serializers.SerializerMethodField()

    class Meta:
        model  = MemberProfile
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'photo_url', 'phone', 'birth_date', 'bio',
            'baptized', 'member_since', 'role',
        )
        read_only_fields = ('role', 'member_since', 'baptized')

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and request:
            return request.build_absolute_uri(obj.photo.url)
        return None

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        instance.user.save()
        return super().update(instance, validated_data)


# ── Pedidos de Oração ─────────────────────────────────────

class PrayerRequestSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model  = PrayerRequest
        fields = (
            'id', 'title', 'description', 'visibility',
            'status', 'author_name', 'created_at', 'updated_at',
        )
        read_only_fields = ('status', 'created_at', 'updated_at')

    def get_author_name(self, obj):
        return obj.profile.user.get_full_name() or obj.profile.user.username

    def create(self, validated_data):
        request = self.context['request']
        profile = request.user.profile
        return PrayerRequest.objects.create(profile=profile, **validated_data)


# ── Testemunhos ───────────────────────────────────────────

class TestimonySerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model  = Testimony
        fields = ('id', 'text', 'status', 'author_name', 'created_at')
        read_only_fields = ('status', 'created_at')

    def get_author_name(self, obj):
        return obj.profile.user.get_full_name() or obj.profile.user.username

    def create(self, validated_data):
        request = self.context['request']
        profile = request.user.profile
        return Testimony.objects.create(profile=profile, **validated_data)


# ── Posts de Célula ───────────────────────────────────────

class CellPostSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    file_url    = serializers.SerializerMethodField()

    class Meta:
        model  = CellPost
        fields = (
            'id', 'post_type', 'content', 'file_url',
            'pinned', 'author_name', 'created_at',
        )
        read_only_fields = ('pinned', 'created_at')

    def get_author_name(self, obj):
        return obj.author.get_full_name() or obj.author.username

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def create(self, validated_data):
        request  = self.context['request']
        cell     = self.context['cell']
        return CellPost.objects.create(author=request.user, cell=cell, **validated_data)


# ── Detalhe da Célula ─────────────────────────────────────

class CellDetailSerializer(CellSerializer):
    posts         = serializers.SerializerMethodField()
    member_status = serializers.SerializerMethodField()

    class Meta(CellSerializer.Meta):
        fields = CellSerializer.Meta.fields + ('posts', 'member_status')

    def get_posts(self, obj):
        request = self.context.get('request')
        posts   = obj.posts.order_by('-pinned', '-created_at')[:20]
        return CellPostSerializer(posts, many=True, context={'request': request}).data

    def get_member_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        membership = CellMembership.objects.filter(cell=obj, user=request.user).first()
        return membership.status if membership else None
