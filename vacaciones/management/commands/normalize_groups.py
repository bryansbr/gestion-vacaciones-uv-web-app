from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction

ALIASES = {
    "Solicitante": "Funcionario",
    "Recursos Humanos": "RRHH",
    "Coordinador administrativo": "Coordinador Administrativo",
    "Coordinación Administrativa": "Coordinador Administrativo",
    "Jefe inmediato": "Jefe Inmediato",
}

CANONICALS = {"Funcionario", "Secretaria", "Jefe Inmediato", "Coordinador Administrativo", "RRHH"}

class Command(BaseCommand):
    help = "Normaliza nombres de grupos: consolida alias en los canónicos y elimina duplicados."

    def move_members_and_perms(self, src: Group, dst: Group):
        for u in src.user_set.all():
            dst.user_set.add(u)
        for p in src.permissions.all():
            dst.permissions.add(p)

    @transaction.atomic
    def handle(self, *args, **kwargs):
        for name in CANONICALS:
            Group.objects.get_or_create(name=name)

        for alias, canonical in ALIASES.items():
            try:
                src = Group.objects.get(name=alias)
            except Group.DoesNotExist:
                continue
            dst = Group.objects.get(name=canonical)
            if src.id == dst.id:
                continue
            self.move_members_and_perms(src, dst)
            src.delete()
            self.stdout.write(self.style.SUCCESS(f"Alias '{alias}' -> '{canonical}' consolidado."))

        variants = [
            "Jefe Inmediato", "jefe inmediato", "Jefe inmediato", "Jefe Inmediato ",
            "Coordinacion Administrativa",
            "Coordinación Administrativa ",
            "Coordinador administrativo"
            "RRHH ", "rrhh", "Recursos humanos",
        ]
        norm = {
            "Jefe Inmediato": "Jefe Inmediato",
            "jefe inmediato": "Jefe Inmediato",
            "Jefe inmediato": "Jefe Inmediato",
            "Jefe Inmediato ": "Jefe Inmediato",
            "Coordinacion Administrativa": "Coordinador Administrativo",
            "Coordinación Administrativa ": "Coordinador Administrativo",
            "Coordinador administrativo" : "Coordinador Administrativo",
            "RRHH ": "RRHH",
            "rrhh": "RRHH",
            "Recursos humanos": "RRHH",
        }
        for name in variants:
            try:
                src = Group.objects.get(name=name)
            except Group.DoesNotExist:
                continue
            canonical = norm[name]
            dst = Group.objects.get(name=canonical)
            if src.id == dst.id:
                continue
            self.move_members_and_perms(src, dst)
            src.delete()
            self.stdout.write(self.style.SUCCESS(f"Variante '{name}' -> '{canonical}' consolidada."))

        leftovers = Group.objects.exclude(name__in=CANONICALS)
        if leftovers.exists():
            names = ", ".join(leftovers.values_list("name", flat=True))
            self.stdout.write(self.style.WARNING(f"Grupos no canónicos aún presentes: {names}"))
        else:
            self.stdout.write(self.style.SUCCESS("Normalización completa. Solo quedan grupos canónicos."))
