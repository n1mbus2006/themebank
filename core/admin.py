"""Админка для занятия 5: доступ к заполненным таблицам и их структура.

Полноценную настройку списков сделаю на занятии 6, сейчас достаточно
просмотра, поиска и фильтров, чтобы проверить данные после миграций.
"""
from django.contrib import admin

from .models import (
    Application,
    ApprovalOrder,
    Direction,
    Group,
    Student,
    Supervisor,
    SupervisorLimit,
    Topic,
)


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'level')
    search_fields = ('code', 'title')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'direction', 'enrollment_year')
    list_filter = ('direction',)
    search_fields = ('name',)


@admin.register(Supervisor)
class SupervisorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'department')
    search_fields = ('full_name',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'record_book_number', 'group')
    list_filter = ('group',)
    search_fields = ('full_name', 'record_book_number')


@admin.register(SupervisorLimit)
class SupervisorLimitAdmin(admin.ModelAdmin):
    list_display = ('supervisor', 'academic_year', 'max_students')
    list_filter = ('academic_year',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'supervisor', 'direction', 'work_type', 'academic_year', 'status')
    list_filter = ('status', 'direction', 'work_type')
    search_fields = ('title', 'supervisor__full_name')


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'short_topic', 'status', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('student__full_name', 'topic__title')

    @admin.display(description='тема')
    def short_topic(self, obj):
        """Длинные названия тем ломают ширину таблицы — режу до 60 символов."""
        title = obj.topic.title
        return title if len(title) <= 60 else title[:57] + '…'


@admin.register(ApprovalOrder)
class ApprovalOrderAdmin(admin.ModelAdmin):
    list_display = ('academic_year', 'file', 'uploaded_at', 'uploaded_by')
