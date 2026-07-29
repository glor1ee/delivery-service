from django import template

register = template.Library()


@register.filter
def elided_range(paginator, page_number):
    """Номера страниц с многоточиями: 1 2 … 7 8 9 … 19 20.

    Обёртка над Paginator.get_elided_page_range — в шаблоне нельзя вызвать
    метод с аргументами, поэтому нужен фильтр.
    """
    return paginator.get_elided_page_range(page_number, on_each_side=1, on_ends=1)
