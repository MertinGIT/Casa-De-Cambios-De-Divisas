from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# ============================
# CLIENTES
# ============================
class Cliente(models.Model):
    """
    Representa a un cliente del banco.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cliente", null=True, blank=True)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    documento = models.CharField(max_length=20, unique=True, null=True)  # DNI, RUC, pasaporte
    telefono = models.CharField(max_length=20, blank=True, null=True)

    def clean(self):
        super().clean()
        if self.documento and len(self.documento) < 6:
            raise ValidationError("El documento debe tener al menos 6 caracteres")

    def __str__(self):
        return f"{self.nombre or self.email}"


# ============================
# MONEDAS Y ENTIDADES
# ============================
class Moneda(models.Model):
    codigo = models.CharField(max_length=10, unique=True)  # PYG, USD, EUR
    nombre = models.CharField(max_length=50)

    def clean(self):
        super().clean()
        if self.codigo:
            self.codigo = self.codigo.upper()

    def __str__(self):
        return self.codigo


class Entidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


# ============================
# CUENTAS
# ============================
class Cuenta(models.Model):
    TIPOS_CUENTA = [
        ("ahorro", "Cuenta de Ahorro"),
        ("corriente", "Cuenta Corriente"),
        ("inversion", "Cuenta de Inversión"),
    ]

    ESTADOS_CUENTA = [
        ("activa", "Activa"),
        ("bloqueada", "Bloqueada"),
        ("cerrada", "Cerrada"),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="cuentas")
    nro_cuenta = models.CharField(max_length=30, unique=True)
    entidad = models.ForeignKey(Entidad, on_delete=models.PROTECT, related_name="cuentas")
    moneda = models.ForeignKey(Moneda, on_delete=models.PROTECT, related_name="cuentas")
    saldo = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    tipo_cuenta = models.CharField(max_length=20, choices=TIPOS_CUENTA, default="ahorro")
    estado = models.CharField(max_length=20, choices=ESTADOS_CUENTA, default="activa")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(saldo__gte=0), 
                name='saldo_no_negativo'
            ),
        ]

    def clean(self):
        super().clean()
        if self.saldo < 0:
            raise ValidationError("El saldo no puede ser negativo")
        if not self.nro_cuenta or len(self.nro_cuenta) < 5:
            raise ValidationError("El número de cuenta debe tener al menos 5 caracteres")

    @property
    def puede_operar(self):
        return self.estado == 'activa'


    def retirar(self, monto):
        """Realiza un retiro de la cuenta"""
        if monto <= 0:
            raise ValueError("El monto debe ser positivo")
        if not self.puede_operar:
            raise ValueError("La cuenta no está activa")
        if self.saldo < monto:
            raise ValueError("Saldo insuficiente")
        self.saldo -= monto
        self.save()

    def __str__(self):
        return f"{self.nro_cuenta} - {self.moneda.codigo} - {self.cliente.email}"


# ============================
# TRANSACCIONES
# ============================
class Transaccion(models.Model):
    

    """
    ESTADOS_TRANSACCION = [
        ("pendiente", "Pendiente"),
        ("completada", "Completada"),
        ("fallida", "Fallida"),
        ("cancelada", "Cancelada"),
    ]
    """
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="transacciones")
    """
    cuenta_destino = models.ForeignKey(
        Cuenta, on_delete=models.SET_NULL, null=True, blank=True, related_name="transferencias_recibidas"
    )
    """
    cedula = models.CharField(max_length=15)
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    tipo = models.CharField(max_length=20)
    estado = models.CharField(max_length=20, default="pendiente")
    fecha = models.DateTimeField(auto_now_add=True)
    referencia = models.CharField(max_length=50, blank=True, null=True, unique=True)
    motivo = models.TextField(blank=True, null=True)
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    """
    usuario_ejecutor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    """

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(monto__gt=0), 
                name='monto_positivo'
            ),
        ]
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['cuenta', 'fecha']),
            models.Index(fields=['estado']),
            models.Index(fields=['tipo']),
        ]

    def clean(self):
        super().clean()
        if self.monto <= 0:
            raise ValidationError("El monto debe ser positivo")
        if self.tipo == 'transferencia' and not self.cuenta_destino:
            raise ValidationError("Las transferencias requieren cuenta destino")
        if self.cuenta_destino and self.cuenta == self.cuenta_destino:
            raise ValidationError("No se puede transferir a la misma cuenta")
        if self.tipo == 'transferencia' and self.cuenta_destino:
            if self.cuenta.moneda != self.cuenta_destino.moneda:
                raise ValidationError("Las transferencias directas deben ser en la misma moneda")

    def __str__(self):
        return f"{self.tipo.upper()} {self.monto} {self.cuenta.moneda.codigo} - {self.cuenta.nro_cuenta}"


# ============================
# AUDITORÍA
# ============================
class AuditoriaSaldo(models.Model):
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE, related_name="auditoria_saldo")
    saldo_anterior = models.DecimalField(max_digits=15, decimal_places=2)
    saldo_nuevo = models.DecimalField(max_digits=15, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    transaccion = models.ForeignKey(Transaccion, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['cuenta', 'fecha']),
        ]

    def __str__(self):
        return f"Auditoría {self.cuenta.nro_cuenta} - {self.fecha}"


# ============================
# TASAS DE CAMBIO Y COMISIONES
# ============================
class TasaCambio(models.Model):
    moneda_origen = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name="tasas_origen")
    moneda_destino = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name="tasas_destino")
    tasa = models.DecimalField(max_digits=15, decimal_places=6)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("moneda_origen", "moneda_destino")
        constraints = [
            models.CheckConstraint(
                check=models.Q(tasa__gt=0), 
                name='tasa_positiva'
            ),
        ]

    def clean(self):
        super().clean()
        if self.tasa <= 0:
            raise ValidationError("La tasa debe ser positiva")
        if self.moneda_origen == self.moneda_destino:
            raise ValidationError("La moneda origen debe ser diferente a la destino")

    @classmethod
    def obtener_tasa_actual(cls, moneda_origen, moneda_destino):
        """Obtiene la tasa de cambio actual entre dos monedas"""
        try:
            return cls.objects.get(
                moneda_origen=moneda_origen, 
                moneda_destino=moneda_destino
            ).tasa
        except cls.DoesNotExist:
            return None

    def __str__(self):
        return f"{self.moneda_origen.codigo} -> {self.moneda_destino.codigo} : {self.tasa}"


class Comision(models.Model):
    TIPOS_TRANSACCION = [
        ("debito", "Débito"),
        ("credito", "Crédito"),
        ("transferencia", "Transferencia"),
    ]
    tipo_transaccion = models.CharField(max_length=20, choices=TIPOS_TRANSACCION)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    monto_fijo = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(porcentaje__gte=0), 
                name='porcentaje_no_negativo'
            ),
            models.CheckConstraint(
                check=models.Q(monto_fijo__gte=0), 
                name='monto_fijo_no_negativo'
            ),
        ]

    def clean(self):
        super().clean()
        if self.porcentaje < 0:
            raise ValidationError("El porcentaje no puede ser negativo")
        if self.monto_fijo < 0:
            raise ValidationError("El monto fijo no puede ser negativo")

    def calcular_comision(self, monto_transaccion):
        """Calcula la comisión para un monto dado"""
        comision_porcentaje = (monto_transaccion * self.porcentaje) / 100
        return comision_porcentaje + self.monto_fijo

    def __str__(self):
        return f"Comisión {self.tipo_transaccion} - {self.porcentaje}% + {self.monto_fijo}"