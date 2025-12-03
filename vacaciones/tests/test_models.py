"""
Pruebas unitarias para los modelos del módulo de vacaciones.
"""
from datetime import date, timedelta
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.contrib.auth import get_user_model

from usuarios.models import Funcionario
from core.models import Estamento, FacultadDependencia, Sede
from vacaciones.models import (
    PeriodoVacacional,
    SolicitudVacaciones,
    ReintegroVacaciones,
    AprobacionEtapa,
    HistoricoAcciones,
)
from vacaciones.tests.test_helpers import (
    BaseTestCaseMixin,
    crear_funcionario_docente_1279,
    crear_funcionario_docente_115,
    crear_funcionario_trabajador_oficial,
)

User = get_user_model()

# ============================================================
# PeriodoVacacional
# ============================================================
class PeriodoVacacionalModelTest(BaseTestCaseMixin, TestCase):
    """Pruebas para el modelo PeriodoVacacional."""
    
    def test_periodo_fecha_inicio_posterior_a_fin_raise_error(self):
        """Validar que fecha_inicio no puede ser posterior a fecha_fin."""
        periodo = PeriodoVacacional(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today(),
            fecha_fin_periodo=date.today() - timedelta(days=10),
            dias_disfrutados_periodo=0,
        )
        with self.assertRaises(ValidationError):
            periodo.full_clean()
    
    def test_periodo_dias_totales_superan_disfrutados_pendientes_raise_error(self):
        """Validar que la suma de días pendientes y disfrutados no supera días totales."""
        periodo = PeriodoVacacional(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=20,
        )
        periodo.dias_totales_periodo = 15
        periodo.dias_pendientes_periodo = 0
        with self.assertRaises(ValidationError):
            periodo.full_clean()
    
    def test_periodo_cruza_con_otro_periodo_raise_error(self):
        """Validar que no se pueden crear periodos que se cruzan."""
        periodo1 = PeriodoVacacional.objects.create(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        
        periodo2 = PeriodoVacacional(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=300),
            fecha_fin_periodo=date.today() - timedelta(days=100),
            dias_disfrutados_periodo=0,
        )
        with self.assertRaises(ValidationError):
            periodo2.full_clean()
    
    def test_periodo_mismo_funcionario_periodos_no_cruzados_ok(self):
        """Permitir periodos del mismo funcionario que no se cruzan."""
        periodo1 = PeriodoVacacional.objects.create(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        
        periodo2 = PeriodoVacacional(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=100),
            fecha_fin_periodo=date.today() - timedelta(days=50),
            dias_disfrutados_periodo=0,
        )
        periodo2.full_clean()
    
    def test_contar_dias_docente_1279_retorna_30(self):
        """Docente decreto 1279 retorna 30 días."""
        funcionario = crear_funcionario_docente_1279()
        periodo = PeriodoVacacional(
            funcionario=funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        self.assertEqual(periodo.contar_dias_por_regimen(), 30)
    
    def test_contar_dias_docente_115_retorna_30(self):
        """Docente decreto 115 retorna 30 días."""
        funcionario = crear_funcionario_docente_115()
        periodo = PeriodoVacacional(
            funcionario=funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        self.assertEqual(periodo.contar_dias_por_regimen(), 30)
    
    def test_contar_dias_docente_sin_decreto_retorna_0(self):
        """Docente sin decreto retorna 0."""
        user = User.objects.create_user(email="docente@test.com", password="test")
        estamento = Estamento.objects.get_or_create(
            nombre="Docente",
            defaults={"descripcion": "Docente"}
        )[0]
        facultad = FacultadDependencia.objects.get_or_create(
            nombre="Facultad",
            defaults={"descripcion": "Facultad"}
        )[0]
        sede = Sede.objects.get_or_create(
            nombre="Sede",
            defaults={"direccion": "Calle"}
        )[0]
        
        funcionario = Funcionario.objects.create(
            user=user,
            nombre="Docente",
            apellido="Sin Decreto",
            numero_identificacion="DOCSIN",
            telefono="3000000000",
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            decreto_resolucion="",
            estamento=estamento,
            facultad_dependencia=facultad,
            sede=sede,
        )
        periodo = PeriodoVacacional(
            funcionario=funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        self.assertEqual(periodo.contar_dias_por_regimen(), 0)
    
    def test_contar_dias_administrativo_retorna_15(self):
        """Administrativo retorna 15 días."""
        periodo = PeriodoVacacional(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        self.assertEqual(periodo.contar_dias_por_regimen(), 15)
    
    def test_contar_dias_trabajador_oficial_retorna_30(self):
        """Trabajador oficial retorna 30 días."""
        funcionario = crear_funcionario_trabajador_oficial()
        periodo = PeriodoVacacional(
            funcionario=funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        self.assertEqual(periodo.contar_dias_por_regimen(), 30)
    
    def test_contar_dias_estamento_desconocido_retorna_0(self):
        """Estamento desconocido retorna 0."""
        estamento = Estamento.objects.create(
            nombre="Desconocido",
            descripcion="Estamento desconocido"
        )
        user = User.objects.create_user(email="desconocido@test.com", password="test")
        funcionario = Funcionario.objects.create(
            user=user,
            nombre="Funcionario",
            apellido="Desconocido",
            numero_identificacion="DESC001",
            telefono="3000000000",
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            estamento=estamento,
            facultad_dependencia=self.facultad,
            sede=self.sede,
        )
        periodo = PeriodoVacacional(
            funcionario=funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        self.assertEqual(periodo.contar_dias_por_regimen(), 0)
    
    def test_save_calcula_dias_totales_automaticamente(self):
        """Al guardar calcula automáticamente días totales."""
        periodo = PeriodoVacacional(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        periodo.save()
        self.assertEqual(periodo.dias_totales_periodo, 15)
    
    def test_save_calcula_dias_pendientes_automaticamente(self):
        """Al guardar calcula automáticamente días pendientes."""
        periodo = PeriodoVacacional(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=5,
        )
        periodo.save()
        self.assertEqual(periodo.dias_pendientes_periodo, 10)
    
    def test_str_periodo_con_fechas_completas(self):
        """String representation con fechas completas."""
        periodo = PeriodoVacacional.objects.create(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date(2024, 1, 1),
            fecha_fin_periodo=date(2024, 12, 31),
            dias_disfrutados_periodo=0,
        )
        str_repr = str(periodo)
        self.assertIn("01/01/2024", str_repr)
        self.assertIn("31/12/2024", str_repr)
    
    def test_str_periodo_solo_fecha_inicio(self):
        """String representation solo con fecha inicio."""
        periodo = PeriodoVacacional(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date(2024, 1, 1),
            fecha_fin_periodo=None,
            dias_disfrutados_periodo=0,
        )
        str_repr = str(periodo)
        self.assertIn("01/01/2024", str_repr)
        self.assertIn("Desde", str_repr)
    
    def test_str_periodo_sin_fechas(self):
        """String representation sin fechas."""
        periodo = PeriodoVacacional(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=None,
            fecha_fin_periodo=None,
            dias_disfrutados_periodo=0,
        )
        self.assertEqual(str(periodo), "Fechas no definidas")

# ============================================================
# SolicitudVacaciones
# ============================================================
class SolicitudVacacionesModelTest(BaseTestCaseMixin, TestCase):
    """Pruebas para el modelo SolicitudVacaciones."""
    
    def setUp(self):
        super().setUp()
        self.ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
    
    def test_solicitud_funcionario_sin_antiguedad_raise_error(self):
        """Funcionario sin antigüedad mínima no puede solicitar."""
        funcionario_nuevo = Funcionario.objects.create(
            user=User.objects.create_user(email="nuevo@test.com", password="test"),
            nombre="Nuevo",
            apellido="Funcionario",
            numero_identificacion="NUEVO001",
            telefono="3000000000",
            fecha_ingreso_universidad=date.today() - timedelta(days=100),
            estamento=self.estamento_admin,
            facultad_dependencia=self.facultad,
            sede=self.sede,
        )
        periodo = PeriodoVacacional.objects.create(
            funcionario=funcionario_nuevo,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        solicitud = SolicitudVacaciones(
            funcionario=funcionario_nuevo,
            periodo_vacacional=periodo,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        with self.assertRaises(ValidationError):
            solicitud.full_clean()
    
    def test_solicitud_fecha_inicio_no_es_habil_raise_error(self):
        """Fecha inicio debe ser día hábil."""
        sabado = date.today()
        while sabado.weekday() != 5:
            sabado += timedelta(days=1)
        
        solicitud = SolicitudVacaciones(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=sabado,
            fecha_fin_vacaciones=sabado + timedelta(days=15),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        with self.assertRaises(ValidationError):
            solicitud.full_clean()
    
    def test_solicitud_fechas_se_cruzan_con_otra_raise_error(self):
        """No puede cruzar fechas con otra solicitud en revisión/aprobada."""
        solicitud1 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud='en_revision',
        )
        
        solicitud2 = SolicitudVacaciones(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=40),
            fecha_fin_vacaciones=date.today() + timedelta(days=55),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        with self.assertRaises(ValidationError):
            solicitud2.full_clean()
    
    def test_solicitud_dias_solicitados_superan_disponibles_raise_error(self):
        """Días solicitados no pueden superar días disponibles del periodo."""
        periodo = PeriodoVacacional.objects.create(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=10,
        )
        
        solicitud = SolicitudVacaciones(
            funcionario=self.funcionario_admin,
            periodo_vacacional=periodo,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=50),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        with self.assertRaises(ValidationError):
            solicitud.full_clean()
    
    def test_calcular_total_dias_docente_1279_15_habiles_15_calendario(self):
        """Docente 1279: 15 hábiles + 15 calendario."""
        funcionario = crear_funcionario_docente_1279()
        periodo = PeriodoVacacional.objects.create(
            funcionario=funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=funcionario,
            periodo_vacacional=periodo,
            fecha_inicio_vacaciones=date(2025, 2, 3),
            fecha_fin_vacaciones=date(2025, 3, 8),
            tiene_dias_pendientes=False,
            creada_por=funcionario.user,
        )
        self.assertEqual(solicitud.total_dias_solicitados, 30)
    
    def test_calcular_total_dias_docente_115_30_calendario(self):
        """Docente 115: 30 calendario."""
        funcionario = crear_funcionario_docente_115()
        periodo = PeriodoVacacional.objects.create(
            funcionario=funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=funcionario,
            periodo_vacacional=periodo,
            fecha_inicio_vacaciones=date(2025, 2, 1),
            fecha_fin_vacaciones=date(2025, 3, 2),
            tiene_dias_pendientes=False,
            creada_por=funcionario.user,
        )
        self.assertEqual(solicitud.total_dias_solicitados, 30)
    
    def test_calcular_total_dias_administrativo_solo_habiles(self):
        """Administrativo: solo hábiles."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date(2025, 2, 3),
            fecha_fin_vacaciones=date(2025, 2, 21),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        self.assertEqual(solicitud.total_dias_solicitados, 15)
    
    def test_calcular_total_dias_trabajador_oficial_30_calendario(self):
        """Trabajador oficial: 30 calendario."""
        funcionario = crear_funcionario_trabajador_oficial()
        periodo = PeriodoVacacional.objects.create(
            funcionario=funcionario,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=0,
        )
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=funcionario,
            periodo_vacacional=periodo,
            fecha_inicio_vacaciones=date(2025, 2, 1),
            fecha_fin_vacaciones=date(2025, 3, 2),
            tiene_dias_pendientes=False,
            creada_por=funcionario.user,
        )
        self.assertEqual(solicitud.total_dias_solicitados, 30)
    
    def test_calcular_total_dias_limita_por_dias_disponibles_periodo(self):
        """Limita por días disponibles del periodo."""
        periodo = PeriodoVacacional.objects.create(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=365),
            fecha_fin_periodo=date.today() - timedelta(days=200),
            dias_disfrutados_periodo=10,
        )
        periodo.refresh_from_db()
        dias_disponibles = periodo.dias_pendientes_periodo
        
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=periodo,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=50),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        solicitud._calcular_total_dias_solicitados()
        self.assertLessEqual(solicitud.total_dias_solicitados, dias_disponibles)
    
    def test_aprobaciones_ordenadas_retorna_jefe_coord_rrhh(self):
        """Aprobaciones ordenadas correctamente."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='pendiente',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='JEFE',
            estado='pendiente',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='COORD',
            estado='pendiente',
        )
        
        aprobaciones = solicitud.aprobaciones_ordenadas
        etapas = [a.etapa for a in aprobaciones]
        self.assertEqual(etapas, ['JEFE', 'COORD', 'RRHH'])
    
    def test_aprobada_por_jefe_true_cuando_jefe_aprobada(self):
        """Flag aprobada_por_jefe funciona."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='JEFE',
            estado='aprobada',
        )
        self.assertTrue(solicitud.aprobada_por_jefe)
    
    def test_aprobada_por_coord_true_cuando_coord_aprobada(self):
        """Flag aprobada_por_coord funciona."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='COORD',
            estado='aprobada',
        )
        self.assertTrue(solicitud.aprobada_por_coord)
    
    def test_autorizada_rrhh_true_cuando_rrhh_autorizada(self):
        """Flag autorizada_rrhh funciona."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        self.assertTrue(solicitud.autorizada_rrhh)
    
    def test_etapa_activa_retorna_primera_devuelta(self):
        """Etapa activa retorna primera devuelta."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='JEFE',
            estado='pendiente',
        )
        etapa_devuelta = AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='COORD',
            estado='devuelta',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='pendiente',
        )
        
        self.assertEqual(solicitud.etapa_activa, etapa_devuelta)
    
    def test_etapa_activa_retorna_primera_pendiente(self):
        """Etapa activa retorna primera pendiente si no hay devueltas."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        etapa_jefe = AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='JEFE',
            estado='pendiente',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='COORD',
            estado='pendiente',
        )
        
        self.assertEqual(solicitud.etapa_activa, etapa_jefe)
    
    def test_estado_global_rechazada_cuando_rrhh_rechaza(self):
        """Estado global rechazada cuando RRHH rechaza."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='rechazada',
        )
        self.assertEqual(solicitud.estado_global, 'rechazada')
    
    def test_estado_global_devuelta_cuando_jefe_o_coord_devuelve(self):
        """Estado global devuelta cuando JEFE/COORD devuelve."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='JEFE',
            estado='devuelta',
        )
        self.assertEqual(solicitud.estado_global, 'devuelta')
    
    def test_estado_global_autorizada_cuando_rrhh_autoriza(self):
        """Estado global autorizada cuando RRHH autoriza."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        self.assertEqual(solicitud.estado_global, 'autorizada')
    
    def test_colores_semaforo_verde_aprobada_rojo_devuelta_amarillo_pendiente(self):
        """Colores semáforo correctos."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='JEFE',
            estado='aprobada',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='COORD',
            estado='devuelta',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='pendiente',
        )
        
        colores = solicitud.colores_semaforo

        self.assertEqual(colores[0], 'verde')
        self.assertEqual(colores[1], 'rojo')
        self.assertEqual(colores[2], 'amarillo')
    
    def test_puede_editar_eliminar_pendiente_true(self):
        """Puede editar/eliminar cuando está pendiente."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud='pendiente',
        )
        self.assertTrue(solicitud.puede_editar_eliminar)
    
    def test_puede_editar_eliminar_devuelta_true(self):
        """Puede editar/eliminar cuando está devuelta."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='JEFE',
            estado='devuelta',
        )
        self.assertTrue(solicitud.puede_editar_eliminar)
    
    def test_puede_editar_eliminar_rechazada_false(self):
        """No puede editar/eliminar cuando está rechazada."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud='en_revision',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='rechazada',
        )
        self.assertFalse(solicitud.puede_editar_eliminar)
    
    def test_puede_editar_eliminar_autorizada_false(self):
        """No puede editar/eliminar cuando está autorizada."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud='en_revision',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        self.assertFalse(solicitud.puede_editar_eliminar)
    
    def test_genera_codigo_sabs_al_guardar_sin_codigo(self):
        """Genera código SABS automáticamente."""
        solicitud = SolicitudVacaciones(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        self.assertFalse(solicitud.codigo_sabs)
        solicitud.save()
        self.assertTrue(solicitud.codigo_sabs)
        self.assertTrue(solicitud.codigo_sabs.startswith('VAC'))
    
    def test_codigo_sabs_formato_correcto_vac_anio_consecutivo(self):
        """Formato correcto VAC{anio}{consecutivo}."""
        anio = date.today().year
        solicitud1 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        solicitud2 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=60),
            fecha_fin_vacaciones=date.today() + timedelta(days=75),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        
        self.assertTrue(solicitud1.codigo_sabs.startswith(f'VAC{anio}'))
        self.assertTrue(solicitud2.codigo_sabs.startswith(f'VAC{anio}'))

        num1 = int(solicitud1.codigo_sabs[len(f'VAC{anio}'):])
        num2 = int(solicitud2.codigo_sabs[len(f'VAC{anio}'):])
        self.assertEqual(num2, num1 + 1)
    
    def test_calcular_fecha_pago_reintegro_anticipado_none(self):
        """Fecha pago None para reintegro anticipado."""
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            es_por_reintegro_anticipado=True,
            creada_por=self.user,
        )
        self.assertIsNone(solicitud.fecha_pago)

# ============================================================
# ReintegroVacaciones
# ============================================================
class ReintegroVacacionesModelTest(BaseTestCaseMixin, TestCase):
    """Pruebas para el modelo ReintegroVacaciones."""
    
    def setUp(self):
        super().setUp()
        self.solicitud_autorizada = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=self.solicitud_autorizada.pk,
            solicitud=self.solicitud_autorizada,
            etapa='RRHH',
            estado='autorizada',
        )
        self.ct_reintegro = ContentType.objects.get_for_model(ReintegroVacaciones)
    
    def test_reintegro_fecha_disfrute_desde_posterior_hasta_raise_error(self):
        """Fecha disfrute desde no puede ser posterior a hasta."""
        reintegro = ReintegroVacaciones(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=45),
            fecha_disfrute_hasta=date.today() + timedelta(days=30),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        with self.assertRaises(ValidationError):
            reintegro.full_clean()
    
    def test_reintegro_anticipado_sin_observaciones_raise_error(self):
        """Reintegro anticipado requiere observaciones."""
        reintegro = ReintegroVacaciones(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="suspension_anticipada",
            es_reintegro_anticipado=True,
            observaciones="",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        with self.assertRaises(ValidationError):
            reintegro.full_clean()
    
    def test_reintegro_solicitud_no_autorizada_raise_error(self):
        """Solo se pueden crear reintegros de solicitudes autorizadas."""
        solicitud_no_autorizada = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=60),
            fecha_fin_vacaciones=date.today() + timedelta(days=75),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        
        reintegro = ReintegroVacaciones(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=80),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=60),
            fecha_disfrute_hasta=date.today() + timedelta(days=75),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=solicitud_no_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        with self.assertRaises(ValidationError):
            reintegro.full_clean()
    
    def test_reintegro_duplicado_activo_raise_error(self):
        """No puede haber reintegro activo duplicado por solicitud."""
        reintegro1 = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
            estado_solicitud='pendiente',
        )
        
        reintegro2 = ReintegroVacaciones(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=55),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        with self.assertRaises(ValidationError):
            reintegro2.full_clean()
    
    def test_reintegro_permite_multiple_si_anteriores_completados(self):
        """Permite múltiples reintegros si anteriores están completados."""
        reintegro1 = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
            estado_solicitud='completado',
        )
        
        solicitud2 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=60),
            fecha_fin_vacaciones=date.today() + timedelta(days=75),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud2.pk,
            solicitud=solicitud2,
            etapa='RRHH',
            estado='autorizada',
        )
        
        reintegro2 = ReintegroVacaciones.objects.create(
            fecha_reintegro=date.today() + timedelta(days=80),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=60),
            fecha_disfrute_hasta=date.today() + timedelta(days=75),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=solicitud2,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        self.assertIsNotNone(reintegro2.pk)
        self.assertTrue(reintegro2.codigo_sabs)
    
    def test_dias_disfrutados_total_suma_habiles_calendario(self):
        """Calcula total días disfrutados."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=3,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        self.assertEqual(reintegro.dias_disfrutados_total, 8)
    
    def test_dias_pendientes_total_suma_habiles_calendario(self):
        """Calcula total días pendientes."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=3,
            dias_pendientes_calendario=2,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        self.assertEqual(reintegro.dias_pendientes_total, 5)
    
    def test_tipo_dias_disfrutados_hc_cuando_ambos(self):
        """Tipo días disfrutados HC cuando ambos."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=3,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        self.assertEqual(reintegro.tipo_dias_disfrutados, 'HC')
    
    def test_tipo_dias_disfrutados_h_cuando_solo_habiles(self):
        """Tipo días disfrutados H cuando solo hábiles."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        self.assertEqual(reintegro.tipo_dias_disfrutados, 'H')
    
    def test_tipo_dias_disfrutados_c_cuando_solo_calendario(self):
        """Tipo días disfrutados C cuando solo calendario."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=0,
            dias_disfrutados_calendario=5,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        self.assertEqual(reintegro.tipo_dias_disfrutados, 'C')
    
    def test_tipo_dias_pendientes_hc_cuando_ambos(self):
        """Tipo días pendientes HC cuando ambos."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=0,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=3,
            dias_pendientes_calendario=2,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        self.assertEqual(reintegro.tipo_dias_pendientes, 'HC')
    
    def test_aprobaciones_ordenadas_retorna_jefe_coord_rrhh(self):
        """Aprobaciones ordenadas correctamente."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='RRHH',
            estado='pendiente',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='JEFE',
            estado='pendiente',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='COORD',
            estado='pendiente',
        )
        
        aprobaciones = reintegro.aprobaciones_ordenadas
        etapas = [a.etapa for a in aprobaciones]
        self.assertEqual(etapas, ['JEFE', 'COORD', 'RRHH'])
    
    def test_etapa_activa_retorna_primera_devuelta(self):
        """Etapa activa retorna primera devuelta."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        etapa_devuelta = AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='COORD',
            estado='devuelta',
        )
        self.assertEqual(reintegro.etapa_activa, etapa_devuelta)
    
    def test_etapa_activa_retorna_primera_pendiente(self):
        """Etapa activa retorna primera pendiente."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        etapa_jefe = AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='JEFE',
            estado='pendiente',
        )
        self.assertEqual(reintegro.etapa_activa, etapa_jefe)
    
    def test_estado_global_rechazada_cuando_rrhh_rechaza(self):
        """Estado global rechazada."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='RRHH',
            estado='rechazada',
        )
        self.assertEqual(reintegro.estado_global, 'rechazada')
    
    def test_estado_global_devuelta_cuando_jefe_o_coord_devuelve(self):
        """Estado global devuelta."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='JEFE',
            estado='devuelta',
        )
        self.assertEqual(reintegro.estado_global, 'devuelta')
    
    def test_estado_global_autorizada_cuando_rrhh_autoriza(self):
        """Estado global autorizada."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='RRHH',
            estado='autorizada',
        )
        self.assertEqual(reintegro.estado_global, 'autorizada')
    
    def test_colores_semaforo_correctos(self):
        """Colores semáforo correctos."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='JEFE',
            estado='aprobada',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='COORD',
            estado='devuelta',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='RRHH',
            estado='pendiente',
        )
        
        colores = reintegro.colores_semaforo

        self.assertEqual(colores[0], 'verde')
        self.assertEqual(colores[1], 'rojo')
        self.assertEqual(colores[2], 'amarillo')
    
    def test_puede_editar_eliminar_pendiente_true(self):
        """Puede editar/eliminar cuando pendiente."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
            estado_solicitud='pendiente',
        )
        self.assertTrue(reintegro.puede_editar_eliminar)
    
    def test_puede_editar_eliminar_devuelta_true(self):
        """Puede editar/eliminar cuando devuelta."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='JEFE',
            estado='devuelta',
        )
        self.assertTrue(reintegro.puede_editar_eliminar)
    
    def test_puede_editar_eliminar_rechazada_false(self):
        """No puede editar/eliminar cuando rechazada."""
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
            estado_solicitud='en_revision',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=reintegro.pk,
            etapa='RRHH',
            estado='rechazada',
        )
        self.assertFalse(reintegro.puede_editar_eliminar)
    
    def test_genera_codigo_sabs_al_guardar_sin_codigo(self):
        """Genera código SABS automáticamente."""
        reintegro = ReintegroVacaciones(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        self.assertFalse(reintegro.codigo_sabs)
        reintegro.save()
        self.assertTrue(reintegro.codigo_sabs)
        self.assertTrue(reintegro.codigo_sabs.startswith('REI'))
    
    def test_codigo_sabs_formato_correcto_rei_anio_consecutivo(self):
        """Formato correcto REI{anio}{consecutivo}."""
        anio = date.today().year
        reintegro1 = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        
        solicitud2 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=60),
            fecha_fin_vacaciones=date.today() + timedelta(days=75),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud2.pk,
            solicitud=solicitud2,
            etapa='RRHH',
            estado='autorizada',
        )
        
        reintegro2 = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=80),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=60),
            fecha_disfrute_hasta=date.today() + timedelta(days=75),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=solicitud2,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        
        self.assertTrue(reintegro1.codigo_sabs.startswith(f'REI{anio}'))
        self.assertTrue(reintegro2.codigo_sabs.startswith(f'REI{anio}'))
        num1 = int(reintegro1.codigo_sabs[len(f'REI{anio}'):])
        num2 = int(reintegro2.codigo_sabs[len(f'REI{anio}'):])
        self.assertEqual(num2, num1 + 1)
    
    def test_actualizar_resumen_dias_calcula_totales(self):
        """Actualiza días disfrutados y pendientes totales."""
        reintegro = ReintegroVacaciones(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=3,
            dias_pendientes_habiles=2,
            dias_pendientes_calendario=1,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        reintegro._actualizar_resumen_dias()
        self.assertEqual(reintegro.dias_disfrutados, 8)
        self.assertEqual(reintegro.dias_pendientes, 3)
    
    def test_actualizar_resumen_dias_actualiza_tipos(self):
        """Actualiza tipos de días correctamente."""
        reintegro = ReintegroVacaciones(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=3,
            dias_pendientes_habiles=2,
            dias_pendientes_calendario=1,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud_autorizada,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        reintegro._actualizar_resumen_dias()
        self.assertEqual(reintegro.tipo_dias_disfrutados, 'HC')
        self.assertEqual(reintegro.tipo_dias_pendientes, 'HC')

# ============================================================
# AprobacionEtapa
# ============================================================
class AprobacionEtapaModelTest(BaseTestCaseMixin, TestCase):
    """Pruebas para el modelo AprobacionEtapa."""
    
    def setUp(self):
        super().setUp()
        self.solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        self.ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
    
    def test_aprobacion_unique_constraint_por_content_object_etapa(self):
        """Constraint único por content_object y etapa."""
        aprobacion1 = AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='JEFE',
            estado='pendiente',
        )
        
        aprobacion2 = AprobacionEtapa(
            content_type=self.ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='JEFE',
            estado='pendiente',
        )
        with self.assertRaises(Exception):
            aprobacion2.save()
    
    def test_aprobacion_save_asigna_content_type_si_tiene_solicitud(self):
        """Asigna content_type automáticamente."""
        aprobacion = AprobacionEtapa(
            solicitud=self.solicitud,
            etapa='JEFE',
            estado='pendiente',
        )
        aprobacion.save()
        self.assertEqual(aprobacion.content_type, self.ct_solicitud)
        self.assertEqual(aprobacion.object_id, self.solicitud.pk)
    
    def test_str_aprobacion_con_codigo_sabs(self):
        """String representation con código SABS."""
        aprobacion = AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='JEFE',
            estado='aprobada',
        )
        str_repr = str(aprobacion)
        self.assertIn('Jefe Inmediato', str_repr)
        self.assertIn('Aprobada', str_repr)
        self.assertIn(self.solicitud.codigo_sabs, str_repr)
    
    def test_str_aprobacion_sin_codigo_sabs(self):
        """String representation sin código SABS."""
        aprobacion = AprobacionEtapa(
            content_type=self.ct_solicitud,
            object_id=99999,
            etapa='JEFE',
            estado='pendiente',
        )
        str_repr = str(aprobacion)
        self.assertIn('Jefe Inmediato', str_repr)
        self.assertIn('ID 99999', str_repr)
    
    def test_aprobacion_relacion_con_solicitud(self):
        """Relación con solicitud funciona."""
        aprobacion = AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='JEFE',
            estado='pendiente',
        )
        self.assertEqual(aprobacion.solicitud, self.solicitud)
        self.assertIn(aprobacion, self.solicitud.aprobaciones.all())
    
    def test_aprobacion_relacion_con_reintegro(self):
        """Relación con reintegro funciona."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        ct_reintegro = ContentType.objects.get_for_model(ReintegroVacaciones)
        aprobacion = AprobacionEtapa.objects.create(
            content_type=ct_reintegro,
            object_id=reintegro.pk,
            etapa='JEFE',
            estado='pendiente',
        )
        self.assertEqual(aprobacion.content_object, reintegro)
    
    def test_aprobacion_generic_relation_funciona(self):
        """Generic relation funciona correctamente."""
        aprobacion = AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='JEFE',
            estado='pendiente',
        )
        self.assertIn(aprobacion, self.solicitud.aprobaciones.all())
        self.assertEqual(aprobacion.content_object, self.solicitud)
    
    def test_aprobacion_estados_validos(self):
        """Estados válidos funcionan."""
        estados_validos = ['pendiente', 'aprobada', 'devuelta', 'rechazada', 'autorizada']
        for estado in estados_validos:
            aprobacion = AprobacionEtapa(
                content_type=self.ct_solicitud,
                object_id=self.solicitud.pk,
                solicitud=self.solicitud,
                etapa='JEFE',
                estado=estado,
            )
            aprobacion.full_clean()
    
    def test_aprobacion_etapas_validas(self):
        """Etapas válidas funcionan."""
        etapas_validas = ['JEFE', 'COORD', 'RRHH']
        for etapa in etapas_validas:
            aprobacion = AprobacionEtapa(
                content_type=self.ct_solicitud,
                object_id=self.solicitud.pk,
                solicitud=self.solicitud,
                etapa=etapa,
                estado='pendiente',
            )
            aprobacion.full_clean()
    
    def test_aprobacion_actualizado_por_se_guarda(self):
        """Campo actualizado_por se guarda correctamente."""
        aprobacion = AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='JEFE',
            estado='pendiente',
            actualizado_por=self.user,
        )
        self.assertEqual(aprobacion.actualizado_por, self.user)

# ============================================================
# HistoricoAcciones
# ============================================================
class HistoricoAccionesModelTest(BaseTestCaseMixin, TestCase):
    """Pruebas para el modelo HistoricoAcciones."""
    
    def setUp(self):
        super().setUp()
        self.solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
    
    def test_historico_save_solicitud_anula_reintegro(self):
        """Al guardar solicitud, anula reintegro."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        
        historico = HistoricoAcciones(
            accion_realizada='aprobacion',
            tipo_accion='solicitud',
            usuario=self.user,
            solicitud_vacaciones=self.solicitud,
            reintegro_vacaciones=reintegro,
            grupo_autorizador='Jefe Inmediato',
            nuevo_estado='aprobada',
        )
        historico.save()
        historico.refresh_from_db()
        self.assertIsNone(historico.reintegro_vacaciones)
    
    def test_historico_save_reintegro_anula_solicitud(self):
        """Al guardar reintegro, anula solicitud."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        
        reintegro = ReintegroVacaciones.objects.create(
            codigo_sabs="",
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro="finalizacion_normal",
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=self.solicitud,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        
        historico = HistoricoAcciones(
            accion_realizada='aprobacion',
            tipo_accion='reintegro',
            usuario=self.user,
            reintegro_vacaciones=reintegro,
            solicitud_vacaciones=self.solicitud,
            grupo_autorizador='Jefe Inmediato',
            nuevo_estado='aprobada',
        )
        historico.save()
        historico.refresh_from_db()
        self.assertIsNone(historico.solicitud_vacaciones)
    
    def test_str_historico_con_accion_y_usuario(self):
        """String representation correcta."""
        historico = HistoricoAcciones.objects.create(
            accion_realizada='aprobacion',
            tipo_accion='solicitud',
            usuario=self.user,
            solicitud_vacaciones=self.solicitud,
            grupo_autorizador='Jefe Inmediato',
            nuevo_estado='aprobada',
        )
        str_repr = str(historico)
        self.assertIn('Solicitud', str_repr)
        self.assertIn('Aprobación', str_repr)
        self.assertIn(self.user.email, str_repr)
    
    def test_historico_tipos_accion_validos(self):
        """Tipos de acción válidos."""
        tipos_validos = ['solicitud', 'reintegro']
        for tipo in tipos_validos:
            historico = HistoricoAcciones(
                accion_realizada='creacion',
                tipo_accion=tipo,
                usuario=self.user,
                solicitud_vacaciones=self.solicitud if tipo == 'solicitud' else None,
                reintegro_vacaciones=None if tipo == 'solicitud' else None,
            )
            historico.full_clean()
    
    def test_historico_acciones_realizadas_validas(self):
        """Acciones realizadas válidas."""
        acciones_validas = ['creacion', 'edicion', 'aprobacion', 'rechazo', 'observacion', 'cancelacion']
        for accion in acciones_validas:
            historico = HistoricoAcciones(
                accion_realizada=accion,
                tipo_accion='solicitud',
                usuario=self.user,
                solicitud_vacaciones=self.solicitud,
            )
            historico.full_clean()
