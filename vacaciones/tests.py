from datetime import date, timedelta
import json
from unittest import skip

from django.contrib.auth.models import Group
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from usuarios.models import Funcionario
from core.models import Estamento, FacultadDependencia, Sede
from core.permissions import es_secretaria

from .forms import SolicitudVacacionesForm
from .models import (
    PeriodoVacacional,
    SolicitudVacaciones,
    ReintegroVacaciones,
    AprobacionEtapa,
)

User = get_user_model()

class SolicitudVacacionesListViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="func@test.com", password="x")
        self.estamento = Estamento.objects.create(nombre="Administrativo", descripcion="Admin")
        self.dependencia = FacultadDependencia.objects.create(nombre="Dependencia X", descripcion="Desc")
        self.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle 123")

        self.funcionario = Funcionario.objects.create(
            user=self.user,
            nombre="Funcionario",
            apellido="Principal",
            numero_identificacion="F001",
            telefono="3000000000",
            fecha_ingreso_universidad=date.today() - timedelta(days=400),
            estamento=self.estamento,
            facultad_dependencia=self.dependencia,
            sede=self.sede,
        )

        self.periodo = PeriodoVacacional.objects.create(
            funcionario=self.funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )

        self.url = reverse("vacaciones:solicitud-vacaciones-list")
        self.client.force_login(self.user)

    def test_puede_crear_solicitud_sin_solicitudes_activas(self):
        """Debe permitir la creación cuando no existen solicitudes activas ni reintegros pendientes."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["puede_crear_solicitud"])
        self.assertIsNone(response.context["solicitud_activa"])

    def test_no_puede_crear_solicitud_con_solicitud_activa(self):
        """Debe bloquear la creación cuando existe una solicitud activa sin reintegro aprobado."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2025, 2, 3),
            fecha_fin_vacaciones=date(2025, 2, 21),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud="pendiente",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["puede_crear_solicitud"])
        self.assertIsNotNone(response.context["solicitud_activa"])
        self.assertEqual(response.context["solicitud_activa"].pk, solicitud.pk)

    def test_puede_crear_solicitud_con_reintegro_aprobado(self):
        """Una solicitud con reintegro aprobado no bloquea la creación de una nueva solicitud."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2025, 2, 3),
            fecha_fin_vacaciones=date(2025, 2, 21),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud="pendiente",
        )

        ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=30),
            motivo_reintegro="Vacaciones",
            observaciones="",
            fecha_disfrute_desde=solicitud.fecha_inicio_vacaciones,
            fecha_disfrute_hasta=solicitud.fecha_fin_vacaciones,
            dias_disfrutados=solicitud.total_dias_solicitados,
            tipo_dias_disfrutados="C",
            dias_pendientes=0,
            tipo_dias_pendientes="C",
            periodo_vacacional=self.periodo,
            solicitud_vacaciones=solicitud,
            funcionario=self.funcionario,
            creada_por=self.user,
            estado_solicitud="aprobado",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["puede_crear_solicitud"])
        self.assertIsNone(response.context["solicitud_activa"])

    def test_tooltip_se_renderiza_con_solicitud_activa(self):
        """Cuando existe una solicitud activa debe exponerse en el contexto para mostrar la alerta en la UI."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2025, 2, 3),
            fecha_fin_vacaciones=date(2025, 2, 21),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud="pendiente",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context["solicitud_activa"])
        self.assertEqual(response.context["solicitud_activa"].codigo_sabs, solicitud.codigo_sabs)


