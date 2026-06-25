from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.html import strip_tags
from django.core.paginator import Paginator
from django.db.models import Q
from html import unescape

from members.permissions import is_teacher, teacher_or_staff_required
from .models import (Course, Module, Lesson, Enrollment, LessonProgress,
                     LessonComment, LessonQuiz, QuizAttempt, QuizQuestion,
                     QuizChoice, CourseCategory)


# ── Helpers ───────────────────────────────────────────────
def members_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('member_login')
        return view_func(request, *args, **kwargs)
    return wrapper

def staff_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('member_login')
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'Acesso restrito a colaboradores.')
            return redirect('course_list')
        return view_func(request, *args, **kwargs)
    return wrapper

def get_enrollment(user, course):
    if not user.is_authenticated:
        return None
    return Enrollment.objects.filter(user=user, course=course, active=True).first()

def get_progress(user, course):
    """Returns set of completed lesson IDs."""
    if not user.is_authenticated:
        return set()
    return set(
        LessonProgress.objects.filter(
            user=user, lesson__module__course=course, completed=True
        ).values_list('lesson_id', flat=True)
    )


def normalize_rich_text(text):
    """Converts escaped/HTML-rich content into plain display text."""
    if not text:
        return ''
    return strip_tags(unescape(text)).strip()


# ══════════════════════════════════════════════════════════
# ── ALUNO — Listagem e detalhes ───────────────────────────
# ══════════════════════════════════════════════════════════

def course_list(request):
    q        = request.GET.get('q', '').strip()
    cat_id   = request.GET.get('categoria', '')
    level    = request.GET.get('nivel', '')

    qs = Course.objects.filter(published=True).select_related('category', 'instructor')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if cat_id:
        qs = qs.filter(category_id=cat_id)
    if level:
        qs = qs.filter(level=level)

    # Para cada curso, verifica se o usuário está inscrito
    enrolled_ids = set()
    if request.user.is_authenticated:
        enrolled_ids = set(
            Enrollment.objects.filter(user=request.user, active=True)
            .values_list('course_id', flat=True)
        )

    page_obj   = Paginator(qs, 12).get_page(request.GET.get('page'))
    categories = CourseCategory.objects.all()

    for course in page_obj.object_list:
        course.description_plain = normalize_rich_text(course.description)

    return render(request, 'courses/course_list.html', {
        'page_obj':     page_obj,
        'courses':      page_obj,
        'categories':   categories,
        'levels':       Course.LEVEL_CHOICES,
        'enrolled_ids': enrolled_ids,
        'q':            q,
        'cat_id':       cat_id,
        'level':        level,
    })


def course_detail(request, slug):
    course  = get_object_or_404(Course, slug=slug, published=True)
    modules = course.modules.prefetch_related('lessons').all()
    enrollment = get_enrollment(request.user, course)
    progress   = get_progress(request.user, course)
    course_description_plain = normalize_rich_text(course.description)

    # Contar aulas e progresso
    total_lessons = sum(m.lessons.filter(published=True).count() for m in modules)
    done_lessons  = len(progress)  # progress is now a set of completed lesson IDs
    pct = int((done_lessons / total_lessons * 100)) if total_lessons else 0

    return render(request, 'courses/course_detail.html', {
        'course':        course,
        'modules':       modules,
        'enrollment':    enrollment,
        'progress':      progress,
        'completed_ids': progress,  # set of completed lesson IDs
        'total_lessons': total_lessons,
        'done_lessons':  done_lessons,
        'pct':           pct,
        'course_description_plain': course_description_plain,
    })


@members_only
def course_enroll(request, slug):
    course = get_object_or_404(Course, slug=slug, published=True)
    enrollment, created = Enrollment.objects.get_or_create(
        user=request.user, course=course,
        defaults={'active': True}
    )
    if not created and not enrollment.active:
        enrollment.active = True
        enrollment.save()
    messages.success(request, f'Inscrição confirmada em "{course.title}"!')
    return redirect('course_detail', slug=slug)


