from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from usuarios.models import Funcionario, Estamento, FacultadDependencia
from .models import PeriodoVacacional, SolicitudVacaciones, ReintegroVacaciones, generar_codigo_sabs
from .forms import SolicitudVacacionesForm
from datetime import date, timedelta

User = get_user_model()

class SolicitudVacacionesListViewTest(TestCase):
    def setUp(self):
        # Crear estamento y facultad
        self.estamento = Estamento.objects.create(nombre='Administrativo')
        self.facultad = FacultadDependencia.objects.create(nombre='Facultad de Prueba')
        
        # Crear usuario y funcionario
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.funcionario = Funcionario.objects.create(
            user=self.user,
            nombre='Juan',
            apellido='Pérez',
            numero_identificacion='12345678',
            estamento=self.estamento,
            facultad_dependencia=self.facultad
        )
        
        # Crear periodo vacacional
        self.periodo = PeriodoVacacional.objects.create(
            funcionario=self.funcionario,
            fecha_inicio_periodo=date(2024, 1, 1),
            fecha_fin_periodo=date(2024, 12, 31),
            dias_totales_periodo=15,  # Se calculará automáticamente según estamento
            dias_pendientes_periodo=15,  # Se calculará automáticamente
            dias_disfrutados_periodo=0
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_puede_crear_solicitud_sin_solicitudes_activas(self):
        """Test que verifica que el usuario puede crear solicitud cuando no tiene solicitudes activas"""
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['puede_crear_solicitud'])
        self.assertIsNone(response.context['solicitud_activa'])

    def test_no_puede_crear_solicitud_con_solicitud_activa(self):
        """Test que verifica que el usuario no puede crear solicitud cuando tiene una activa"""
        # Crear solicitud activa
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2024, 6, 1),
            fecha_fin_vacaciones=date(2024, 6, 15),
            total_dias_solicitados=15,
            estado_solicitud='pendiente',
            fecha_solicitud=date.today()
        )
        
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_list'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['puede_crear_solicitud'])
        self.assertEqual(response.context['solicitud_activa'], solicitud)

    def test_puede_crear_solicitud_con_reintegro_aprobado(self):
        """Test que verifica que el usuario puede crear solicitud cuando tiene reintegro aprobado"""
        # Crear solicitud activa
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2024, 6, 1),
            fecha_fin_vacaciones=date(2024, 6, 15),
            total_dias_solicitados=15,
            estado_solicitud='aprobado',
            fecha_solicitud=date.today()
        )
        
        # Crear reintegro aprobado (lo que significa que la solicitud está culminada)
        reintegro = ReintegroVacaciones.objects.create(
            funcionario=self.funcionario,
            solicitud_vacaciones=solicitud,
            periodo_vacacional=self.periodo,
            fecha_disfrute_desde=date(2024, 6, 1),
            fecha_disfrute_hasta=date(2024, 6, 15),
            dias_disfrutados=15,
            dias_pendientes=0,
            estado_solicitud='aprobado'
        )
        
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['puede_crear_solicitud'])
        self.assertIsNone(response.context['solicitud_activa'])

    def test_tooltip_se_renderiza_con_solicitud_activa(self):
        """Test que verifica que el tooltip se renderiza correctamente cuando hay una solicitud activa"""
        # Crear solicitud activa
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2024, 6, 1),
            fecha_fin_vacaciones=date(2024, 6, 15),
            total_dias_solicitados=15,
            estado_solicitud='pendiente',
            fecha_solicitud=date.today()
        )
        
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_list'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el tooltip se renderiza en la respuesta
        self.assertContains(response, 'tooltip-container')
        self.assertContains(response, 'tooltip')
        self.assertContains(response, 'No puedes crear una nueva solicitud mientras tengas una solicitud activa.')
        
        # Verificar que NO se renderiza información detallada
        self.assertNotContains(response, 'Solicitud Activa')
        self.assertNotContains(response, 'Estado actual:')
        self.assertNotContains(response, 'Acción requerida:')
        self.assertNotContains(response, 'Tu solicitud está siendo procesada')
        
        # Verificar que NO se renderiza el mensaje informativo
        self.assertNotContains(response, 'alert-info')
        self.assertNotContains(response, 'Solicitud activa:')


