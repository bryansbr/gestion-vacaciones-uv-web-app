from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from vacaciones.roles import ALL

class Command(BaseCommand):
    help = "Limpia (deja en blanco) los permisos de los grupos canónicos."

    def handle(self, *args, **kwargs):
        for name in ALL:
            g, _ = Group.objects.get_or_create(name=name)
            count = g.permissions.count()
            g.permissions.clear()
            self.stdout.write(self.style.SUCCESS(f"{name}: {count} permisos removidos."))
        self.stdout.write(self.style.SUCCESS("Grupos sin permisos."))
