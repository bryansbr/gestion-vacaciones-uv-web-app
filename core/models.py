from django.db import models

class Estamento(models.Model):
    nombre = models.CharField(max_length=30, unique=True)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Estamento"
        verbose_name_plural = "Estamentos"

class FacultadDependencia(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Facultad - Dependencia"
        verbose_name_plural = "Facultades - Dependencias"

class Sede(models.Model):
    nombre = models.CharField(max_length=30, unique=True)
    direccion = models.TextField()

    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"
