from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """Adiciona classe CSS a um campo de formulário Django.
    Retorna o campo sem modificação se não for um BoundField válido.
    """
    try:
        return field.as_widget(attrs={'class': css_class})
    except AttributeError:
        return field


@register.filter(name='add_placeholder')
def add_placeholder(field, placeholder):
    try:
        existing = field.field.widget.attrs.get('class', '')
        return field.as_widget(attrs={'placeholder': placeholder, 'class': existing})
    except AttributeError:
        return field
