"""Представления занятий 7-9: каталог, карточка темы, заявки, сводка.

Страницы собираются из данных моделей занятия 5, никакого «выдуманного»
контента в шаблонах нет. Все проверки особого требования (занятость
темы, лимит руководителя) выполняются на сервере.
"""
import csv

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST


from .forms import ApplicationForm, LimitForm, OrderUploadForm, RejectForm
from .models import (
    Application,
    ApprovalOrder,
    Direction,
    Group,
    Supervisor,
    SupervisorLimit,
    Topic,
)
from .roles import ROLE_HEAD, ROLE_SUPERVISOR, ROLE_STUDENT, role_of, role_required

# В год берём только темы активного набора — остальные года в каталог не отдаём.
TOPICS_PER_PAGE = 20  # FR-05: пагинация по 20 тем


def home(request):
    """Главная страница проекта — каталог, отдельной витрины нет (занятие 6)."""
    return redirect('core:topics')


def _limit_info(supervisor_ids, academic_year):
    """Словарь «руководитель -> (лимит, закреплено, остаток)».

    Карточкам каталога и сводке нужны одни и те же три числа, поэтому
    они считаются в одном месте. Учебный объём данных (10 руководителей)
    позволяет считать закреплённых отдельным запросом на каждого.
    """
    info = {}
    limits = SupervisorLimit.objects.filter(
        supervisor_id__in=supervisor_ids, academic_year=academic_year,
    ).select_related('supervisor')
    for limit in limits:
        occupied = limit.occupied()
        info[limit.supervisor_id] = {
            'max_students': limit.max_students,
            'occupied': occupied,
            'remaining': limit.remaining(),
        }
    return info


def _catalog_queryset(request):
    """Список тем с поиском, тремя фильтрами и сортировкой (FR-02..FR-04)."""
    topics = Topic.objects.filter(
        academic_year=Topic.CURRENT_YEAR,
    ).select_related('supervisor', 'direction')

    # Поиск по названию и по ФИО руководителя.
    query = request.GET.get('q', '').strip()
    if query:
        topics = topics.filter(
            Q(title__icontains=query) | Q(supervisor__full_name__icontains=query),
        )

    # Фильтр по направлению (select) и по руководителю (select).
    direction_id = request.GET.get('direction', '')
    if direction_id.isdigit():
        topics = topics.filter(direction_id=int(direction_id))
    supervisor_id = request.GET.get('supervisor', '')
    if supervisor_id.isdigit():
        topics = topics.filter(supervisor_id=int(supervisor_id))

    # Фильтр по статусу: чипы «Все / Свободны / Закреплены».
    status = request.GET.get('status', '')
    if status == Topic.Status.FREE or status == Topic.Status.TAKEN:
        topics = topics.filter(status=status)

    # Фильтр по типу работы: курсовая / дипломная.
    work_type = request.GET.get('work_type', '')
    if work_type in (Topic.WorkType.COURSE, Topic.WorkType.GRADUATE):
        topics = topics.filter(work_type=work_type)

    # Сортировка: по дате добавления (умолчание), названию, ФИО руководителя.
    sort = request.GET.get('sort', 'new')
    orderings = {
        'new': '-created_at',
        'title': 'title',
        'supervisor': 'supervisor__full_name',
    }
    topics = topics.order_by(orderings.get(sort, '-created_at'))
    return topics


