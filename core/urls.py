"""Маршруты занятий 7-9. Все имена маршрутов используются в шаблонах
только через {% url %} — прямых ссылок вида /catalog/ нет (занятие 9,
«частые ошибки»).
"""
from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    # Главная — каталог тем.
    path('', views.home, name='home'),
    path('topics/', views.catalog, name='topics'),
    # Живой поиск (JSON) — раньше чем <int:pk>, чтобы адрес был читаемым.
    path('topics/suggest.json/', views.topic_suggest, name='topic_suggest'),
    path('topics/<int:pk>/', views.topic_detail, name='topic_detail'),
    # Статус темы и лимит руководителя для fetch-обновления (FR-23).
    path('topics/<int:pk>/status.json/', views.topic_status, name='topic_status'),
    path('topics/<int:pk>/apply/', views.application_create, name='application_create'),
    # Кабинет студента.
    path('my/applications/', views.my_applications, name='my_applications'),
    path('my/applications/<int:pk>/withdraw/', views.application_withdraw,
         name='application_withdraw'),
    # Кабинет руководителя.
    path('supervisor/applications/', views.supervisor_applications,
         name='supervisor_applications'),
    path('supervisor/applications/<int:pk>/approve/', views.application_approve,
         name='application_approve'),
    path('supervisor/applications/<int:pk>/reject/', views.application_reject,
         name='application_reject'),
    # Сводка заведующего отделением.
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/limits/<int:pk>/', views.limit_update, name='limit_update'),
    path('dashboard/order/upload/', views.order_upload, name='order_upload'),
    path('dashboard/vedomost/', views.vedomost, name='vedomost'),
    path('dashboard/export/csv/', views.csv_export, name='csv_export'),
    # Статическая страница.
    path('about/', views.about, name='about'),
]
