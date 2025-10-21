
from decimal import Decimal
from django.db import transaction
from .models import StockTauser, Denominacion, MovimientoStock, RetiroEfectivo, DetalleRetiroEfectivo


class GestorStockTauser:
    """
    Clase para manejar la lógica de stock del TAUSER
    """
    
    @staticmethod
    def calcular_billetes_optimo(monto, moneda):
        """
        Calcula la combinación óptima de billetes para entregar un monto.
        Usa algoritmo greedy: siempre intenta usar las denominaciones más grandes primero.
        
        Returns:
            tuple: (billetes_dict, monto_entregado, diferencia, posible)
            - billetes_dict: {denominacion_id: cantidad}
            - monto_entregado: monto real que se puede entregar
            - diferencia: monto que no se pudo entregar
            - posible: True si se puede entregar el monto completo
        """
        # Obtener denominaciones disponibles ordenadas de mayor a menor
        stocks = StockTauser.objects.filter(
            denominacion__moneda=moneda,
            denominacion__activo=True,
            cantidad__gt=0
        ).select_related('denominacion').order_by('-denominacion__valor')
        
        billetes = {}
        monto_restante = Decimal(str(monto))
        
        for stock in stocks:
            denominacion_valor = stock.denominacion.valor
            cantidad_disponible = stock.cantidad
            
            # Calcular cuántos billetes de esta denominación se necesitan
            cantidad_necesaria = int(monto_restante / denominacion_valor)
            
            # Usar el mínimo entre lo necesario y lo disponible
            cantidad_usar = min(cantidad_necesaria, cantidad_disponible)
            
            if cantidad_usar > 0:
                billetes[stock.denominacion.id] = cantidad_usar
                monto_restante -= denominacion_valor * cantidad_usar
            
            # Si ya cubrimos el monto, salir
            if monto_restante <= 0:
                break
        
        monto_entregado = Decimal(str(monto)) - monto_restante
        diferencia = monto_restante
        posible = diferencia == 0
        
        return billetes, monto_entregado, diferencia, posible
    
    @staticmethod
    @transaction.atomic
    def registrar_retiro(transaccion_obj, billetes_dict, monto_total, monto_entregado, diferencia):
        """
        Registra un retiro de efectivo y actualiza el stock.
        
        Args:
            transaccion_obj: Objeto Transaccion
            billetes_dict: Diccionario {denominacion_id: cantidad}
            monto_total: Monto solicitado
            monto_entregado: Monto realmente entregado
            diferencia: Diferencia no entregada
        """
        # Crear el registro de retiro
        retiro = RetiroEfectivo.objects.create(
            transaccion=transaccion_obj,
            monto_total=monto_total,
            monto_entregado=monto_entregado,
            diferencia=diferencia,
            metodo_pago='efectivo'
        )
        
        # Registrar cada denominación usada y actualizar stock
        for denominacion_id, cantidad in billetes_dict.items():
            denominacion = Denominacion.objects.get(id=denominacion_id)
            stock = StockTauser.objects.select_for_update().get(denominacion=denominacion)
            
            # Crear detalle del retiro
            DetalleRetiroEfectivo.objects.create(
                retiro=retiro,
                denominacion=denominacion,
                cantidad=cantidad
            )
            
            # Actualizar stock
            stock_anterior = stock.cantidad
            stock.cantidad -= cantidad
            stock.save()
            
            # Registrar movimiento de stock
            MovimientoStock.objects.create(
                denominacion=denominacion,
                tipo='retiro',
                cantidad=-cantidad,
                stock_anterior=stock_anterior,
                stock_posterior=stock.cantidad,
                transaccion=transaccion_obj,
                observaciones=f'Retiro cliente - Transacción #{transaccion_obj.id}'
            )
        
        return retiro
    
    @staticmethod
    @transaction.atomic
    def aprovisionar(denominacion_id, cantidad, observaciones=''):
        """
        Carga/aprovisiona billetes en el TAUSER.
        """
        denominacion = Denominacion.objects.get(id=denominacion_id)
        stock, created = StockTauser.objects.get_or_create(
            denominacion=denominacion,
            defaults={'cantidad': 0}
        )
        
        stock_anterior = stock.cantidad
        stock.cantidad += cantidad
        stock.save()
        
        MovimientoStock.objects.create(
            denominacion=denominacion,
            tipo='carga',
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            stock_posterior=stock.cantidad,
            observaciones=observaciones or 'Aprovisionamiento de TAUSER'
        )
        
        return stock
    
    @staticmethod
    def obtener_stock_por_moneda(moneda):
        """
        Obtiene el stock disponible de todas las denominaciones de una moneda.
        """
        return StockTauser.objects.filter(
            denominacion__moneda=moneda,
            denominacion__activo=True
        ).select_related('denominacion').order_by('-denominacion__valor')
    
    @staticmethod
    def verificar_stock_suficiente(monto, moneda):
        """
        Verifica si hay stock suficiente para entregar un monto.
        """
        billetes, monto_entregado, diferencia, posible = GestorStockTauser.calcular_billetes_optimo(monto, moneda)
        return posible, diferencia
    

    @staticmethod
    @transaction.atomic
    def registrar_deposito(transaccion_obj, monto=None):
        """
        Registra un depósito en efectivo en el TAUSER y actualiza el stock.
        Si no se pasa un monto, se calcula automáticamente según el tipo de transacción.
        
        Args:
            transaccion_obj: objeto Transaccion
            monto: monto depositado (opcional)
        """
        # Determinar monto a depositar
        if monto is None:
            if transaccion_obj.tipo == 'venta':
                # Venta → cliente entrega guaraníes
                monto = transaccion_obj.monto * transaccion_obj.tasa_usada
            else:
                # Compra → cliente entrega monto directo
                monto = transaccion_obj.monto

        # Determinar moneda en la que entra el depósito
        if transaccion_obj.tipo == 'venta':
            moneda_deposito = transaccion_obj.moneda_destino  # ej. PYG
        else:
            moneda_deposito = transaccion_obj.moneda_origen

        # Buscar denominaciones disponibles de esa moneda
        stocks = StockTauser.objects.filter(
            denominacion__moneda=moneda_deposito,
            denominacion__activo=True
        ).select_related('denominacion').order_by('-denominacion__valor')

        if not stocks.exists():
            raise ValueError(f"No hay stock configurado para la moneda {moneda_deposito.abreviacion}")

        monto_restante = monto
        for stock in stocks:
            if monto_restante <= 0:
                break

            denom = stock.denominacion
            cantidad_a_agregar = int(monto_restante / denom.valor)

            if cantidad_a_agregar > 0:
                stock_anterior = stock.cantidad
                stock.cantidad += cantidad_a_agregar
                stock.save()

                MovimientoStock.objects.create(
                    denominacion=denom,
                    tipo='deposito',
                    cantidad=cantidad_a_agregar,
                    stock_anterior=stock_anterior,
                    stock_posterior=stock.cantidad,
                    transaccion=transaccion_obj,
                    observaciones=f'Depósito cliente - Transacción #{transaccion_obj.id}'
                )

                monto_restante -= denom.valor * cantidad_a_agregar

        # En caso de que sobre una pequeña diferencia (por redondeo)
        if monto_restante > 0:
            MovimientoStock.objects.create(
                denominacion=stocks.last().denominacion,
                tipo='ajuste',
                cantidad=0,
                stock_anterior=stocks.last().cantidad,
                stock_posterior=stocks.last().cantidad,
                transaccion=transaccion_obj,
                observaciones=f'Diferencia no registrada: {monto_restante:.2f} {moneda_deposito.abreviacion}'
            )

        return True