def catalog(request):
    """Каталог тем — главная страница (FR-01..FR-05, занятие 7)."""
    topics = _catalog_queryset(request)

    paginator = Paginator(topics, TOPICS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Для счётчика «Найдено X из Y» нужен и отфильтрованный итог, и общий.
    found_total = paginator.count
    all_total = Topic.objects.filter(academic_year=Topic.CURRENT_YEAR).count()

    # Строка параметров без page — так фильтры и сортировка не сбрасываются
    # при переходе по страницам пагинации.
    base_params = request.GET.copy()
    base_params.pop('page', None)

    # Лимиты руководителей показанных тем: «Закреплено 3 из 5» (FR-09).
    page_supervisors = {t.supervisor_id for t in page_obj.object_list}
    limits = _limit_info(page_supervisors, Topic.CURRENT_YEAR)

    cards = []
    for topic in page_obj.object_list:
        limit = limits.get(topic.supervisor_id)
        cards.append({
            'topic': topic,
            'limit': limit,
            'limit_exhausted': limit is not None and limit['remaining'] <= 0,
        })

    context = {
        'cards': cards,
        'page_obj': page_obj,
        'base_params': base_params,
        'found_total': found_total,
        'all_total': all_total,
        'directions': Direction.objects.all(),
        'supervisors': Supervisor.objects.all(),
        'nav': 'topics',
        'page_title': 'Каталог тем',
    }
    return render(request, 'catalog.html', context)


def _topic_context(request, topic, form=None):
    """Общий контекст страницы темы: блок руководителя и форма заявки."""
    limit = SupervisorLimit.objects.filter(
        supervisor=topic.supervisor, academic_year=topic.academic_year,
    ).first()

    my_application = None
    if role_of(request.user) == ROLE_STUDENT and hasattr(request.user, 'student_profile'):
        my_application = Application.objects.filter(
            student=request.user.student_profile, topic=topic,
        ).first()

    # Активная заявка ожидает решения — форма подачи уже не нужна.
    my_application_active = bool(my_application and my_application.status in (
        Application.Status.SUBMITTED, Application.Status.IN_REVIEW,
    ))

    if form is None:
        form = ApplicationForm(
            topic=topic, student=request.user.student_profile
            if hasattr(request.user, 'student_profile') else None,
        )

    return {
        'topic': topic,
        'limit': limit,
        'form': form,
        'my_application': my_application,
        'my_application_active': my_application_active,
        'nav': 'topics',
        'page_title': topic.title,
    }


def topic_detail(request, pk):
    """Карточка темы: описание, руководитель, форма заявки (FR-06, FR-09)."""
    topic = get_object_or_404(
        Topic.objects.select_related('supervisor', 'direction'), pk=pk,
    )
    return render(request, 'topic_detail.html', _topic_context(request, topic))
def topic_status(request, pk):
    """JSON со статусом темы и остатком лимита (FR-23).

    К нему ходит fetch со страницы темы: бейдж статуса и строка
    «Закреплено 3 из 5» обновляются без перезагрузки.
    """
    topic = get_object_or_404(Topic, pk=pk)
    limit = SupervisorLimit.objects.filter(
        supervisor=topic.supervisor, academic_year=topic.academic_year,
    ).first()
    return JsonResponse({
        'status': topic.status,
        'status_label': topic.get_status_display(),
        'is_free': topic.is_free(),
        'occupied': limit.occupied() if limit else 0,
        'max_students': limit.max_students if limit else 0,
        'remaining': limit.remaining() if limit else 0,
    })


def topic_suggest(request):
    """JSON для живого поиска в шапке: до 6 подходящих тем."""
    query = request.GET.get('q', '').strip()
    items = []
    if len(query) >= 2:
        topics = Topic.objects.filter(
            academic_year=Topic.CURRENT_YEAR,
        ).filter(
            Q(title__icontains=query) | Q(supervisor__full_name__icontains=query),
        ).select_related('supervisor')[:6]
        items = [{
            'id': t.id,
            'url': reverse('core:topic_detail', args=[t.id]),
            'title': t.title[:70],
            'supervisor': t.supervisor.full_name,
            'status_label': t.get_status_display(),
            'is_free': t.is_free(),
        } for t in topics]
    return JsonResponse({'items': items, 'query': query})


@login_required
@role_required(ROLE_STUDENT)
def application_create(request, pk):
    """Подача заявки (FR-06): только POST, проверка занятости и лимита.

    Двум студентам, нажавшим «Подать заявку» одновременно, форма обе
    пройдёт (обе записи «Подана» — это разрешено), но одобрить вторую
    нельзя: уникальный частичный индекс из занятия 5 не даст базе
    записать вторую одобренную заявку на тему.
    """
    topic = get_object_or_404(Topic, pk=pk)
    student = (
        request.user.student_profile
        if hasattr(request.user, 'student_profile') else None
    )
    if student is None:
        raise PermissionDenied
    if request.method != 'POST':
        return redirect('core:topic_detail', pk=topic.pk)

    form = ApplicationForm(request.POST, topic=topic, student=student)
    if form.is_valid():
        with transaction.atomic():
            Application.objects.create(
                student=student,
                topic=topic,
                status=Application.Status.SUBMITTED,
                comment=form.cleaned_data['comment'],
            )
        messages.success(request, 'Заявка подана. Руководитель получит уведомление.')
        return redirect('core:my_applications')

    messages.error(request, 'Заявку не удалось отправить: исправьте ошибки в форме.')
    context = _topic_context(request, topic, form=form)
    context['server_reject'] = True
    return render(request, 'topic_detail.html', context, status=200)


@login_required
@role_required(ROLE_STUDENT)
def my_applications(request):
    """Мои заявки (FR-10): статусы, причины отклонения, отзыв (FR-13)."""
    student = request.user.student_profile
    applications = (Application.objects.filter(student=student)
                    .select_related('topic', 'topic__supervisor', 'topic__direction'))
    return render(request, 'my_applications.html', {
        'applications': applications,
        'nav': 'my',
        'page_title': 'Мои заявки',
    })


@login_required
@role_required(ROLE_STUDENT)
@require_POST
def application_withdraw(request, pk):
    """Отзыв заявки (FR-13): только пока она не одобрена."""
    student = request.user.student_profile
    application = get_object_or_404(Application, pk=pk, student=student)
    if application.status not in (Application.Status.SUBMITTED, Application.Status.IN_REVIEW):
        messages.warning(
            request,
            f'Заявку «{application.topic.title}» отозвать нельзя: она уже '
            f'{application.get_status_display().lower()}.'
        )
        return redirect('core:my_applications')

    application.status = Application.Status.WITHDRAWN
    application.decided_at = None
    application.decided_by = None
    application.save(update_fields=['status', 'decided_at', 'decided_by'])
    messages.info(request, 'Заявка отозвана. Можно подать заявку на другую тему.')
    return redirect('core:my_applications')


@login_required
@role_required(ROLE_SUPERVISOR)
def supervisor_applications(request):
    """Заявки на мои темы (FR-11, FR-16): плитка нагрузки и список."""
    supervisor = request.user.supervisor_profile if hasattr(request.user, 'supervisor_profile') else None
    if supervisor is None:
        raise PermissionDenied

    applications = (Application.objects
                    .filter(topic__supervisor=supervisor)
                    .select_related('topic', 'student', 'student__group')
                    .order_by('-submitted_at'))

    # Плитка нагрузки: сколько закреплено из лимита на активный год (FR-16).
    limit = SupervisorLimit.objects.filter(
        supervisor=supervisor, academic_year=Topic.CURRENT_YEAR,
    ).first()
    return render(request, 'supervisor_applications.html', {
        'applications': applications,
        'limit': limit,
        'nav': 'supervisor',
        'page_title': 'Заявки на мои темы',
    })


@login_required
@role_required(ROLE_SUPERVISOR)
@require_POST
def application_approve(request, pk):
    """Одобрение заявки (FR-12): одна транзакция на три изменения.

    Меняются заявка, статус темы и остаток лимита руководителя. Частичный
    уникальный индекс на одобренные заявки не даёт закрепить тему дважды:
    при гонке вторая попытка получит IntegrityError и аккуратное сообщение.
    """
    supervisor = request.user.supervisor_profile
    application = get_object_or_404(Application, pk=pk)
    if application.topic.supervisor_id != supervisor.id:
        raise PermissionDenied  # чужая заявка — 403
    if application.status not in (Application.Status.SUBMITTED, Application.Status.IN_REVIEW):
        messages.warning(request, 'Заявка уже обработана.')
        return redirect('core:supervisor_applications')

    topic = application.topic
    try:
        with transaction.atomic():
            # Повторная проверка лимита внутри транзакции: между просмотром
            # страницы и нажатием «Одобрить» другой студент мог занять место.
            limit = SupervisorLimit.objects.filter(
                supervisor=supervisor, academic_year=topic.academic_year,
            ).first()
            if limit is None:
                messages.error(request, 'У вас не задан лимит на этот учебный год.')
                return redirect('core:supervisor_applications')
            if limit.remaining() <= 0:
                messages.warning(
                    request,
                    f'Лимит исчерпан ({limit.max_students} из '
                    f'{limit.max_students}). Заявка не одобрена.'
                )
                return redirect('core:supervisor_applications')

            application.status = Application.Status.APPROVED
            application.decided_at = timezone.now()
            application.decided_by = supervisor
            application.save()

            topic.status = Topic.Status.TAKEN
            topic.save(update_fields=['status'])
    except IntegrityError:
        messages.error(request, 'Тема уже закреплена за другим студентом.')
        return redirect('core:supervisor_applications')


    messages.success(
        request,
        f'Заявка одобрена: тема закреплена за {application.student.full_name}.'
    )
    return redirect('core:supervisor_applications')


@login_required
@role_required(ROLE_SUPERVISOR)
@require_POST
def application_reject(request, pk):
    """Отклонение заявки с обязательной причиной (FR-11)."""
    supervisor = request.user.supervisor_profile
    application = get_object_or_404(Application, pk=pk)
    if application.topic.supervisor_id != supervisor.id:
        raise PermissionDenied
    if application.status not in (Application.Status.SUBMITTED, Application.Status.IN_REVIEW):
        messages.warning(request, 'Заявка уже обработана.')
        return redirect('core:supervisor_applications')

    form = RejectForm(request.POST)
    if form.is_valid():
        application.status = Application.Status.REJECTED
        application.reject_reason = form.cleaned_data['reason']
        application.decided_at = timezone.now()
        application.decided_by = supervisor
        application.save()
        messages.info(request, 'Заявка отклонена, студент увидит причину в «Моих заявках».')
        return redirect('core:supervisor_applications')


    messages.error(request, 'Причина отклонения не заполнена, заявка не изменена.')
    return redirect('core:supervisor_applications')


@login_required
@role_required(ROLE_HEAD)
def dashboard(request):
    """Сводка распределения (FR-17): 4 показателя, график, лимиты, приказ."""
    year = Topic.CURRENT_YEAR
    year_topics = Topic.objects.filter(academic_year=year)
    topics_total = year_topics.count()
    topics_free = year_topics.filter(status=Topic.Status.FREE).count()

    applications_total = Application.objects.filter(topic__academic_year=year).count()
    approved_total = Application.objects.filter(
        topic__academic_year=year, status=Application.Status.APPROVED,
    ).count()

    limits = (SupervisorLimit.objects.filter(academic_year=year)
              .select_related('supervisor').order_by('supervisor__full_name'))
    chart_rows = []
    for limit in limits:
        chart_rows.append({
            'supervisor': limit.supervisor,
            'occupied': limit.occupied(),
            'max_students': limit.max_students,
        })

    # Доля закреплённых и средняя загрузка — два из четырёх показателей.
    share = round(approved_total * 100 / topics_total) if topics_total else 0
    average_load = approved_total / len(limits) if limits else 0

    order = ApprovalOrder.objects.order_by('-academic_year').first()

    return render(request, 'dashboard.html', {
        'topics_total': topics_total,
        'topics_free': topics_free,
        'applications_total': applications_total,
        'approved_total': approved_total,
        'share': share,
        'average_load': average_load,
        'chart_rows': chart_rows,
        'limits': limits,
        'order': order,
        'order_form': OrderUploadForm(),
        'limit_forms': {limit.pk: LimitForm(instance=limit) for limit in limits},
        'nav': 'dashboard',
        'page_title': 'Сводка распределения',
    })


@login_required
@role_required(ROLE_HEAD)
@require_POST
def limit_update(request, pk):
    """Сохранение лимита руководителя (FR-22): диапазон 1-30 на сервере."""
    limit = get_object_or_404(SupervisorLimit, pk=pk)
    form = LimitForm(request.POST, instance=limit)
    if form.is_valid():
        form.save()
        messages.success(
            request,
            f'Лимит {limit.supervisor.full_name} на {limit.academic_year} сохранён: '
            f'{limit.max_students} студентов.'
        )
    else:
        first_error = next(iter(form.errors.values()), ['Проверьте значение лимита.'])[0]
        messages.error(request, f'Лимит не сохранён: {first_error}')
    return redirect('core:dashboard')


@login_required
@role_required(ROLE_HEAD)
@require_POST
def order_upload(request):
    """Загрузка файла приказа за активный год (FR-19, NFR-09).

    Приказ уникален на учебный год, поэтому повторная загрузка заменяет
    файл и примечание у существующей записи.
    """
    order = ApprovalOrder.objects.filter(academic_year=Topic.CURRENT_YEAR).first()
    form = OrderUploadForm(request.POST, request.FILES, instance=order)
    if form.is_valid():
        new_order = form.save(commit=False)
        new_order.academic_year = Topic.CURRENT_YEAR
        new_order.uploaded_by = request.user
        new_order.save()
        messages.success(request, 'Приказ загружен и виден студентам на странице сводки.')
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, f'Приказ не загружен: {error}')
                break
            break
    return redirect('core:dashboard')


