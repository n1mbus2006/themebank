"""Команда наполнения базы демонстрационными данными (занятие 5).

Запуск: python manage.py load_demo_data
Все ФИО, темы и номера документов вымышленные, данные демонстрационные.
Команда идемпотентная: перед загрузкой удаляет старые записи core.
"""
import datetime

from django.contrib.auth.hashers import make_password
# AuthGroup под псевдонимом: в core.models есть своя учебная Group,
# и без псевдонима группы ролей создались бы как учебные группы.
from django.contrib.auth.models import Group as AuthGroup, User
from django.core.management.base import BaseCommand
from django.utils import timezone


from core.models import (
    Application,
    ApprovalOrder,
    Direction,
    Group,
    Student,
    Supervisor,
    SupervisorLimit,
    Topic,
)

DEMO_PASSWORD = 'Demo2026!'


def dt(day, month, year=2026, hour=10, minute=0):
    """Момент времени в московской зоне — так даты в фикстуре читаются честно."""
    return datetime.datetime(
        year, month, day, hour, minute, tzinfo=timezone.get_current_timezone(),
    )


class Command(BaseCommand):
    help = 'Загружает демонстрационные данные банка тем (занятие 5)'

    def handle(self, *args, **options):
        # Чистим таблицы приложения, чтобы команду можно было запускать повторно.
        for model in (Application, Topic, SupervisorLimit, ApprovalOrder,
                      Student, Supervisor, Group, Direction, User):
            model.objects.all().delete()

        self.stdout.write('Создаю суперпользователя...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                'admin', 'admin@example.edu', 'Admin2026!',
            )
        admin_user = User.objects.get(username='admin')

        # Группы ролей (FR-20): доступ разграничивается через группы Django.
        self.stdout.write('Группы ролей...')
        group_student, _ = AuthGroup.objects.get_or_create(name='Студент')
        group_supervisor, _ = AuthGroup.objects.get_or_create(name='Руководитель')
        group_head, _ = AuthGroup.objects.get_or_create(name='Заведующий отделением')
        admin_user.groups.add(group_head)


        self.stdout.write('Направления и группы...')
        directions = [
            ('09.03.02', 'Информационные системы и технологии', Direction.LEVEL_BACHELOR),
            ('09.03.01', 'Информатика и вычислительная техника', Direction.LEVEL_BACHELOR),
            ('09.03.03', 'Прикладная информатика', Direction.LEVEL_BACHELOR),
            ('09.03.04', 'Программная инженерия', Direction.LEVEL_BACHELOR),
            ('09.04.01', 'Информатика и вычислительная техника', Direction.LEVEL_MASTER),
            ('09.02.07', 'Информационные системы и программирование', Direction.LEVEL_SPO),
        ]
        directions = [
            Direction.objects.create(code=code, title=title, level=level)
            for code, title, level in directions
        ]
        DIR_IS, DIR_IVT, DIR_PI, DIR_PING, DIR_MAG, DIR_SPO = directions

        groups = [
            ('ИСдо-45', DIR_SPO, 2022),
            ('ИСдо-46', DIR_SPO, 2023),
            ('ИСдо-47', DIR_SPO, 2024),
            ('ИСбо-41', DIR_IS, 2023),
            ('ИСбо-42', DIR_IS, 2024),
            ('ИВТ-21', DIR_IVT, 2025),
            ('ПИ-31', DIR_PI, 2024),
            ('ПИнж-31', DIR_PING, 2024),
            ('ПИ-11', DIR_MAG, 2025),
            ('ПИ-21', DIR_MAG, 2024),
        ]
        groups = [Group.objects.create(name=n, direction=d, enrollment_year=y)
                  for n, d, y in groups]
        G_SPO45, G_SPO46, G_SPO47, G_IS41, G_IS42, G_IVT, G_PI, G_PING, G_MAG1, G_MAG2 = groups

        self.stdout.write('Руководители...')
        supervisor_data = [
            ('i.petrov', 'Петров Игорь Владимирович', 'доцент', 'Кафедра информационных систем'),
            ('s.kuznetsova', 'Кузнецова Светлана Андреевна', 'профессор', 'Кафедра программной инженерии'),
            ('a.sokolov', 'Соколов Артём Дмитриевич', 'старший преподаватель', 'Кафедра информационных систем'),
            ('m.lebedeva', 'Лебедева Марина Олеговна', 'доцент', 'Кафедра прикладной математики и информатики'),
            ('d.kozlov', 'Козлов Денис Сергеевич', 'старший преподаватель', 'Кафедра программной инженерии'),
            ('e.novikova', 'Новикова Елена Витальевна', 'доцент', 'Кафедра информационных систем'),
            ('p.morozov', 'Морозов Павел Ильич', 'профессор', 'Кафедра прикладной математики и информатики'),
            ('o.volkova', 'Волкова Ольга Сергеевна', 'старший преподаватель', 'Кафедра программной инженерии'),
            ('a.zaytsev', 'Зайцев Андрей Николаевич', 'доцент', 'Кафедра информационных систем'),
            ('i.pavlova', 'Павлова Ирина Михайловна', 'преподаватель', 'Отделение информационных технологий'),
        ]
        supervisors = []
        for username, full_name, position, department in supervisor_data:
            user = User.objects.create(
                username=username,
                email=f'{username}@staff.example.edu',
                password=make_password(DEMO_PASSWORD),
                first_name=full_name.split()[0],
                last_name=' '.join(full_name.split()[1:]),
            )
            user.groups.add(group_supervisor)
            supervisors.append(Supervisor.objects.create(
                user=user, full_name=full_name, position=position,
                department=department,
            ))


        self.stdout.write('Студенты...')
        student_data = [
            ('a.stepanova', 'Степанова Анна Кирилловна', 'ИС-230114', G_SPO46),
            ('m.orlov', 'Орлов Максим Дмитриевич', 'ИС-230121', G_SPO46),
            ('p.kirillova', 'Кириллова Полина Егоровна', 'ИС-230133', G_SPO46),
            ('d.efimov', 'Ефимов Данила Романович', 'ИС-230145', G_SPO46),
            ('y.zakharova', 'Захарова Юлия Артёмовна', 'ИС-230150', G_SPO46),
            ('e.smirnov', 'Смирнов Егор Львович', 'ИС-230158', G_SPO46),
            ('d.ivanova', 'Иванова Дарья Максимовна', 'ИС-240102', G_SPO47),
            ('a.nikitin', 'Никитин Артём Валерьевич', 'ИС-240110', G_SPO47),
            ('v.grigoreva', 'Григорьева Вера Олеговна', 'ПИ-240025', G_PING),
            ('i.fedorov', 'Фёдоров Илья Константинович', 'ПИ-240031', G_PING),
            ('s.romanova', 'Романова Софья Игоревна', 'МГ-250012', G_MAG1),
            ('t.belov', 'Белов Тимофей Артурович', 'МГ-250018', G_MAG1),
        ]
        students = []
        for username, full_name, record_book, group in student_data:
            user = User.objects.create(
                username=username,
                email=f'{username}@students.example.edu',
                password=make_password(DEMO_PASSWORD),
                first_name=full_name.split()[0],
                last_name=' '.join(full_name.split()[1:]),
            )
            user.groups.add(group_student)
            students.append(Student.objects.create(
                user=user, full_name=full_name,
                record_book_number=record_book, group=group,
            ))

        # Мой аккаунт для показа кабинета студента (занятие 8): заявки
        # во всех основных статусах — «Подана», «На рассмотрении»,
        # «Отклонена» с причиной и «Отозвана».
        self.stdout.write('Аккаунт автора для показа кабинета студента...')
        me = User.objects.create(
            username='m.yarochkin',
            email='m.yarochkin@students.example.edu',
            password=make_password(DEMO_PASSWORD),
            first_name='Ярочкин',
            last_name='Максим Сергеевич',
        )
        me.groups.add(group_student)
        me_student = Student.objects.create(
            user=me, full_name='Ярочкин Максим Сергеевич',
            record_book_number='ИС-230160', group=G_SPO46,
        )
        students.append(me_student)

        # Заведующий отделением — учётная запись для страницы сводки (FR-17).
        self.stdout.write('Заведующий отделением...')
        head_user = User.objects.create(
            username='i.kuznetsov',
            email='i.kuznetsov@staff.example.edu',
            password=make_password(DEMO_PASSWORD),
            first_name='Кузнецов',
            last_name='Игорь Павлович',
        )
        head_user.groups.add(group_head)


        self.stdout.write('Лимиты руководителей на 2026/2027...')
        max_by_supervisor = [5, 4, 4, 3, 3, 3, 4, 3, 5, 3]
        for supervisor, max_students in zip(supervisors, max_by_supervisor):
            SupervisorLimit.objects.create(
                supervisor=supervisor, academic_year='2026/2027',
                max_students=max_students,
            )

        self.stdout.write('Темы (40 шт., 10 закреплены)...')
        # (название, направление, руководитель, тип работы, статус)
        topic_data = [
            ('Разработка веб-сервиса бронирования учебных аудиторий на Django', DIR_SPO, 0, Topic.WorkType.GRADUATE, Topic.Status.TAKEN),
            ('Интеллектуальная классификация обращений в техподдержку с использованием больших языковых моделей', DIR_SPO, 0, Topic.WorkType.GRADUATE, Topic.Status.TAKEN),
            ('Автоматизация учёта заявок лаборатории колледжа средствами Django ORM', DIR_SPO, 0, Topic.WorkType.GRADUATE, Topic.Status.TAKEN),
            ('Прогнозирование успеваемости студентов на основе данных электронного журнала', DIR_SPO, 1, Topic.WorkType.GRADUATE, Topic.Status.TAKEN),
            ('Веб-платформа олимпиадных задач с автоматической проверкой решений на Python', DIR_SPO, 1, Topic.WorkType.GRADUATE, Topic.Status.TAKEN),
            ('Разработка мобильного приложения навигации по учебному корпусу', DIR_SPO, 2, Topic.WorkType.GRADUATE, Topic.Status.TAKEN),
            ('Анализ уязвимостей REST API учебного сервиса и способы их устранения', DIR_SPO, 2, Topic.WorkType.COURSE, Topic.Status.TAKEN),
            ('Система учёта инвентаря компьютерных классов с QR-метками', DIR_SPO, 3, Topic.WorkType.COURSE, Topic.Status.TAKEN),
            ('Панель показателей успеваемости для заведующего отделением', DIR_PING, 4, Topic.WorkType.COURSE, Topic.Status.TAKEN),
            ('Чат-бот расписания занятий на платформе мессенджера MAX', DIR_PING, 5, Topic.WorkType.COURSE, Topic.Status.TAKEN),
            ('Telegram-бот напоминаний о сроках сдачи учебных работ', DIR_SPO, 6, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Мониторинг компьютера класса на Raspberry Pi с выводом метрик', DIR_SPO, 7, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Лендинг приёмной комиссии с формой записи на дни открытых дверей', DIR_SPO, 8, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Анализ тональности отзывов студентов о преподавателях', DIR_SPO, 9, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Визуализация расписания группы в виде канбан-доски', DIR_SPO, 0, Topic.WorkType.GRADUATE, Topic.Status.FREE),
            ('Хранилище учебных материалов с версиями на Django и SQLite', DIR_SPO, 1, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Сервис проверки лабораторных работ на совпадения по метаданным', DIR_SPO, 2, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Генератор индивидуальных заданий по SQL для практики', DIR_SPO, 3, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Веб-сервис подбора наставников для первокурсников', DIR_SPO, 4, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Электронный стенд «История отделения» на MapLibre', DIR_SPO, 5, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Разработка REST API мобильного расписания занятий', DIR_IS, 6, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Сравнение SQLite и PostgreSQL в учебном проекте на Django', DIR_IS, 7, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Автоматизация проверки каталога тем тестами на Selenium', DIR_IS, 8, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('ИИ-подсказки формулировок тем курсовых работ', DIR_IS, 9, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Система обратной связи по практическим заданиям', DIR_IS, 0, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Сервис подтверждения авторства учебных работ', DIR_IS, 1, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Мониторинг PageSpeed учебного портала с автоматическими отчётами', DIR_IVT, 2, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Разработка плагина VS Code для учебного репозитория', DIR_IVT, 3, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Анализ журналов сервера Django средствами Prometheus', DIR_IVT, 4, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Кэширование каталога тем для ускорения отдачи страниц', DIR_IVT, 5, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Настольный календарь дедлайнов для учебной группы', DIR_IVT, 6, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Голосовой ассистент навигации для слабовидящих студентов', DIR_PI, 7, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Тема оформления для учебной CMS отделения', DIR_PI, 8, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Переход от монолита к микросервисам на учебном примере', DIR_PI, 9, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Аутентификация по QR-коду в учебной сети колледжа', DIR_PI, 0, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Сравнение Django и FastAPI на типовом учебном проекте', DIR_PING, 1, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Дополненная реальность в подсказках лаборатории электроники', DIR_PING, 2, Topic.WorkType.COURSE, Topic.Status.FREE),
            ('Оптимизация SQL-запросов каталога тем и индексов', DIR_MAG, 3, Topic.WorkType.GRADUATE, Topic.Status.FREE),
            ('Обмен в реальном времени на Django Channels для уведомлений', DIR_MAG, 4, Topic.WorkType.GRADUATE, Topic.Status.FREE),
            ('Дашборд ресурсов компьютерного кластера колледжа', DIR_MAG, 5, Topic.WorkType.GRADUATE, Topic.Status.FREE),
        ]
        topics = []
        base_date = dt(1, 9, hour=9)
        for i, (title, direction, sup_idx, work_type, status) in enumerate(topic_data):
            # Новые темы добавили позже — сортировка по дате будет наглядной.
            created = base_date + datetime.timedelta(hours=i * 3)
            if i >= 37:
                created = dt(8, 11, hour=9 + (i - 37))
            topics.append(Topic.objects.create(
                title=title, direction=direction, supervisor=supervisors[sup_idx],
                work_type=work_type, academic_year='2026/2027',
                status=status, description=(
                    f'Демонстрационная тема {i + 1}. Работа включает разработку и '
                    'исследование в рамках выбранного направления, защиту в конце семестра.'
                ),
                created_at=created,
            ))

        self.stdout.write('Заявки (20 шт.: 10 одобрено, 3 поданы, 1 на рассмотрении, 3 отклонено, 3 отозвано)...')
        # Одобренные заявки: студенты 1–10 закрепили темы 1–10.
        approved = [
            (0, 0, dt(20, 10, hour=10), dt(23, 10), 'Пишу на Django с прошлого курса, хочу продолжить проект.'),
            (1, 1, dt(20, 10, hour=11, minute=15), dt(23, 10, hour=12), ''),
            (2, 2, dt(21, 10, hour=9, minute=40), dt(27, 10), 'Работаю в службе техподдержки колледжа, есть доступ к данным.'),
            (3, 3, dt(22, 10, hour=14, minute=20), dt(29, 10), ''),
            (4, 4, dt(23, 10, hour=10, minute=5), dt(30, 10), 'Участвую в олимпиадах по программированию.'),
            (5, 5, dt(27, 10, hour=16, minute=30), dt(3, 11), ''),
            (6, 6, dt(28, 10, hour=9, minute=10), dt(4, 11), 'Прошёл практику по информационной безопасности.'),
            (7, 7, dt(28, 10, hour=12, minute=45), dt(4, 11, hour=13), ''),
            (8, 8, dt(3, 11, hour=10, minute=30), dt(6, 11), 'Готовлю панель показателей для своего диплома.'),
            (9, 9, dt(4, 11, hour=11), dt(10, 11), ''),
        ]
        applications = []
        for s_idx, t_idx, submitted, decided, comment in approved:
            topic = topics[t_idx]
            applications.append(Application.objects.create(
                student=students[s_idx], topic=topic,
                status=Application.Status.APPROVED, comment=comment,
                submitted_at=submitted, decided_at=decided,
                decided_by=topic.supervisor,
            ))

        # Отклонённые заявки с обязательной причиной (проверка CheckConstraint).
        rejected = [
            (10, 28, dt(29, 10, hour=15), dt(31, 10, hour=10, minute=30),
             'Тема рассчитана на бакалавриат, выберите тему из магистерского списка.'),
            (11, 27, dt(29, 10, hour=16, minute=20), dt(2, 11, hour=11),
             'Тема пока не согласована для магистратуры, предложу её в следующем наборе.'),
        ]
        for s_idx, t_idx, submitted, decided, reason in rejected:
            topic = topics[t_idx]
            applications.append(Application.objects.create(
                student=students[s_idx], topic=topic,
                status=Application.Status.REJECTED, reject_reason=reason,
                submitted_at=submitted, decided_at=decided,
                decided_by=topic.supervisor,
            ))

        # Отозванные студентом заявки.
        withdrawn = [
            (9, 14, dt(20, 10, hour=10, minute=30), dt(21, 10, hour=9),
             'Передумал, тема окажется слишком похожей на прошлый проект.'),
            (10, 29, dt(27, 10, hour=13), dt(3, 11, hour=12, minute=30),
             'Нашёл тему, которая ближе к диссертационным планам.'),
        ]
        for s_idx, t_idx, submitted, decided, comment in withdrawn:
            applications.append(Application.objects.create(
                student=students[s_idx], topic=topics[t_idx],
                status=Application.Status.WITHDRAWN, comment=comment,
                submitted_at=submitted, decided_at=decided,
            ))

        # Активные заявки в статусе «Подана» — их рассматривает руководитель.
        submitted = [
            (10, 38, dt(14, 11, hour=10), ''),
            (11, 37, dt(14, 11, hour=11, minute=30),
             'Занимаюсь оптимизацией запросов на своей прошлой работе.'),
        ]
        for s_idx, t_idx, submitted_at, comment in submitted:
            applications.append(Application.objects.create(
                student=students[s_idx], topic=topics[t_idx],
                status=Application.Status.SUBMITTED, comment=comment,
                submitted_at=submitted_at,
            ))

        # Заявки автора проекта — кабинет студента в отчётах занятий 8-9
        # показывают все основные статусы: подана, на рассмотрении,
        # отклонена (с причиной) и отозвана.
        self.stdout.write('Заявки автора для кабинета студента...')
        me_applications = [
            # Заявка в статусе «Подана» — на свободную магистерскую тему.
            (37, Application.Status.SUBMITTED, dt(14, 11, hour=11, minute=30), '', None, None, ''),
            # Заявка «На рассмотрении» — Соколов её взял в работу.
            (26, Application.Status.IN_REVIEW, dt(15, 11, hour=9, minute=12),
             'Делаю метрики на работе, тема по специальности.', None, None, ''),
            # Отклонённая заявка с причиной: тема дипломная, а нужен курсовой уровень.
            (1, Application.Status.REJECTED, dt(12, 11, hour=16, minute=40),
             '', dt(13, 11, hour=10), topics[1].supervisor,
             'Тема рассчитана на выпускную работу, выберите курсовую из списка.'),
            # Отозванная студентом заявка.
            (10, Application.Status.WITHDRAWN, dt(11, 11, hour=10), '',
             None, None, 'Передумал: подал заявку на тему по оптимизации запросов.'),
        ]
        for t_idx, status, submitted_at, comment, decided_at, decided_by, reason in me_applications:
            applications.append(Application.objects.create(
                student=me_student, topic=topics[t_idx], status=status,
                comment=comment, reject_reason=reason or None,
                submitted_at=submitted_at, decided_at=decided_at,
                decided_by=decided_by,
            ))


        self.stdout.write('Приказ за прошлый учебный год...')
        pdf_path = ApprovalOrder._meta.get_field('file').storage.generate_filename(
            'orders/2025/prikaz_2025-2026.pdf',
        )
        full_path = ApprovalOrder._meta.get_field('file').storage.path(pdf_path)
        import os
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        write_demo_pdf(full_path)
        ApprovalOrder.objects.create(
            academic_year='2025/2026', file=pdf_path,
            uploaded_by=admin_user, uploaded_at=dt(10, 12, year=2025, hour=12),
            note='Приказ № 312 от 01.12.2025 — демонстрационный образец для страницы сводки',
        )

        # Контрольная сверка особого требования.
        approved_count = Application.objects.filter(status=Application.Status.APPROVED).count()
        taken_count = Topic.objects.filter(status=Topic.Status.TAKEN).count()
        assert approved_count == taken_count, 'Число одобренных заявок должно совпадать с числом занятых тем'
        self.stdout.write(self.style.SUCCESS(
            f'Готово: направлений {Direction.objects.count()}, групп {Group.objects.count()}, '
            f'руководителей {Supervisor.objects.count()}, студентов {Student.objects.count()}, '
            f'лимитов {SupervisorLimit.objects.count()}, тем {Topic.objects.count()}, '
            f'заявок {Application.objects.count()}, приказов {ApprovalOrder.objects.count()}'
        ))


def write_demo_pdf(path):
    """Минимальный одностраничный PDF — файл приказа для демонстрации."""
    text = 'PRIKAZ o zakreplenii tem za 2025/2026 uchebnyy god (demonstratsionnyy obrazets)'
    stream = f'BT /F1 12 Tf 60 780 Td ({text}) Tj ET'.encode('cp1252', errors='replace')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        b'<< /Length %d >>\nstream\n%s\nendstream' % (len(stream), stream),
    ]
    out = bytearray(b'%PDF-1.4\n')
    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f'{i} 0 obj\n'.encode() + body + b'\nendobj\n'
    xref_pos = len(out)
    out += f'xref\n0 {len(objects) + 1}\n'.encode()
    out += b'0000000000 65535 f \n'
    for offset in offsets:
        out += f'{offset:010d} 00000 n \n'.encode()
    out += (f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n'
            f'startxref\n{xref_pos}\n%%EOF').encode()
    with open(path, 'wb') as fh:
        fh.write(out)
