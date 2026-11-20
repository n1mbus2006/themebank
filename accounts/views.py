"""Представления входа, регистрации и смены пароля (FR-21).

Вход и выход — стандартные классы django.contrib.auth.views, свои
только шаблоны и сообщения. Регистрация полностью своя.
"""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from core.models import Group as StudyGroup

from .forms import LoginForm, RegisterForm


class LoginViewCustom(LoginView):
    """Вход: форма с подписью «Логин или e-mail» и карточка из макета."""

    template_name = 'login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Вход'
        context['nav'] = 'login'
        return context


class LogoutViewCustom(LogoutView):
    """Выход только по POST (кнопка в меню пользователя)."""


class PasswordChangeViewCustom(PasswordChangeView):
    """Смена пароля средствами django.contrib.auth (FR-21)."""

    template_name = 'password_change.html'
    success_url = reverse_lazy('accounts:password_change_done')

    def form_valid(self, form):
        messages.success(self.request, 'Пароль изменён. Используйте новый при следующем входе.')
        return super().form_valid(form)


class PasswordChangeDoneViewCustom(PasswordChangeDoneView):
    template_name = 'password_change_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Пароль изменён'
        return context


def register(request):
    """Регистрация с выбором роли; после успеха — вход и сообщение."""
    if request.user.is_authenticated:
        return redirect('core:topics')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        # Бэкендов два (e-mail и стандартный), поэтому вход после регистрации
        # требует явного указания, каким из них аутентифицирован пользователь.
        login(request, user, backend='accounts.backends.EmailOrUsernameBackend')
        role_label = 'студент' if form.cleaned_data['role'] == 'student' else 'руководитель'
        messages.success(request, f'Аккаунт создан, вы вошли как {role_label}.')
        return redirect('core:topics')

    return render(request, 'register.html', {
        'form': form,
        'groups': StudyGroup.objects.all(),
        'page_title': 'Регистрация',
        'nav': 'register',
    })
