from django.db import models
#from django.contrib.auth.models import User, AbstractUser
#from django.conf import settings 
#from core.models import Catalogo, Sede

"""
class CustomUser(AbstractUser):
    #Modelo de usuario personalizado.
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class Funcionario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    numero_identificacion = models.CharField(max_length=50, unique=True)
    telefono = models.CharField(max_length=20)
    fecha_ingreso_universidad = models.DateField()
    decreto_resolucion = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Código de resolución para docentes ('1279' o '115')"
    )

    estamento = models.ForeignKey(Catalogo, on_delete=models.PROTECT, related_name='funcionarios_estamento')
    facultad_dependencia = models.ForeignKey(Catalogo, on_delete=models.PROTECT, related_name='funcionarios_facultad_dependencia')
    sede = models.ForeignKey(Sede, on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"
    
    @property
    def correo_electronico(self):
        #Devuelve el email que se encuentra en el modelo CustomUser asociado.
        return self.user.email if self.user else None
"""
    