@login_required
@role_required(ROLE_HEAD)
def vedomost(request):
    """Печатная форма ведомости закреплённых тем (FR-18)."""
    year = Topic.CURRENT_YEAR
    rows = (Application.objects
            .filter(topic__academic_year=year, status=Application.Status.APPROVED)
            .select_related('topic', 'topic__supervisor', 'student', 'student__group')
            .order_by('topic__supervisor__full_name', 'topic__title'))
    return render(request, 'vedomost.html', {
        'rows': rows,
        'nav': 'dashboard',
        'page_title': 'Ведомость для печати',
    })


@login_required
@role_required(ROLE_HEAD)
def csv_export(request):
    """Выгрузка сводного списка в CSV (FR-18).

    Кодировка utf-8-sig и разделитель «;» — чтобы файл сразу открывался
    в Excel без мастера импорта (требование ТЗ, раздел 4.5).
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        'attachment; filename="vedomost_2026-2027.csv"'
    )
    writer = csv.writer(response, delimiter=';')
    writer.writerow([
        '№', 'Тема', 'Тип работы', 'Направление', 'Руководитель',
        'Студент', 'Группа', 'Номер зачётной книжки', 'Дата закрепления',
    ])
    rows = (Application.objects
            .filter(topic__academic_year=Topic.CURRENT_YEAR,
                    status=Application.Status.APPROVED)
            .select_related('topic', 'topic__supervisor', 'topic__direction',
                            'student', 'student__group')
            .order_by('topic__supervisor__full_name', 'topic__title'))
    for number, application in enumerate(rows, start=1):
        writer.writerow([
            number,
            application.topic.title,
            application.topic.get_work_type_display(),
            application.topic.direction.__str__(),
            application.topic.supervisor.full_name,
            application.student.full_name,
            application.student.group.name,
            application.student.record_book_number,
            application.decided_at.strftime('%d.%m.%Y') if application.decided_at else '',
        ])
    return response


@login_required
@role_required(ROLE_HEAD)
def about(request):
    """Статическая страница «О проекте» (занятие 8)."""
    return render(request, 'about.html', {
        'nav': 'about',
        'page_title': 'О проекте',
    })
