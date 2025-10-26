from django import template

register = template.Library()

@register.filter
def has_group(user, group_name: str) -> bool:
    """
    Uso en templates:  {{ request.user|has_group:"Jefe Inmediato" }}
    """
    if not getattr(user, "is_authenticated", False):
        return False
    try:
        return user.groups.filter(name=group_name).exists()
    except Exception:
        return False
