from django.db import models

class Estamento(models.Model):
    nombre = models.CharField(max_length=30, unique=True)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

class FacultadDependencia(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre

class Sede(models.Model):
    nombre = models.CharField(max_length=30, unique=True)
    direccion = models.TextField()

    def __str__(self):
        return self.nombre
