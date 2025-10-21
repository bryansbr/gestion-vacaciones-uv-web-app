from datetime import date, datetime, timedelta
from typing import NamedTuple, Optional, Tuple

import holidays
import pytz

class PlazoLimiteResult(NamedTuple):
    """Resultado del cálculo de plazo límite para solicitudes de vacaciones."""
    fecha_limite: date
    mensaje_explicativo: str
    fecha_salida: str


def get_colombia_date_today() -> date:
    """
    Obtiene la fecha actual en la zona horaria de Colombia.
    
    Returns:
        Fecha actual en Colombia
    """
    colombia_tz = pytz.timezone('America/Bogota')
    
    return datetime.now(colombia_tz).date()

def obtener_festivos_colombia(year: int) -> set:
    """
    Obtiene los días festivos de Colombia para un año específico.
    
    Args:
        year: Año para el cual obtener los festivos
        
    Returns:
        Set con las fechas festivas
    """
    return set(holidays.Colombia(years=[year]).keys())

def es_dia_habil(fecha: date) -> bool:
    """
    Verifica si una fecha es un día hábil (no es fin de semana ni festivo).
    
    Args:
        fecha: Fecha a verificar
        
    Returns:
        True si es día hábil, False en caso contrario
    """
    # Verificar si es fin de semana (sábado=5, domingo=6)
    if fecha.weekday() >= 5:
        return False
    
    # Verificar si es festivo
    festivos = obtener_festivos_colombia(fecha.year)
    return fecha not in festivos

def obtener_ultimo_dia_del_mes(year: int, month: int) -> date:
    """
    Obtiene el último día del mes especificado (30 o 31).
    
    Args:
        year: Año
        month: Mes (1-12)
        
    Returns:
        Último día del mes
    """
    # Obtener el último día del mes
    if month == 12:
        ultimo_dia = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        ultimo_dia = date(year, month + 1, 1) - timedelta(days=1)
    
    return ultimo_dia

def obtener_ultimo_dia_habil_del_mes(year: int, month: int) -> date:
    """
    Obtiene el último día hábil del mes especificado.
    
    Args:
        year: Año
        month: Mes (1-12)
        
    Returns:
        Último día hábil del mes
    """

    ultimo_dia = obtener_ultimo_dia_del_mes(year, month)
    
    while not es_dia_habil(ultimo_dia):
        ultimo_dia -= timedelta(days=1)
    
    return ultimo_dia

def obtener_ultimo_dia_habil_antes_de(fecha_limite: date) -> date:
    """
    Obtiene el último día hábil antes de una fecha límite específica.
    
    Args:
        fecha_limite: Fecha límite (no incluida)
        
    Returns:
        Último día hábil antes de la fecha límite
    """
    fecha_anterior = fecha_limite - timedelta(days=1)
    
    while not es_dia_habil(fecha_anterior):
        fecha_anterior -= timedelta(days=1)
    
    return fecha_anterior

