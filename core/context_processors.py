"""Контекст-процессор: в каждый шаблон попадают роль и учебный год.

Так шапка сама подбирает пункты меню и аватар под роль, а страницы
не хардкодят год в тексте.
"""
from core.templatetags.core_extras import initials, short_fio

from .models import Topic
from .roles import ROLE_HEAD, ROLE_GUEST, ROLE_SUPERVISOR, ROLE_STUDENT, role_of


def common(request):
    """Общие данные для base.html и дочерних шаблонов."""
    user = request.user
    role = role_of(user)

    # Подпись и инициалы для аватара: берём ФИО из профиля занятия 5,
    # у заведующего отделением — из учётной записи.
    full_name = ''
    if user.is_authenticated:
        profile = getattr(user, 'student_profile', None)
        if profile is None:
            profile = getattr(user, 'supervisor_profile', None)
        full_name = profile.full_name if profile else user.get_full_name()

    return {
        'role': role,
        'academic_year': Topic.CURRENT_YEAR,
        'search_query': request.GET.get('q', ''),
        'user_full_name': full_name,
        'user_short_name': short_fio(full_name) if full_name else '',
        'user_initials': initials(full_name) if full_name else '',
        'nav': '',
    }
