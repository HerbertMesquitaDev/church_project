from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import EbdClass, EbdTrimester, EbdLesson, Quiz, Question, Choice, QuizAttempt, LessonCertificate


# ── Public preview ────────────────────────────────────────
def ebd_home(request):
    classes = EbdClass.objects.filter(active=True).prefetch_related(
        'trimesters__lessons'
    )
    return render(request, 'ebd/home.html', {'classes': classes})


def ebd_lesson_preview(request, pk):
    """Prévia pública — mostra título, resumo, escritura. Conteúdo exige login."""
    lesson = get_object_or_404(EbdLesson, pk=pk, published=True)
    if request.user.is_authenticated:
        return redirect('ebd_lesson_detail', pk=pk)
    return render(request, 'ebd/lesson_preview.html', {'lesson': lesson})


# ── Members area ──────────────────────────────────────────
@login_required
def ebd_lesson_detail(request, pk):
    lesson   = get_object_or_404(EbdLesson, pk=pk, published=True)
    has_quiz = hasattr(lesson, 'quiz')
    certificate = None
    last_attempt = None

    if has_quiz:
        certificate = LessonCertificate.objects.filter(
            user=request.user, lesson=lesson
        ).first()
        last_attempt = QuizAttempt.objects.filter(
            quiz=lesson.quiz, user=request.user
        ).first()

    return render(request, 'ebd/lesson_detail.html', {
        'lesson':       lesson,
        'has_quiz':     has_quiz,
        'certificate':  certificate,
        'last_attempt': last_attempt,
    })


@login_required
def ebd_quiz(request, lesson_pk):
    lesson = get_object_or_404(EbdLesson, pk=lesson_pk, published=True)
    quiz   = get_object_or_404(Quiz, lesson=lesson)

    # Check max attempts
    attempt_count = QuizAttempt.objects.filter(quiz=quiz, user=request.user).count()
    if quiz.max_attempts > 0 and attempt_count >= quiz.max_attempts:
        messages.warning(request, f'Você atingiu o limite de {quiz.max_attempts} tentativa(s).')
        return redirect('ebd_lesson_detail', pk=lesson_pk)

    # Check already certified
    if LessonCertificate.objects.filter(user=request.user, lesson=lesson).exists():
        messages.info(request, 'Você já possui certificado para esta lição!')
        return redirect('ebd_lesson_detail', pk=lesson_pk)

    questions = quiz.questions.prefetch_related('choices').all()

    if request.method == 'POST':
        answers  = {}
        correct  = 0
        total    = questions.count()

        for q in questions:
            selected_id = request.POST.get(f'q_{q.pk}')
            answers[str(q.pk)] = selected_id
            if selected_id:
                try:
                    choice = q.choices.get(pk=int(selected_id))
                    if choice.is_correct:
                        correct += 1
                except Choice.DoesNotExist:
                    pass

        score  = int((correct / total) * 100) if total else 0
        passed = score >= quiz.passing_score

        attempt = QuizAttempt.objects.create(
            quiz=quiz, user=request.user,
            score=score, passed=passed, answers=answers
        )

        if passed:
            LessonCertificate.objects.get_or_create(
                user=request.user, lesson=lesson,
                defaults={'attempt': attempt}
            )
            messages.success(request, f'Parabéns! Você foi aprovado com {score}%! Certificado emitido.')
        else:
            remaining = (quiz.max_attempts - attempt_count - 1) if quiz.max_attempts > 0 else '∞'
            messages.warning(request, f'Você obteve {score}%. Mínimo: {quiz.passing_score}%. Tentativas restantes: {remaining}.')

        return redirect('ebd_quiz_result', attempt_pk=attempt.pk)

    return render(request, 'ebd/quiz.html', {
        'lesson':    lesson,
        'quiz':      quiz,
        'questions': questions,
        'attempt_count': attempt_count,
    })


@login_required
def ebd_quiz_result(request, attempt_pk):
    attempt   = get_object_or_404(QuizAttempt, pk=attempt_pk, user=request.user)
    quiz      = attempt.quiz
    lesson    = quiz.lesson
    questions = quiz.questions.prefetch_related('choices').all()
    certificate = LessonCertificate.objects.filter(
        user=request.user, lesson=lesson
    ).first()

    # Build result list (templates can't do dict[variable])
    results = []
    for q in questions:
        selected_id  = attempt.answers.get(str(q.pk))
        correct_ch   = q.choices.filter(is_correct=True).first()
        sel_int      = int(selected_id) if selected_id else None
        is_correct   = bool(sel_int and correct_ch and sel_int == correct_ch.pk)
        choices_data = []
        for ch in q.choices.all():
            choices_data.append({
                'pk':         ch.pk,
                'text':       ch.text,
                'is_correct': ch.is_correct,
                'selected':   ch.pk == sel_int,
                'wrong_pick': ch.pk == sel_int and not ch.is_correct,
            })
        results.append({
            'question':   q,
            'is_correct': is_correct,
            'choices':    choices_data,
            'explanation': q.explanation,
        })

    return render(request, 'ebd/quiz_result.html', {
        'attempt':     attempt,
        'quiz':        quiz,
        'lesson':      lesson,
        'results':     results,
        'certificate': certificate,
    })


@login_required
def ebd_my_progress(request):
    certificates = LessonCertificate.objects.filter(
        user=request.user
    ).select_related('lesson__trimester__ebd_class', 'attempt')
    attempts = QuizAttempt.objects.filter(
        user=request.user
    ).select_related('quiz__lesson').order_by('-created_at')[:20]

    return render(request, 'ebd/my_progress.html', {
        'certificates': certificates,
        'attempts':     attempts,
    })