def calcular_plazo_limite_solicitud(funcionario_estamento: str, funcionario_decreto: Optional[str] = None) -> PlazoLimiteResult:
    """
    Calcula el plazo límite para presentar solicitudes de vacaciones según el tipo de funcionario.
    
    Args:
        funcionario_estamento: Estamento del funcionario ('docente', 'administrativo', 'trabajador oficial')
        funcionario_decreto: Decreto del funcionario (solo para docentes: '1279' o '115')
        
    Returns:
        PlazoLimiteResult con:
        - fecha_limite: Última fecha hábil para presentar solicitud (tipo date)
        - mensaje_explicativo: Mensaje explicativo del plazo (str)
        - fecha_salida: Fecha estimada de salida a vacaciones (formato string 'dd/mm/yyyy')
    
    Example:
        >>> calcular_plazo_limite_solicitud('docente', '1279')
        PlazoLimiteResult(
            fecha_limite=datetime.date(2024, 6, 14),
            mensaje_explicativo='Plazo recomendado para solicitar vacaciones: hasta el 14/06/2024. Si solicita antes de esta fecha, podrá salir a vacaciones a partir del 01/07/2024 y recibirá el pago el día 30 o 31 del mes actual.',
            fecha_salida='01/07/2024'
        )    
    """
    
    hoy = get_colombia_date_today()
    estamento = funcionario_estamento.lower()
    decreto = (funcionario_decreto or '').strip()
    
    if estamento == 'docente' or estamento == 'trabajador oficial':
        # Funcionarios Docentes (Decreto 1279 y Resolución 115) y Trabajadores Oficiales
        # Plazo límite: día 15 del mes (si es hábil) o día hábil anterior
        
        # Crear fecha límite del día 15 del mes actual
        fecha_limite_teorica = date(hoy.year, hoy.month, 15)
        
        # Si el día 15 no es hábil, obtener el último día hábil anterior
        if es_dia_habil(fecha_limite_teorica):
            fecha_limite = fecha_limite_teorica
        else:
            fecha_limite = obtener_ultimo_dia_habil_antes_de(fecha_limite_teorica)
        
        # Calcular fecha de salida (día 1 del mes siguiente)
        if hoy.month == 12:
            fecha_salida = date(hoy.year + 1, 1, 1)
        else:
            fecha_salida = date(hoy.year, hoy.month + 1, 1)
        
        # Asegurar que la fecha de salida sea hábil
        while not es_dia_habil(fecha_salida):
            fecha_salida += timedelta(days=1)
        
        mensaje_explicativo = (
            f"Plazo recomendado para solicitar vacaciones: hasta el {fecha_limite.strftime('%d/%m/%Y')}. "
            f"Si solicita antes de esta fecha, podrá salir a vacaciones a partir del "
            f"{fecha_salida.strftime('%d/%m/%Y')} y recibirá el pago el día 30 o 31 del mes actual."
        )
        
        return PlazoLimiteResult(fecha_limite, mensaje_explicativo, fecha_salida.strftime('%d/%m/%Y'))
    
    elif estamento == 'administrativo':
        # Funcionarios Administrativos
        # Plazo límite: día 10 del mes (si es hábil) o día hábil anterior
        
        # Crear fecha límite del día 10 del mes actual
        fecha_limite_teorica = date(hoy.year, hoy.month, 10)
        
        # Si el día 10 no es hábil, obtener el último día hábil anterior
        if es_dia_habil(fecha_limite_teorica):
            fecha_limite = fecha_limite_teorica
        else:
            fecha_limite = obtener_ultimo_dia_habil_antes_de(fecha_limite_teorica)
        
        # Calcular fecha de salida (día 16 del mismo mes)
        fecha_salida = date(hoy.year, hoy.month, 16)
        
        # Asegurar que la fecha de salida sea hábil
        while not es_dia_habil(fecha_salida):
            fecha_salida += timedelta(days=1)
        
        mensaje_explicativo = (
            f"Plazo recomendado para solicitar vacaciones: hasta el {fecha_limite.strftime('%d/%m/%Y')}. "
            f"Si solicita antes de esta fecha, podrá salir a vacaciones a partir del "
            f"{fecha_salida.strftime('%d/%m/%Y')} y recibirá el pago el día 15 del mes actual."
        )
        
        return PlazoLimiteResult(fecha_limite, mensaje_explicativo, fecha_salida.strftime('%d/%m/%Y'))
    
    else:
        # Estamento no reconocido
        fecha_limite = hoy
        mensaje_explicativo = "Estamento no reconocido. Contacte al administrador."
        fecha_salida = hoy.strftime('%d/%m/%Y')
        
        return PlazoLimiteResult(fecha_limite, mensaje_explicativo, fecha_salida)

