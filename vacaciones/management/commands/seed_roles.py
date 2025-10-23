from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from vacaciones import roles

class Command(BaseCommand):
    help = "Crea/verifica grupos canónicos para el MVP"

    def handle(self, *args, **kwargs):
        for name in roles.ALL:
            Group.objects.get_or_create(name=name)
        self.stdout.write(self.style.SUCCESS("Grupos canónicos creados/verificados."))
