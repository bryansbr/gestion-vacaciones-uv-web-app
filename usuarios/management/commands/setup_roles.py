from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from usuarios.models import CustomUser

class Command(BaseCommand):
    help = 'Crea los grupos de roles y asigna los permisos iniciales para el sistema'

    def handle(self, *args, **kwargs):
        ########## Definición de grupos ##########
        GRUPOS = [
            "Solicitante",
            "Jefe inmediato",
            "Coordinador administrativo",
            "Recursos Humanos",
        ]

        ########## Creación de grupos si no existen ##########
        for nombre_grupo in GRUPOS:
            group, created = Group.objects.get_or_create(name=nombre_grupo)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Grupo '{nombre_grupo}' creado."))
            else:
                self.stdout.write(f"Grupo '{nombre_grupo}' ya existe.")

        ########## Obtención de permisos necesarios ##########
        permiso_add_solicitud = Permission.objects.filter(codename__icontains='add_solicitudvacaciones')
        permiso_view_solicitud = Permission.objects.filter(codename__icontains='view_solicitudvacaciones')
        permiso_change_solicitud = Permission.objects.filter(codename__icontains='change_solicitudvacaciones')
        permiso_add_reintegro = Permission.objects.filter(codename__icontains='add_reintegrovacaciones')
        permiso_view_reintegro = Permission.objects.filter(codename__icontains='view_reintegrovacaciones')
        permiso_change_reintegro = Permission.objects.filter(codename__icontains='change_reintegrovacaciones')
        permiso_view_funcionario = Permission.objects.filter(codename__icontains='view_funcionario')
        permiso_view_historico = Permission.objects.filter(codename__icontains='view_historicoacciones')

        ########## Asignación de permisos a los grupos ##########

        # 1. Solicitante
        grupo_solicitante = Group.objects.get(name="Solicitante")
        grupo_solicitante.permissions.set(
            list(permiso_add_solicitud) + list(permiso_view_solicitud) + list(permiso_change_solicitud) +
            list(permiso_add_reintegro) + list(permiso_view_reintegro) + list(permiso_change_reintegro)
        )

        # 2. Jefe inmediato
        grupo_jefe = Group.objects.get(name="Jefe inmediato")
        grupo_jefe.permissions.set(
            list(permiso_view_solicitud) + list(permiso_change_solicitud) +
            list(permiso_view_reintegro) + list(permiso_change_reintegro) +
            list(permiso_view_funcionario) + list(permiso_view_historico)
        )

        # 3. Coordinador administrativo
        grupo_coordinador = Group.objects.get(name="Coordinador administrativo")
        grupo_coordinador.permissions.set(
            list(permiso_view_solicitud) + list(permiso_change_solicitud) +
            list(permiso_view_reintegro) + list(permiso_change_reintegro) +
            list(permiso_view_funcionario) + list(permiso_view_historico)
        )

        # 4. Recursos Humanos
        grupo_rrhh = Group.objects.get(name="Recursos Humanos")
        grupo_rrhh.permissions.set(
            list(permiso_view_solicitud) + list(permiso_change_solicitud) +
            list(permiso_view_reintegro) + list(permiso_change_reintegro) +
            list(permiso_view_funcionario) + list(permiso_view_historico)
        )

        self.stdout.write(self.style.SUCCESS("\nPermisos asignados correctamente a los grupos."))

        ########## Añadir todos los usuarios al grupo "Solicitante" si no están ##########
        usuarios = CustomUser.objects.all()

        for usuario in usuarios:
            if not usuario.groups.filter(name="Solicitante").exists():
                usuario.groups.add(grupo_solicitante)
                self.stdout.write(self.style.SUCCESS(f"Usuario {usuario.email} añadido al grupo 'Solicitante'."))

        self.stdout.write(self.style.SUCCESS("\n¡Configuración de roles completada con éxito!"))
