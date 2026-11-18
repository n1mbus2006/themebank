"""Бэкенд аутентификации: вход по логину ИЛИ по e-mail (FR-21).

Пароль проверяет стандартный механизм django.contrib.auth, свой код
только находит пользователя по e-mail.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailOrUsernameBackend(ModelBackend):
    """Первый в списке AUTHENTICATION_BACKENDS, стандартный ModelBackend — второй."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(email__iexact=username.strip())
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            # По e-mail не нашли — отдаём поиск по логину стандартному бэкенду.
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