class CodigoSABSTest(TestCase):
    """Test para verificar la generación secuencial de códigos SABS"""
    
    def setUp(self):
        # Crear estamento y facultad
        self.estamento = Estamento.objects.create(nombre='Administrativo')
        self.facultad = FacultadDependencia.objects.create(nombre='Facultad de Prueba')
        
        # Crear usuario y funcionario
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.funcionario = Funcionario.objects.create(
            user=self.user,
            nombre='Juan',
            apellido='Pérez',
            numero_identificacion='12345678',
            estamento=self.estamento,
            facultad_dependencia=self.facultad
        )
        
        # Crear periodo vacacional
        self.periodo = PeriodoVacacional.objects.create(
            funcionario=self.funcionario,
            fecha_inicio_periodo=date(2025, 1, 1),
            fecha_fin_periodo=date(2025, 12, 31),
            dias_totales_periodo=15,  # Se calculará automáticamente según estamento
            dias_pendientes_periodo=15,  # Se calculará automáticamente
            dias_disfrutados_periodo=0
        )

    def test_generacion_codigo_sabs_secuencial(self):
        """Test que verifica que los códigos SABS se generen secuencialmente"""
        anio_actual = 2025
        
        # Generar primer código
        codigo1 = generar_codigo_sabs('VAC', anio_actual)
        self.assertEqual(codigo1, 'VAC20250001')
        
        # Crear primera solicitud
        solicitud1 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2025, 6, 1),
            fecha_fin_vacaciones=date(2025, 6, 15),
            total_dias_solicitados=15,
            estado_solicitud='pendiente',
            fecha_solicitud=date.today(),
            codigo_sabs=codigo1
        )
        
        # Generar segundo código
        codigo2 = generar_codigo_sabs('VAC', anio_actual)
        self.assertEqual(codigo2, 'VAC20250002')
        
        # Crear segunda solicitud
        solicitud2 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2025, 7, 1),
            fecha_fin_vacaciones=date(2025, 7, 15),
            total_dias_solicitados=15,
            estado_solicitud='pendiente',
            fecha_solicitud=date.today(),
            codigo_sabs=codigo2
        )
        
        # Generar tercer código
        codigo3 = generar_codigo_sabs('VAC', anio_actual)
        self.assertEqual(codigo3, 'VAC20250003')

    def test_generacion_codigo_sabs_por_anio(self):
        """Test que verifica que los códigos SABS se reinicien por año"""
        anio_2024 = 2024
        anio_2025 = 2025
        
        # Crear solicitud del año 2024
        periodo_2024 = PeriodoVacacional.objects.create(
            funcionario=self.funcionario,
            fecha_inicio_periodo=date(2024, 1, 1),
            fecha_fin_periodo=date(2024, 12, 31),
            dias_totales_periodo=15,  # Se calculará automáticamente según estamento
            dias_pendientes_periodo=15,  # Se calculará automáticamente
            dias_disfrutados_periodo=0
        )
        
        solicitud_2024 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=periodo_2024,
            fecha_inicio_vacaciones=date(2024, 6, 1),
            fecha_fin_vacaciones=date(2024, 6, 15),
            total_dias_solicitados=15,
            estado_solicitud='pendiente',
            fecha_solicitud=date.today(),
            codigo_sabs='VAC20240001'
        )
        
        # Generar código para 2025 (debe empezar en 0001)
        codigo_2025 = generar_codigo_sabs('VAC', anio_2025)
        self.assertEqual(codigo_2025, 'VAC20250001')

    def test_generacion_codigo_sabs_reintegro(self):
        """Test que verifica la generación de códigos SABS para reintegros"""
        anio_actual = 2025
        
        # Crear solicitud base
        solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2025, 6, 1),
            fecha_fin_vacaciones=date(2025, 6, 15),
            total_dias_solicitados=15,
            estado_solicitud='aprobado',
            fecha_solicitud=date.today(),
            codigo_sabs='VAC20250001'
        )
        
        # Generar código para reintegro
        codigo_reintegro = generar_codigo_sabs('REI', anio_actual)
        self.assertEqual(codigo_reintegro, 'REI20250001')
        
        # Crear reintegro
        reintegro = ReintegroVacaciones.objects.create(
            funcionario=self.funcionario,
            solicitud_vacaciones=solicitud,
            periodo_vacacional=self.periodo,
            fecha_disfrute_desde=date(2025, 6, 1),
            fecha_disfrute_hasta=date(2025, 6, 15),
            dias_disfrutados=15,
            dias_pendientes=0,
            estado_solicitud='pendiente',
            codigo_sabs=codigo_reintegro
        )
        
        # Generar segundo código de reintegro
        codigo_reintegro2 = generar_codigo_sabs('REI', anio_actual)
        self.assertEqual(codigo_reintegro2, 'REI20250002')

    def test_codigo_sabs_unico(self):
        """Test que verifica que los códigos SABS sean únicos"""
        # Intentar crear dos solicitudes con el mismo código
        solicitud1 = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2025, 6, 1),
            fecha_fin_vacaciones=date(2025, 6, 15),
            total_dias_solicitados=15,
            estado_solicitud='pendiente',
            fecha_solicitud=date.today(),
            codigo_sabs='VAC20250001'
        )
        
        # Intentar crear segunda solicitud con código duplicado
        with self.assertRaises(Exception):  # Debe fallar por unique=True
            SolicitudVacaciones.objects.create(
                funcionario=self.funcionario,
                periodo_vacacional=self.periodo,
                fecha_inicio_vacaciones=date(2025, 7, 1),
                fecha_fin_vacaciones=date(2025, 7, 15),
                total_dias_solicitados=15,
                estado_solicitud='pendiente',
                fecha_solicitud=date.today(),
                codigo_sabs='VAC20250001'  # Código duplicado
            )


