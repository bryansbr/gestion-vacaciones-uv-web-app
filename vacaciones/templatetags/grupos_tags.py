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

@register.filter(name='es_jefe_inmediato')
def es_jefe_inmediato(user):
    """
    Filtro de template que verifica si un usuario pertenece al grupo "Jefe Inmediato".
    """
    return has_group(user, "Jefe Inmediato")

@register.filter(name='es_coordinador_administrativo')
def es_coordinador_administrativo(user):
    """
    Filtro de template que verifica si un usuario pertenece al grupo "Coordinador Administrativo".
    """
    return has_group(user, "Coordinador Administrativo")

@register.filter(name='es_rrhh')
def es_rrhh(user):
    """
    Filtro de template que verifica si un usuario pertenece al grupo "Recursos Humanos".
    """
    return has_group(user, "Recursos Humanos")

@register.filter(name='es_funcionario')
def es_funcionario(user):
    """
    Filtro de template que verifica si un usuario es un funcionario regular
    (no es secretaria ni jefe inmediato).
    Nota: Coordinador Administrativo también puede acceder a funcionalidades de funcionario.
    """
    if not user or not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return False
    
    has_secretaria = user.groups.filter(name="Secretaria").exists()
    has_jefe = user.groups.filter(name="Jefe Inmediato").exists()
    
    return not has_secretaria and not has_jefe
