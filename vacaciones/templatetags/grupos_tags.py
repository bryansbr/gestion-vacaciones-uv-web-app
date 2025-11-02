from django import template

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """
    Filtro de template que verifica si un usuario pertenece a un grupo específico.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    return user.groups.filter(name=group_name).exists()

@register.filter(name='es_secretaria')
def es_secretaria(user):
    """
    Filtro de template que verifica si un usuario pertenece al grupo "Secretaria".
    """
    return has_group(user, "Secretaria")
