from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LessonProgress, Enrollment, PerfectStudentSeal


@receiver(post_save, sender=LessonProgress)
def check_perfect_attendance(sender, instance, **kwargs):
    if not instance.completed:
        return

    course = instance.lesson.module.course

    try:
        enrollment = Enrollment.objects.get(
            user=instance.user, course=course, active=True
        )
    except Enrollment.DoesNotExist:
        return

    if enrollment.progress_percent == 100:
        PerfectStudentSeal.objects.get_or_create(enrollment=enrollment)
