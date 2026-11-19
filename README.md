# Банк тем курсовых и дипломных работ (вариант 25)

Учебный проект занятий 7–9: серверная система распределения тем на отделении.
Занятие 7 — каркас и главная страница-каталог, занятие 8 — страницы из
моделей, кабинеты ролей и адаптив, занятие 9 — формы, валидация и динамические
элементы. Дизайн повторяет макеты Figma из занятия 6 (UI-kit, каталог,
карточка темы, вход, регистрация, мои заявки, заявки руководителя, сводка).

## Стек

- Python 3.15, Django 6.1 (только стандартная поставка, без сторонних пакетов)
- SQLite через ORM, модели и миграции из занятия 5
- HTML5 + CSS с переменными UI-kit, ванильный JavaScript (без фреймворков)
- Вертикальная вёрстка по БЭМ-подобным классам, один файл стилей `main.css`

## Запуск

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py load_demo_data
python manage.py createsuperuser    # если нужен доступ в админку
python manage.py runserver
```

Сайт: <http://127.0.0.1:8000/> — главная страница сразу открывает каталог.
Демо-данные создаются командой `load_demo_data` (6 направлений, 10 групп,
10 руководителей, 12 студентов, 40 тем, 20 заявок, лимиты на 2026/2027,
приказ 2025/2026).

## Учётные записи демо-данных

| Кто | Логин | Пароль | Что видит |
|---|---|---|---|
| Студент | `m.yarochkin` | `Demo2026!` | каталог, карточки тем, свои заявки |
| Руководитель | `a.sokolov` | `Demo2026!` | заявки на свои темы, нагрузка |
| Заведующий отделением | `i.kuznetsov` | `Demo2026!` | сводка, лимиты, приказ, ведомость |
| Администратор | `admin` | `Admin2026!` | `/admin/` |

Вход работает и по логину, и по e-mail (свой бэкенд `accounts/backends.py`).
Роли — группы Django «Студент», «Руководитель» (группа «Заведующий
отделением» создаётся командой загрузки, суперпользователь считается
заведующим).

## Структура проекта

```
themebank/
├── manage.py
├── requirements.txt
├── themebank/            # настройки проекта (settings, корневые urls)
├── core/                 # модели занятия 5 + страницы занятий 7–9
│   ├── models.py         # Direction, Group, Student, Supervisor, Topic,
│   │                     # SupervisorLimit, Application, ApprovalOrder
│   ├── views.py          # каталог, карточка, заявки, сводка, ведомость, CSV
│   ├── forms.py          # заявка, отклонение, лимит, приказ
│   ├── roles.py          # роли по группам Django, декоратор role_required
│   ├── urls.py           # маршруты core (все имена используются через {% url %})
│   ├── templatetags/core_extras.py   # initials, short_fio, basename, get_item
│   ├── context_processors.py         # role, academic_year, инициалы в шапке
│   └── management/commands/load_demo_data.py   # демо-данные
├── accounts/             # вход, регистрация, смена пароля (FR-21)
│   ├── forms.py          # LoginForm, RegisterForm (роль переключателем)
│   ├── views.py, urls.py, backends.py
├── templates/            # base.html + страницы + includes
├── static/
│   ├── css/main.css      # единственный файл стилей (переменные UI-kit)
│   ├── js/main.js        # меню, полосы нагрузки, клиентская валидация
│   ├── js/catalog.js     # живой поиск в шапке (fetch к suggest.json)
│   ├── js/topic.js       # fetch-обновление статуса темы (FR-23)
│   └── img/userflow.jpg  # схема процесса с занятия 6 (сжата до 50 КБ)
└── db.sqlite3            # создаётся migrate + load_demo_data
```

## Маршруты

| Адрес | Имя | Что делает |
|---|---|---|
| `/` | `core:home` | редирект на каталог |
| `/topics/` | `core:topics` | каталог: поиск, 3 фильтра, сортировка, пагинация по 20 |
| `/topics/<id>/` | `core:topic_detail` | карточка темы, форма заявки |
| `/topics/<id>/status.json/` | `core:topic_status` | JSON для fetch-обновления |
| `/topics/suggest.json/` | `core:topic_suggest` | JSON живого поиска |
| `/topics/<id>/apply/` | `core:application_create` | подача заявки (POST) |
| `/my/applications/` | `core:my_applications` | кабинет студента |
| `/my/applications/<id>/withdraw/` | `core:application_withdraw` | отзыв заявки |
| `/supervisor/applications/` | `core:supervisor_applications` | кабинет руководителя |
| `/supervisor/applications/<id>/approve/` | `core:application_approve` | одобрение (транзакция) |
| `/supervisor/applications/<id>/reject/` | `core:application_reject` | отклонение с причиной |
| `/dashboard/` | `core:dashboard` | сводка: показатели, график, лимиты, приказ |
| `/dashboard/limits/<id>/` | `core:limit_update` | правка лимита 1–30 |
| `/dashboard/order/upload/` | `core:order_upload` | загрузка приказа |
| `/dashboard/vedomost/` | `core:vedomost` | ведомость для печати |
| `/dashboard/export/csv/` | `core:csv_export` | CSV (utf-8-sig, разделитель «;») |
| `/about/` | `core:about` | статическая страница «О проекте» |
| `/accounts/login/`, `/accounts/register/`, `/accounts/password_change/` | `accounts:*` | вход, регистрация, пароль |

## Особое требование варианта

Одна тема закрепляется только за одним студентом, а у руководителя нельзя
превысить лимит: частичные уникальные индексы в базе (занятие 5), проверки
в `clean()` формы и одобрение в `transaction.atomic` с повторной проверкой
остатка. Все проверки выполняются на сервере, JavaScript только помогает
заметить ошибку до отправки.
