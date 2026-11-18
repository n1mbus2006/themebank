"""Формы занятий 9: заявка, отклонение, лимит, приказ.

Вся проверка занятости темы и лимита — на сервере (особое требование
варианта), клиентская валидация её не отменяет.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

from .models import Application, ApprovalOrder, SupervisorLimit, Topic

COMMENT_MAX = 500
REASON_MAX = 500


class ApplicationForm(forms.ModelForm):
    """Заявка студента на тему (FR-06): необязательный комментарий.

    Объект темы передаётся в конструктор, потому что проверки clean()
    смотрят именно на её состояние на момент отправки формы.
    """

    class Meta:
        model = Application
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'maxlength': COMMENT_MAX,
                'data-validate': 'maxlen:500',
                'placeholder': 'Например: хочу заниматься базами данных, есть опыт с PostgreSQL',
            }),
        }

    def __init__(self, *args, topic=None, student=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.topic = topic
        self.student = student

    def clean_comment(self):
        # Браузерный maxlength обрезает ввод не во всех браузерах,
        # поэтому дублирую проверку длины на сервере.
        comment = self.cleaned_data.get('comment', '')
        if len(comment) > COMMENT_MAX:
            raise ValidationError(
                f'Комментарий длиннее {COMMENT_MAX} символов, сократите его.'
            )
        return comment

    def clean(self):
        """Проверки особого требования варианта (FR-07, FR-08)."""
        cleaned = super().clean()

        if Application.objects.filter(
            student=self.student, topic=self.topic,
        ).exclude(status=Application.Status.WITHDRAWN).exists():
            raise ValidationError('Вы уже подавали заявку на эту тему.')

        if self.topic and not self.topic.is_free():
            raise ValidationError('Тема уже закреплена за другим студентом.')

        if self.topic:
            limit = SupervisorLimit.objects.filter(
                supervisor=self.topic.supervisor,
                academic_year=self.topic.academic_year,
            ).first()
            if limit is None:
                raise ValidationError(
                    'У руководителя не задан лимит на этот учебный год, '
                    'обратитесь к заведующему отделением.'
                )
            if limit.remaining() <= 0:
                raise ValidationError(
                    'Остаток лимита руководителя — 0. Выберите другую тему.'
                )
        return cleaned


class RejectForm(forms.Form):
    """Отклонение заявки руководителем (FR-11): причина обязательна.

    Ограничение «без причины отклонять нельзя» уже стоит в базе
    (CheckConstraint из занятия 5), форма повторяет его для дружелюбной
    ошибки вместо IntegrityError.
    """

    reason = forms.CharField(
        label='Причина отклонения',
        max_length=REASON_MAX,
        widget=forms.Textarea(attrs={'rows': 3, 'data-validate': 'required,maxlen:500'}),
        error_messages={'required': 'Укажите причину отклонения — без неё студент не поймёт отказ.'},
    )


class LimitForm(forms.ModelForm):
    """Правка лимита руководителя заведующим отделением (FR-22).

    Диапазон 1-30 задан и в базе (CheckConstraint), и здесь — чтобы
    форма показывала понятную ошибку, а не падение сохранения.
    """

    max_students = forms.IntegerField(
        label='Максимум студентов',
        validators=[MinValueValidator(1), MaxValueValidator(30)],
        error_messages={
            'required': 'Укажите новое значение лимита.',
            'invalid': 'Лимит — целое число.',
        },
        widget=forms.NumberInput(attrs={'data-validate': 'required,int,range:1-30'}),
    )

    class Meta:
        model = SupervisorLimit
        fields = ['max_students']


class OrderUploadForm(forms.ModelForm):
    """Загрузка файла приказа (FR-19): PDF/JPG/PNG до 5 МБ (NFR-09).

    Проверки типа и размера уже живут на модели (занятие 5), форма
    только выводит их ошибки рядом с полем.
    """

    note = forms.CharField(
        label='Примечание',
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Например: приказ № 312 от 01.12.2025, страницы 1–3',
            'data-validate': 'maxlen:255',
        }),
    )

    class Meta:
        model = ApprovalOrder
        fields = ['file', 'note']
        widgets = {
            'file': forms.FileInput(attrs={
                'accept': '.pdf,.jpg,.jpeg,.png',
                'data-validate': 'filetype:pdf,jpg,jpeg,png,filesize:5',
            }),
        }
