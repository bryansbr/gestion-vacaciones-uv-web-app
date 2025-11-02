from django.contrib.auth.decorators import user_passes_test

def group_required(*group_names):
    def in_groups(u):
        if u.is_authenticated:
            if bool(u.groups.filter(name__in=group_names)) or u.is_superuser:
                return True
        return False
    return user_passes_test(in_groups)


def es_secretaria(user) -> bool:
    """
    Verifica si el usuario pertenece al grupo "Secretaria".
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name="Secretaria").exists()
