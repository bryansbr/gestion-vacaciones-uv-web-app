from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.models import Estamento, FacultadDependencia, Sede
from notificaciones.models import Notificacion
from usuarios.models import Funcionario
from vacaciones.models import PeriodoVacacional, SolicitudVacaciones, ReintegroVacaciones

class NotificacionModeloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estamento = Estamento.objects.create(nombre="Administrativo", descripcion="Admin")
        cls.facultad = FacultadDependencia.objects.create(nombre="Facultad X", descripcion="Desc")
        cls.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle 123")

        User = get_user_model()
        cls.usuario_principal = User.objects.create_user(email="principal@test.com", password="pwd")
        cls.funcionario_principal = Funcionario.objects.create(
            user=cls.usuario_principal,
            nombre="Ana",
            apellido="Principal",
            numero_identificacion="1000",
            telefono="3000000000",
            fecha_ingreso_universidad=date.today() - timedelta(days=400),
            estamento=cls.estamento,
            facultad_dependencia=cls.facultad,
            sede=cls.sede,
        )

        cls.usuario_secundario = User.objects.create_user(email="secundario@test.com", password="pwd")
        cls.funcionario_secundario = Funcionario.objects.create(
            user=cls.usuario_secundario,
            nombre="Luis",
            apellido="Secundario",
            numero_identificacion="2000",
            telefono="3000000001",
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            estamento=cls.estamento,
            facultad_dependencia=cls.facultad,
            sede=cls.sede,
        )

        cls.periodo = PeriodoVacacional.objects.create(
            funcionario=cls.funcionario_principal,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )

        cls.solicitud = SolicitudVacaciones.objects.create(
            funcionario=cls.funcionario_principal,
            periodo_vacacional=cls.periodo,
            fecha_inicio_vacaciones=date.today() + timedelta(days=10),
            fecha_fin_vacaciones=date.today() + timedelta(days=20),
            tiene_dias_pendientes=False,
            creada_por=cls.usuario_principal,
        )
        cls.solicitud.aprobaciones.filter(etapa='RRHH').update(estado='autorizada')

        cls.reintegro = ReintegroVacaciones.objects.create(
            funcionario=cls.funcionario_principal,
            periodo_vacacional=cls.periodo,
            solicitud_vacaciones=cls.solicitud,
            fecha_reintegro=date.today() + timedelta(days=21),
            motivo_reintegro="finalizacion_normal",
            observaciones="",
            periodo_correspondiente_desde=cls.periodo.fecha_inicio_periodo,
            periodo_correspondiente_hasta=cls.periodo.fecha_fin_periodo,
            fecha_disfrute_desde=date.today() + timedelta(days=10),
            fecha_disfrute_hasta=date.today() + timedelta(days=15),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            creada_por=cls.usuario_principal,
        )

    def test_retiro_reintegro_en_notificacion_de_solicitud(self):
        notificacion = Notificacion.objects.create(
            asunto="Solicitud aprobada",
            mensaje="Mensaje",
            funcionario=self.funcionario_principal,
            funcionario_cc=self.funcionario_secundario,
            solicitud_vacaciones=self.solicitud,
            reintegro_vacaciones=self.reintegro,
            tipo_notificacion="solicitud",
        )

        self.assertIsNone(notificacion.reintegro_vacaciones)
        self.assertEqual(notificacion.solicitud_vacaciones, self.solicitud)

    def test_retiro_solicitud_en_notificacion_de_reintegro(self):
        notificacion = Notificacion.objects.create(
            asunto="Reintegro creado",
            mensaje="Mensaje",
            funcionario=self.funcionario_principal,
            funcionario_cc=None,
            solicitud_vacaciones=self.solicitud,
            reintegro_vacaciones=self.reintegro,
            tipo_notificacion="reintegro",
        )

        self.assertIsNone(notificacion.solicitud_vacaciones)
        self.assertEqual(notificacion.reintegro_vacaciones, self.reintegro)
