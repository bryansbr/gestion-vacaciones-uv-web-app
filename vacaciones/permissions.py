from .roles import FUNCIONARIO, SECRETARIA, JEFE, COORD, RRHH

def u_in(u, group_name: str) -> bool:
    """True si el usuario pertenece al grupo (o es superusuario)."""
    return u.is_superuser or u.groups.filter(name=group_name).exists()

def scope_queryset_for(u, qs):
    """Filtra listas según el rol del usuario."""
    if u_in(u, RRHH):
        return qs
    if u_in(u, COORD) or u_in(u, SECRETARIA):
        return qs.filter(funcionario__facultad_dependencia=u.funcionario.facultad_dependencia)
    if u_in(u, JEFE):
        return qs.filter(funcionario__jefe_inmediato=u.funcionario)

    return qs.filter(funcionario=u.funcionario)

def can_delete(u, obj) -> bool:
    """Reglas simples de borrado por rol + estado."""
    if obj.funcionario.user == u and obj.estado in ["BORRADOR", "PEND_JEFE", "DEVUELTA"]:
        return True
    if u_in(u, SECRETARIA) and obj.misma_dependencia(u) and obj.estado in ["BORRADOR", "PEND_JEFE", "DEVUELTA"]:
        return True
    if u_in(u, JEFE) and obj.bajo_jefe(u) and obj.estado in ["BORRADOR", "PEND_JEFE", "DEVUELTA"]:
        return True
    if u_in(u, COORD) and obj.propietario(u) and obj.estado in ["BORRADOR", "PEND_JEFE", "PEND_COORD", "DEVUELTA"]:
        return True
    if u_in(u, RRHH) and obj.propietario(u) and obj.estado != "AUTORIZADA":
        return True
    if u.is_superuser:
        return True
    return False

def next_action_allowed(u, obj, action: str) -> bool:
    """
    action in {"aprobar","devolver","rechazar"}.
    Define qué rol puede actuar sobre qué estado.
    """
    if action == "aprobar":
        return (
            (u_in(u, JEFE)  and obj.estado == "PEND_JEFE"  and obj.bajo_jefe(u)) or
            (u_in(u, COORD) and obj.estado == "PEND_COORD" and obj.misma_dependencia(u)) or
            (u_in(u, RRHH)  and obj.estado == "PEND_RRHH") or
            u.is_superuser
        )
    if action == "devolver":
        return (
            (u_in(u, JEFE)  and obj.estado == "PEND_JEFE"  and obj.bajo_jefe(u)) or
            (u_in(u, COORD) and obj.estado == "PEND_COORD" and obj.misma_dependencia(u)) or
            (u_in(u, RRHH)  and obj.estado in ["PEND_RRHH", "PEND_COORD", "PEND_JEFE"]) or
            u.is_superuser
        )
    if action == "rechazar":
        return (u_in(u, RRHH) and obj.estado == "PEND_RRHH") or u.is_superuser
    return False