@members_only
def course_unenroll(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == 'POST':
        Enrollment.objects.filter(user=request.user, course=course).update(active=False)
        messages.success(request, f'Você cancelou a inscrição em "{course.title}".')
        return redirect('my_courses')
    return render(request, 'courses/course_unenroll_confirm.html', {'course': course})


@members_only
def my_courses(request):
    enrollments = (
        Enrollment.objects
        .filter(user=request.user, active=True)
        .select_related('course__category', 'course__instructor')
        .order_by('-enrolled_at')
    )
    # Calcula progresso para cada inscrição
    data = []
    for enr in enrollments:
        data.append({
            'enrollment': enr,
            'pct': enr.progress_percent,
        })
    return render(request, 'courses/my_courses.html', {'data': data})


@members_only
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, published=True)
    course = lesson.module.course

    # Verifica inscrição
    enrollment = get_enrollment(request.user, course)
    if not enrollment and not (request.user.is_staff or request.user.is_superuser):
        messages.warning(request, 'Inscreva-se no curso para acessar as aulas.')
        return redirect('course_detail', slug=course.slug)

    # Progresso desta aula
    progress, _ = LessonProgress.objects.get_or_create(
        user=request.user, lesson=lesson
    )

    # Aulas anterior e próxima
    siblings = list(Lesson.objects.filter(
        module__course=course, published=True
    ).order_by('module__order', 'order'))
    idx = next((i for i, l in enumerate(siblings) if l.pk == lesson.pk), None)
    prev_lesson = siblings[idx - 1] if idx and idx > 0 else None
    next_lesson = siblings[idx + 1] if idx is not None and idx < len(siblings) - 1 else None

    # Comentários (somente raiz)
    comments = lesson.comments.filter(parent=None).prefetch_related('replies__user').select_related('user')

    # Quiz
    quiz = getattr(lesson, 'quiz', None)
    last_attempt = None
    if quiz and request.user.is_authenticated:
        last_attempt = QuizAttempt.objects.filter(quiz=quiz, user=request.user).first()

    return render(request, 'courses/lesson_detail.html', {
        'lesson':      lesson,
        'course':      course,
        'progress':    progress,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'comments':    comments,
        'quiz':        quiz,
        'last_attempt':last_attempt,
        'enrollment':  enrollment,
    })


@members_only
def lesson_complete(request, pk):
    lesson   = get_object_or_404(Lesson, pk=pk, published=True)
    progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    if not progress.completed:
        progress.completed    = True
        progress.completed_at = timezone.now()
        progress.save()
        messages.success(request, f'Aula "{lesson.title}" marcada como concluída! ✓')
    return redirect('lesson_detail', pk=pk)


@members_only
def lesson_comment(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, published=True)
    if request.method == 'POST':
        body      = request.POST.get('body', '').strip()
        parent_id = request.POST.get('parent_id')
        if body:
            parent = LessonComment.objects.filter(pk=parent_id).first() if parent_id else None
            LessonComment.objects.create(
                lesson=lesson, user=request.user, body=body, parent=parent
            )
            messages.success(request, 'Comentário enviado!')
        else:
            messages.error(request, 'O comentário não pode estar vazio.')
    return redirect('lesson_detail', pk=pk)


@members_only
def lesson_quiz(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, published=True)
    quiz   = get_object_or_404(LessonQuiz, lesson=lesson)

    # Verifica tentativas
    attempts_count = QuizAttempt.objects.filter(quiz=quiz, user=request.user).count()
    if quiz.max_attempts > 0 and attempts_count >= quiz.max_attempts:
        messages.error(request, f'Você atingiu o limite de {quiz.max_attempts} tentativa(s).')
        return redirect('lesson_detail', pk=pk)

    questions = quiz.questions.prefetch_related('choices').all()

    if request.method == 'POST':
        answers  = {}
        correct  = 0
        total    = questions.count()

        for q in questions:
            chosen_id = request.POST.get(f'q_{q.pk}')
            answers[str(q.pk)] = chosen_id
            if chosen_id:
                try:
                    choice = q.choices.get(pk=int(chosen_id))
                    if choice.is_correct:
                        correct += 1
                except Exception:
                    pass

        score  = int((correct / total) * 100) if total else 0
        passed = score >= quiz.passing_score

        attempt = QuizAttempt.objects.create(
            quiz=quiz, user=request.user,
            score=score, passed=passed, answers=answers
        )

        if passed:
            # Marca aula como concluída automaticamente
            progress, _ = LessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
            if not progress.completed:
                progress.completed = True
                progress.completed_at = timezone.now()
                progress.save()

        return render(request, 'courses/quiz_result.html', {
            'quiz': quiz, 'lesson': lesson, 'attempt': attempt,
            'questions': questions, 'answers': answers,
            'correct': correct, 'total': total,
        })

    return render(request, 'courses/quiz.html', {
        'quiz': quiz, 'lesson': lesson, 'questions': questions,
        'attempt_num': attempts_count + 1,
    })