def calcular_fecha_salida_y_pago_fuera_plazo(funcionario_estamento: str, funcionario_decreto: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Calcula la fecha de salida y pago cuando la solicitud se hace fuera del plazo límite.
    
    Args:
        funcionario_estamento: Estamento del funcionario
        funcionario_decreto: Decreto del funcionario (solo para docentes)
        
    Returns:
        Tupla con:
        - fecha_salida: Fecha de salida a vacaciones
        - fecha_pago: Fecha de pago
        - mensaje_explicativo: Mensaje explicativo
    """
    
    hoy = get_colombia_date_today()
    estamento = funcionario_estamento.lower()
    decreto = (funcionario_decreto or '').strip()
    
    if estamento == 'docente' or estamento == 'trabajador oficial':
        # Si se excede el plazo, salir a partir del mes subsiguiente
        if hoy.month == 12:
            fecha_salida = date(hoy.year + 1, 2, 1)
            fecha_pago = date(hoy.year + 1, 1, 30)
        elif hoy.month == 11:
            fecha_salida = date(hoy.year + 1, 1, 1)
            fecha_pago = date(hoy.year, 12, 30)
        else:
            fecha_salida = date(hoy.year, hoy.month + 2, 1)
            fecha_pago = date(hoy.year, hoy.month + 1, 30)
        
        # Asegurar que las fechas sean hábiles
        while not es_dia_habil(fecha_salida):
            fecha_salida += timedelta(days=1)
        
        mensaje_explicativo = (
            f"Si las solicita hoy, podrá salir a vacaciones a partir del "
            f"{fecha_salida.strftime('%d/%m/%Y')} y recibirá el pago el "
            f"{fecha_pago.strftime('%d/%m/%Y')}."
        )
        
        return fecha_salida.strftime('%d/%m/%Y'), fecha_pago.strftime('%d/%m/%Y'), mensaje_explicativo
    
    elif estamento == 'administrativo':
        # Reglas especiales para administrativos fuera de plazo
        if hoy.day <= 25:
            # Si solicita después del día 10 y hasta el 25
            fecha_salida = date(hoy.year, hoy.month + 1, 1) if hoy.month < 12 else date(hoy.year + 1, 1, 1)
            fecha_pago = obtener_ultimo_dia_del_mes(hoy.year, hoy.month)
            
            # Asegurar que la fecha de salida sea hábil
            while not es_dia_habil(fecha_salida):
                fecha_salida += timedelta(days=1)
            
            mensaje_explicativo = (
                f"Al solicitar después del plazo recomendado (entre el día 11 y 25), podrá salir a vacaciones a partir del "
                f"{fecha_salida.strftime('%d/%m/%Y')} y recibirá el pago el "
                f"{fecha_pago.strftime('%d/%m/%Y')}."
            )
        else:
            # Si solicita después del día 25
            fecha_salida = date(hoy.year, hoy.month + 1, 16) if hoy.month < 12 else date(hoy.year + 1, 1, 16)
            fecha_pago = date(hoy.year, hoy.month + 1, 15) if hoy.month < 12 else date(hoy.year + 1, 1, 15)
            
            # Asegurar que la fecha de salida sea hábil
            while not es_dia_habil(fecha_salida):
                fecha_salida += timedelta(days=1)
            
            mensaje_explicativo = (
                f"Al solicitar después del día 25, podrá salir a vacaciones a partir del "
                f"{fecha_salida.strftime('%d/%m/%Y')} y recibirá el pago el "
                f"{fecha_pago.strftime('%d/%m/%Y')}."
            )
        
        return fecha_salida.strftime('%d/%m/%Y'), fecha_pago.strftime('%d/%m/%Y'), mensaje_explicativo
    
    else:
        # Estamento no reconocido
        mensaje_explicativo = "Estamento no reconocido. Contacte al administrador."
        return hoy.strftime('%d/%m/%Y'), hoy.strftime('%d/%m/%Y'), mensaje_explicativo

def puede_solicitar_vacaciones_hoy(funcionario_estamento: str, funcionario_decreto: Optional[str] = None) -> Tuple[bool, str]:
    """
    Proporciona información sobre los plazos de solicitud de vacaciones.
    Siempre permite solicitar, pero informa sobre las consecuencias según la fecha.
    
    Args:
        funcionario_estamento: Estamento del funcionario
        funcionario_decreto: Decreto del funcionario (solo para docentes)
        
    Returns:
        Tupla con:
        - puede_solicitar: Siempre True (se permite solicitar en cualquier momento)
        - mensaje: Mensaje informativo sobre plazos y consecuencias
    """
    
    hoy = get_colombia_date_today()
    plazo_resultado = calcular_plazo_limite_solicitud(funcionario_estamento, funcionario_decreto)
    
    if hoy <= plazo_resultado.fecha_limite:
        return True, plazo_resultado.mensaje_explicativo
    else:
        fecha_salida_fuera, fecha_pago_fuera, mensaje_fuera = calcular_fecha_salida_y_pago_fuera_plazo(funcionario_estamento, funcionario_decreto)
        mensaje_completo = f"El plazo recomendado para solicitar vacaciones era hasta el {plazo_resultado.fecha_limite.strftime('%d/%m/%Y')}. {mensaje_fuera}"
        return True, mensaje_completo
