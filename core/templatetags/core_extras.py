"""Свои шаблонные фильтры для ФИО (аватар и подписи в шапке)."""
from django import template

register = template.Library()


@register.filter
def initials(fio):
    """Первые буквы фамилии и имени: «Ярочкин Максим Сергеевич» -> «ЯМ»."""
    words = (fio or '').split()
    if not words:
        return '?'
    first = words[0][0]
    second = words[1][0] if len(words) > 1 else ''
    return (first + second).upper()


@register.filter
def short_fio(fio):
    """Фамилия с инициалами: «Соколов Артём Дмитриевич» -> «Соколов А. Д.»."""
    words = (fio or '').split()
    if not words:
        return '—'
    rest = ' '.join(w[0] + '.' for w in words[1:3])
    return ' '.join([words[0], rest]) if rest else words[0]


@register.filter
def basename(path):
    """Имя файла без каталогов: «orders/2025/prikaz.pdf» -> «prikaz.pdf»."""
    return str(path or '').split('/')[-1]


@register.filter
def get_item(mapping, key):
    """Достаёт значение словаря по ключу в шаблоне: {{ mapping|get_item:key }}."""
    if mapping is None:
        return None
    return mapping.get(key)