# ══════════════════════════════════════════════════════════
# ── STAFF — Gestão de Cursos ──────────────────────────────
# ══════════════════════════════════════════════════════════

@teacher_or_staff_required
def manage_courses(request):
    q  = request.GET.get('q', '').strip()
    qs = Course.objects.select_related('category', 'instructor').order_by('order', 'title')
    if is_teacher(request.user):
        qs = qs.filter(instructor=request.user)
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    page_obj = Paginator(qs, 20).get_page(request.GET.get('page'))
    return render(request, 'courses/manage/course_list.html', {
        'page_obj': page_obj, 'courses': page_obj, 'q': q
    })


@teacher_or_staff_required
def manage_course_create(request):
    from .forms import CourseForm
    form = CourseForm(request.POST or None, request.FILES or None)
    if is_teacher(request.user):
        form.fields.pop('instructor', None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        if is_teacher(request.user):
            course.instructor = request.user
        course.save()
        messages.success(request, 'Curso criado! Agora adicione os módulos e aulas.')
        return redirect('manage_modules', pk=course.pk)
    return render(request, 'courses/manage/course_form.html', {
        'form': form, 'title': 'Novo Curso'
    })


@teacher_or_staff_required
def manage_course_edit(request, pk):
    from .forms import CourseForm
    course = get_object_or_404(Course, pk=pk)
    if is_teacher(request.user) and course.instructor != request.user:
        messages.error(request, 'Você não pode editar este curso.')
        return redirect('manage_courses')
    form   = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if is_teacher(request.user):
        form.fields.pop('instructor', None)
    if request.method == 'POST' and form.is_valid():
        course = form.save(commit=False)
        if is_teacher(request.user):
            course.instructor = request.user
        course.save()
        messages.success(request, 'Curso atualizado!')
        return redirect('manage_courses')
    return render(request, 'courses/manage/course_form.html', {
        'form': form, 'title': 'Editar Curso', 'course': course
    })


@teacher_or_staff_required
def manage_course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if is_teacher(request.user) and course.instructor != request.user:
        messages.error(request, 'Você não pode excluir este curso.')
        return redirect('manage_courses')
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Curso removido.')
        return redirect('manage_courses')
    return render(request, 'members/confirm_delete.html',
                  {'object': course, 'tipo': 'curso'})


@teacher_or_staff_required
def manage_modules(request, pk):
    from .forms import ModuleForm
    course  = get_object_or_404(Course, pk=pk)
    if is_teacher(request.user) and course.instructor != request.user:
        messages.error(request, 'Você não pode gerenciar módulos deste curso.')
        return redirect('manage_courses')
    modules = course.modules.prefetch_related('lessons').all()

    form = ModuleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        m = form.save(commit=False)
        m.course = course
        m.order  = course.modules.count()
        m.save()
        messages.success(request, f'Módulo "{m.title}" criado!')
        return redirect('manage_modules', pk=pk)

    return render(request, 'courses/manage/modules.html', {
        'course': course, 'modules': modules, 'form': form
    })


@teacher_or_staff_required
def manage_lessons(request, pk):
    module  = get_object_or_404(Module, pk=pk)
    if is_teacher(request.user) and module.course.instructor != request.user:
        messages.error(request, 'Você não pode gerenciar aulas deste curso.')
        return redirect('manage_courses')
    lessons = module.lessons.all()
    return render(request, 'courses/manage/lessons.html', {
        'module': module, 'lessons': lessons
    })


@teacher_or_staff_required
def manage_lesson_create(request, module_pk):
    from .forms import LessonForm
    module = get_object_or_404(Module, pk=module_pk)
    if is_teacher(request.user) and module.course.instructor != request.user:
        messages.error(request, 'Você não pode adicionar aulas a este curso.')
        return redirect('manage_courses')
    form   = LessonForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        lesson = form.save(commit=False)
        lesson.module = module
        lesson.order  = module.lessons.count()
        lesson.save()
        messages.success(request, f'Aula "{lesson.title}" criada!')
        return redirect('manage_lessons', pk=module_pk)
    return render(request, 'courses/manage/lesson_form.html', {
        'form': form, 'module': module, 'title': 'Nova Aula'
    })


@teacher_or_staff_required
def manage_lesson_edit(request, pk):
    from .forms import LessonForm
    lesson = get_object_or_404(Lesson, pk=pk)
    if is_teacher(request.user) and lesson.module.course.instructor != request.user:
        messages.error(request, 'Você não pode editar esta aula.')
        return redirect('manage_courses')
    form   = LessonForm(request.POST or None, request.FILES or None, instance=lesson)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Aula atualizada!')
        return redirect('manage_lessons', pk=lesson.module_id)
    return render(request, 'courses/manage/lesson_form.html', {
        'form': form, 'module': lesson.module, 'title': 'Editar Aula', 'lesson': lesson
    })


@teacher_or_staff_required
def manage_lesson_delete(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    if is_teacher(request.user) and lesson.module.course.instructor != request.user:
        messages.error(request, 'Você não pode excluir esta aula.')
        return redirect('manage_courses')
    module_pk = lesson.module_id
    if request.method == 'POST':
        lesson.delete()
        messages.success(request, 'Aula removida.')
        return redirect('manage_lessons', pk=module_pk)
    return render(request, 'members/confirm_delete.html',
                  {'object': lesson, 'tipo': 'aula'})


@teacher_or_staff_required
def manage_enrollments(request, pk):
    course      = get_object_or_404(Course, pk=pk)
    if is_teacher(request.user) and course.instructor != request.user:
        messages.error(request, 'Você não pode ver inscrições deste curso.')
        return redirect('manage_courses')
    enrollments = course.enrollments.filter(active=True).select_related('user')
    data = [{'enr': e, 'pct': e.progress_percent} for e in enrollments]
    return render(request, 'courses/manage/enrollments.html', {
        'course': course, 'data': data
    })


# ══════════════════════════════════════════════════════════
# ── Quiz — Gestão para Staff ──────────────────────────────
# ══════════════════════════════════════════════════════════
from .models import LessonQuiz, QuizQuestion, QuizChoice
from .forms import LessonQuizForm, QuizQuestionForm, QuizChoiceForm


@teacher_or_staff_required
def manage_quiz(request, lesson_pk):
    """Página principal do quiz de uma aula: configura o quiz e lista perguntas."""
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    if is_teacher(request.user) and lesson.module.course.instructor != request.user:
        messages.error(request, 'Você não pode gerenciar este quiz.')
        return redirect('manage_courses')
    quiz   = getattr(lesson, 'quiz', None)

    # Criar ou editar configurações do quiz
    quiz_form = LessonQuizForm(request.POST or None, instance=quiz)
    if request.method == 'POST' and 'save_quiz' in request.POST and quiz_form.is_valid():
        q = quiz_form.save(commit=False)
        q.lesson = lesson
        q.save()
        messages.success(request, 'Configurações do quiz salvas!')
        return redirect('manage_quiz', lesson_pk=lesson_pk)

    questions = quiz.questions.prefetch_related('choices').all() if quiz else []

    return render(request, 'courses/manage/quiz.html', {
        'lesson':    lesson,
        'quiz':      quiz,
        'quiz_form': quiz_form,
        'questions': questions,
    })


@teacher_or_staff_required
def manage_quiz_question_create(request, lesson_pk):
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    if is_teacher(request.user) and lesson.module.course.instructor != request.user:
        messages.error(request, 'Você não pode adicionar perguntas a este quiz.')
        return redirect('manage_courses')
    quiz   = get_object_or_404(LessonQuiz, lesson=lesson)
    form   = QuizQuestionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        q = form.save(commit=False)
        q.quiz  = quiz
        q.order = quiz.questions.count()
        q.save()
        messages.success(request, 'Pergunta adicionada!')
        return redirect('manage_quiz', lesson_pk=lesson_pk)
    return render(request, 'courses/manage/quiz_question_form.html', {
        'lesson': lesson, 'quiz': quiz, 'form': form, 'title': 'Nova Pergunta'
    })


@teacher_or_staff_required
def manage_quiz_question_edit(request, pk):
    question = get_object_or_404(QuizQuestion, pk=pk)
    lesson   = question.quiz.lesson
    if is_teacher(request.user) and lesson.module.course.instructor != request.user:
        messages.error(request, 'Você não pode editar esta pergunta.')
        return redirect('manage_courses')
    form     = QuizQuestionForm(request.POST or None, instance=question)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Pergunta atualizada!')
        return redirect('manage_quiz', lesson_pk=lesson.pk)
    return render(request, 'courses/manage/quiz_question_form.html', {
        'lesson': lesson, 'quiz': question.quiz,
        'form': form, 'title': 'Editar Pergunta', 'question': question,
        'choices': question.choices.all(),
    })


@teacher_or_staff_required
def manage_quiz_question_delete(request, pk):
    question  = get_object_or_404(QuizQuestion, pk=pk)
    if is_teacher(request.user) and question.quiz.lesson.module.course.instructor != request.user:
        messages.error(request, 'Você não pode excluir esta pergunta.')
        return redirect('manage_courses')
    lesson_pk = question.quiz.lesson_id
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Pergunta removida.')
        return redirect('manage_quiz', lesson_pk=lesson_pk)
    return render(request, 'members/confirm_delete.html',
                  {'object': question, 'tipo': 'pergunta do quiz'})


@teacher_or_staff_required
def manage_quiz_choice_create(request, question_pk):
    question = get_object_or_404(QuizQuestion, pk=question_pk)
    if is_teacher(request.user) and question.quiz.lesson.module.course.instructor != request.user:
        messages.error(request, 'Você não pode adicionar alternativas a esta pergunta.')
        return redirect('manage_courses')
    lesson   = question.quiz.lesson
    form     = QuizChoiceForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        c = form.save(commit=False)
        c.question = question
        c.order    = question.choices.count()
        c.save()
        messages.success(request, 'Alternativa adicionada!')
        return redirect('manage_quiz_question_edit', pk=question.pk)
    return render(request, 'courses/manage/quiz_choice_form.html', {
        'lesson': lesson, 'question': question, 'form': form, 'title': 'Nova Alternativa'
    })


@teacher_or_staff_required
def manage_quiz_choice_edit(request, pk):
    choice   = get_object_or_404(QuizChoice, pk=pk)
    question = choice.question
    if is_teacher(request.user) and question.quiz.lesson.module.course.instructor != request.user:
        messages.error(request, 'Você não pode editar esta alternativa.')
        return redirect('manage_courses')
    lesson   = question.quiz.lesson
    form     = QuizChoiceForm(request.POST or None, instance=choice)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Alternativa atualizada!')
        return redirect('manage_quiz_question_edit', pk=question.pk)
    return render(request, 'courses/manage/quiz_choice_form.html', {
        'lesson': lesson, 'question': question, 'form': form,
        'title': 'Editar Alternativa', 'choice': choice
    })


@teacher_or_staff_required
def manage_quiz_choice_delete(request, pk):
    choice      = get_object_or_404(QuizChoice, pk=pk)
    if is_teacher(request.user) and choice.question.quiz.lesson.module.course.instructor != request.user:
        messages.error(request, 'Você não pode excluir esta alternativa.')
        return redirect('manage_courses')
    question_pk = choice.question_id
    if request.method == 'POST':
        choice.delete()
        messages.success(request, 'Alternativa removida.')
        return redirect('manage_quiz_question_edit', pk=question_pk)
    return render(request, 'members/confirm_delete.html',
                  {'object': choice, 'tipo': 'alternativa'})