class SolicitudVacacionesEdicionTest(TestCase):
    """Test para verificar el comportamiento correcto al editar solicitudes"""
    
    def setUp(self):
        # Crear estamento y facultad
        self.estamento = Estamento.objects.create(nombre='Administrativo')
        self.facultad = FacultadDependencia.objects.create(nombre='Facultad de Prueba')
        
        # Crear usuario y funcionario
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.funcionario = Funcionario.objects.create(
            user=self.user,
            nombre='Juan',
            apellido='Pérez',
            numero_identificacion='12345678',
            estamento=self.estamento,
            facultad_dependencia=self.facultad
        )
        
        # Crear periodo vacacional
        self.periodo = PeriodoVacacional.objects.create(
            funcionario=self.funcionario,
            fecha_inicio_periodo=date(2024, 1, 1),
            fecha_fin_periodo=date(2024, 12, 31),
            dias_totales_periodo=15,  # Se calculará automáticamente según estamento
            dias_pendientes_periodo=15,  # Se calculará automáticamente
            dias_disfrutados_periodo=0
        )
        
        # Crear solicitud para editar
        self.solicitud = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2024, 6, 1),
            fecha_fin_vacaciones=date(2024, 6, 15),
            total_dias_solicitados=15,
            estado_solicitud='pendiente',
            fecha_solicitud=date.today(),
            codigo_sabs='VAC20240001'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_edicion_no_muestra_alerta_solicitud_activa(self):
        """Test que verifica que no se muestre la alerta de solicitud activa en modo edición"""
        # Crear otra solicitud activa para simular el escenario
        solicitud_activa = SolicitudVacaciones.objects.create(
            funcionario=self.funcionario,
            periodo_vacacional=self.periodo,
            fecha_inicio_vacaciones=date(2024, 7, 1),
            fecha_fin_vacaciones=date(2024, 7, 15),
            total_dias_solicitados=15,
            estado_solicitud='pendiente',
            fecha_solicitud=date.today(),
            codigo_sabs='VAC20240002'
        )
        
        # Acceder al formulario de edición
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_update', kwargs={'pk': self.solicitud.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que NO se muestre la alerta de solicitud activa
        self.assertNotContains(response, 'alerta-solicitud-activa')
        self.assertNotContains(response, 'Ya tiene una solicitud de vacaciones activa')
        self.assertNotContains(response, 'modal-alerta-solicitud-activa')
        
        # Verificar que el contexto esté configurado correctamente para edición
        self.assertTrue(response.context['puede_crear_solicitud'])
        self.assertIsNone(response.context['solicitud_activa'])
        self.assertIsNone(response.context['plazo_solicitud'])

    def test_edicion_no_muestra_alerta_plazo_solicitud(self):
        """Test que verifica que no se muestre la alerta de plazo de solicitud en modo edición"""
        # Acceder al formulario de edición
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_update', kwargs={'pk': self.solicitud.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que NO se muestre la alerta de plazo de solicitud
        self.assertNotContains(response, 'alerta-plazo-solicitud')
        self.assertNotContains(response, 'Información sobre su solicitud')
        
        # Verificar que el contexto esté configurado correctamente
        self.assertIsNone(response.context['plazo_solicitud'])

    def test_edicion_muestra_formulario_correctamente(self):
        """Test que verifica que el formulario de edición se muestre correctamente"""
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_update', kwargs={'pk': self.solicitud.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el título indique que es edición
        self.assertContains(response, 'Editar solicitud de vacaciones')
        
        # Verificar que el botón indique guardar cambios
        self.assertContains(response, 'Guardar cambios')
        
        # Verificar que el formulario tenga los datos de la solicitud
        self.assertEqual(response.context['form'].instance, self.solicitud)

    def test_edicion_muestra_codigo_sabs_y_fecha_solicitud(self):
        """Test que verifica que los campos código SABS y fecha de solicitud se muestren en modo edición"""
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_update', kwargs={'pk': self.solicitud.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se muestren los campos
        self.assertContains(response, 'Código SABS')
        self.assertContains(response, 'Fecha de solicitud')
        
        # Verificar que los campos tengan los valores correctos
        form = response.context['form']
        self.assertEqual(form.initial.get('codigo_sabs'), self.solicitud.codigo_sabs)
        self.assertEqual(form.initial.get('fecha_solicitud'), self.solicitud.fecha_solicitud)
        
        # Verificar que los valores se rendericen en la respuesta HTML
        self.assertContains(response, self.solicitud.codigo_sabs)
        self.assertContains(response, self.solicitud.fecha_solicitud.strftime('%Y-%m-%d'))


