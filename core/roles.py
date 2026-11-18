"""Роли пользователей и проверка доступа (FR-20 техзадания).

Роли закрепляются через группы Django: «Студент», «Руководитель»,
«Заведующий отделением» (их создаёт команда load_demo_data и
регистрация). Суперпользователь приравнен к заведующему отделением —
ему тоже нужна сводка.
"""
from functools import wraps

from django.core.exceptions import PermissionDenied

ROLE_HEAD = 'head'
ROLE_SUPERVISOR = 'supervisor'
ROLE_STUDENT = 'student'
ROLE_GUEST = 'guest'


def role_of(user):
    """Возвращает строку-роль: guest / student / supervisor / head."""
    if not user.is_authenticated:
        return ROLE_GUEST
    if user.is_superuser or user.groups.filter(name='Заведующий отделением').exists():
        return ROLE_HEAD
    if user.groups.filter(name='Руководитель').exists():
        return ROLE_SUPERVISOR
    if user.groups.filter(name='Студент').exists():
        return ROLE_STUDENT
    return ROLE_GUEST


def role_required(*roles):
    """Декоратор: пускать на страницу только перечисленные роли.

    По таблице доступа занятия 6 чужая страница возвращает 403,
    а не редирект на вход, поэтому кидаем PermissionDenied.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if role_of(request.user) not in roles:
                raise PermissionDenied('Недостаточно прав для этой страницы.')
            return view(request, *args, **kwargs)
        return wrapper
    return decorator
