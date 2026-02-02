from django import template

register = template.Library()


@register.filter
def notif_color(notif_type):
    colors = {
        'product': 'success',
        'category': 'info',
        'supplier': 'primary',
        'order': 'dark',
        'stock': 'warning text-dark',
        'purchase': 'secondary',
    }
    return colors.get(notif_type, 'secondary')
