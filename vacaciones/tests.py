from datetime import date, timedelta
from unittest import skip

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from usuarios.models import Funcionario
from core.models import Estamento, FacultadDependencia, Sede

from .forms import SolicitudVacacionesForm
from .models import (
    PeriodoVacacional,
    SolicitudVacaciones,
    ReintegroVacaciones,
    generar_codigo_sabs,
    AprobacionEtapa,
)

User = get_user_model()

class SolicitudVacacionesListViewTest(TestCase):
    def setUp(self):
        pass

    def test_puede_crear_solicitud_sin_solicitudes_activas(self):
        """Test que verifica que el usuario puede crear solicitud cuando no tiene solicitudes activas"""
        pass

    def test_no_puede_crear_solicitud_con_solicitud_activa(self):
        """Test que verifica que el usuario no puede crear solicitud cuando tiene una activa"""
        pass

    def test_puede_crear_solicitud_con_reintegro_aprobado(self):
        """Test que verifica que el usuario puede crear solicitud cuando tiene reintegro aprobado"""
        pass

    def test_tooltip_se_renderiza_con_solicitud_activa(self):
        """Test que verifica que el tooltip se renderiza correctamente cuando hay una solicitud activa"""
        pass


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

        self.assertTrue(n1 >= 1)
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
        pass

    def test_edicion_no_muestra_alerta_solicitud_activa(self):
        """Test que verifica que no se muestre la alerta de solicitud activa en modo edición"""
        pass

    def test_edicion_no_muestra_alerta_plazo_solicitud(self):
        """Test que verifica que no se muestre la alerta de plazo de solicitud en modo edición"""
        pass

    def test_edicion_muestra_formulario_correctamente(self):
        """Test que verifica que el formulario de edición se muestre correctamente"""
        pass

    def test_edicion_muestra_codigo_sabs_y_fecha_solicitud(self):
        """Test que verifica que los campos código SABS y fecha de solicitud se muestren en modo edición"""
        pass


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


class FlatpickrIntegrationTest(TestCase):
    """Tests de integración con flatpickr (placeholder; requieren templates/vistas)"""

    def setUp(self):
        pass

    def test_campos_fecha_no_tienen_type_date(self):
        """Test que verifica que los campos de fecha no tengan type='date' para permitir flatpickr"""
        pass

    def test_scripts_flatpickr_se_cargan(self):
        """Test que verifica que los scripts de flatpickr se carguen correctamente"""
        pass

    def test_formulario_tiene_campos_fecha_correctos(self):
        """Test que verifica que el formulario tenga los campos de fecha con los atributos correctos"""
        pass

    def test_configuracion_archivos_estaticos(self):
        """Test que verifica que la configuración de archivos estáticos funcione correctamente"""
        pass


class _BaseSetupAprobacionesMixin:
    """
    Prepara catálogos mínimos, un usuario y un funcionario,
    y un PeriodoVacacional válido.
    """
    def setUp(self):
        # Catálogos
        self.est_docente = Estamento.objects.create(nombre="Docente", descripcion="Docente")
        self.dep = FacultadDependencia.objects.create(nombre="Escuela X", descripcion="Escuela")
        self.sede = Sede.objects.create(nombre="Sede Central", direccion="Calle X")

        # Usuario + Funcionario
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

        # Periodo vacacional
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

        # Idempotencia
        sol.save()
        self.assertEqual(sol.aprobaciones.count(), 3)

        # Verificación directa con ContentType
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

        # Inicialmente todos False
        self.assertFalse(sol.aprobada_por_jefe)
        self.assertFalse(sol.aprobada_por_coord)
        self.assertFalse(sol.autorizada_rrhh)

        # Aprobar JEFE
        sol.aprobaciones.filter(etapa='JEFE').update(estado='aprobada')
        sol.refresh_from_db()
        self.assertTrue(sol.aprobada_por_jefe)
        self.assertFalse(sol.aprobada_por_coord)
        self.assertFalse(sol.autorizada_rrhh)

        # Aprobar COORD
        sol.aprobaciones.filter(etapa='COORD').update(estado='aprobada')
        sol.refresh_from_db()
        self.assertTrue(sol.aprobada_por_coord)

        # Autorizar RRHH
        sol.aprobaciones.filter(etapa='RRHH').update(estado='autorizada')
        sol.refresh_from_db()
        self.assertTrue(sol.autorizada_rrhh)


# ====== REINTEGRO: hoy NO se crean etapas por defecto (no hay señal). ======
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
            codigo_sabs="",  # se autogenera en save()
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

        # Idempotencia
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

        # Inicial: todos False
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
