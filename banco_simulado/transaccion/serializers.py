from rest_framework import serializers
from .models import Cliente, Cuenta, Transaccion, Moneda, Entidad

class MonedaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moneda
        fields = "__all__"

class EntidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entidad
        fields = "__all__"

class CuentaSerializer(serializers.ModelSerializer):
    cliente = serializers.StringRelatedField()  # trae email o nombre del cliente
    moneda = MonedaSerializer(read_only=True)
    entidad = EntidadSerializer(read_only=True)

    class Meta:
        model = Cuenta
        fields = "__all__"

class ClienteSerializer(serializers.ModelSerializer):
    cuentas = CuentaSerializer(many=True, read_only=True)

    class Meta:
        model = Cliente
        fields = "__all__"

class TransaccionBancoSerializer(serializers.ModelSerializer):
    cuenta = CuentaSerializer(read_only=True)
    cuenta_destino = CuentaSerializer(read_only=True)

    class Meta:
        model = Transaccion
        fields = "__all__"
