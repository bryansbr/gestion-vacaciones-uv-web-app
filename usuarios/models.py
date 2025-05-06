from datetime import date
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from core.models import Estamento, FacultadDependencia, Sede

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio.')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if not extra_fields.get('username'):
            extra_fields['username'] = email
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

class Funcionario(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='funcionario',
        verbose_name='Usuario'
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
        help_text="Solo para docentes ('1279' o '115')"
    )
    estamento = models.ForeignKey(
        Estamento,
        on_delete=models.PROTECT,
        related_name='funcionarios'
    )
    facultad_dependencia = models.ForeignKey(
        FacultadDependencia,
        on_delete=models.PROTECT,
        related_name='funcionarios'
    )
    sede = models.ForeignKey(
        Sede,
        on_delete=models.PROTECT,
        related_name='funcionarios'
    )

    def puede_solicitar_vacaciones(self):
        """
        Un funcionario puede solicitar vacaciones si:
         - Ha cumplido al menos 1 año en el cargo
         - O bien tiene días pendientes por reintegro anticipado
        """
        hoy = date.today()
        antiguedad = (hoy - self.fecha_ingreso_universidad).days >= 365
        tiene_pendientes = self.reintegros_vacaciones.filter(
            dias_pendientes__gt=0,
            estado_solicitud__in=['aprobado', 'cerrado']
        ).exists()
        
        return antiguedad or tiene_pendientes

    def estado_de_vacaciones(self):
        """
        Devuelve un resumen del estado:
         - antigüedad en días
         - si puede solicitar
         - datos de su último periodo vacacional
        """
        hoy = date.today()
        antiguedad_dias = (hoy - self.fecha_ingreso_universidad).days
        ultimo = self.periodos_vacacionales.order_by('-fecha_inicio_periodo').first()
        return {
            "antiguedad_dias": antiguedad_dias,
            "puede_solicitar": self.puede_solicitar_vacaciones(),
            "ultimo_periodo": {
                "id": ultimo.id,
                "dias_totales": ultimo.dias_totales_periodo,
                "dias_pendientes": ultimo.dias_pendientes_periodo,
                "dias_disfrutados": ultimo.dias_disfrutados_periodo,
            } if ultimo else None
        }

    @property
    def correo_electronico(self):
        return self.user.email if self.user else None

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.numero_identificacion})"

    class Meta:
        verbose_name = "Funcionario"
        verbose_name_plural = "Funcionarios"