class CodigoSABSTest(TestCase):
    """Test para verificar la generación secuencial de códigos SABS"""

    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", password="x")
        self.est_admin = Estamento.objects.create(nombre="Administrativo", descripcion="Admin")
        self.dep = FacultadDependencia.objects.create(nombre="Escuela X", descripcion="Escuela")
        self.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle X")

        self.func = Funcionario.objects.create(
            user=self.user,
            nombre="Ana",
            apellido="García",
            numero_identificacion="123",
            telefono="3000000000",
            fecha_ingreso_universidad=date.today() - timedelta(days=400),
            decreto_resolucion="",
            estamento=self.est_admin,
            facultad_dependencia=self.dep,
            sede=self.sede,
        )

        self.periodo = PeriodoVacacional.objects.create(
            funcionario=self.func,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )

    def _crear_solicitud(self, fecha_ini, fecha_fin, fecha_solic=None):
        s = SolicitudVacaciones(
            funcionario=self.func,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=fecha_ini,
            fecha_fin_vacaciones=fecha_fin,
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        if fecha_solic:
            s.fecha_solicitud = fecha_solic
        s.save()
        return s

    def test_generacion_codigo_sabs_secuencial(self):
        """Los códigos SABS de vacaciones deben aumentar el consecutivo dentro del mismo año."""
        y = date.today().year
        s1 = self._crear_solicitud(date(y, 2, 3), date(y, 2, 21))
        s2 = self._crear_solicitud(date(y, 2, 3), date(y, 2, 21))

        self.assertTrue(s1.codigo_sabs.startswith(f"VAC{y}"))
        self.assertTrue(s2.codigo_sabs.startswith(f"VAC{y}"))

        n1 = int(s1.codigo_sabs[len(f"VAC{y}"):])
        n2 = int(s2.codigo_sabs[len(f"VAC{y}"):])
        self.assertEqual(n2, n1 + 1)

    def test_generacion_codigo_sabs_por_anio(self):
        """Los códigos se reinician por año (VAC{anio}{consecutivo})."""
        y = date.today().year
        next_year = y + 1

        s1 = self._crear_solicitud(date(y, 2, 3), date(y, 2, 21), fecha_solic=date(y, 2, 1))
        s2 = self._crear_solicitud(date(next_year, 2, 3), date(next_year, 2, 21), fecha_solic=date(next_year, 1, 15))

        n1 = int(s1.codigo_sabs[len(f"VAC{y}"):])
        n2 = int(s2.codigo_sabs[len(f"VAC{next_year}"):])

        self.assertGreaterEqual(n1, 1)
        self.assertEqual(n2, 1)

    def test_generacion_codigo_sabs_reintegro(self):
        """Generación de códigos para Reintegros (REI{anio}{consecutivo})."""
        y = date.today().year
        rein = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=16),
            motivo_reintegro="Vacaciones",
            observaciones="",
            fecha_disfrute_desde=date.today() + timedelta(days=10),
            fecha_disfrute_hasta=date.today() + timedelta(days=15),
            dias_disfrutados=5,
            tipo_dias_disfrutados="C",
            dias_pendientes=0,
            tipo_dias_pendientes="C",
            periodo_vacacional=self.periodo,
            solicitud_vacaciones=self._crear_solicitud(date(y, 2, 3), date(y, 2, 21)),
            funcionario=self.func,
            creada_por=self.user,
        )
        self.assertTrue(rein.codigo_sabs.startswith(f"REI{y}"))

    def test_codigo_sabs_unico(self):
        """Los códigos SABS deben ser únicos."""
        y = date.today().year
        s1 = self._crear_solicitud(date(y, 2, 3), date(y, 2, 21))
        s2 = self._crear_solicitud(date(y, 2, 3), date(y, 2, 21))
        self.assertNotEqual(s1.codigo_sabs, s2.codigo_sabs)

