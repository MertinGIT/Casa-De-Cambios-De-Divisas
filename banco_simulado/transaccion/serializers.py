from rest_framework import serializers
from .models import Cliente, Transaccion

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"   # incluye id, email, saldo


class TransaccionBancoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaccion
        fields = "__all__"
