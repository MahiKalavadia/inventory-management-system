from django import template

register = template.Library()


@register.filter
def split(value, sep=","):
    """Splits the string by separator"""
    if not value:
        return []
    return value.split(sep)
