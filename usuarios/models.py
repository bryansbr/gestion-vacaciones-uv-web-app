from django.db import models
from core.models import Catalogo, Sede

class Funcionario(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    numero_identificacion = models.CharField(max_length=50, unique=True)
    correo_electronico = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20)
    fecha_ingreso_universidad = models.DateField()

    estamento = models.ForeignKey(Catalogo, on_delete=models.PROTECT, related_name='funcionarios_estamento')
    facultad_dependencia = models.ForeignKey(Catalogo, on_delete=models.PROTECT, related_name='funcionarios_facultad_dependencia')
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