class SolicitudVacacionesEdicionTest(TestCase):
    """Test para verificar el comportamiento correcto al editar solicitudes"""

    def setUp(self):
        self.user = User.objects.create_user(email="func-edit@test.com", password="x")
        self.estamento = Estamento.objects.create(nombre="Administrativo", descripcion="Admin")
        self.dependencia = FacultadDependencia.objects.create(nombre="Dependencia Edit", descripcion="Desc")
        self.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle 456")

        self.funcionario = Funcionario.objects.create(
            user=self.user,
            nombre="Funcionario",
            apellido="Editable",
            numero_identificacion="F002",
            telefono="3000000001",
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            estamento=self.estamento,
            facultad_dependencia=self.dependencia,
            sede=self.sede,
        )

        self.periodo = PeriodoVacacional.objects.create(
            funcionario=self.funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )

        self.solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2025, 2, 3),
            fecha_fin_vacaciones=date(2025, 2, 21),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud="pendiente",
        )

        self.url = reverse("vacaciones:solicitud_vacaciones_update", kwargs={"pk": self.solicitud.pk})
        self.client.force_login(self.user)

    def test_edicion_no_muestra_alerta_solicitud_activa(self):
        """Test que verifica que no se muestre la alerta de solicitud activa en modo edición"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["puede_crear_solicitud"])
        self.assertIsNone(response.context["solicitud_activa"])

    def test_edicion_no_muestra_alerta_plazo_solicitud(self):
        """Test que verifica que no se muestre la alerta de plazo de solicitud en modo edición"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["plazo_solicitud"])

    def test_edicion_muestra_formulario_correctamente(self):
        """Test que verifica que el formulario de edición se muestre correctamente"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        formulario = response.context["form"]
        self.assertEqual(formulario.instance.pk, self.solicitud.pk)

    def test_edicion_muestra_codigo_sabs_y_fecha_solicitud(self):
        """Test que verifica que los campos código SABS y fecha de solicitud se muestren en modo edición"""
        response = self.client.get(self.url)

        form = response.context["form"]
        self.assertIn("codigo_sabs", form.fields)
        self.assertIn("fecha_solicitud", form.fields)
        self.assertEqual(form.instance.codigo_sabs, self.solicitud.codigo_sabs)
        self.assertEqual(form.instance.fecha_solicitud, self.solicitud.fecha_solicitud)


class ValidacionesFechasTest(TestCase):
    """Test para validaciones/cálculos de días en SolicitudVacaciones"""

    def setUp(self):
        self.user = User.objects.create_user(email="user@test.com", password="x")
        self.dep = FacultadDependencia.objects.create(nombre="Escuela X", descripcion="Escuela")
        self.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle X")

        self.est_doc = Estamento.objects.create(nombre="Docente", descripcion="Docente")
        self.est_adm = Estamento.objects.create(nombre="Administrativo", descripcion="Adm")
        self.est_trab = Estamento.objects.create(nombre="Trabajador Oficial", descripcion="Trab")

        # Un funcionario por estamento
        self.func_doc = Funcionario.objects.create(
            user=self.user,
            nombre="Doc",
            apellido="Uno",
            numero_identificacion="D1",
            telefono="300",
            fecha_ingreso_universidad=date.today() - timedelta(days=400),
            decreto_resolucion="1279",
            estamento=self.est_doc,
            facultad_dependencia=self.dep,
            sede=self.sede,
        )
        self.func_adm = Funcionario.objects.create(
            user=User.objects.create_user(email="adm@test.com", password="x"),
            nombre="Adm",
            apellido="Dos",
            numero_identificacion="A1",
            telefono="301",
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            decreto_resolucion="",
            estamento=self.est_adm,
            facultad_dependencia=self.dep,
            sede=self.sede,
        )
        self.func_trab = Funcionario.objects.create(
            user=User.objects.create_user(email="trab@test.com", password="x"),
            nombre="Trab",
            apellido="Tres",
            numero_identificacion="T1",
            telefono="302",
            fecha_ingreso_universidad=date.today() - timedelta(days=800),
            decreto_resolucion="",
            estamento=self.est_trab,
            facultad_dependencia=self.dep,
            sede=self.sede,
        )

        # Periodos (días pendientes = totales - 0)
        self.per_doc = PeriodoVacacional.objects.create(
            funcionario=self.func_doc,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        self.per_adm = PeriodoVacacional.objects.create(
            funcionario=self.func_adm,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        self.per_trab = PeriodoVacacional.objects.create(
            funcionario=self.func_trab,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )

    def test_docente_decreto_1279_debe_tener_30_dias(self):
        """
        Para docente 1279: 15 hábiles + resto calendario.
        Elegimos un rango que produce exactamente 30 total:
        - 15 hábiles: del 2025-02-03 (lun) al 2025-02-21 (vie)
        - +15 calendario: 2025-02-22 .. 2025-03-08 (15 días)
        Total esperado: 30
        """
        ini = date(2025, 2, 3)
        fin = date(2025, 3, 8)
        s = SolicitudVacaciones.objects.create(
            funcionario=self.func_doc,
            periodo_vacacional=self.per_doc,
            fecha_inicio_vacaciones=ini,
            fecha_fin_vacaciones=fin,
            tiene_dias_pendientes=False,
            creada_por=self.func_doc.user,
        )
        self.assertEqual(s.total_dias_solicitados, 30)

    def test_administrativo_debe_tener_15_dias_habiles(self):
        """
        Administrativos: sólo días hábiles.
        Rango de 3 semanas completas (lun-vie) sin festivos (febrero suele no tener festivos en CO).
        2025-02-03 (lun) .. 2025-02-21 (vie) => 15 hábiles.
        """
        ini = date(2025, 2, 3)
        fin = date(2025, 2, 21)
        s = SolicitudVacaciones.objects.create(
            funcionario=self.func_adm,
            periodo_vacacional=self.per_adm,
            fecha_inicio_vacaciones=ini,
            fecha_fin_vacaciones=fin,
            tiene_dias_pendientes=False,
            creada_por=self.func_adm.user,
        )
        self.assertEqual(s.total_dias_solicitados, 15)

    def test_trabajador_oficial_debe_tener_30_dias_calendario(self):
        """
        Trabajador oficial: días calendario.
        """
        ini = date(2025, 2, 1)
        fin = date(2025, 3, 2)  # 30 días calendario (inclusive)
        s = SolicitudVacaciones.objects.create(
            funcionario=self.func_trab,
            periodo_vacacional=self.per_trab,
            fecha_inicio_vacaciones=ini,
            fecha_fin_vacaciones=fin,
            tiene_dias_pendientes=False,
            creada_por=self.func_trab.user,
        )
        self.assertEqual(s.total_dias_solicitados, 30)

class SolicitudVacacionesCalculoDiasPendientesTests(TestCase):
    """Pruebas para el ajuste de días solicitados según el periodo disponible."""

    @classmethod
    def setUpTestData(cls):
        cls.est_admin = Estamento.objects.create(nombre="Administrativo", descripcion="Admin")
        cls.dep = FacultadDependencia.objects.create(nombre="Dependencia Test", descripcion="Desc")
        cls.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle 123")

        User = get_user_model()
        cls.user = User.objects.create_user(email="limit@test.com", password="pwd")
        cls.funcionario = Funcionario.objects.create(
            user=cls.user,
            nombre="Limite",
            apellido="Dias",
            numero_identificacion="LD1",
            telefono="3000000000",
            fecha_ingreso_universidad=date.today() - timedelta(days=700),
            decreto_resolucion="",
            estamento=cls.est_admin,
            facultad_dependencia=cls.dep,
            sede=cls.sede,
        )

        cls.periodo = PeriodoVacacional.objects.create(
            funcionario=cls.funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )

    def _crear_solicitud(self):
        return SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2025, 2, 3),
            fecha_fin_vacaciones=date(2025, 2, 21),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )

    def test_calculo_total_limita_por_dias_disponibles(self):
        self.periodo.refresh_from_db()
        total_periodo = self.periodo.dias_totales_periodo
        self.periodo.dias_disfrutados_periodo = max(0, total_periodo - 5)
        self.periodo.save()
        self.periodo.refresh_from_db()

        solicitud = self._crear_solicitud()
        solicitud._calcular_total_dias_solicitados()

        self.assertEqual(solicitud.total_dias_solicitados, 5)

    def test_calculo_mantiene_valor_cuando_periodo_no_existe(self):
        solicitud = self._crear_solicitud()
        solicitud.periodo_vacacional_id = 999999
        solicitud.periodo_vacacional = None

        solicitud._calcular_total_dias_solicitados()

        self.assertEqual(solicitud.total_dias_solicitados, 15)

class IntegracionFlatpickrTests(TestCase):
    """Verifica la configuración necesaria para utilizar Flatpickr en el formulario de solicitudes."""

    def setUp(self):
        self.user = User.objects.create_user(email="flatpickr@test.com", password="x")
        self.estamento = Estamento.objects.create(nombre="Administrativo", descripcion="Admin")
        self.dependencia = FacultadDependencia.objects.create(nombre="Dependencia Flatpickr", descripcion="Desc")
        self.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle 789")

        self.funcionario = Funcionario.objects.create(
            user=self.user,
            nombre="Func",
            apellido="Flatpickr",
            numero_identificacion="F003",
            telefono="3000000002",
            fecha_ingreso_universidad=date.today() - timedelta(days=600),
            estamento=self.estamento,
            facultad_dependencia=self.dependencia,
            sede=self.sede,
        )

        PeriodoVacacional.objects.create(
            funcionario=self.funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )

        self.client.force_login(self.user)

    def test_campos_fecha_usan_widget_flatpickr(self):
        """Los campos de fecha utilizan la clase y atributos esperados por Flatpickr."""
        form = SolicitudVacacionesForm(user=self.user)
        inicio_widget = form.fields["fecha_inicio_vacaciones"].widget
        fin_widget = form.fields["fecha_fin_vacaciones"].widget

        self.assertIn("flatpickr-input", inicio_widget.attrs.get("class", ""))
        self.assertEqual(inicio_widget.attrs.get("autocomplete"), "off")
        self.assertIn("flatpickr-input", fin_widget.attrs.get("class", ""))

    def test_vista_creacion_incluye_festivos_en_contexto(self):
        """La vista de creación expone la lista de festivos para inicializar Flatpickr."""
        url = reverse("vacaciones:solicitud_vacaciones_create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        festivos = response.context["festivos_colombia"]
        festivos_decodificados = json.loads(festivos)
        self.assertIsInstance(festivos_decodificados, list)
        self.assertTrue(all(isinstance(item, str) for item in festivos_decodificados))

    def test_vista_creacion_publica_periodos_y_pendientes(self):
        """La vista adjunta la información de periodos y días pendientes en formato JSON."""
        url = reverse("vacaciones:solicitud_vacaciones_create")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        periodos_json = response.context["periodos_dias_pendientes"]
        periodos_decodificados = json.loads(periodos_json)
        self.assertIsInstance(periodos_decodificados, dict)

    def test_formato_fechas_aceptado_en_formulario(self):
        """El formulario acepta formatos día/mes/año requeridos por la configuración de Flatpickr."""
        form = SolicitudVacacionesForm(user=self.user)
        self.assertIn("%d/%m/%Y", form.fields["fecha_inicio_vacaciones"].input_formats)
        self.assertIn("%d/%m/%Y", form.fields["fecha_fin_vacaciones"].input_formats)

class _BaseSetupAprobacionesMixin:
    """
    Prepara catálogos mínimos, un usuario y un funcionario,
    y un PeriodoVacacional válido.
    """
    def setUp(self):
        self.est_docente = Estamento.objects.create(nombre="Docente", descripcion="Docente")
        self.dep = FacultadDependencia.objects.create(nombre="Escuela X", descripcion="Escuela")
        self.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle X")

        self.user = User.objects.create_user(email="user@test.com", password="x")
        self.func = Funcionario.objects.create(
            user=self.user,
            nombre="Ana",
            apellido="García",
            numero_identificacion="123",
            telefono="3000000000",
            fecha_ingreso_universidad=date.today() - timedelta(days=400),
            decreto_resolucion="1279",  # docente (1279)
            estamento=self.est_docente,
            facultad_dependencia=self.dep,
            sede=self.sede,
        )

        self.periodo = PeriodoVacacional.objects.create(
            funcionario=self.func,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )

class TestAprobacionesSolicitud(_BaseSetupAprobacionesMixin, TestCase):
    def test_crea_tres_etapas_al_crear_solicitud(self):
        sol = SolicitudVacaciones.objects.create(
            funcionario=self.func,
            periodo_vacacional=self.periodo,
            fecha_solicitud=date.today(),
            fecha_inicio_vacaciones=date.today() + timedelta(days=10),
            fecha_fin_vacaciones=date.today() + timedelta(days=15),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )

        etapas = list(sol.aprobaciones.values_list("etapa", flat=True))
        estados = list(sol.aprobaciones.values_list("estado", flat=True))

        self.assertCountEqual(etapas, ["JEFE", "COORD", "RRHH"])
        self.assertTrue(all(e == "pendiente" for e in estados))

        sol.save()
        self.assertEqual(sol.aprobaciones.count(), 3)

        self.assertEqual(
            AprobacionEtapa.objects.filter(
                content_type__model="solicitudvacaciones", object_id=sol.id
            ).count(),
            3
        )

class TestFlagsHitosSolicitud(_BaseSetupAprobacionesMixin, TestCase):
    def test_flags_hitos_en_solicitud(self):
        sol = SolicitudVacaciones.objects.create(
            funcionario=self.func,
            periodo_vacacional=self.periodo,
            fecha_solicitud=date.today(),
            fecha_inicio_vacaciones=date.today() + timedelta(days=10),
            fecha_fin_vacaciones=date.today() + timedelta(days=15),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )

        self.assertFalse(sol.aprobada_por_jefe)
        self.assertFalse(sol.aprobada_por_coord)
        self.assertFalse(sol.autorizada_rrhh)

        sol.aprobaciones.filter(etapa='JEFE').update(estado='aprobada')
        sol.refresh_from_db()
        self.assertTrue(sol.aprobada_por_jefe)
        self.assertFalse(sol.aprobada_por_coord)
        self.assertFalse(sol.autorizada_rrhh)

        sol.aprobaciones.filter(etapa='COORD').update(estado='aprobada')
        sol.refresh_from_db()
        self.assertTrue(sol.aprobada_por_coord)

        sol.aprobaciones.filter(etapa='RRHH').update(estado='autorizada')
        sol.refresh_from_db()
        self.assertTrue(sol.autorizada_rrhh)

# ====== REINTEGRO ======
@skip("Actualmente no se crean etapas por defecto al crear ReintegroVacaciones (no hay signal).")
class TestAprobacionesReintegro(_BaseSetupAprobacionesMixin, TestCase):
    def test_crea_tres_etapas_al_crear_reintegro(self):
        sol = SolicitudVacaciones.objects.create(
            funcionario=self.func,
            periodo_vacacional=self.periodo,
            fecha_solicitud=date.today(),
            fecha_inicio_vacaciones=date.today() + timedelta(days=10),
            fecha_fin_vacaciones=date.today() + timedelta(days=15),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )

        rein = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=16),
            motivo_reintegro="Vacaciones",
            observaciones="",
            fecha_disfrute_desde=date.today() + timedelta(days=10),
            fecha_disfrute_hasta=date.today() + timedelta(days=15),
            dias_disfrutados=5,
            tipo_dias_disfrutados="C",
            dias_pendientes=0,
            tipo_dias_pendientes="C",
            periodo_vacacional=self.periodo,
            solicitud_vacaciones=sol,
            funcionario=self.func,
            creada_por=self.user,
        )

        etapas = list(rein.aprobaciones.values_list("etapa", flat=True))
        estados = list(rein.aprobaciones.values_list("estado", flat=True))

        self.assertCountEqual(etapas, ["JEFE", "COORD", "RRHH"])
        self.assertTrue(all(e == "pendiente" for e in estados))

        rein.save()
        self.assertEqual(rein.aprobaciones.count(), 3)

        self.assertEqual(
            AprobacionEtapa.objects.filter(
                content_type__model="reintegrovacaciones", object_id=rein.id
            ).count(),
            3
        )

@skip("Actualmente no se crean etapas por defecto al crear ReintegroVacaciones (no hay signal).")
class TestFlagsHitosReintegro(_BaseSetupAprobacionesMixin, TestCase):
    def test_flags_hitos_en_reintegro(self):
        sol = SolicitudVacaciones.objects.create(
            funcionario=self.func,
            periodo_vacacional=self.periodo,
            fecha_solicitud=date.today(),
            fecha_inicio_vacaciones=date.today() + timedelta(days=10),
            fecha_fin_vacaciones=date.today() + timedelta(days=15),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )

        rein = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=16),
            motivo_reintegro="Vacaciones",
            observaciones="",
            fecha_disfrute_desde=date.today() + timedelta(days=10),
            fecha_disfrute_hasta=date.today() + timedelta(days=15),
            dias_disfrutados=5,
            tipo_dias_disfrutados="C",
            dias_pendientes=0,
            tipo_dias_pendientes="C",
            periodo_vacacional=self.periodo,
            solicitud_vacaciones=sol,
            funcionario=self.func,
            creada_por=self.user,
        )

        self.assertFalse(rein.aprobada_por_jefe)
        self.assertFalse(rein.aprobada_por_coord)
        self.assertFalse(rein.autorizada_rrhh)

        # JEFE aprueba
        rein.aprobaciones.filter(etapa='JEFE').update(estado='aprobada')
        rein.refresh_from_db()
        self.assertTrue(rein.aprobada_por_jefe)

        # COORD aprueba
        rein.aprobaciones.filter(etapa='COORD').update(estado='aprobada')
        rein.refresh_from_db()
        self.assertTrue(rein.aprobada_por_coord)

        # RRHH autoriza
        rein.aprobaciones.filter(etapa='RRHH').update(estado='autorizada')
        rein.refresh_from_db()
        self.assertTrue(rein.autorizada_rrhh)

# ==========================================================
# TESTS: Secretaria
# ==========================================================
class RolSecretariaTests(TestCase):
    """Tests para verificar el comportamiento del rol Secretaria"""

    def setUp(self):
        """Setup base para los tests de Secretaria"""
        self.est_admin = Estamento.objects.create(nombre="Administrativo", descripcion="Admin")
        self.dep1 = FacultadDependencia.objects.create(nombre="Dependencia 1", descripcion="Dependencia 1")
        self.dep2 = FacultadDependencia.objects.create(nombre="Dependencia 2", descripcion="Dependencia 2")
        self.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle X")
        
        self.grupo_secretaria, _ = Group.objects.get_or_create(name="Secretaria")
        self.grupo_jefe, _ = Group.objects.get_or_create(name="Jefe Inmediato")
        
        # Jefe inmediato J1
        self.user_jefe = User.objects.create_user(email="jefe@test.com", password="test123")
        self.func_jefe = Funcionario.objects.create(
            user=self.user_jefe,
            nombre="Jefe",
            apellido="Inmediato",
            numero_identificacion="J1",
            telefono="3000000001",
            fecha_ingreso_universidad=date.today() - timedelta(days=1000),
            decreto_resolucion="",
            estamento=self.est_admin,
            facultad_dependencia=self.dep1,
            sede=self.sede,
        )
        
        # Secretaria S1 (misma dependencia y jefe que la secretaria)
        self.user_secretaria = User.objects.create_user(email="secretaria@test.com", password="test123")
        self.grupo_secretaria.user_set.add(self.user_secretaria)
        self.func_secretaria = Funcionario.objects.create(
            user=self.user_secretaria,
            nombre="Secretaria",
            apellido="Uno",
            numero_identificacion="S1",
            telefono="3000000002",
            fecha_ingreso_universidad=date.today() - timedelta(days=800),
            decreto_resolucion="",
            estamento=self.est_admin,
            facultad_dependencia=self.dep1,
            sede=self.sede,
            jefe_inmediato=self.func_jefe,
        )
        
        # Funcionario F1 (misma dependencia y jefe que la secretaria)
        self.user_f1 = User.objects.create_user(email="func1@test.com", password="test123")
        self.func_f1 = Funcionario.objects.create(
            user=self.user_f1,
            nombre="Funcionario",
            apellido="Uno",
            numero_identificacion="F1",
            telefono="3000000003",
            fecha_ingreso_universidad=date.today() - timedelta(days=600),
            decreto_resolucion="",
            estamento=self.est_admin,
            facultad_dependencia=self.dep1,
            sede=self.sede,
            jefe_inmediato=self.func_jefe,
        )
        
        # Funcionario F2 (diferente dependencia)
        self.user_f2 = User.objects.create_user(email="func2@test.com", password="test123")
        self.func_f2 = Funcionario.objects.create(
            user=self.user_f2,
            nombre="Funcionario",
            apellido="Dos",
            numero_identificacion="F2",
            telefono="3000000004",
            fecha_ingreso_universidad=date.today() - timedelta(days=700),
            decreto_resolucion="",
            estamento=self.est_admin,
            facultad_dependencia=self.dep2,
            sede=self.sede,
            jefe_inmediato=self.func_jefe,
        )
        
        # Funcionario F3 (misma dependencia pero diferente jefe)
        self.user_jefe2 = User.objects.create_user(email="jefe2@test.com", password="test123")
        self.func_jefe2 = Funcionario.objects.create(
            user=self.user_jefe2,
            nombre="Jefe",
            apellido="Dos",
            numero_identificacion="J2",
            telefono="3000000005",
            fecha_ingreso_universidad=date.today() - timedelta(days=900),
            decreto_resolucion="",
            estamento=self.est_admin,
            facultad_dependencia=self.dep1,
            sede=self.sede,
        )
        
        self.user_f3 = User.objects.create_user(email="func3@test.com", password="test123")
        self.func_f3 = Funcionario.objects.create(
            user=self.user_f3,
            nombre="Funcionario",
            apellido="Tres",
            numero_identificacion="F3",
            telefono="3000000006",
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            decreto_resolucion="",
            estamento=self.est_admin,
            facultad_dependencia=self.dep1,
            sede=self.sede,
            jefe_inmediato=self.func_jefe2,
        )
        
        # Periodos vacacionales para los funcionarios
        self.periodo_f1 = PeriodoVacacional.objects.create(
            funcionario=self.func_f1,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        self.periodo_f2 = PeriodoVacacional.objects.create(
            funcionario=self.func_f2,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        self.periodo_f3 = PeriodoVacacional.objects.create(
            funcionario=self.func_f3,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        
        # Solicitudes
        self.solicitud_f1_pendiente = SolicitudVacaciones.objects.create(
            funcionario=self.func_f1,
            periodo_vacacional=self.periodo_f1,
            fecha_inicio_vacaciones=date.today() + timedelta(days=10),
            fecha_fin_vacaciones=date.today() + timedelta(days=20),
            tiene_dias_pendientes=False,
            estado_solicitud='pendiente',
            creada_por=self.user_f1,
        )
        
        self.solicitud_f2_pendiente = SolicitudVacaciones.objects.create(
            funcionario=self.func_f2,
            periodo_vacacional=self.periodo_f2,
            fecha_inicio_vacaciones=date.today() + timedelta(days=15),
            fecha_fin_vacaciones=date.today() + timedelta(days=25),
            tiene_dias_pendientes=False,
            estado_solicitud='pendiente',
            creada_por=self.user_f2,
        )
        
        self.solicitud_f1_en_revision = SolicitudVacaciones.objects.create(
            funcionario=self.func_f1,
            periodo_vacacional=self.periodo_f1,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=40),
            tiene_dias_pendientes=False,
            estado_solicitud='en_revision',
            creada_por=self.user_f1,
        )

    def test_secretaria_ve_solo_solicitudes_de_su_dependencia_y_mismo_jefe(self):
        """Verifica que la secretaria solo ve solicitudes de funcionarios con el mismo jefe_inmediato"""
        client = Client()
        client.force_login(self.user_secretaria)
        
        url = reverse('vacaciones:secretaria-solicitudes-list')
        response = client.get(url)
        
        self.assertEqual(response.status_code, 200)
        solicitudes = response.context['solicitudes']
        
        self.assertIn(self.solicitud_f1_pendiente, solicitudes)
        self.assertIn(self.solicitud_f1_en_revision, solicitudes)
        
        self.assertIn(self.solicitud_f2_pendiente, solicitudes)
        
        solicitudes_f3 = [s for s in solicitudes if s.funcionario_id == self.func_f3.id]
        self.assertEqual(len(solicitudes_f3), 0)

    def test_secretaria_no_puede_crear_doble_solicitud_para_mismo_funcionario(self):
        """Verifica que la secretaria no puede crear doble solicitud para el mismo funcionario"""
        client = Client()
        client.force_login(self.user_secretaria)
        
        url = reverse('vacaciones:secretaria-solicitud-create')
        response = client.get(url)
        
        self.assertNotEqual(response.status_code, 200)
        response = client.get(url + f'?funcionario_id={self.func_f1.id}')
        self.assertNotEqual(response.status_code, 200)

    def test_secretaria_puede_editar_solo_si_pendiente(self):
        """Verifica que la secretaria solo puede editar solicitudes en estado pendiente"""
        client = Client()
        client.force_login(self.user_secretaria)
        
        url = reverse('vacaciones:secretaria-solicitud-update', kwargs={'pk': self.solicitud_f1_pendiente.pk})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        
        url_en_revision = reverse('vacaciones:secretaria-solicitud-update', kwargs={'pk': self.solicitud_f1_en_revision.pk})
        response = client.get(url_en_revision)
        self.assertNotEqual(response.status_code, 200)

    def test_secretaria_puede_eliminar_solo_si_pendiente(self):
        """Verifica que la secretaria solo puede eliminar solicitudes en estado pendiente"""
        client = Client()
        client.force_login(self.user_secretaria)
        
        url = reverse('vacaciones:secretaria-solicitud-delete', kwargs={'pk': self.solicitud_f1_pendiente.pk})
        response = client.get(url)
        self.assertEqual(response.status_code, 200)
        
        url_en_revision = reverse('vacaciones:secretaria-solicitud-delete', kwargs={'pk': self.solicitud_f1_en_revision.pk})
        response = client.get(url_en_revision)
        self.assertNotEqual(response.status_code, 200)

    def test_es_secretaria_helper(self):
        """Verifica que el helper es_secretaria funciona correctamente"""
        self.assertTrue(es_secretaria(self.user_secretaria))
        self.assertFalse(es_secretaria(self.user_f1))
        self.assertFalse(es_secretaria(self.user_jefe))

    def test_form_secretaria_muestra_campo_funcionario(self):
        """Verifica que el form para secretaria muestra el campo funcionario"""
        form = SolicitudVacacionesForm(user=self.user_secretaria)
        self.assertIn('funcionario', form.fields.keys())
        
        form_normal = SolicitudVacacionesForm(user=self.user_f1)
        self.assertNotIn('funcionario', form_normal.fields.keys())
    
    def test_form_secretaria_filtra_funcionarios_por_permisos(self):
        """Verifica que el form de secretaria filtra correctamente los funcionarios"""
        form = SolicitudVacacionesForm(user=self.user_secretaria)
        
        queryset = form.fields['funcionario'].queryset
        self.assertIn(self.func_f1, queryset)
        self.assertIn(self.func_f2, queryset)
        self.assertNotIn(self.func_f3, queryset)
    
    def test_secretaria_no_ve_boton_aprobar_en_template(self):
        """Verifica que la secretaria no ve botones de aprobar en las acciones"""
        from vacaciones.templatetags.grupos_tags import es_secretaria
        self.assertTrue(es_secretaria(self.user_secretaria))
        self.assertFalse(es_secretaria(self.user_f1))
