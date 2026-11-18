"""Формы аккаунтов (FR-21): вход и регистрация с выбором роли.

Регистрация одна на обе роли: студент заполняет группу и номер
зачётной книжки, руководитель — должность и подразделение
(так заполняются Student и Supervisor из занятия 5).
"""
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

from core.models import Group as StudyGroup, Student, Supervisor

ROLE_STUDENT = 'student'
ROLE_SUPERVISOR = 'supervisor'
ROLE_CHOICES = [
    (ROLE_STUDENT, 'Студент'),
    (ROLE_SUPERVISOR, 'Руководитель'),
]


class LoginForm(AuthenticationForm):
    """Стандартная форма входа с подписями под макет занятия 6."""

    username = forms.CharField(
        label='Логин или e-mail',
        widget=forms.TextInput(attrs={'data-validate': 'required', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput(attrs={'data-validate': 'required'}),
    )


class RegisterForm(forms.Form):
    """Регистрация: роль переключателем, поля зависят от роли (FR-21)."""

    role = forms.ChoiceField(
        label='Кто вы', choices=ROLE_CHOICES, initial=ROLE_STUDENT,
        widget=forms.RadioSelect(attrs={'data-role-switch': True}),
    )
    full_name = forms.CharField(
        label='ФИО', max_length=150,
        widget=forms.TextInput(attrs={'data-validate': 'required,minlen:5,maxlen:150'}),
    )
    group = forms.ModelChoiceField(
        label='Группа', queryset=StudyGroup.objects.all(), required=False,
        empty_label='Выберите группу',
        widget=forms.Select(attrs={'data-validate': 'required-if-student'}),
    )
    record_book_number = forms.CharField(
        label='Номер зачётной книжки', max_length=20, required=False,
        widget=forms.TextInput(attrs={
            'data-validate': 'required-if-student,maxlen:20',
            'placeholder': 'ИС-230114',
        }),
    )
    position = forms.CharField(
        label='Должность', max_length=100, required=False,
        widget=forms.TextInput(attrs={
            'data-validate': 'required-if-supervisor,maxlen:100',
            'placeholder': 'доцент',
        }),
    )
    department = forms.CharField(
        label='Подразделение', max_length=150, required=False,
        widget=forms.TextInput(attrs={
            'data-validate': 'required-if-supervisor,maxlen:150',
            'placeholder': 'Кафедра информационных систем',
        }),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'data-validate': 'required,email,maxlen:254'}),
    )
    password1 = forms.CharField(
        label='Пароль', strip=False,
        widget=forms.PasswordInput(attrs={'data-validate': 'required'}),
    )
    password2 = forms.CharField(
        label='Повтор пароля', strip=False,
        widget=forms.PasswordInput(attrs={'data-validate': 'required,match:password1'}),
    )

    def clean_email(self):
        """E-mail один на аккаунт, логином становится его часть до @."""
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Этот e-mail уже зарегистрирован.')
        return email

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get('role', ROLE_STUDENT)

        # Поля своей роли обязательны, чужой роли — игнорируются.
        if role == ROLE_STUDENT:
            if not cleaned.get('group'):
                self.add_error('group', 'Укажите учебную группу.')
            record = (cleaned.get('record_book_number') or '').strip()
            if not record:
                self.add_error('record_book_number', 'Укажите номер зачётной книжки.')
            elif Student.objects.filter(record_book_number__iexact=record).exists():
                self.add_error('record_book_number', 'Такой номер зачётной книжки уже есть.')
        else:
            if not (cleaned.get('position') or '').strip():
                self.add_error('position', 'Укажите должность.')
            if not (cleaned.get('department') or '').strip():
                self.add_error('department', 'Укажите подразделение.')

        # Проверка паролей: совпадение уже на клиенте, здесь — на сервере.
        password1 = cleaned.get('password1') or ''
        password2 = cleaned.get('password2') or ''
        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Пароли не совпадают.')
        elif password1:
            try:
                password_validation.validate_password(password1)
            except ValidationError as errors:
                self.add_error('password1', list(errors))
        return cleaned

    def save(self):
        """Создаёт пользователя, назначает группу роли и профиль занятия 5."""
        data = self.cleaned_data
        email = data['email']
        role = data['role']

        # Логин строим из e-mail: стандартная часть до «@», при совпадении
        # добавляем номер — вручную логин придумывать не нужно.
        base = email.split('@')[0].replace('.', '_') or 'user'
        username, suffix = base, 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f'{base}{suffix}'

        user = User.objects.create_user(
            username=username, email=email, password=data['password1'],
            first_name=data['full_name'].split()[0],
            last_name=' '.join(data['full_name'].split()[1:]),
        )

        if role == ROLE_STUDENT:
            group_name = 'Студент'
            Student.objects.create(
                user=user, full_name=data['full_name'],
                record_book_number=data['record_book_number'].strip(),
                group=data['group'],
            )
        else:
            group_name = 'Руководитель'
            Supervisor.objects.create(
                user=user, full_name=data['full_name'],
                position=data['position'].strip(),
                department=data['department'].strip(),
            )
        user.groups.add(Group.objects.get_or_create(name=group_name)[0])
        return user
