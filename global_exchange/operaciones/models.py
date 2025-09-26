from django.db import models
from usuarios.models import CustomUser
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio

class TransaccionQuerySet(models.QuerySet):
    """
    Conjunto de consultas personalizadas para el modelo Transaccion.

    Métodos
    -------
    recientes(limite=5, usuario=None)
        Devuelve las transacciones más recientes, opcionalmente filtradas por usuario.
    """
    def recientes(self, limite=5, usuario=None):
        """
        Obtiene las transacciones más recientes.

        Parameters
        ----------
        limite : int, opcional
            Número máximo de transacciones a devolver (por defecto 5).
        usuario : User, opcional
            Usuario para filtrar las transacciones. Si no se especifica,
            devuelve las transacciones de todos los usuarios.

        Returns
        -------
        QuerySet
            Conjunto de transacciones ordenadas por fecha descendente.
        """
        qs = self.order_by('-fecha')
        if usuario is not None:
            qs = qs.filter(usuario=usuario)
        return qs[:limite]

class TransaccionManager(models.Manager):
    """
    Administrador personalizado para el modelo Transaccion.

    Sobrescribe el queryset por defecto para utilizar TransaccionQuerySet
    y expone métodos de consulta especializados.
    """
    def get_queryset(self):
        return TransaccionQuerySet(self.model, using=self._db)
    def recientes(self, limite=5, usuario=None):
        return self.get_queryset().recientes(limite=limite, usuario=usuario)

class Transaccion(models.Model):
    """
    Representa una operación de cambio de moneda realizada por un usuario.

    Este modelo guarda la información de cada transacción, incluyendo
    el usuario que la realiza, las monedas origen y destino, la tasa usada,
    el monto y el estado actual de la operación.

    Atributos:
        usuario (CustomUser): Usuario que realiza la transacción. Puede ser None.
        id (int): Identificador único de la transacción.
        fecha (datetime): Fecha y hora en que se creó la transacción.
        monto (Decimal): Cantidad de dinero involucrada en la transacción.
        tipo (str): Tipo de operación: "compra" o "venta".
        estado (str): Estado actual de la transacción. Valores posibles:
            - "pendiente"
            - "confirmada"
            - "cancelada_cotizacion"
            - "cancelada_usuario"
        moneda_origen (Moneda): Moneda desde la cual se hace la conversión.
        moneda_destino (Moneda): Moneda a la cual se convierte el monto.
        tasa_usada (Decimal): Tasa de cambio congelada al iniciar la operación.
        tasa_ref (TasaDeCambio): Referencia a la tasa vigente utilizada.
    """
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("confirmada", "Confirmada"),
        ("cancelada_cotizacion", "Cancelada por cambio de cotización"),
        ("cancelada_usuario", "Cancelada por decisión del usuario"),
    ]

    TIPOS = [
        ("compra", "Compra"),
        ("venta", "Venta"),
    ]

    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="transacciones", null=True, blank=True)
    id = models.AutoField(primary_key=True)
    fecha = models.DateTimeField(auto_now_add=True)  # fecha de creación
    monto = models.DecimalField(max_digits=23, decimal_places=8)

    tipo = models.CharField(max_length=10, choices=TIPOS)  # compra o venta
    estado = models.CharField(max_length=30, choices=ESTADOS, default="pendiente")

    # 🔑 info extra para control de cotización
    moneda_origen = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name="transacciones_origen")
    moneda_destino = models.ForeignKey(Moneda, on_delete=models.CASCADE, related_name="transacciones_destino")
    
    tasa_usada = models.DecimalField(max_digits=23, decimal_places=8)  # tasa congelada al iniciar la operación
    tasa_ref = models.ForeignKey(TasaDeCambio, on_delete=models.PROTECT)  # referencia a la tasa vigente


    
    def __str__(self):
        """
        Devuelve una representación legible de la transacción.

        :return: String con la información de la transacción.
        :rtype: str
        :example: "Transacción 1 - COMPRA 1000 Dólar -> Guaraní [pendiente]"
        """
        return f"Transacción {self.id} - {self.tipo.upper()} {self.monto} {self.moneda_origen} -> {self.moneda_destino} [{self.estado}]"

    objects = TransaccionManager()


    class Meta:
        ordering = ["-fecha"]
        indexes = [
            models.Index(fields=["-fecha"]),
            models.Index(fields=["estado"]),
        ]

    @classmethod
    def ultimas(cls, limite=5, usuario=None):
        return cls.objects.recientes(limite=limite, usuario=usuario)

    def __str__(self):
        return f"Transacción {self.id} - {self.tipo.upper()} {self.monto} {self.moneda_origen} -> {self.moneda_destino} [{self.estado}]"
