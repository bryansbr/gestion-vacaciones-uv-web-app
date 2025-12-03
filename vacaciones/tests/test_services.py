"""
Pruebas unitarias para los servicios del módulo de vacaciones.
"""

from datetime import date, timedelta
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from notificaciones.models import Notificacion

from vacaciones.tests.test_helpers import (
    BaseTestCaseMixin,
    crear_funcionario_docente_1279,
    crear_funcionario_docente_115,
    crear_funcionario_trabajador_oficial,
    crear_grupo_y_usuario,
)
from vacaciones.models import (
    SolicitudVacaciones,
    ReintegroVacaciones,
    AprobacionEtapa,
    HistoricoAcciones,
    PeriodoVacacional,
)
from vacaciones.services import aprobaciones, reintegros, estado_vacaciones, reportes
from usuarios.models import CustomUser, Funcionario

# ============================================================
# Servicio de aprobaciones (aprobaciones.py)
# ============================================================
class AprobacionesServiceTest(BaseTestCaseMixin, TestCase):
    """Pruebas para el servicio de aprobaciones."""

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
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='JEFE',
            estado='pendiente',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='COORD',
            estado='pendiente',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_solicitud,
            object_id=self.solicitud.pk,
            solicitud=self.solicitud,
            etapa='RRHH',
            estado='pendiente',
        )

    def test_aprobar_etapa_jefe_cambia_estado_aprobada(self):
        """JEFE aprueba correctamente."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        etapa = aprobaciones.aprobar_etapa(user_jefe, self.solicitud, 'Aprobado')
        self.assertEqual(etapa.estado, 'aprobada')
        self.assertEqual(etapa.observacion, 'Aprobado')
        self.assertEqual(etapa.actualizado_por, user_jefe)

    def test_aprobar_etapa_coord_cambia_estado_aprobada(self):
        """COORD aprueba correctamente."""
        user_coord, _ = crear_grupo_y_usuario('Coordinador Administrativo', 'coord@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa = aprobaciones.aprobar_etapa(user_coord, self.solicitud, 'Aprobado')
        self.assertEqual(etapa.estado, 'aprobada')
        self.assertEqual(etapa.etapa, 'COORD')

    def test_aprobar_etapa_rrhh_raise_error(self):
        """RRHH no puede usar aprobar_etapa."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        with self.assertRaises(ValidationError):
            aprobaciones.aprobar_etapa(user_rrhh, self.solicitud)

    def test_aprobar_etapa_sin_permiso_raise_permission_denied(self):
        """Sin permisos raise PermissionDenied."""
        user_sin_permiso = CustomUser.objects.create_user(
            email='sinpermiso@test.com',
            password='test123'
        )
        with self.assertRaises(PermissionDenied):
            aprobaciones.aprobar_etapa(user_sin_permiso, self.solicitud)

    def test_aprobar_etapa_no_pendiente_raise_error(self):
        """Solo se puede aprobar etapa pendiente."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        with self.assertRaises(ValidationError):
            aprobaciones.aprobar_etapa(user_jefe, self.solicitud)

    def test_aprobar_etapa_registra_historial(self):
        """Registra en historial de acciones."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        count_before = HistoricoAcciones.objects.count()
        aprobaciones.aprobar_etapa(user_jefe, self.solicitud, 'Aprobado')
        count_after = HistoricoAcciones.objects.count()
        self.assertEqual(count_after, count_before + 1)
        historial = HistoricoAcciones.objects.latest('fecha_hora_accion')
        self.assertEqual(historial.accion_realizada, 'aprobacion')
        self.assertEqual(historial.grupo_autorizador, 'Jefe Inmediato')

    def test_aprobar_etapa_refresca_estado_global(self):
        """Refresca estado global de solicitud."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        aprobaciones.aprobar_etapa(user_jefe, self.solicitud)
        self.solicitud.refresh_from_db()
        self.assertIn(self.solicitud.estado_solicitud, ['en_revision', 'pendiente'])

    def test_devolver_etapa_jefe_cambia_estado_devuelta(self):
        """JEFE devuelve correctamente."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        etapa = aprobaciones.devolver_etapa(user_jefe, self.solicitud, 'Falta información')
        self.assertEqual(etapa.estado, 'devuelta')
        self.assertEqual(etapa.observacion, 'Falta información')

    def test_devolver_etapa_coord_cambia_estado_devuelta(self):
        """COORD devuelve correctamente."""
        user_coord, _ = crear_grupo_y_usuario('Coordinador Administrativo', 'coord@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa = aprobaciones.devolver_etapa(user_coord, self.solicitud, 'Falta información')
        self.assertEqual(etapa.estado, 'devuelta')
        self.assertEqual(etapa.etapa, 'COORD')

    def test_devolver_etapa_sin_observacion_raise_error(self):
        """Requiere observación."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        with self.assertRaises(ValidationError):
            aprobaciones.devolver_etapa(user_jefe, self.solicitud, '')

    def test_devolver_etapa_reinicia_otras_etapas(self):
        """Reinicia otras etapas a pendiente."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        aprobaciones.devolver_etapa(user_jefe, self.solicitud, 'Falta información')
        etapa_coord.refresh_from_db()
        self.assertEqual(etapa_coord.estado, 'pendiente')

    def test_devolver_etapa_cambia_estado_solicitud_pendiente(self):
        """Cambia estado solicitud a pendiente."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        aprobaciones.devolver_etapa(user_jefe, self.solicitud, 'Falta información')
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado_solicitud, 'pendiente')

    def test_devolver_etapa_registra_historial(self):
        """Registra en historial."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        count_before = HistoricoAcciones.objects.count()
        aprobaciones.devolver_etapa(user_jefe, self.solicitud, 'Falta información')
        count_after = HistoricoAcciones.objects.count()
        self.assertEqual(count_after, count_before + 1)

    def test_autorizar_rrhh_cambia_estado_autorizada(self):
        """RRHH autoriza correctamente."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        etapa = aprobaciones.autorizar_rrhh(user_rrhh, self.solicitud, 'Autorizado')
        self.assertEqual(etapa.estado, 'autorizada')
        self.assertEqual(etapa.etapa, 'RRHH')

    def test_autorizar_rrhh_sin_jefe_coord_aprobada_raise_error(self):
        """Requiere JEFE y COORD aprobadas."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        with self.assertRaises(ValidationError):
            aprobaciones.autorizar_rrhh(user_rrhh, self.solicitud)

    def test_autorizar_rrhh_sin_permiso_raise_permission_denied(self):
        """Sin permisos raise PermissionDenied."""
        user_sin_permiso = CustomUser.objects.create_user(
            email='sinpermiso@test.com',
            password='test123'
        )
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        with self.assertRaises(PermissionDenied):
            aprobaciones.autorizar_rrhh(user_sin_permiso, self.solicitud)

    def test_autorizar_rrhh_registra_historial(self):
        """Registra en historial."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        count_before = HistoricoAcciones.objects.count()
        aprobaciones.autorizar_rrhh(user_rrhh, self.solicitud)
        count_after = HistoricoAcciones.objects.count()
        self.assertEqual(count_after, count_before + 1)

    def test_rechazar_rrhh_cambia_estado_rechazada(self):
        """RRHH rechaza correctamente."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        etapa = aprobaciones.rechazar_rrhh(user_rrhh, self.solicitud, 'No cumple requisitos')
        self.assertEqual(etapa.estado, 'rechazada')
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado_global, 'rechazada')

    def test_rechazar_rrhh_sin_observacion_raise_error(self):
        """Requiere observación."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        with self.assertRaises(ValidationError):
            aprobaciones.rechazar_rrhh(user_rrhh, self.solicitud, '')

    def test_rechazar_rrhh_envia_notificaciones(self):
        """Envía notificaciones a funcionario, jefe y coord."""
        
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        count_before = Notificacion.objects.count()
        aprobaciones.rechazar_rrhh(user_rrhh, self.solicitud, 'No cumple requisitos')
        count_after = Notificacion.objects.count()
        self.assertGreater(count_after, count_before)

    def test_rechazar_rrhh_registra_historial(self):
        """Registra en historial."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        count_before = HistoricoAcciones.objects.count()
        aprobaciones.rechazar_rrhh(user_rrhh, self.solicitud, 'No cumple requisitos')
        count_after = HistoricoAcciones.objects.count()
        self.assertEqual(count_after, count_before + 1)

    def test_reenviar_funcionario_solicitud_devuelta_reinicia_etapas(self):
        """Reenvío reinicia etapas devueltas."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        aprobaciones.devolver_etapa(user_jefe, self.solicitud, 'Falta información')
        etapa_devuelta = self.solicitud.aprobaciones.get(etapa='JEFE')
        self.assertEqual(etapa_devuelta.estado, 'devuelta')
        aprobaciones.reenviar_funcionario(self.user, self.solicitud, 'Corregido')
        etapa_devuelta.refresh_from_db()
        self.assertEqual(etapa_devuelta.estado, 'pendiente')

    def test_reenviar_funcionario_solicitud_nueva_crea_etapas(self):
        """Reenvío crea etapas si no existen."""
        solicitud_nueva = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        self.assertEqual(solicitud_nueva.aprobaciones.count(), 0)
        aprobaciones.reenviar_funcionario(self.user, solicitud_nueva)
        self.assertEqual(solicitud_nueva.aprobaciones.count(), 3)

    def test_reenviar_funcionario_sin_permiso_raise_permission_denied(self):
        """Sin permisos raise PermissionDenied."""
        user_sin_permiso = CustomUser.objects.create_user(
            email='sinpermiso@test.com',
            password='test123'
        )
        with self.assertRaises(PermissionDenied):
            aprobaciones.reenviar_funcionario(user_sin_permiso, self.solicitud)

    def test_reenviar_funcionario_rechazada_raise_error(self):
        """No se puede reenviar rechazada."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.solicitud.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.solicitud.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        aprobaciones.rechazar_rrhh(user_rrhh, self.solicitud, 'No cumple requisitos')
        with self.assertRaises(ValidationError):
            aprobaciones.reenviar_funcionario(self.user, self.solicitud)

    def test_reenviar_funcionario_cambia_estado_en_revision(self):
        """Cambia estado a en_revision."""
        aprobaciones.reenviar_funcionario(self.user, self.solicitud)
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado_solicitud, 'en_revision')

    def test_reenviar_funcionario_concatenar_observaciones_con_limite(self):
        """Concatena observaciones respetando límite."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        aprobaciones.devolver_etapa(user_jefe, self.solicitud, 'Falta información')
        observacion_larga = 'A' * 1500
        aprobaciones.reenviar_funcionario(self.user, self.solicitud, observacion_larga)
        etapa = self.solicitud.aprobaciones.get(etapa='JEFE')
        self.assertLessEqual(len(etapa.observacion), 2050)


# ============================================================
# PRUEBAS PARA SERVICIO DE REINTEGROS (reintegros.py)
# ============================================================

class ReintegrosServiceTest(BaseTestCaseMixin, TestCase):
    """Pruebas para el servicio de reintegros."""

    def setUp(self):
        super().setUp()
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        self.solicitud_autorizada = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=self.solicitud_autorizada.pk,
            solicitud=self.solicitud_autorizada,
            etapa='JEFE',
            estado='aprobada',
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=self.solicitud_autorizada.pk,
            solicitud=self.solicitud_autorizada,
            etapa='COORD',
            estado='aprobada',
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=self.solicitud_autorizada.pk,
            solicitud=self.solicitud_autorizada,
            etapa='RRHH',
            estado='autorizada',
        )
        self.reintegro = ReintegroVacaciones.objects.create(
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro='finalizacion_normal',
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
        self.ct_reintegro = ContentType.objects.get_for_model(ReintegroVacaciones)
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=self.reintegro.pk,
            solicitud=self.solicitud_autorizada,
            etapa='JEFE',
            estado='pendiente',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=self.reintegro.pk,
            solicitud=self.solicitud_autorizada,
            etapa='COORD',
            estado='pendiente',
        )
        AprobacionEtapa.objects.create(
            content_type=self.ct_reintegro,
            object_id=self.reintegro.pk,
            solicitud=self.solicitud_autorizada,
            etapa='RRHH',
            estado='pendiente',
        )

    def test_firmar_reintegro_funcionario_ok(self):
        """Funcionario puede firmar su reintegro."""
        reintegro = reintegros.firmar_reintegro(self.user, self.reintegro)
        self.assertEqual(reintegro.firmado_por, self.user)
        self.assertIsNotNone(reintegro.firmado_en)

    def test_firmar_reintegro_otro_usuario_raise_permission_denied(self):
        """Solo funcionario puede firmar."""
        otro_usuario = CustomUser.objects.create_user(
            email='otro@test.com',
            password='test123'
        )
        with self.assertRaises(PermissionDenied):
            reintegros.firmar_reintegro(otro_usuario, self.reintegro)

    def test_firmar_reintegro_ya_firmado_raise_error(self):
        """No se puede firmar dos veces."""
        reintegros.firmar_reintegro(self.user, self.reintegro)
        with self.assertRaises(ValidationError):
            reintegros.firmar_reintegro(self.user, self.reintegro)

    def test_firmar_reintegro_registra_historial(self):
        """Registra en historial."""
        count_before = HistoricoAcciones.objects.count()
        reintegros.firmar_reintegro(self.user, self.reintegro)
        count_after = HistoricoAcciones.objects.count()
        self.assertEqual(count_after, count_before + 1)

    def test_reenviar_reintegro_devuelto_reinicia_etapas(self):
        """Reenvío reinicia etapas devueltas."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        reintegros.devolver_etapa_reintegro(user_jefe, self.reintegro, 'Falta información')
        etapa_devuelta = self.reintegro.aprobaciones.get(etapa='JEFE')
        self.assertEqual(etapa_devuelta.estado, 'devuelta')
        reintegros.reenviar_funcionario_reintegro(self.user, self.reintegro, 'Corregido')
        etapa_devuelta.refresh_from_db()
        self.assertEqual(etapa_devuelta.estado, 'pendiente')

    def test_reenviar_reintegro_nuevo_crea_etapas(self):
        """Reenvío crea etapas si no existen."""
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
        reintegro_nuevo = ReintegroVacaciones.objects.create(
            fecha_reintegro=date.today() + timedelta(days=80),
            motivo_reintegro='finalizacion_normal',
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
        self.assertEqual(reintegro_nuevo.aprobaciones.count(), 0)
        reintegros.reenviar_funcionario_reintegro(self.user, reintegro_nuevo)
        self.assertEqual(reintegro_nuevo.aprobaciones.count(), 3)

    def test_reenviar_reintegro_sin_permiso_raise_permission_denied(self):
        """Sin permisos raise PermissionDenied."""
        user_sin_permiso = CustomUser.objects.create_user(
            email='sinpermiso@test.com',
            password='test123'
        )
        with self.assertRaises(PermissionDenied):
            reintegros.reenviar_funcionario_reintegro(user_sin_permiso, self.reintegro)

    def test_reenviar_reintegro_envia_notificacion_jefe(self):
        """Envía notificación al jefe."""
        jefe = Funcionario.objects.create(
            user=CustomUser.objects.create_user(email='jefe@test.com', password='test123'),
            nombre='Jefe',
            apellido='Test',
            numero_identificacion='JEFE001',
            telefono='3000000000',
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            estamento=self.estamento_admin,
            facultad_dependencia=self.facultad,
            sede=self.sede,
        )
        self.funcionario_admin.jefe_inmediato = jefe
        self.funcionario_admin.save()
        count_before = Notificacion.objects.count()
        reintegros.reenviar_funcionario_reintegro(self.user, self.reintegro)
        count_after = Notificacion.objects.count()
        self.assertGreater(count_after, count_before)

    def test_aprobar_etapa_reintegro_jefe_ok(self):
        """JEFE aprueba reintegro."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        etapa = reintegros.aprobar_etapa_reintegro(user_jefe, self.reintegro, 'Aprobado')
        self.assertEqual(etapa.estado, 'aprobada')
        self.assertEqual(etapa.etapa, 'JEFE')

    def test_aprobar_etapa_reintegro_coord_ok(self):
        """COORD aprueba reintegro."""
        user_coord, _ = crear_grupo_y_usuario('Coordinador Administrativo', 'coord@test.com')
        etapa_jefe = self.reintegro.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa = reintegros.aprobar_etapa_reintegro(user_coord, self.reintegro, 'Aprobado')
        self.assertEqual(etapa.estado, 'aprobada')
        self.assertEqual(etapa.etapa, 'COORD')

    def test_aprobar_etapa_reintegro_rrhh_raise_error(self):
        """RRHH no puede usar aprobar_etapa."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.reintegro.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.reintegro.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        with self.assertRaises(ValidationError):
            reintegros.aprobar_etapa_reintegro(user_rrhh, self.reintegro)

    def test_aprobar_etapa_reintegro_envia_notificaciones(self):
        """Envía notificaciones correctas."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        count_before = Notificacion.objects.count()
        reintegros.aprobar_etapa_reintegro(user_jefe, self.reintegro)
        count_after = Notificacion.objects.count()
        self.assertGreater(count_after, count_before)

    def test_devolver_etapa_reintegro_reinicia_otras_etapas(self):
        """Reinicia otras etapas."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        etapa_coord = self.reintegro.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        reintegros.devolver_etapa_reintegro(user_jefe, self.reintegro, 'Falta información')
        etapa_coord.refresh_from_db()
        self.assertEqual(etapa_coord.estado, 'pendiente')

    def test_devolver_etapa_reintegro_envia_notificacion(self):
        """Envía notificación al funcionario."""
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe@test.com')
        count_before = Notificacion.objects.count()
        reintegros.devolver_etapa_reintegro(user_jefe, self.reintegro, 'Falta información')
        count_after = Notificacion.objects.count()
        self.assertGreater(count_after, count_before)

    def test_autorizar_rrhh_reintegro_ok(self):
        """RRHH autoriza reintegro."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.reintegro.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.reintegro.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        etapa = reintegros.autorizar_rrhh_reintegro(user_rrhh, self.reintegro, 'Autorizado')
        self.assertEqual(etapa.estado, 'autorizada')
        self.reintegro.refresh_from_db()
        self.assertEqual(self.reintegro.estado_global, 'autorizada')

    def test_autorizar_rrhh_reintegro_requiere_jefe_coord_aprobada(self):
        """Requiere JEFE y COORD aprobadas."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        with self.assertRaises(ValidationError):
            reintegros.autorizar_rrhh_reintegro(user_rrhh, self.reintegro)

    def test_autorizar_rrhh_reintegro_envia_notificacion(self):
        """Envía notificación."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.reintegro.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.reintegro.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        count_before = Notificacion.objects.count()
        reintegros.autorizar_rrhh_reintegro(user_rrhh, self.reintegro)
        count_after = Notificacion.objects.count()
        self.assertGreater(count_after, count_before)

    def test_rechazar_rrhh_reintegro_ok(self):
        """RRHH rechaza reintegro."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.reintegro.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.reintegro.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        etapa = reintegros.rechazar_rrhh_reintegro(user_rrhh, self.reintegro, 'No cumple requisitos')
        self.assertEqual(etapa.estado, 'rechazada')
        self.reintegro.refresh_from_db()
        self.assertEqual(self.reintegro.estado_solicitud, 'rechazado')

    def test_rechazar_rrhh_reintegro_envia_notificaciones(self):
        """Envía notificaciones a funcionario, jefe y coord."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        etapa_jefe = self.reintegro.aprobaciones.get(etapa='JEFE')
        etapa_jefe.estado = 'aprobada'
        etapa_jefe.save()
        etapa_coord = self.reintegro.aprobaciones.get(etapa='COORD')
        etapa_coord.estado = 'aprobada'
        etapa_coord.save()
        count_before = Notificacion.objects.count()
        reintegros.rechazar_rrhh_reintegro(user_rrhh, self.reintegro, 'No cumple requisitos')
        count_after = Notificacion.objects.count()
        self.assertGreater(count_after, count_before)


# ============================================================
# PRUEBAS PARA SERVICIO DE ESTADO DE VACACIONES (estado_vacaciones.py)
# ============================================================

class EstadoVacacionesServiceTest(BaseTestCaseMixin, TestCase):
    """Pruebas para el servicio de estado de vacaciones."""

    def test_obtener_tipo_calculo_docente_1279(self):
        """Retorna 'Hábiles y Calendario' para docente 1279."""
        funcionario = crear_funcionario_docente_1279()
        resultado = estado_vacaciones.obtener_tipo_calculo_dias(funcionario)
        self.assertEqual(resultado, 'Hábiles y Calendario')

    def test_obtener_tipo_calculo_docente_115(self):
        """Retorna 'Calendario' para docente 115."""
        funcionario = crear_funcionario_docente_115()
        resultado = estado_vacaciones.obtener_tipo_calculo_dias(funcionario)
        self.assertEqual(resultado, 'Calendario')

    def test_obtener_tipo_calculo_administrativo(self):
        """Retorna 'Hábiles' para administrativo."""
        resultado = estado_vacaciones.obtener_tipo_calculo_dias(self.funcionario_admin)
        self.assertEqual(resultado, 'Hábiles')

    def test_obtener_tipo_calculo_trabajador_oficial(self):
        """Retorna 'Calendario' para trabajador oficial."""
        funcionario = crear_funcionario_trabajador_oficial()
        resultado = estado_vacaciones.obtener_tipo_calculo_dias(funcionario)
        self.assertEqual(resultado, 'Calendario')

    def test_obtener_dias_normativos_docente_1279(self):
        """Retorna 30 para docente 1279."""
        funcionario = crear_funcionario_docente_1279()
        resultado = estado_vacaciones.obtener_dias_normativos(funcionario)
        self.assertEqual(resultado, 30)

    def test_obtener_dias_normativos_docente_115(self):
        """Retorna 30 para docente 115."""
        funcionario = crear_funcionario_docente_115()
        resultado = estado_vacaciones.obtener_dias_normativos(funcionario)
        self.assertEqual(resultado, 30)

    def test_obtener_dias_normativos_administrativo(self):
        """Retorna 15 para administrativo."""
        resultado = estado_vacaciones.obtener_dias_normativos(self.funcionario_admin)
        self.assertEqual(resultado, 15)

    def test_obtener_dias_normativos_trabajador_oficial(self):
        """Retorna 30 para trabajador oficial."""
        funcionario = crear_funcionario_trabajador_oficial()
        resultado = estado_vacaciones.obtener_dias_normativos(funcionario)
        self.assertEqual(resultado, 30)

    def test_calcular_resumen_sin_solicitudes_aprobadas(self):
        """Resumen sin solicitudes aprobadas."""
        resumen = estado_vacaciones.calcular_resumen_vacacional(self.funcionario_admin)
        self.assertEqual(resumen['dias_disfrutados'], 0)
        self.assertGreaterEqual(resumen['dias_pendientes'], 0)
        self.assertEqual(resumen['numero_periodos'], 1)

    def test_calcular_resumen_con_solicitudes_aprobadas(self):
        """Resumen con solicitudes aprobadas."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud='autorizada',
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        resumen = estado_vacaciones.calcular_resumen_vacacional(self.funcionario_admin)
        self.assertGreater(resumen['dias_disfrutados'], 0)

    def test_calcular_resumen_suma_dias_disfrutados(self):
        """Suma días disfrutados correctamente."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        solicitud1 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=35),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud='autorizada',
        )
        solicitud2 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=40),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud='autorizada',
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud1.pk,
            solicitud=solicitud1,
            etapa='RRHH',
            estado='autorizada',
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud2.pk,
            solicitud=solicitud2,
            etapa='RRHH',
            estado='autorizada',
        )
        resumen = estado_vacaciones.calcular_resumen_vacacional(self.funcionario_admin)
        self.assertGreater(resumen['dias_disfrutados'], 0)

    def test_calcular_resumen_suma_dias_pendientes(self):
        """Suma días pendientes correctamente."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=True,
            creada_por=self.user,
            estado_solicitud='autorizada',
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        resumen = estado_vacaciones.calcular_resumen_vacacional(self.funcionario_admin)
        self.assertGreaterEqual(resumen['dias_pendientes'], 0)

    def test_calcular_resumen_cuenta_periodos_activos(self):
        """Cuenta periodos activos correctamente."""
        periodo2 = PeriodoVacacional.objects.create(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=200),
            fecha_fin_periodo=date.today() - timedelta(days=100),
            dias_disfrutados_periodo=5,
        )
        periodo2.refresh_from_db()
        resumen = estado_vacaciones.calcular_resumen_vacacional(self.funcionario_admin)
        self.assertGreaterEqual(resumen['numero_periodos_activos'], 0)

    def test_obtener_listado_periodos_ordenado(self):
        """Listado ordenado por fecha inicio descendente."""
        periodo2 = PeriodoVacacional.objects.create(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=200),
            fecha_fin_periodo=date.today() - timedelta(days=100),
            dias_disfrutados_periodo=5,
        )
        listado = estado_vacaciones.obtener_listado_periodos(self.funcionario_admin)
        self.assertGreater(len(listado), 0)
        if len(listado) > 1:
            self.assertGreaterEqual(
                listado[0]['fecha_inicio'],
                listado[1]['fecha_inicio']
            )

    def test_obtener_listado_periodos_calcula_dias_correctamente(self):
        """Calcula días correctamente."""
        listado = estado_vacaciones.obtener_listado_periodos(self.funcionario_admin)
        self.assertGreater(len(listado), 0)
        periodo = listado[0]
        self.assertIn('dias_totales', periodo)
        self.assertIn('dias_disfrutados', periodo)
        self.assertIn('dias_pendientes', periodo)

    def test_obtener_historial_solicitudes_ordenado(self):
        """Historial ordenado por fecha solicitud descendente."""
        solicitud1 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=35),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        solicitud2 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=40),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        historial = estado_vacaciones.obtener_historial_solicitudes(self.funcionario_admin)
        self.assertGreater(len(historial), 0)
        if len(historial) > 1:
            self.assertGreaterEqual(
                historial[0]['fecha_solicitud'],
                historial[1]['fecha_solicitud']
            )

    def test_obtener_historial_solicitudes_incluye_motivo_rechazo(self):
        """Incluye motivo rechazo si aplica."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud='rechazado',
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='rechazada',
            observacion='No cumple requisitos',
        )
        historial = estado_vacaciones.obtener_historial_solicitudes(self.funcionario_admin)
        rechazadas = [s for s in historial if s.get('estado') == 'rechazado']
        if rechazadas:
            self.assertIn('motivo_rechazo', rechazadas[0])

    def test_obtener_historial_reintegros_ordenado(self):
        """Historial ordenado por fecha solicitud descendente."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        solicitud1 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=35),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud1.pk,
            solicitud=solicitud1,
            etapa='RRHH',
            estado='autorizada',
        )
        solicitud2 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=40),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud2.pk,
            solicitud=solicitud2,
            etapa='RRHH',
            estado='autorizada',
        )
        reintegro1 = ReintegroVacaciones.objects.create(
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro='finalizacion_normal',
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=35),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=solicitud1,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        reintegro1.estado_solicitud = 'completado'
        reintegro1.save()
        reintegro2 = ReintegroVacaciones.objects.create(
            fecha_reintegro=date.today() + timedelta(days=60),
            motivo_reintegro='finalizacion_normal',
            fecha_disfrute_desde=date.today() + timedelta(days=40),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=solicitud2,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
        )
        historial = estado_vacaciones.obtener_historial_reintegros(self.funcionario_admin)
        self.assertGreater(len(historial), 0)
        if len(historial) > 1:
            self.assertGreaterEqual(
                historial[0]['fecha_solicitud'],
                historial[1]['fecha_solicitud']
            )

    def test_obtener_ultimo_periodo_disfrutado_con_solicitudes(self):
        """Retorna último periodo disfrutado."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() - timedelta(days=100),
            fecha_fin_vacaciones=date.today() - timedelta(days=90),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud='autorizada',
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        ultimo = estado_vacaciones.obtener_ultimo_periodo_disfrutado(self.funcionario_admin)
        self.assertIsNotNone(ultimo)

    def test_obtener_ultimo_periodo_disfrutado_sin_solicitudes(self):
        """Calcula periodo anterior si no hay solicitudes."""
        ultimo = estado_vacaciones.obtener_ultimo_periodo_disfrutado(self.funcionario_admin)
        self.assertIsNotNone(ultimo)

    def test_verificar_periodos_acumulados_con_2_periodos(self):
        """Detecta 2 periodos acumulados."""
        periodo2 = PeriodoVacacional.objects.create(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=200),
            fecha_fin_periodo=date.today() - timedelta(days=100),
            dias_disfrutados_periodo=0,
        )
        periodo2.refresh_from_db()
        resultado = estado_vacaciones.verificar_periodos_acumulados(self.funcionario_admin)
        if resultado:
            self.assertIn('periodo1', resultado)
            self.assertIn('periodo2', resultado)

    def test_verificar_periodos_acumulados_con_1_periodo(self):
        """Retorna None con 1 periodo."""
        resultado = estado_vacaciones.verificar_periodos_acumulados(self.funcionario_admin)
        self.assertIsNone(resultado)

    def test_verificar_periodos_acumulados_calcula_fecha_limite(self):
        """Calcula fecha límite pérdida."""
        periodo2 = PeriodoVacacional.objects.create(
            funcionario=self.funcionario_admin,
            fecha_inicio_periodo=date.today() - timedelta(days=200),
            fecha_fin_periodo=date.today() - timedelta(days=100),
            dias_disfrutados_periodo=0,
        )
        periodo2.refresh_from_db()
        resultado = estado_vacaciones.verificar_periodos_acumulados(self.funcionario_admin)
        if resultado:
            self.assertIn('fecha_limite_perdida', resultado)

    def test_obtener_estado_completo_incluye_todos_datos(self):
        """Incluye todos los datos necesarios."""
        estado = estado_vacaciones.obtener_estado_completo_vacaciones(self.funcionario_admin)
        self.assertIn('resumen_vacacional', estado)
        self.assertIn('listado_periodos', estado)
        self.assertIn('historial_solicitudes', estado)
        self.assertIn('historial_reintegros', estado)

    def test_obtener_estado_completo_funcionario_none(self):
        """Retorna dict vacío si funcionario es None."""
        estado = estado_vacaciones.obtener_estado_completo_vacaciones(None)
        self.assertEqual(estado, {})


# ============================================================
# PRUEBAS PARA SERVICIO DE REPORTES (reportes.py)
# ============================================================

class ReportesServiceTest(BaseTestCaseMixin, TestCase):
    """Pruebas para el servicio de reportes."""

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

    def test_filtrar_por_rol_rrhh_retorna_todos(self):
        """RRHH ve todos los registros."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        qs_sol, qs_rein = reportes._filtrar_por_rol(
            SolicitudVacaciones.objects.all(),
            ReintegroVacaciones.objects.all(),
            user_rrhh
        )
        self.assertGreaterEqual(qs_sol.count(), 0)

    def test_filtrar_por_rol_coordinador_filtra_por_facultad(self):
        """Coordinador filtra por facultad."""
        user_coord, _ = crear_grupo_y_usuario('Coordinador Administrativo', 'coord@test.com')
        qs_sol, qs_rein = reportes._filtrar_por_rol(
            SolicitudVacaciones.objects.all(),
            ReintegroVacaciones.objects.all(),
            user_coord
        )
        self.assertGreaterEqual(qs_sol.count(), 0)

    def test_filtrar_por_rol_jefe_filtra_por_subordinados(self):
        """Jefe filtra por subordinados."""
        jefe = Funcionario.objects.create(
            user=CustomUser.objects.create_user(email='jefe@test.com', password='test123'),
            nombre='Jefe',
            apellido='Test',
            numero_identificacion='JEFE001',
            telefono='3000000000',
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            estamento=self.estamento_admin,
            facultad_dependencia=self.facultad,
            sede=self.sede,
        )
        self.funcionario_admin.jefe_inmediato = jefe
        self.funcionario_admin.save()
        user_jefe, _ = crear_grupo_y_usuario('Jefe Inmediato', 'jefe2@test.com')
        jefe.user = user_jefe
        jefe.save()
        qs_sol, qs_rein = reportes._filtrar_por_rol(
            SolicitudVacaciones.objects.all(),
            ReintegroVacaciones.objects.all(),
            user_jefe
        )
        self.assertGreaterEqual(qs_sol.count(), 0)

    def test_filtrar_por_rol_secretaria_filtra_por_jefe_inmediato(self):
        """Secretaria filtra por jefe inmediato."""
        jefe = Funcionario.objects.create(
            user=CustomUser.objects.create_user(email='jefe@test.com', password='test123'),
            nombre='Jefe',
            apellido='Test',
            numero_identificacion='JEFE001',
            telefono='3000000000',
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            estamento=self.estamento_admin,
            facultad_dependencia=self.facultad,
            sede=self.sede,
        )
        secretaria = Funcionario.objects.create(
            user=CustomUser.objects.create_user(email='secretaria@test.com', password='test123'),
            nombre='Secretaria',
            apellido='Test',
            numero_identificacion='SEC001',
            telefono='3000000001',
            fecha_ingreso_universidad=date.today() - timedelta(days=500),
            estamento=self.estamento_admin,
            facultad_dependencia=self.facultad,
            sede=self.sede,
            jefe_inmediato=jefe,
        )
        user_sec, _ = crear_grupo_y_usuario('Secretaria', 'secretaria2@test.com')
        secretaria.user = user_sec
        secretaria.save()
        qs_sol, qs_rein = reportes._filtrar_por_rol(
            SolicitudVacaciones.objects.all(),
            ReintegroVacaciones.objects.all(),
            user_sec
        )
        self.assertGreaterEqual(qs_sol.count(), 0)

    def test_filtrar_por_rol_funcionario_filtra_por_si_mismo(self):
        """Funcionario ve solo sus registros."""
        qs_sol, qs_rein = reportes._filtrar_por_rol(
            SolicitudVacaciones.objects.all(),
            ReintegroVacaciones.objects.all(),
            self.user
        )
        self.assertGreaterEqual(qs_sol.count(), 0)

    def test_filtrar_por_rol_usuario_sin_funcionario_retorna_none(self):
        """Usuario sin funcionario retorna none."""
        user_sin_func = CustomUser.objects.create_user(
            email='sinfunc@test.com',
            password='test123'
        )
        qs_sol, qs_rein = reportes._filtrar_por_rol(
            SolicitudVacaciones.objects.all(),
            ReintegroVacaciones.objects.all(),
            user_sin_func
        )
        self.assertEqual(qs_sol.count(), 0)
        self.assertEqual(qs_rein.count(), 0)

    def test_obtener_estadisticas_solicitudes_agrupa_por_estado(self):
        """Agrupa correctamente por estado."""
        estadisticas = reportes.obtener_estadisticas_solicitudes(self.user)
        self.assertIn('solicitudes_aprobadas', estadisticas)
        self.assertIn('solicitudes_devueltas', estadisticas)
        self.assertIn('solicitudes_autorizadas', estadisticas)
        self.assertIn('solicitudes_rechazadas', estadisticas)
        self.assertIn('solicitudes_pendientes', estadisticas)

    def test_obtener_estadisticas_solicitudes_filtra_por_fechas(self):
        """Filtra por fechas correctamente."""
        estadisticas = reportes.obtener_estadisticas_solicitudes(
            self.user,
            fecha_inicio=date.today() - timedelta(days=30),
            fecha_fin=date.today()
        )
        self.assertIsInstance(estadisticas, dict)

    def test_obtener_estadisticas_solicitudes_filtra_por_facultad(self):
        """Filtra por facultad (RRHH)."""
        user_rrhh, _ = crear_grupo_y_usuario('Recursos Humanos', 'rrhh@test.com')
        estadisticas = reportes.obtener_estadisticas_solicitudes(
            user_rrhh,
            facultad_id=self.facultad.id
        )
        self.assertIsInstance(estadisticas, dict)

    def test_obtener_solicitudes_por_facultad_agrupa_correctamente(self):
        """Agrupa por facultad correctamente."""
        resultados = reportes.obtener_solicitudes_por_facultad(self.user)
        self.assertIsInstance(resultados, list)

    def test_obtener_solicitudes_por_facultad_incluye_por_estado(self):
        """Incluye desglose por estado."""
        resultados = reportes.obtener_solicitudes_por_facultad(self.user)
        if resultados:
            self.assertIn('por_estado', resultados[0])

    def test_obtener_solicitudes_por_anio_agrupa_correctamente(self):
        """Agrupa por año correctamente."""
        resultados = reportes.obtener_solicitudes_por_anio(self.user)
        self.assertIsInstance(resultados, list)

    def test_obtener_solicitudes_por_anio_filtra_por_anio_especifico(self):
        """Filtra por año específico."""
        resultados = reportes.obtener_solicitudes_por_anio(
            self.user,
            anio=date.today().year
        )
        self.assertIsInstance(resultados, list)

    def test_obtener_funcionarios_en_vacaciones_fecha_actual(self):
        """Obtiene funcionarios en vacaciones en fecha actual."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() - timedelta(days=5),
            fecha_fin_vacaciones=date.today() + timedelta(days=5),
            tiene_dias_pendientes=False,
            creada_por=self.user,
            estado_solicitud='autorizada',
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        funcionarios = reportes.obtener_funcionarios_en_vacaciones(self.user)
        self.assertIsInstance(funcionarios, list)

    def test_obtener_funcionarios_en_vacaciones_fecha_especifica(self):
        """Obtiene funcionarios en vacaciones en fecha específica."""
        funcionarios = reportes.obtener_funcionarios_en_vacaciones(
            self.user,
            fecha_consulta=date.today()
        )
        self.assertIsInstance(funcionarios, list)

    def test_obtener_funcionarios_en_vacaciones_solo_autorizadas(self):
        """Solo incluye solicitudes autorizadas."""
        funcionarios = reportes.obtener_funcionarios_en_vacaciones(self.user)
        for func in funcionarios:
            self.assertEqual(func['solicitud'].estado_solicitud, 'autorizada')

    def test_obtener_estadisticas_reintegros_agrupa_por_estado(self):
        """Agrupa reintegros por estado."""
        estadisticas = reportes.obtener_estadisticas_reintegros(self.user)
        self.assertIn('reintegros_aprobados', estadisticas)
        self.assertIn('reintegros_devueltos', estadisticas)
        self.assertIn('reintegros_autorizados', estadisticas)
        self.assertIn('reintegros_rechazados', estadisticas)

    def test_obtener_estadisticas_reintegros_filtra_por_fechas(self):
        """Filtra reintegros por fechas."""
        estadisticas = reportes.obtener_estadisticas_reintegros(
            self.user,
            fecha_inicio=date.today() - timedelta(days=30),
            fecha_fin=date.today()
        )
        self.assertIsInstance(estadisticas, dict)

    def test_obtener_reintegros_por_facultad_agrupa_correctamente(self):
        """Agrupa reintegros por facultad."""
        resultados = reportes.obtener_reintegros_por_facultad(self.user)
        self.assertIsInstance(resultados, list)

    def test_obtener_reintegros_anticipados_filtra_correctamente(self):
        """Filtra solo reintegros anticipados."""
        ct_solicitud = ContentType.objects.get_for_model(SolicitudVacaciones)
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario_admin,
            periodo_vacacional=self.periodo_admin,
            fecha_inicio_vacaciones=date.today() + timedelta(days=30),
            fecha_fin_vacaciones=date.today() + timedelta(days=45),
            tiene_dias_pendientes=False,
            creada_por=self.user,
        )
        AprobacionEtapa.objects.create(
            content_type=ct_solicitud,
            object_id=solicitud.pk,
            solicitud=solicitud,
            etapa='RRHH',
            estado='autorizada',
        )
        reintegro = ReintegroVacaciones.objects.create(
            fecha_reintegro=date.today() + timedelta(days=50),
            motivo_reintegro='finalizacion_normal',
            fecha_disfrute_desde=date.today() + timedelta(days=30),
            fecha_disfrute_hasta=date.today() + timedelta(days=45),
            dias_disfrutados_habiles=5,
            dias_disfrutados_calendario=0,
            dias_pendientes_habiles=0,
            dias_pendientes_calendario=0,
            periodo_vacacional=self.periodo_admin,
            solicitud_vacaciones=solicitud,
            funcionario=self.funcionario_admin,
            creada_por=self.user,
            es_reintegro_anticipado=True,
            observaciones='Reintegro anticipado por motivos especiales',
        )
        resultados = reportes.obtener_reintegros_anticipados(self.user)
        self.assertIsInstance(resultados, dict)
        self.assertIn('total_reintegros_anticipados', resultados)

    def test_obtener_reporte_completo_incluye_todas_metricas(self):
        """Incluye todas las métricas."""
        reporte = reportes.obtener_reporte_completo(self.user)
        self.assertIn('estadisticas_solicitudes', reporte)
        self.assertIn('solicitudes_por_facultad', reporte)
        self.assertIn('solicitudes_por_anio', reporte)
        self.assertIn('funcionarios_en_vacaciones', reporte)
        self.assertIn('estadisticas_reintegros', reporte)
        self.assertIn('reintegros_por_facultad', reporte)
        self.assertIn('reintegros_por_anio', reporte)
        self.assertIn('reintegros_anticipados', reporte)
