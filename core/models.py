from django.db import models

"""
class Catalogo(models.Model):
    tipo_catalogo = models.CharField(max_length=50) # 'estamento', 'facultad_dependencia'
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.tipo_catalogo} - {self.nombre}"
    
class Sede(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre
    
class DiaFestivoColombia(models.Model):
    fecha_festivo = models.DateField(unique=True)
    descripcion = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"{self.fecha_festivo}: {self.descripcion}"
"""
