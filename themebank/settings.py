"""
Настройки проекта «Банк тем курсовых и дипломных работ» (вариант 25).

Занятия 7-9: к базе из занятия 5 добавились шаблоны, статика, роли
(группы Django) и почтовый бэкенд для уведомлений.
Секретный ключ читается из переменной окружения DJANGO_SECRET_KEY,
в репозиторий настоящий ключ не попадает (требование ТЗ, раздел 4.5).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-key-zanyatie-7-9-ne-dlya-produkshena')

DEBUG = os.environ.get('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',        # модели из занятия 5 + каталог, заявки, сводка
    'accounts',    # вход, регистрация, смена пароля (FR-21)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'themebank.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Общие шаблоны лежат в каталоге templates на уровне проекта.
        'DIRS': [BASE_DIR / 'templates'],
        # APP_DIRS выключен: список каталогов задан явно через loaders.
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Роль пользователя и учебный год для шапки и навигации.
                'core.context_processors.common',
            ],
            # Кэш компиляции шаблонов включаем только без DEBUG:
            # при отладке правки шаблонов подхватываются без рестарта.
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ] if not DEBUG else [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
        },
    },
]

WSGI_APPLICATION = 'themebank.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Вход по логину ИЛИ по e-mail (FR-21): первый свой бэкенд, потом стандартный.
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Маршруты входа и выхода называются так же, как в таблице страниц занятия 6.
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:topics'
LOGOUT_REDIRECT_URL = 'core:topics'

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
# Общая статика проекта: один файл стилей и три файла скриптов.
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# В учебной версии письма выводятся в консоль (FR-15, NFR-08 из ТЗ).
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
