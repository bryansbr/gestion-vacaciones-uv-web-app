from django import template
register = template.Library()

@register.inclusion_tag("vacaciones/partials/_semaforo.html")
def semaforo_estado(estado):
    return {
        "ji":    "verde"   if estado in ("APROBADA_JEFE","PENDIENTE_COORD","APROBADA_COORD","PENDIENTE_RRHH","APROBADA_FINAL") else ("amarillo" if estado=="PENDIENTE_JEFE" else "rojo"),
        "coord": "amarillo" if estado in ("PENDIENTE_COORD",) else ("verde" if estado in ("APROBADA_COORD","PENDIENTE_RRHH","APROBADA_FINAL") else "apagado"),
        "rrhh":  "amarillo" if estado in ("PENDIENTE_RRHH",) else ("verde" if estado=="APROBADA_FINAL" else "apagado"),
    }
