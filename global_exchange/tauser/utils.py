from decimal import Decimal
from django.db import transaction
from .models import StockTauser, Denominacion, MovimientoStock, RetiroEfectivo, DetalleRetiroEfectivo, ReservaTauser, DetalleReservaTauser
from django.utils import timezone
from datetime import timedelta

from django.utils import timezone
from datetime import timedelta
from .models import ReservaTauser

class GestorStockTauser:
    """
    Clase encargada de gestionar el stock de efectivo (billetes) en el TAUSER.

    Contiene métodos para reservar, liberar, retirar y aprovisionar efectivo,
    así como para registrar depósitos y movimientos asociados al stock.
    Todos los procesos críticos usan transacciones atómicas para garantizar
    la consistencia de datos.
    """

    @staticmethod
    @transaction.atomic
    def reservar_efectivo(transaccion_obj, monto, moneda, localidad, duracion_minutos=4320):
        """
        Reserva billetes para una operación pendiente de confirmación.

        Calcula la combinación óptima de billetes para cubrir el monto solicitado
        (solo usa la parte entera del monto para la reserva física), descuenta
        temporalmente el stock y guarda la reserva en la base de datos.

        Args:
            transaccion_obj (Transaccion): Objeto de la transacción asociada.
            monto (Decimal | float): Monto total a reservar.
            moneda (Moneda): Moneda de la reserva.
            duracion_minutos (int, opcional): Tiempo de expiración de la reserva.
                Por defecto, 15 minutos.

        Returns:
            ReservaTauser: Objeto de reserva creado.

        Raises:
            ValueError: Si no hay suficiente stock para cubrir la reserva.
        """
        print(f"💸 Iniciando reserva TAUSER para {monto} {moneda.abreviacion}", flush=True)
        print(f"   Localidad: {localidad.nombre}", flush=True)

        # Tomar solo la parte entera para calcular billetes
        monto_entero = int(Decimal(monto))
        print(f"🔹 Monto entero para billetes: {monto_entero}", flush=True)

        # Calcular combinación óptima de billetes
        billetes_dict, monto_entregado, diferencia, posible = GestorStockTauser.calcular_billetes_optimo(
            monto_entero,
            moneda,
            localidad
        )

        print(f"🔹 Billetes calculados: {billetes_dict}", flush=True)
        print(f"🔹 Monto entregable (entero): {monto_entregado}", flush=True)
        print(f"🔹 Diferencia restante: {diferencia}", flush=True)
        print(f"🔹 Posible entregar todo el entero?: {posible}", flush=True)

        if not posible:
            raise ValueError(f"No hay suficiente stock en {localidad.nombre} para reservar {monto_entero} {moneda.abreviacion}")

        # Crear la reserva con el monto decimal real
        reserva = ReservaTauser.objects.create(
            transaccion=transaccion_obj,
            moneda=moneda,
            monto_total=monto,  # aquí guardamos el decimal real
            expiracion=timezone.now() + timedelta(minutes=duracion_minutos),
            activa=True
        )
        print(f"🔹 Reserva creada: ID {reserva.id}, monto_total {reserva.monto_total}", flush=True)
        print(f"🔹 Expira en: {reserva.expiracion}", flush=True)

        # Registrar denominaciones reservadas
        for denom_id, cantidad in billetes_dict.items():
            denominacion = Denominacion.objects.get(id=denom_id)
            DetalleReservaTauser.objects.create(
                reserva=reserva,
                denominacion=denominacion,
                cantidad_reservada=cantidad
            )
            print(f"   → Reservados {cantidad} billetes de {denominacion.valor} {moneda.abreviacion}", flush=True)

            # Reducir stock de la localidad específica
            stock = StockTauser.objects.select_for_update().get(
                denominacion=denominacion,
                localidad=localidad
            )
            stock.cantidad -= cantidad
            stock.save()
            print(f"   → Stock actualizado en {localidad.nombre}: {stock.cantidad} billetes restantes", flush=True)

        print(f"✅ Reserva TAUSER finalizada para transacción {transaccion_obj.id}", flush=True)
        return reserva
        
    @staticmethod
    @transaction.atomic
    def liberar_reserva(transaccion_obj):
        """
        Libera una reserva activa (por cancelación o expiración).

        Args:
            transaccion_obj (Transaccion): Objeto de la transacción asociada.

        Returns:
            bool: True si se liberó una reserva activa, False si no existía.
        """
        try:
            reserva = ReservaTauser.objects.select_for_update().get(
                   transaccion=transaccion_obj, activa=True
            )
        except ReservaTauser.DoesNotExist:
            return False

        reserva.activa = False
        reserva.save()
        return True
        
    @staticmethod
    def calcular_billetes_optimo(monto, moneda,localidad):
        """
        Calcula la combinación óptima de billetes disponibles para entregar un monto.

        Usa un algoritmo "greedy" (voraz) que prioriza denominaciones más grandes
        hasta cubrir el monto deseado o agotar el stock disponible.

        Args:
            monto (Decimal | float): Monto solicitado.
            moneda (Moneda): Moneda del monto.
            localidad (Localidad): Localidad del TAUSER.

        Returns:
            tuple:
                - billetes_dict (dict): {denominacion_id: cantidad}
                - monto_entregado (Decimal): Monto efectivamente cubierto.
                - diferencia (Decimal): Monto restante no entregado.
                - posible (bool): True si se pudo cubrir el monto completo.
        """
        # Obtener denominaciones disponibles ordenadas de mayor a menor
        stocks = StockTauser.objects.filter(
            localidad=localidad,
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

        Crea los registros correspondientes en las tablas:
        - RetiroEfectivo
        - DetalleRetiroEfectivo
        - MovimientoStock

        Args:
            transaccion_obj (Transaccion): Transacción asociada al retiro.
            billetes_dict (dict): Diccionario {denominacion_id: cantidad}.
            monto_total (Decimal): Monto solicitado por el cliente.
            monto_entregado (Decimal): Monto realmente entregado.
            diferencia (Decimal): Diferencia no entregada (por falta de billetes).

        Returns:
            RetiroEfectivo: Objeto del retiro registrado.
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
        Carga o reaprovisiona billetes en el TAUSER.

        Incrementa el stock de una denominación específica y registra el movimiento.

        Args:
            denominacion_id (int): ID de la denominación.
            cantidad (int): Número de billetes agregados.
            observaciones (str, opcional): Nota descriptiva del movimiento.

        Returns:
            StockTauser: Objeto de stock actualizado.
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
        Obtiene todas las denominaciones activas y su stock disponible para una moneda.

        Args:
            moneda (Moneda): Moneda a consultar.

        Returns:
            QuerySet[StockTauser]: Lista de stocks ordenados por valor descendente.
        """
        return StockTauser.objects.filter(
            denominacion__moneda=moneda,
            denominacion__activo=True
        ).select_related('denominacion').order_by('-denominacion__valor')
    
    @staticmethod
    def verificar_stock_suficiente(monto, moneda):
        """
        Verifica si existe stock suficiente para cubrir un monto solicitado.

        Args:
            monto (Decimal): Monto solicitado.
            moneda (Moneda): Moneda del monto.

        Returns:
            tuple:
                - posible (bool): True si puede cubrirse completamente.
                - diferencia (Decimal): Monto faltante en caso contrario.
        """
        billetes, monto_entregado, diferencia, posible = GestorStockTauser.calcular_billetes_optimo(monto, moneda)
        return posible, diferencia
    

    @staticmethod
    @transaction.atomic
    def registrar_deposito(transaccion_obj, monto=None):
        """
        Registra un depósito en efectivo y actualiza el stock.

        Distribuye el monto en las denominaciones de la moneda correspondiente
        y registra los movimientos de stock asociados.

        Args:
            transaccion_obj (Transaccion): Objeto de la transacción asociada.
            monto (Decimal | None): Monto depositado. Si es None, se calcula automáticamente.

        Returns:
            bool: True si el depósito se registró correctamente.

        Raises:
            ValueError: Si no hay denominaciones configuradas para la moneda.
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
    
    @staticmethod
    @transaction.atomic
    def registrar_deposito_efectivo(monto, moneda,localidad):
        """
        Registra un depósito en efectivo incrementando el stock de billetes.

        Distribuye el monto total en las denominaciones disponibles según un
        orden predefinido (de mayor a menor) y actualiza los registros de stock.

        Args:
            monto (Decimal | float): Monto total depositado.
            moneda (Moneda): Moneda del depósito.
            localidad (Localidad): Localidad del TAUSER.

        Returns:
            dict: {denominacion_id: cantidad} con los billetes agregados.

        Raises:
            ValueError: Si no existen denominaciones o el orden no está configurado.
        """
        from decimal import Decimal
        
        # Definir el orden de denominaciones por moneda
        ORDEN_DENOMINACIONES = {
            'PYG': [100000, 50000, 20000, 10000, 5000, 2000],  # Mayor a menor
            'USD': [100, 50, 20, 10, 5, 1],
            'EUR': [500, 200, 100, 50, 20, 10, 5],
        }
        
        orden = ORDEN_DENOMINACIONES.get(moneda.abreviacion, [])
        
        if not orden:
            raise ValueError(f"No hay orden de denominaciones configurado para {moneda.abreviacion}")
        
        # Obtener las denominaciones existentes para esta moneda
        denominaciones_disponibles = Denominacion.objects.filter(
            moneda=moneda,
            activo=True
        ).select_related('moneda')
        
        if not denominaciones_disponibles.exists():
            raise ValueError(f"No hay denominaciones configuradas para {moneda.abreviacion}")
        
        # Crear dict de denominaciones por valor
        denoms_dict = {float(d.valor): d for d in denominaciones_disponibles}
        
        # Algoritmo greedy: usar billetes más grandes primero
        monto_restante = Decimal(str(monto))
        billetes_depositados = {}
        
        for valor in orden:
            if valor not in denoms_dict:
                continue
                
            denominacion = denoms_dict[valor]
            valor_decimal = Decimal(str(valor))
            
            # Calcular cuántos billetes de esta denominación caben
            cantidad_billetes = int(monto_restante / valor_decimal)
            
            if cantidad_billetes > 0:
                billetes_depositados[denominacion.id] = cantidad_billetes
                monto_restante -= valor_decimal * cantidad_billetes
                
                # Actualizar stock
                stock, created = StockTauser.objects.get_or_create(
                    denominacion=denominacion,
                    localidad=localidad,
                    defaults={'cantidad': 0}
                )
                stock.cantidad += cantidad_billetes
                stock.save()
                
                print(f"Depositado en {localidad.nombre}: {cantidad_billetes} x {valor} {moneda.abreviacion}")
        
        # Si sobra algo (por ejemplo, centavos), lo ignoramos o lanzamos error
        if monto_restante > Decimal('0.01'):
            print(f"Advertencia: Sobró {monto_restante} {moneda.abreviacion} sin asignar")
        
        return billetes_depositados