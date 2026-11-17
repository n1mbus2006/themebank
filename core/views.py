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

