from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Transaccion, Cliente
from .serializers import TransaccionBancoSerializer, ClienteSerializer

@api_view(['GET', 'POST', 'PUT'])
def transaccion_banco_view(request):
    if request.method == 'GET':
        transacciones = Transaccion.objects.all()
        serializer = TransaccionBancoSerializer(transacciones, many=True)
        return Response({
            "mensaje": "Listado de transacciones",
            "estado": "ok",
            "datos": serializer.data
        }, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = TransaccionBancoSerializer(data=request.data)
        if serializer.is_valid():
            email = request.data.get("email")
            monto = float(request.data.get("monto", 0))
            tipo = request.data.get("tipo")  # debito / credito

            cuenta, created = Cliente.objects.get_or_create(email=email)

            if tipo == "compra":
                if cuenta.saldo >= monto:
                    cuenta.saldo -= monto
                    cuenta.save()
                    transaccion = serializer.save(estado="aceptada")
                else:
                    transaccion = serializer.save(estado="rechazada", motivo="Saldo insuficiente")
                    return Response({
                        "mensaje": "Saldo insuficiente para la transacción",
                        "estado": transaccion.estado,
                        "datos": TransaccionBancoSerializer(transaccion).data
                    }, status=status.HTTP_201_CREATED)
            elif tipo == "venta":
                cuenta.saldo += monto
                cuenta.save()
                transaccion = serializer.save(estado="aceptada")
            else:
                return Response({
                    "mensaje": "Tipo de transacción inválido (use 'debito' o 'credito')",
                    "estado": "rechazada"
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "mensaje": "Transacción procesada correctamente",
                "estado": transaccion.estado,
                "datos": TransaccionBancoSerializer(transaccion).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "mensaje": "Error en los datos enviados",
                "estado": "rechazada",
                "errores": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PUT':
        referencia = request.data.get("referencia")
        if not referencia:
            return Response({
                "mensaje": "Se requiere 'referencia' para actualizar la transacción",
                "estado": "rechazada"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            transaccion = Transaccion.objects.get(referencia=referencia)
        except Transaccion.DoesNotExist:
            return Response({
                "mensaje": "Transacción no encontrada",
                "estado": "rechazada"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TransaccionBancoSerializer(transaccion, data=request.data, partial=True)
        if serializer.is_valid():
            transaccion_actualizada = serializer.save()
            return Response({
                "mensaje": "Transacción actualizada correctamente",
                "estado": transaccion_actualizada.estado,
                "datos": TransaccionBancoSerializer(transaccion_actualizada).data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "mensaje": "Error en los datos enviados",
                "estado": "rechazada",
                "errores": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    



@api_view(['GET', 'POST'])
def cliente_view(request):
    if request.method == 'GET':
        # Obtener el email del usuario que hizo la solicitud
        email = request.GET.get("email")  # lo pasaremos desde el frontend

        if not email:
            return Response({"error": "Falta el parámetro 'email'."}, status=400)

        try:
            cliente = Cliente.objects.get(email=email)
            serializer = ClienteSerializer(cliente)
            return Response(serializer.data)
        except Cliente.DoesNotExist:
            return Response({"error": "Cliente no encontrado"}, status=404)
    
    elif request.method == 'POST':
        serializer = ClienteSerializer(data=request.data)
        if serializer.is_valid():
            cliente = serializer.save()
            return Response(ClienteSerializer(cliente).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
