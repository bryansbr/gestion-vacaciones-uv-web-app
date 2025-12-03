"""
Helpers y fixtures comunes para las pruebas del módulo de vacaciones.
"""
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from usuarios.models import Funcionario
from core.models import Estamento, FacultadDependencia, Sede
from vacaciones.models import PeriodoVacacional

User = get_user_model()

class BaseTestCaseMixin:
    """Mixin base con setup común para todas las pruebas."""
    
    @classmethod
    def setUpTestData(cls):
        """Crea datos comunes para todas las pruebas."""
        cls.estamento_admin = Estamento.objects.create(
            nombre="Administrativo", 
            descripcion="Administrativo"
        )
        cls.estamento_docente = Estamento.objects.create(
            nombre="Docente", 
            descripcion="Docente"
        )
        cls.estamento_trabajador = Estamento.objects.create(
            nombre="Trabajador Oficial", 
            descripcion="Trabajador Oficial"
        )
        
        cls.facultad = FacultadDependencia.objects.create(
            nombre="Facultad de Pruebas", 
            descripcion="Facultad para pruebas"
        )
        
        cls.sede = Sede.objects.create(
            nombre="Sede Central", 
            direccion="Calle 123"
        )
        
        cls.user = User.objects.create_user(
            email="test@test.com", 
            password="test123"
        )
        
        cls.funcionario_admin = Funcionario.objects.create(
            user=cls.user,
            nombre="Funcionario",
            apellido="Prueba",
            numero_identificacion="123456789",
            telefono="3000000000",
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            estamento=cls.estamento_admin,
            facultad_dependencia=cls.facultad,
            sede=cls.sede,
        )
        
        cls.periodo_admin = PeriodoVacacional.objects.create(
            funcionario=cls.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )

def crear_funcionario_docente_1279():
    """Helper para crear funcionario docente con decreto 1279."""
    user = User.objects.create_user(
        email="docente1279@test.com",
        password="test123"
    )
    estamento = Estamento.objects.get_or_create(
        nombre="Docente",
        defaults={"descripcion": "Docente"}
    )[0]
    facultad = FacultadDependencia.objects.get_or_create(
        nombre="Facultad Docente",
        defaults={"descripcion": "Facultad"}
    )[0]
    sede = Sede.objects.get_or_create(
        nombre="Sede Central",
        defaults={"direccion": "Calle 123"}
    )[0]
    
    funcionario = Funcionario.objects.create(
        user=user,
        nombre="Docente",
        apellido="1279",
        numero_identificacion="DOC1279",
        telefono="3000000001",
        fecha_ingreso_universidad=date.today() - timedelta(days=500),
        decreto_resolucion="1279",
        estamento=estamento,
        facultad_dependencia=facultad,
        sede=sede,
    )
    return funcionario

def crear_funcionario_docente_115():
    """Helper para crear funcionario docente con decreto 115."""
    user = User.objects.create_user(
        email="docente115@test.com",
        password="test123"
    )
    estamento = Estamento.objects.get_or_create(
        nombre="Docente",
        defaults={"descripcion": "Docente"}
    )[0]
    facultad = FacultadDependencia.objects.get_or_create(
        nombre="Facultad Docente",
        defaults={"descripcion": "Facultad"}
    )[0]
    sede = Sede.objects.get_or_create(
        nombre="Sede Central",
        defaults={"direccion": "Calle 123"}
    )[0]
    
    funcionario = Funcionario.objects.create(
        user=user,
        nombre="Docente",
        apellido="115",
        numero_identificacion="DOC115",
        telefono="3000000002",
        fecha_ingreso_universidad=date.today() - timedelta(days=500),
        decreto_resolucion="115",
        estamento=estamento,
        facultad_dependencia=facultad,
        sede=sede,
    )
    return funcionario

def crear_funcionario_trabajador_oficial():
    """Helper para crear funcionario trabajador oficial."""
    user = User.objects.create_user(
        email="trabajador@test.com",
        password="test123"
    )
    estamento = Estamento.objects.get_or_create(
        nombre="Trabajador Oficial",
        defaults={"descripcion": "Trabajador Oficial"}
    )[0]
    facultad = FacultadDependencia.objects.get_or_create(
        nombre="Facultad Trabajador",
        defaults={"descripcion": "Facultad"}
    )[0]
    sede = Sede.objects.get_or_create(
        nombre="Sede Central",
        defaults={"direccion": "Calle 123"}
    )[0]
    
    funcionario = Funcionario.objects.create(
        user=user,
        nombre="Trabajador",
        apellido="Oficial",
        numero_identificacion="TRAB001",
        telefono="3000000003",
        fecha_ingreso_universidad=date.today() - timedelta(days=500),
        estamento=estamento,
        facultad_dependencia=facultad,
        sede=sede,
    )
    return funcionario

def crear_grupo_y_usuario(nombre_grupo, email):
    """Helper para crear grupo y usuario con ese grupo."""
    grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
    user = User.objects.create_user(email=email, password="test123")
    grupo.user_set.add(user)
    return user, grupo
