from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from usuarios.models import Funcionario
from .serializers import EstadoVacacionesSerializer

class EstadoVacacionesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            funcionario = request.user.funcionario
        except Funcionario.DoesNotExist:
            return Response(
                {"detail": "No se encontró funcionario asociado al usuario actual."},
                status=status.HTTP_404_NOT_FOUND
            )

        estado = funcionario.estado_de_vacaciones()
        serializer = EstadoVacacionesSerializer(estado)
        return Response(serializer.data)
