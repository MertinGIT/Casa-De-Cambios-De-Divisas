from django.db import models
from monedas.models import Moneda


class TasaDeCambio(models.Model):
    """
    Modelo que representa la tasa de cambio entre dos monedas.

    Atributos:
        moneda_origen (ForeignKey[Moneda]):
            Moneda de origen en la conversión (ejemplo: USD).
            - Relación many-to-one con el modelo Moneda.
            - related_name="tasas_origen" permite acceder a todas las tasas
              donde la moneda es usada como origen.
            - on_delete=models.CASCADE asegura que si la moneda es eliminada,
              también lo serán sus tasas de cambio asociadas.

        moneda_destino (ForeignKey[Moneda]):
            Moneda de destino en la conversión (ejemplo: EUR).
            - Relación many-to-one con el modelo Moneda.
            - related_name="tasas_destino" permite acceder a todas las tasas
              donde la moneda es usada como destino.
            - on_delete=models.CASCADE asegura que si la moneda es eliminada,
              también lo serán sus tasas de cambio asociadas.

        monto_compra (DecimalField):
            Valor al que la entidad compra la moneda de origen.
            - Máximo: 23 dígitos
            - Decimales: hasta 8

        monto_venta (DecimalField):
            Valor al que la entidad vende la moneda de origen.
            - Máximo: 23 dígitos
            - Decimales: hasta 8
            
        comision_compra (DecimalField):
            Comisión que se resta del monto de compra para calcular el precio final al usuario.
            - Máximo: 23 dígitos
            - Decimales: hasta 8

        comision_venta (DecimalField):
            Comisión que se suma al monto de venta para calcular el precio final al usuario.
            - Máximo: 23 dígitos
            - Decimales: hasta 8
            
        vigencia (DateTimeField):
            Fecha y hora a partir de la cual la tasa de cambio entra en vigencia.

        fecha_actualizacion (DateTimeField):
            Última fecha de modificación del registro.
            - Se actualiza automáticamente cada vez que se guarda el objeto.

        estado (BooleanField):
            Indica si la tasa de cambio está activa.
            - True: activa
            - False: inactiva
            - Valor por defecto: True

    Meta:
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        ordering = ["-fecha_actualizacion"]  
        # Ordena los registros de más reciente a más antiguo por fecha_actualizacion.

    Métodos:
        __str__:
            Devuelve una representación legible de la tasa de cambio, mostrando
            el par de monedas y sus valores de compra y venta.

    """
    moneda_origen = models.ForeignKey(Moneda,related_name="tasas_origen",on_delete=models.CASCADE)
    moneda_destino = models.ForeignKey(Moneda,related_name="tasas_destino",on_delete=models.CASCADE)
    precio_base = models.DecimalField(max_digits=23, decimal_places=8)  # 👈 nuevo campo
    #monto_compra = models.DecimalField(max_digits=23, decimal_places=8)
    #monto_venta = models.DecimalField(max_digits=23, decimal_places=8)
    comision_compra = models.DecimalField(max_digits=23,decimal_places=8,default=0)
    comision_venta = models.DecimalField(max_digits=23,decimal_places=8,default=0)
    vigencia = models.DateTimeField()
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    estado = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        ordering = ["-fecha_actualizacion"]

    def __str__(self):
        return f"{self.moneda_origen}/{self.moneda_destino} - Precio: {self.precio_base} (+{self.comision_venta}/-{self.comision_compra})"
    """
    def __str__(self):
        ""
        Retorna una representación legible de la tasa de cambio,
        mostrando el par de monedas, valores de compra/venta y comisiones.
        ""
        return (f"{self.moneda_origen}/{self.moneda_destino} - "
                f"Compra: {self.monto_compra} (Com: {self.comision_compra}) "
                f"Venta: {self.monto_venta} (Com: {self.comision_venta})")
    """