class ValidacionesFechasTest(TestCase):
    """Test para validaciones de fechas en el formulario de solicitud de vacaciones"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        self.estamento = Estamento.objects.create(nombre='Docente')
        self.facultad = FacultadDependencia.objects.create(nombre='Facultad de Ingeniería')
        
        self.funcionario = Funcionario.objects.create(
            user=self.user,
            numero_identificacion='12345678',
            nombre='Juan',
            apellido='Pérez',
            estamento=self.estamento,
            facultad_dependencia=self.facultad,
            decreto_resolucion='1279'
        )
        
        self.periodo = PeriodoVacacional.objects.create(
            funcionario=self.funcionario,
            fecha_inicio_periodo=date(2024, 1, 1),
            fecha_fin_periodo=date(2024, 12, 31),
            dias_disfrutados_periodo=0
        )
        
        self.client.login(username='testuser', password='testpass123')

    def test_fecha_inicio_no_puede_ser_igual_fecha_solicitud(self):
        """Test que verifica que la fecha de inicio no puede ser igual a la fecha de solicitud"""
        hoy = date.today()
        form_data = {
            'periodo_vacacional': self.periodo.pk,
            'fecha_inicio_vacaciones': hoy,
            'fecha_fin_vacaciones': hoy + timedelta(days=30),
            'fecha_solicitud': hoy,
            'observaciones': 'Test'
        }
        
        form = SolicitudVacacionesForm(data=form_data, initial={'user_id': self.user.id})
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_inicio_vacaciones', form.errors)
        self.assertIn('no puede ser igual a la fecha de solicitud', str(form.errors['fecha_inicio_vacaciones']))

    def test_fecha_fin_debe_ser_posterior_fecha_inicio(self):
        """Test que verifica que la fecha de fin debe ser posterior a la fecha de inicio"""
        hoy = date.today()
        form_data = {
            'periodo_vacacional': self.periodo.pk,
            'fecha_inicio_vacaciones': hoy + timedelta(days=10),
            'fecha_fin_vacaciones': hoy + timedelta(days=5),  # Fecha anterior
            'observaciones': 'Test'
        }
        
        form = SolicitudVacacionesForm(data=form_data, initial={'user_id': self.user.id})
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_fin_vacaciones', form.errors)
        self.assertIn('debe ser posterior a la fecha de inicio', str(form.errors['fecha_fin_vacaciones']))

    def test_docente_decreto_1279_debe_tener_30_dias(self):
        """Test que verifica que docentes del decreto 1279 deben tener exactamente 30 días"""
        hoy = date.today()
        form_data = {
            'periodo_vacacional': self.periodo.pk,
            'fecha_inicio_vacaciones': hoy + timedelta(days=10),
            'fecha_fin_vacaciones': hoy + timedelta(days=25),  # Solo 15 días
            'observaciones': 'Test'
        }
        
        form = SolicitudVacacionesForm(data=form_data, initial={'user_id': self.user.id})
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_fin_vacaciones', form.errors)
        self.assertIn('exactamente 30 días', str(form.errors['fecha_fin_vacaciones']))

    def test_administrativo_debe_tener_15_dias_habiles(self):
        """Test que verifica que funcionarios administrativos deben tener exactamente 15 días hábiles"""
        # Cambiar estamento a administrativo
        self.funcionario.estamento = Estamento.objects.create(nombre='Administrativo')
        self.funcionario.decreto_resolucion = ''
        self.funcionario.save()
        
        hoy = date.today()
        form_data = {
            'periodo_vacacional': self.periodo.pk,
            'fecha_inicio_vacaciones': hoy + timedelta(days=10),
            'fecha_fin_vacaciones': hoy + timedelta(days=20),  # Solo 10 días
            'observaciones': 'Test'
        }
        
        form = SolicitudVacacionesForm(data=form_data, initial={'user_id': self.user.id})
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_fin_vacaciones', form.errors)
        self.assertIn('exactamente 15 días hábiles', str(form.errors['fecha_fin_vacaciones']))

    def test_trabajador_oficial_debe_tener_30_dias_calendario(self):
        """Test que verifica que trabajadores oficiales deben tener exactamente 30 días calendario"""
        # Cambiar estamento a trabajador oficial
        self.funcionario.estamento = Estamento.objects.create(nombre='Trabajador Oficial')
        self.funcionario.decreto_resolucion = ''
        self.funcionario.save()
        
        hoy = date.today()
        form_data = {
            'periodo_vacacional': self.periodo.pk,
            'fecha_inicio_vacaciones': hoy + timedelta(days=10),
            'fecha_fin_vacaciones': hoy + timedelta(days=25),  # Solo 15 días
            'observaciones': 'Test'
        }
        
        form = SolicitudVacacionesForm(data=form_data, initial={'user_id': self.user.id})
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_fin_vacaciones', form.errors)
        self.assertIn('exactamente 30 días calendario', str(form.errors['fecha_fin_vacaciones']))

    def test_formulario_valido_con_fechas_correctas(self):
        """Test que verifica que el formulario es válido con fechas correctas"""
        hoy = date.today()
        form_data = {
            'periodo_vacacional': self.periodo.pk,
            'fecha_inicio_vacaciones': hoy + timedelta(days=10),
            'fecha_fin_vacaciones': hoy + timedelta(days=40),  # 30 días después
            'observaciones': 'Test'
        }
        
        form = SolicitudVacacionesForm(data=form_data, initial={'user_id': self.user.id})
        self.assertTrue(form.is_valid())


class FlatpickrIntegrationTest(TestCase):
    """Test para verificar que flatpickr se integre correctamente con los campos de fecha"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        self.estamento = Estamento.objects.create(nombre='Docente')
        self.facultad = FacultadDependencia.objects.create(nombre='Facultad de Ingeniería')
        
        self.funcionario = Funcionario.objects.create(
            user=self.user,
            numero_identificacion='12345678',
            nombre='Juan',
            apellido='Pérez',
            estamento=self.estamento,
            facultad_dependencia=self.facultad,
            decreto_resolucion='1279'
        )
        
        self.periodo = PeriodoVacacional.objects.create(
            funcionario=self.funcionario,
            fecha_inicio_periodo=date(2024, 1, 1),
            fecha_fin_periodo=date(2024, 12, 31),
            dias_disfrutados_periodo=0
        )
        
        self.client.login(username='testuser', password='testpass123')

    def test_campos_fecha_no_tienen_type_date(self):
        """Test que verifica que los campos de fecha no tengan type='date' para permitir flatpickr"""
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_create'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que los campos no tengan type="date"
        self.assertNotContains(response, 'type="date"')
        
        # Verificar que tengan las clases correctas para flatpickr
        self.assertContains(response, 'flatpickr-input')
        self.assertContains(response, 'placeholder="Seleccionar fecha"')

    def test_scripts_flatpickr_se_cargan(self):
        """Test que verifica que los scripts de flatpickr se carguen correctamente"""
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_create'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se carguen los scripts necesarios
        self.assertContains(response, 'flatpickr.min.css')
        self.assertContains(response, 'flatpickr')
        self.assertContains(response, 'vacaciones/js/datepicker-vacaciones.js')
        self.assertContains(response, 'vacaciones/css/datepicker_icon.css')
        
        # Verificar que no haya errores 404 en la respuesta
        self.assertNotContains(response, '404')
        self.assertNotContains(response, 'Not Found')

    def test_formulario_tiene_campos_fecha_correctos(self):
        """Test que verifica que el formulario tenga los campos de fecha con los atributos correctos"""
        response = self.client.get(reverse('vacaciones:solicitud_vacaciones_create'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que existan los campos de fecha
        self.assertContains(response, 'id_fecha_inicio_vacaciones')
        self.assertContains(response, 'id_fecha_fin_vacaciones')
        
        # Verificar que tengan los placeholders correctos
        self.assertContains(response, 'placeholder="Seleccionar fecha"')

    def test_configuracion_archivos_estaticos(self):
        """Test que verifica que la configuración de archivos estáticos funcione correctamente"""
        from django.conf import settings
        from django.contrib.staticfiles import finders
        
        # Verificar que STATICFILES_DIRS incluya el directorio de vacaciones
        static_dirs = [str(d) for d in settings.STATICFILES_DIRS]
        self.assertTrue(any('vacaciones/static' in d for d in static_dirs))
        
        # Verificar que STATIC_URL esté configurado
        self.assertEqual(settings.STATIC_URL, 'static/')
        
        # Verificar que los archivos específicos se puedan encontrar
        self.assertTrue(finders.find('vacaciones/js/datepicker-vacaciones.js'))
        self.assertTrue(finders.find('vacaciones/js/solicitud-vacaciones.js'))
        self.assertTrue(finders.find('vacaciones/css/datepicker_icon.css'))
