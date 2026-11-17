"""Модели базы данных «Банка тем курсовых и дипломных работ».

Занятие 5: сущности перенесены из концептуальной модели занятия 1,
ограничения особого требования (одна тема — один студент, лимит
руководителя) закреплены на уровне базы данных и серверного кода.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


def validate_order_file_size(file):
    """Файл приказа — не больше 5 МБ (NFR-09 техзадания)."""
    if file.size > 5 * 1024 * 1024:
        raise ValidationError('Файл приказа больше 5 МБ. Максимальный размер — 5 МБ.')


class Direction(models.Model):
    """Направление подготовки. Справочник, на него опираются темы и группы."""

    LEVEL_BACHELOR = 'bachelor'
    LEVEL_MASTER = 'master'
    LEVEL_SPO = 'spo'
    LEVEL_CHOICES = [
        (LEVEL_BACHELOR, 'Бакалавриат'),
        (LEVEL_MASTER, 'Магистратура'),
        (LEVEL_SPO, 'СПО'),
    ]

    code = models.CharField(
        'код направления', max_length=20, unique=True,
        help_text='Код по классификатору, например 09.03.02',
    )
    title = models.CharField('название направления', max_length=255)
    level = models.CharField(
        'уровень образования', max_length=20,
        choices=LEVEL_CHOICES, default=LEVEL_BACHELOR,
    )

    class Meta:
        verbose_name = 'направление подготовки'
        verbose_name_plural = 'направления подготовки'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} — {self.title}'


class Group(models.Model):
    """Учебная группа. У одной группы одно направление, у направления много групп."""

    name = models.CharField('название группы', max_length=20, unique=True)
    direction = models.ForeignKey(
        Direction, on_delete=models.PROTECT, related_name='groups',
        verbose_name='направление',
    )
    enrollment_year = models.PositiveSmallIntegerField(
        'год набора', help_text='Например, 2023',
    )

    class Meta:
        verbose_name = 'учебная группа'
        verbose_name_plural = 'учебные группы'
        ordering = ['name']
        constraints = [
            models.CheckConstraint(
                condition=Q(enrollment_year__gte=2015, enrollment_year__lte=2035),
                name='core_group_year_range',
            ),
        ]

    def __str__(self):
        return self.name


class Supervisor(models.Model):
    """Профиль руководителя работы (преподавателя). Привязан к учётной записи."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='supervisor_profile', verbose_name='учётная запись',
    )
    full_name = models.CharField('ФИО руководителя', max_length=150)
    position = models.CharField('должность', max_length=100)
    department = models.CharField('подразделение', max_length=150)

    class Meta:
        verbose_name = 'руководитель работы'
        verbose_name_plural = 'руководители работ'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Student(models.Model):
    """Профиль студента. Связь «студент — тема» идёт через таблицу заявок."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='student_profile', verbose_name='учётная запись',
    )
    full_name = models.CharField('ФИО студента', max_length=150)
    record_book_number = models.CharField(
        'номер зачётной книжки', max_length=20, unique=True,
    )
    group = models.ForeignKey(
        Group, on_delete=models.PROTECT, related_name='students',
        verbose_name='группа',
    )
    # Связь «многие ко многим» со связующей таблицей заявок:
    # у студента несколько заявок, у темы несколько заявок.
    topics = models.ManyToManyField(
        'Topic', through='Application', related_name='applicants',
        verbose_name='темы (через заявки)', blank=True,
    )

    class Meta:
        verbose_name = 'студент'
        verbose_name_plural = 'студенты'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class SupervisorLimit(models.Model):
    """Лимит закреплённых студентов на учебный год (FR-22).

    Количество закреплённых не храню отдельным полем — считаю по одобренным
    заявкам тем этого руководителя за учебный год (см. свойство occupied).
    Так число не разойдётся с реальными данными.
    """

    supervisor = models.ForeignKey(
        Supervisor, on_delete=models.PROTECT, related_name='limits',
        verbose_name='руководитель',
    )
    academic_year = models.CharField(
        'учебный год', max_length=9, help_text='Формат 2026/2027',
    )
    max_students = models.PositiveSmallIntegerField(
        'максимум студентов', default=5,
        help_text='Сколько студентов может закрепить руководитель за год',
    )

    class Meta:
        verbose_name = 'лимит руководителя'
        verbose_name_plural = 'лимиты руководителей'
        ordering = ['academic_year', 'supervisor']
        constraints = [
            models.UniqueConstraint(
                fields=['supervisor', 'academic_year'],
                name='core_limit_supervisor_year',
            ),
            models.CheckConstraint(
                condition=Q(max_students__gte=1, max_students__lte=30),
                name='core_limit_max_students_range',
            ),
        ]

    def occupied(self):
        """Сколько студентов уже закреплено за руководителем в этом году."""
        return Application.objects.filter(
            status=Application.Status.APPROVED,
            topic__supervisor=self.supervisor,
            topic__academic_year=self.academic_year,
        ).count()

    def remaining(self):
        """Остаток лимита — то, что показывает студенту карточка темы (FR-09)."""
        return self.max_students - self.occupied()

    def __str__(self):
        return f'{self.supervisor} — {self.academic_year} — лимит {self.max_students}'


class Topic(models.Model):
    """Тема курсовой или дипломной работы.

    Поле status осознанно храню, хотя его можно вывести из одобренных заявок:
    каталог (FR-01) фильтрует темы по статусу напрямую, а смена статуса
    происходит в одной транзакции с одобрением заявки (FR-12). Целостность
    страхует частичный уникальный индекс на модели заявки.
    """

    # Активный учебный год набора тем: каталог называется
    # «Каталог тем · 2026/2027» (макет занятия 6).
    CURRENT_YEAR = '2026/2027'


    class WorkType(models.TextChoices):
        COURSE = 'course', 'Курсовая работа'
        GRADUATE = 'graduate', 'Дипломная работа'

    class Status(models.TextChoices):
        FREE = 'free', 'Свободна'
        TAKEN = 'taken', 'Закреплена'

    title = models.CharField('название темы', max_length=300)
    direction = models.ForeignKey(
        Direction, on_delete=models.PROTECT, related_name='topics',
        verbose_name='направление',
    )
    supervisor = models.ForeignKey(
        Supervisor, on_delete=models.PROTECT, related_name='topics',
        verbose_name='руководитель',
    )
    proposed_by = models.ForeignKey(
        Student, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='proposed_topics',
        verbose_name='кто предложил (инициативная тема)',
        help_text='Заполняется для FR-14: студент предлагает свою тему',
    )
    work_type = models.CharField(
        'тип работы', max_length=10, choices=WorkType.choices,
        default=WorkType.COURSE,
    )
    academic_year = models.CharField(
        'учебный год', max_length=9, help_text='Формат 2026/2027',
    )
    status = models.CharField(
        'статус', max_length=10, choices=Status.choices, default=Status.FREE,
    )
    description = models.TextField('описание темы')
    created_at = models.DateTimeField(
        'дата добавления', default=timezone.now,
        help_text='Время создания записи в каталоге (сортировка FR-04)',
    )

    class Meta:
        verbose_name = 'тема работы'
        verbose_name_plural = 'темы работ'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status'], name='core_topic_status_idx'),
            models.Index(fields=['academic_year'], name='core_topic_year_idx'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'academic_year'],
                name='core_topic_title_year',
            ),
        ]

    def is_free(self):
        return self.status == self.Status.FREE

    def __str__(self):
        return self.title


class Application(models.Model):
    """Заявка студента на тему. Связующая таблица связи «студент — тема».

    Одна тема закрепляется только за одним студентом, и у студента
    может быть только одна одобренная тема — оба правила держат частичные
    уникальные индексы ниже. Проверять их вручную в каждой представлении
    не нужно: база сама не даст записать вторую одобренную заявку.
    """

    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Подана'
        IN_REVIEW = 'in_review', 'На рассмотрении'
        APPROVED = 'approved', 'Одобрена'
        REJECTED = 'rejected', 'Отклонена'
        WITHDRAWN = 'withdrawn', 'Отозвана'

    student = models.ForeignKey(
        Student, on_delete=models.PROTECT, related_name='applications',
        verbose_name='студент',
    )
    topic = models.ForeignKey(
        Topic, on_delete=models.PROTECT, related_name='applications',
        verbose_name='тема',
    )
    status = models.CharField(
        'статус заявки', max_length=12, choices=Status.choices,
        default=Status.SUBMITTED,
    )
    comment = models.TextField(
        'комментарий студента', blank=True,
        help_text='Пояснение студента, почему он хочет эту тему (FR-14)',
    )
    reject_reason = models.TextField(
        'причина отклонения', null=True, blank=True,
        help_text='Обязательна, когда руководитель отклоняет заявку (FR-11)',
    )
    submitted_at = models.DateTimeField('дата подачи', default=timezone.now)
    decided_at = models.DateTimeField('дата решения', null=True, blank=True)
    decided_by = models.ForeignKey(
        Supervisor, on_delete=models.PROTECT, null=True, blank=True,
        related_name='decisions', verbose_name='кто принял решение',
    )

    class Meta:
        verbose_name = 'заявка на тему'
        verbose_name_plural = 'заявки на темы'
        ordering = ['-submitted_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'topic'],
                name='core_application_student_topic',
            ),
            models.UniqueConstraint(
                fields=['topic'],
                condition=Q(status='approved'),
                name='core_application_one_approved_per_topic',
            ),
            models.UniqueConstraint(
                fields=['student'],
                condition=Q(status='approved'),
                name='core_application_one_approved_per_student',
            ),
            models.CheckConstraint(
                condition=(~Q(status='rejected')) | (
                    Q(reject_reason__isnull=False) & ~Q(reject_reason='')
                ),
                name='core_application_reject_reason_required',
            ),
        ]

    def __str__(self):
        return f'{self.student.full_name} — «{self.topic.title}» ({self.get_status_display()})'


class ApprovalOrder(models.Model):
    """Файл приказа о закреплении тем (FR-19). Один приказ на учебный год."""

    academic_year = models.CharField('учебный год', max_length=9, unique=True)
    file = models.FileField(
        'файл приказа', upload_to='orders/%Y/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'],
                message='Приказ можно прикрепить только в PDF, JPG или PNG.',
            ),
            validate_order_file_size,
        ],
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        blank=True, related_name='uploaded_orders', verbose_name='кто загрузил',
    )
    uploaded_at = models.DateTimeField('дата загрузки', default=timezone.now)
    note = models.CharField(
        'примечание', max_length=255, blank=True,
        help_text='Например: приказ № 312 от 01.12.2025, страницы 1–3',
    )

    class Meta:
        verbose_name = 'приказ о закреплении тем'
        verbose_name_plural = 'приказы о закреплении тем'
        ordering = ['-academic_year']

    def __str__(self):
        return f'Приказ за {self.academic_year} учебный год'
