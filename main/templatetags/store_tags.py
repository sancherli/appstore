from django import template

register = template.Library()

@register.filter
def stars(value):
    full = int(value)
    return '★' * full + '☆' * (5 - full)
