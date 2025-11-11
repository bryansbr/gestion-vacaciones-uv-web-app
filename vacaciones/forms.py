from datetime import date, datetime

from django import forms

from core.permissions import es_secretaria, es_jefe_inmediato
from usuarios.models import Funcionario

from .models import PeriodoVacacional, ReintegroVacaciones, SolicitudVacaciones
from .utils import get_current_date_colombia

class PeriodoVacacionalForm(forms.ModelForm):
    class Meta:
        model = PeriodoVacacional
        fields = [
            'funcionario',
            'fecha_inicio_periodo',
            'fecha_fin_periodo',
            'dias_disfrutados_periodo',
        ]
        widgets = {
            'fecha_inicio_periodo': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'fecha_fin_periodo': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'dias_disfrutados_periodo': forms.NumberInput(attrs={'class': 'form-input'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class SolicitudVacacionesForm(forms.ModelForm):
    numero_identificacion = forms.CharField(required=False, disabled=True)
    nombre_funcionario = forms.CharField(required=False, disabled=True)
    estamento = forms.CharField(required=False, disabled=True)
    facultad_dependencia = forms.CharField(required=False, disabled=True)

    dias_derecho = forms.IntegerField(
        label='Días a los que tiene derecho',
        required=False,
        disabled=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-input bg-gray-100',
            'readonly': 'readonly'
        })
    )
    tipo_habiles = forms.BooleanField(label='Hábiles', required=False, disabled=True)
    tipo_calendario = forms.BooleanField(label='Calendario', required=False, disabled=True)

    dias_pendientes = forms.IntegerField(
        label='Días pendientes',
        required=False,
        disabled=True,
        widget=forms.NumberInput(attrs={
            'class': 'form-input bg-gray-100',
            'readonly': 'readonly'
        })
    )
    periodos_pendientes = forms.CharField(
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input bg-gray-100',
            'readonly': 'readonly'
        })
    )
    tiene_dias_pendientes = forms.BooleanField(
        label='Disfrute de días pendientes',
        required=False,
        help_text='Marque esta opción si desea solicitar vacaciones por días pendientes de reintegros aprobados'
    )

    fecha_inicio_vacaciones = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-input flatpickr-input', 'placeholder': 'Seleccionar fecha', 'autocomplete': 'off'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        required=True
    )
    fecha_fin_vacaciones = forms.DateField(
        widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-input flatpickr-input', 'placeholder': 'Seleccionar fecha', 'autocomplete': 'off'}),
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        required=True
    )

    class Meta:
        model = SolicitudVacaciones
        fields = [
            'periodo_vacacional',
            'fecha_inicio_vacaciones',
            'fecha_fin_vacaciones',
            'fecha_pago',
            'observaciones',
            'tiene_dias_pendientes',
            'codigo_sabs',
            'fecha_solicitud'
        ]
        labels = {
            'periodo_vacacional': 'Periodo(s) vacacional(es)',
            'fecha_inicio_vacaciones': 'Fecha de inicio vacaciones',
            'fecha_fin_vacaciones': 'Fecha de fin vacaciones',
            'fecha_pago': 'Fecha de pago vacaciones',
            'codigo_sabs': 'Código SABS',
            'fecha_solicitud': 'Fecha de solicitud',
        }
        widgets = {
            'fecha_pago': forms.DateInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'observaciones': forms.Textarea(attrs={'class': 'form-textarea'}),
            'periodo_vacacional': forms.Select(attrs={'class': 'form-select'}),
            'codigo_sabs': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly'
            }),
            'fecha_solicitud': forms.DateInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly'
            }),
            'numero_identificacion': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'nombre_funcionario': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'estamento': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
            'facultad_dependencia': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly',
                'disabled': 'disabled'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        funcionario_id = kwargs.pop('funcionario_id', None)
        super().__init__(*args, **kwargs)
        
        self.user = user
        funcionario = None
        
        if self.instance and self.instance.pk:
            funcionario = self.instance.funcionario
        elif funcionario_id:
            try:
                funcionario = Funcionario.objects.get(pk=funcionario_id)
            except Funcionario.DoesNotExist:
                funcionario = None
        elif user and hasattr(user, 'funcionario'):
            funcionario = user.funcionario

        if user and es_secretaria(user) and not (self.instance and self.instance.pk) and not funcionario_id:
            secretaria_func = user.funcionario
            if secretaria_func and secretaria_func.jefe_inmediato:
                self.fields['funcionario'] = forms.ModelChoiceField(
                    queryset=Funcionario.objects.filter(jefe_inmediato=secretaria_func.jefe_inmediato),
                    widget=forms.Select(attrs={'class': 'form-select'}),
                    required=True,
                    empty_label="Seleccione un funcionario"
                )
        elif user and es_jefe_inmediato(user) and not (self.instance and self.instance.pk) and not funcionario_id:
            f = funcionario
            self.fields['funcionario'] = forms.ModelChoiceField(
                queryset=Funcionario.objects.filter(jefe_inmediato=f),
                widget=forms.Select(attrs={'class': 'form-select'}),
                required=True,
                empty_label="Seleccione un funcionario"
            )

        if funcionario:
            periodos_funcionario = PeriodoVacacional.objects.filter(funcionario=funcionario).order_by('fecha_inicio_periodo')
            self.fields['periodo_vacacional'].queryset = periodos_funcionario

            self.periodos_acumulados = None
            self.periodo_mas_antiguo = None
            self.periodo_mas_reciente = None
            self.periodo_mas_antiguo_habilitado = True
            self.periodo_mas_reciente_habilitado = True

            if periodos_funcionario.count() == 2:
                self.periodos_acumulados = list(periodos_funcionario)
                self.periodo_mas_antiguo = self.periodos_acumulados[0]
                self.periodo_mas_reciente = self.periodos_acumulados[1]
                self.periodo_mas_antiguo_habilitado = self.periodo_mas_antiguo.dias_pendientes_periodo > 0
                self.periodo_mas_reciente_habilitado = not self.periodo_mas_antiguo_habilitado

            self.initial.update({
                'numero_identificacion': funcionario.numero_identificacion,
                'nombre_funcionario': f"{funcionario.nombre} {funcionario.apellido}",
                'estamento': funcionario.estamento.nombre,
                'facultad_dependencia': funcionario.facultad_dependencia.nombre,
            })

            estamento_nombre = funcionario.estamento.nombre.lower()
            decreto = (funcionario.decreto_resolucion or '').strip()
        else:
            estamento_nombre = ''
            decreto = ''
            dias_derecho = 0

        if estamento_nombre == 'docente':
            if decreto == '1279':
                dias_derecho = 30
                self.initial['tipo_habiles'] = True
                self.initial['tipo_calendario'] = True
            elif decreto == '115':
                dias_derecho = 30
                self.initial['tipo_habiles'] = False
                self.initial['tipo_calendario'] = True
            else:
                dias_derecho = 0
                self.initial['tipo_habiles'] = False
                self.initial['tipo_calendario'] = False
        elif estamento_nombre == 'administrativo':
            dias_derecho = 15
            self.initial['tipo_habiles'] = True
            self.initial['tipo_calendario'] = False
        elif estamento_nombre == 'trabajador oficial':
            dias_derecho = 30
            self.initial['tipo_habiles'] = False
            self.initial['tipo_calendario'] = True
        else:
            dias_derecho = 0
            self.initial['tipo_habiles'] = False
            self.initial['tipo_calendario'] = False
        self.initial['dias_derecho'] = dias_derecho

        if funcionario:
            dias_pendientes = 0
            if hasattr(funcionario, 'periodos_vacacionales'):
                dias_pendientes = sum(p.dias_pendientes_periodo for p in funcionario.periodos_vacacionales.all())
            self.initial['dias_pendientes'] = dias_pendientes

            hoy = get_current_date_colombia()

            if estamento_nombre == 'docente':
                # Docentes: pago mensual el día 30
                if hoy.day <= 10:
                    if hoy.month == 12:
                        fecha_pago = date(hoy.year, 12, 30)
                    else:
                        fecha_pago = date(hoy.year, hoy.month, 30)
                else:
                    if hoy.month == 12:
                        fecha_pago = date(hoy.year + 1, 1, 30)
                    else:
                        fecha_pago = date(hoy.year, hoy.month + 1, 30)
            else:
                # Administrativos y trabajadores oficiales: pago quincenal (15 y 30)
                if hoy.day <= 3:
                    fecha_pago = date(hoy.year, hoy.month, 15)
                elif hoy.day <= 18:
                    fecha_pago = date(hoy.year, hoy.month, 30)
                else:
                    if hoy.month == 12:
                        fecha_pago = date(hoy.year + 1, 1, 15)
                    else:
                        fecha_pago = date(hoy.year, hoy.month + 1, 15)

            self.initial['fecha_pago'] = fecha_pago

            periodos_pendientes_count = PeriodoVacacional.objects.filter(
                funcionario=funcionario,
                dias_pendientes_periodo__gt=0
            ).count()

            self.initial['periodos_pendientes'] = periodos_pendientes_count

        if self.instance and self.instance.pk:
            if self.instance.fecha_inicio_vacaciones:
                self.fields['fecha_inicio_vacaciones'].initial = self.instance.fecha_inicio_vacaciones.strftime('%d/%m/%Y')
            if self.instance.fecha_fin_vacaciones:
                self.fields['fecha_fin_vacaciones'].initial = self.instance.fecha_fin_vacaciones.strftime('%d/%m/%Y')

    def clean_tiene_dias_pendientes(self):
        """
        Limpia y establece el valor de tiene_dias_pendientes basado en la lógica de negocio.
        Si no se proporciona en el POST, se establece basado en la existencia de reintegros pendientes.
        """
        tiene_dias_pendientes = self.cleaned_data.get('tiene_dias_pendientes', False)
        
        if 'tiene_dias_pendientes' not in self.data:
            funcionario = None
            if hasattr(self, 'cleaned_data') and 'funcionario' in self.cleaned_data:
                funcionario = self.cleaned_data['funcionario']
            elif 'instance' in self.__dict__ and self.instance and self.instance.funcionario:
                funcionario = self.instance.funcionario
            elif 'user' in self.__dict__ and hasattr(self.__dict__['user'], 'funcionario'):
                funcionario = self.__dict__['user'].funcionario
            
            if funcionario:
                reintegros_pendientes = ReintegroVacaciones.objects.filter(
                    funcionario=funcionario,
                    estado_solicitud='aprobado',
                    dias_pendientes__gt=0
                )
                tiene_dias_pendientes = reintegros_pendientes.exists()
        
        return tiene_dias_pendientes

    def clean(self):
        cleaned_data = super().clean()
        
        if 'funcionario' in self.fields and 'funcionario' in cleaned_data:
            funcionario_seleccionado = cleaned_data.get('funcionario')
            if funcionario_seleccionado and hasattr(funcionario_seleccionado, 'pk'):
                periodos_funcionario = PeriodoVacacional.objects.filter(funcionario=funcionario_seleccionado).order_by('fecha_inicio_periodo')
                self.fields['periodo_vacacional'].queryset = periodos_funcionario
                periodo_seleccionado = cleaned_data.get('periodo_vacacional')
                
                if periodo_seleccionado and periodo_seleccionado not in periodos_funcionario:
                    raise forms.ValidationError({'periodo_vacacional': 'El periodo vacacional seleccionado no pertenece al funcionario seleccionado.'})
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        user = getattr(self, 'user', None)
        if user and not instance.creada_por_id:
            instance.creada_por = user
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ReintegroVacacionesForm(forms.ModelForm):
    numero_identificacion = forms.CharField(required=False, disabled=True)
    nombre_funcionario = forms.CharField(required=False, disabled=True)
    estamento = forms.CharField(required=False, disabled=True)
    facultad_dependencia = forms.CharField(required=False, disabled=True)
    sede = forms.CharField(required=False, disabled=True)
    codigo_sabs = forms.CharField(required=False, disabled=True)

    dias_disfrutados_habiles = forms.IntegerField(
        label='Días hábiles disfrutados',
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'data-default-zero': 'true'})
    )
    dias_disfrutados_calendario = forms.IntegerField(
        label='Días calendario disfrutados',
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'data-default-zero': 'true'})
    )
    dias_pendientes_habiles = forms.IntegerField(
        label='Días hábiles por disfrutar',
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'data-default-zero': 'true'})
    )
    dias_pendientes_calendario = forms.IntegerField(
        label='Días calendario por disfrutar',
        required=False,
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'min': '0', 'data-default-zero': 'true'})
    )
    periodo_correspondiente_resumen = forms.CharField(
        label='Vacaciones correspondientes al periodo',
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-md border border-gray-300 bg-gray-100 px-4 py-2 text-gray-600 cursor-not-allowed',
            'readonly': 'readonly',
            'tabindex': '-1'
        })
    )
    periodo_disfrute_resumen = forms.CharField(
        label='Periodo en el cual disfrutó',
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-md border border-gray-300 bg-gray-100 px-4 py-2 text-gray-600 cursor-not-allowed',
            'readonly': 'readonly',
            'tabindex': '-1'
        })
    )

    class Meta:
        model = ReintegroVacaciones
        fields = [
            'solicitud_vacaciones',
            'fecha_reintegro',
            'motivo_reintegro',
            'observaciones',
            'periodo_correspondiente_desde',
            'periodo_correspondiente_hasta',
            'fecha_disfrute_desde',
            'fecha_disfrute_hasta',
            'dias_disfrutados_habiles',
            'dias_disfrutados_calendario',
            'dias_pendientes_habiles',
            'dias_pendientes_calendario',
            'codigo_sabs',
        ]
        widgets = {
            'solicitud_vacaciones': forms.Select(attrs={'class': 'form-select'}),
            'fecha_reintegro': forms.DateInput(format='%d/%m/%Y', attrs={'class': 'form-input flatpickr-input', 'placeholder': 'Seleccionar fecha', 'autocomplete': 'off'}),
            'periodo_correspondiente_desde': forms.HiddenInput(),
            'periodo_correspondiente_hasta': forms.HiddenInput(),
            'fecha_disfrute_desde': forms.HiddenInput(),
            'fecha_disfrute_hasta': forms.HiddenInput(),
            'observaciones': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
            'motivo_reintegro': forms.Select(attrs={'class': 'form-select'}),
            'codigo_sabs': forms.TextInput(attrs={
                'class': 'form-input bg-gray-100 cursor-not-allowed',
                'readonly': 'readonly'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        funcionario = None
        if self.instance and self.instance.pk:
            funcionario = self.instance.funcionario
        elif self.user and hasattr(self.user, 'funcionario'):
            funcionario = self.user.funcionario

        if self.user and hasattr(self.user, 'funcionario'):
            funcionario = self.user.funcionario

        if funcionario is not None:
            estamento_nombre = getattr(funcionario.estamento, 'nombre', '') or ''
            decreto_valor = (getattr(funcionario, 'decreto_resolucion', '') or '').strip()

            self.initial.update({
                'numero_identificacion': funcionario.numero_identificacion,
                'nombre_funcionario': f"{funcionario.nombre} {funcionario.apellido}",
                'estamento': estamento_nombre,
                'facultad_dependencia': getattr(funcionario.facultad_dependencia, 'nombre', ''),
                'sede': getattr(funcionario.sede, 'nombre', '') or getattr(funcionario.sede, 'descripcion', ''),
            })
            self.funcionario_estamento = estamento_nombre
            self.funcionario_decreto = decreto_valor
            solicitudes_autorizadas = (
                SolicitudVacaciones.objects.filter(
                    funcionario=funcionario,
                    aprobaciones__etapa='RRHH',
                    aprobaciones__estado='autorizada',
                )
                .select_related('periodo_vacacional')
                .distinct()
            )
            solicitudes_autorizadas = solicitudes_autorizadas.exclude(
                reintegrovacaciones__estado_solicitud__in=['pendiente', 'en_revision', 'devuelta', 'aprobado']
            )
            self.fields['solicitud_vacaciones'].queryset = solicitudes_autorizadas
        else:
            self.funcionario_estamento = ''
            self.funcionario_decreto = ''
            self.fields['solicitud_vacaciones'].queryset = SolicitudVacaciones.objects.none()

        if self.instance and self.instance.pk:
            self.fields['solicitud_vacaciones'].disabled = True
            self.fields['fecha_reintegro'].initial = self.instance.fecha_reintegro
            self.fields['periodo_correspondiente_desde'].initial = self.instance.periodo_correspondiente_desde
            self.fields['periodo_correspondiente_hasta'].initial = self.instance.periodo_correspondiente_hasta
            self.fields['fecha_disfrute_desde'].initial = self.instance.fecha_disfrute_desde
            self.fields['fecha_disfrute_hasta'].initial = self.instance.fecha_disfrute_hasta
            self.fields['dias_disfrutados_habiles'].initial = self.instance.dias_disfrutados_habiles
            self.fields['dias_disfrutados_calendario'].initial = self.instance.dias_disfrutados_calendario
            self.fields['dias_pendientes_habiles'].initial = self.instance.dias_pendientes_habiles
            self.fields['dias_pendientes_calendario'].initial = self.instance.dias_pendientes_calendario

        self._initialize_range_field(
            'periodo_correspondiente_desde',
            'periodo_correspondiente_hasta',
            'periodo_correspondiente_resumen'
        )
        self._initialize_range_field(
            'fecha_disfrute_desde',
            'fecha_disfrute_hasta',
            'periodo_disfrute_resumen'
        )

    def _initialize_range_field(self, start_field, end_field, target_field):
        start_date = self._extract_date_value(start_field)
        end_date = self._extract_date_value(end_field)

        if start_date:
            display_value = self._format_display_range(start_date, end_date)
            self.fields[target_field].initial = display_value
            self.initial[target_field] = display_value

    def _extract_date_value(self, field_name):
        value = None
        if self.is_bound:
            value = self.data.get(field_name)
        if not value:
            if field_name in self.initial:
                value = self.initial[field_name]
            elif getattr(self.instance, field_name, None):
                value = getattr(self.instance, field_name)

        if isinstance(value, date):
            return value

        if isinstance(value, str) and value:
            for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        return None

    @staticmethod
    def _format_display_range(start_date, end_date):
        end_date = end_date or start_date
        start_text = start_date.strftime('%d/%m/%Y')
        end_text = end_date.strftime('%d/%m/%Y')
        return f'Del {start_text} al {end_text}'

    def clean_solicitud_vacaciones(self):
        solicitud = self.cleaned_data.get('solicitud_vacaciones')
        if not solicitud:
            raise forms.ValidationError("Debe seleccionar la solicitud autorizada que desea reintegrar.")

        if not solicitud.autorizada_rrhh:
            raise forms.ValidationError("Solo se pueden reintegrar solicitudes autorizadas por Recursos Humanos.")

        if self.user and hasattr(self.user, 'funcionario'):
            if solicitud.funcionario != self.user.funcionario:
                raise forms.ValidationError("La solicitud seleccionada no pertenece al funcionario autenticado.")
        return solicitud

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get('solicitud_vacaciones') and self.instance and self.instance.pk:
            cleaned_data['solicitud_vacaciones'] = self.instance.solicitud_vacaciones

        solicitud = cleaned_data.get('solicitud_vacaciones')
        if solicitud:
            periodo = solicitud.periodo_vacacional
            if periodo and not cleaned_data.get('periodo_correspondiente_desde'):
                cleaned_data['periodo_correspondiente_desde'] = periodo.fecha_inicio_periodo
            if periodo and not cleaned_data.get('periodo_correspondiente_hasta'):
                cleaned_data['periodo_correspondiente_hasta'] = periodo.fecha_fin_periodo

            if not cleaned_data.get('fecha_disfrute_desde'):
                cleaned_data['fecha_disfrute_desde'] = solicitud.fecha_inicio_vacaciones
            if not cleaned_data.get('fecha_disfrute_hasta'):
                cleaned_data['fecha_disfrute_hasta'] = solicitud.fecha_fin_vacaciones

            if cleaned_data.get('dias_disfrutados_habiles') is None and cleaned_data.get('dias_disfrutados_calendario') is None:
                cleaned_data['dias_disfrutados_habiles'] = solicitud.total_dias_solicitados or 0

        numeric_fields = [
            'dias_disfrutados_habiles',
            'dias_disfrutados_calendario',
            'dias_pendientes_habiles',
            'dias_pendientes_calendario',
        ]
        for field in numeric_fields:
            value = cleaned_data.get(field)
            if value in (None, ''):
                cleaned_data[field] = 0

        dias_disfrutados_h = cleaned_data.get('dias_disfrutados_habiles') or 0
        dias_disfrutados_c = cleaned_data.get('dias_disfrutados_calendario') or 0
        if dias_disfrutados_h == 0 and dias_disfrutados_c == 0:
            raise forms.ValidationError("Debe registrar al menos un día disfrutado (hábil o calendario).")

        obs = cleaned_data.get('observaciones', '')
        motivo = cleaned_data.get('motivo_reintegro')
        if motivo == 'suspension_anticipada' and (not obs or not obs.strip()):
            self.add_error('observaciones', "Las observaciones son obligatorias cuando el motivo es suspensión anticipada por necesidad del servicio.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user and hasattr(self.user, 'funcionario') and not instance.pk:
            instance.funcionario = self.user.funcionario

        if instance.solicitud_vacaciones_id and not instance.periodo_vacacional_id:
            instance.periodo_vacacional = instance.solicitud_vacaciones.periodo_vacacional

        if commit:
            instance.save()
            self.save_m2m()
        return instance
