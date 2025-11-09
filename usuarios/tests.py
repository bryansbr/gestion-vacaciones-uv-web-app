from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.models import Estamento, FacultadDependencia, Sede
from notificaciones.models import Notificacion
from usuarios.models import Funcionario
from usuarios import services
from vacaciones.models import (
    HistoricoAcciones,
    PeriodoVacacional,
    SolicitudVacaciones,
)

class ServiciosDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.estamento = Estamento.objects.create(nombre="Administrativo", descripcion="Admin")
        cls.facultad = FacultadDependencia.objects.create(nombre="Facultad X", descripcion="Desc")
        cls.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle 123")

        User = get_user_model()
        cls.usuario_jefe = User.objects.create_user(email="jefe@test.com", password="pwd")
        cls.usuario_coord = User.objects.create_user(email="coord@test.com", password="pwd")
        cls.usuario_sub = User.objects.create_user(email="sub@test.com", password="pwd")

        cls.funcionario_jefe = Funcionario.objects.create(
            user=cls.usuario_jefe,
            nombre="Carlos",
            apellido="Jefe",
            numero_identificacion="111",
            telefono="3000000000",
            fecha_ingreso_universidad=date.today() - timedelta(days=800),
            estamento=cls.estamento,
            facultad_dependencia=cls.facultad,
            sede=cls.sede,
        )

        cls.funcionario_coord = Funcionario.objects.create(
            user=cls.usuario_coord,
            nombre="Laura",
            apellido="Coord",
            numero_identificacion="222",
            telefono="3000000001",
            fecha_ingreso_universidad=date.today() - timedelta(days=600),
            estamento=cls.estamento,
            facultad_dependencia=cls.facultad,
            sede=cls.sede,
        )

        cls.funcionario_sub = Funcionario.objects.create(
            user=cls.usuario_sub,
            nombre="María",
            apellido="Sub",
            numero_identificacion="333",
            telefono="3000000002",
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            estamento=cls.estamento,
            facultad_dependencia=cls.facultad,
            sede=cls.sede,
            jefe_inmediato=cls.funcionario_jefe,
        )

        cls.periodo = PeriodoVacacional.objects.create(
            funcionario=cls.funcionario_sub,
            fecha_inicio_periodo=date.today() - timedelta(days=400),
            fecha_fin_periodo=date.today() - timedelta(days=100),
            dias_disfrutados_periodo=0,
        )

        cls.solicitud = SolicitudVacaciones.objects.create(
            funcionario=cls.funcionario_sub,
            periodo_vacacional=cls.periodo,
            fecha_inicio_vacaciones=date.today() + timedelta(days=10),
            fecha_fin_vacaciones=date.today() + timedelta(days=25),
            tiene_dias_pendientes=False,
            creada_por=cls.usuario_sub,
        )

        cls.notificacion_jefe = Notificacion.objects.create(
            asunto="Aviso",
            mensaje="Mensaje para jefe",
            funcionario=cls.funcionario_jefe,
            solicitud_vacaciones=cls.solicitud,
            tipo_notificacion="solicitud",
        )

        cls.notificacion_coord = Notificacion.objects.create(
            asunto="Aviso coord",
            mensaje="Mensaje para coord",
            funcionario=cls.funcionario_coord,
            solicitud_vacaciones=cls.solicitud,
            tipo_notificacion="solicitud",
        )

        cls.historial_para_jefe = HistoricoAcciones.objects.create(
            accion_realizada="aprobacion",
            tipo_accion="solicitud",
            usuario=cls.usuario_coord,
            solicitud_vacaciones=cls.solicitud,
            grupo_autorizador="Jefe Inmediato",
            nuevo_estado="aprobada",
            estado_anterior="pendiente",
            observacion="Sin observaciones",
        )

        cls.historial_para_coord = HistoricoAcciones.objects.create(
            accion_realizada="aprobacion",
            tipo_accion="solicitud",
            usuario=cls.usuario_jefe,
            solicitud_vacaciones=cls.solicitud,
            grupo_autorizador="Jefe Inmediato",
            nuevo_estado="aprobada",
            estado_anterior="pendiente",
            observacion="Observación para coordinador",
        )

        for historial in (cls.historial_para_jefe, cls.historial_para_coord):
            historial.fecha_hora_accion = timezone.now() + timedelta(minutes=5)
            historial.save(update_fields=["fecha_hora_accion"])

    def test_novedad_historial_incluye_codigo_y_actor(self):
        resultado = services._formatear_novedad_historial(self.historial_para_jefe)

        self.assertIsNotNone(resultado)
        self.assertIn(self.solicitud.codigo_sabs, resultado.mensaje)
        self.assertIn("aprobada por Jefe Inmediato", resultado.mensaje)

    def test_novedad_historial_ignora_estados_no_relevantes(self):
        historial = HistoricoAcciones.objects.create(
            accion_realizada="aprobacion",
            tipo_accion="solicitud",
            usuario=self.usuario_jefe,
            solicitud_vacaciones=self.solicitud,
            grupo_autorizador="Jefe Inmediato",
            nuevo_estado="en_revision",
            estado_anterior="pendiente",
        )

        self.assertIsNone(services._formatear_novedad_historial(historial))

    def test_combinacion_notificaciones_respeta_orden(self):
        extra = services._formatear_novedad_historial(self.historial_para_jefe)
        extra = services._formatear_novedad_historial(self.historial_para_jefe)
        combined = services._combinar_notificaciones(
            Notificacion.objects.filter(funcionario=self.funcionario_jefe),
            [extra],
        )

        self.assertEqual(len(combined), 2)
        mensajes_combined = [getattr(n, "mensaje", "") for n in combined]
        self.assertTrue(any("La solicitud" in mensaje for mensaje in mensajes_combined))

    def test_datos_dashboard_jefe_incluyen_novedades(self):
        datos = services.obtener_datos_dashboard_jefe(self.usuario_jefe)

        self.assertEqual(datos["solicitudes_totales"], 1)
        self.assertEqual(datos["solicitudes_pendientes"], 1)
        mensajes = [getattr(n, "mensaje", "") for n in datos["notificaciones"]]
        self.assertTrue(any("aprobada por Jefe Inmediato" in mensaje for mensaje in mensajes))

    def test_datos_dashboard_coordinador_incluyen_novedades(self):
        datos = services.obtener_datos_dashboard_coordinador(self.usuario_coord)

        self.assertEqual(datos["solicitudes_totales"], 1)
        mensajes = [getattr(n, "mensaje", "") for n in datos["notificaciones"]]
        self.assertTrue(any("aprobada por Jefe Inmediato" in mensaje for mensaje in mensajes))
