"""
Seed de datos iniciales para Global Exchange (idempotente).
Crea SOLO si no existen:
- Roles y perfiles de grupo (ADMIN, Analista, Usuario, Usuario Asociado)
- Usuarios base (superadmin, analista, usuario, usuario_asociado)
- Segmentaciones (VIP 10%, CORPORATIVO 5%, MINORISTA 0%)
- Clientes demo y relaciones Usuario-Cliente
- Monedas (PYG, USD, EUR)
- Tasas de cambio base (precio_base + comisiones)
- Métodos de pago (Efectivo, Transferencia, Tarjeta)
- Medios de acreditación y tipos básicos
- Límites por moneda (si el modelo existe)
- Notificación de bienvenida (si existe)
- Transacciones demo confirmadas (y una factura de ejemplo si el modelo existe)

Se puede ejecutar múltiples veces sin duplicar.
"""
from decimal import Decimal
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta


User = get_user_model()

def get_model(label):
    """
    Intenta resolver una app.Model, retorna None si no existe.
    """
    try:
        return apps.get_model(label)
    except Exception:
        return None

def fields_filter(model, **kwargs):
    """
    Filtra kwargs dejando solo los campos que existen en el model.
    """
    if model is None:
        return {}
    model_fields = {f.name for f in model._meta.get_fields()}
    return {k: v for k, v in kwargs.items() if k in model_fields}

def safe_get_or_create(model, defaults=None, **lookup):
    """
    get_or_create tolerante a duplicados o claves primarias ya usadas.
    Si hay múltiples coincidencias o error de clave duplicada, devuelve el primero existente.
    """
    if model is None:
        return None, False
    lookup_f = fields_filter(model, **lookup)
    defaults_f = fields_filter(model, **(defaults or {}))
    try:
        return model.objects.get_or_create(**lookup_f, defaults=defaults_f)
    except model.MultipleObjectsReturned:
        return model.objects.filter(**lookup_f).first(), False
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            # Buscar el primero con mismo campo (ej: abreviación)
            existing = model.objects.filter(**lookup_f).first()
            if existing:
                return existing, False
        raise

def safe_update(instance, **values):
    """
    setattr solo para campos existentes.
    """
    if instance is None:
        return
    model_fields = {f.name for f in instance._meta.get_fields()}
    for k, v in values.items():
        if k in model_fields:
            setattr(instance, k, v)
    instance.save()

def ensure_roles_and_profiles():
    """
    Solo asegura que los grupos y perfiles existan.
    Los permisos ya se configuran automáticamente desde signals.py (post_migrate).
    """
    GroupProfile = get_model("roles_permisos.GroupProfile")
    g_admin, _ = Group.objects.get_or_create(name="ADMIN")
    g_analista, _ = Group.objects.get_or_create(name="Analista")
    g_usuario, _ = Group.objects.get_or_create(name="Usuario")
    g_uasoc, _ = Group.objects.get_or_create(name="Usuario Asociado")

    if GroupProfile:
        for g in (g_admin, g_analista, g_usuario, g_uasoc):
            GroupProfile.objects.get_or_create(group=g, defaults={"estado": "Activo"})

    return {
        "ADMIN": g_admin,
        "Analista": g_analista,
        "Usuario": g_usuario,
        "Usuario Asociado": g_uasoc,
    }
def ensure_users(groups):
    def safe_user_get_or_create(username, email, cedula, password, main_group, extra_groups=None, is_superuser=False, is_staff=False):
        """
        Crea o recupera un usuario de forma idempotente.
        Si ya existe por username o cédula, lo reutiliza.
        Puede pertenecer a uno o varios grupos.
        """
        user = User.objects.filter(username=username).first() or User.objects.filter(cedula=cedula).first()
        if not user:
            user = User.objects.create_user(
                username=username,
                email=email,
                cedula=cedula,
                password=password,
                is_superuser=is_superuser,
                is_staff=is_staff,
                is_active=True,
            )
            print(f"🧩 Usuario creado: {username}")
        else:
            print(f"✅ Usuario existente: {username}")

        # Asignar grupo principal
        user.groups.add(main_group)

        # Asignar grupos adicionales si hay
        if extra_groups:
            for g in extra_groups:
                user.groups.add(g)

        return user

    su = safe_user_get_or_create(
        "superadmin", "admin@empresa.com", "00000000", "ContraseñaSegura123",
        groups["ADMIN"], is_superuser=True, is_staff=True
    )
    ua = safe_user_get_or_create(
        "analista", "analista@empresa.com", "11111111", "Global123",
        groups["Analista"]
    )
    u = safe_user_get_or_create(
        "usuario", "usuario@empresa.com", "22222222", "Global123",
        groups["Usuario"]
    )

    # === Usuarios Asociados ===
    uas1 = safe_user_get_or_create(
        "usuario_asociado", "leandro.f3418@fpuna.edu.py", "33333333", "Global123",
        groups["Usuario Asociado"], extra_groups=[groups["Usuario"]]
    )
    uas2 = safe_user_get_or_create(
        "usuario_asociado2", "rodriguezmartinv02@gmail.com", "44444444", "Global123",
        groups["Usuario Asociado"], extra_groups=[groups["Usuario"]]
    )
    uas3 = safe_user_get_or_create(
        "usuario_asociado3", "alanalcaraz010@gmail.com", "55555555", "Global123",
        groups["Usuario Asociado"], extra_groups=[groups["Usuario"]]
    )

    return {
        "superadmin": su,
        "analista": ua,
        "usuario": u,
        "usuario_asociado": uas1,
        "usuario_asociado2": uas2,
        "usuario_asociado3": uas3,
    }

# def ensure_demo_invoices(users):
#     """
#     Genera 5 facturas demo asociadas a transacciones confirmadas,
#     usando los rangos de facturación disponibles.
#     """
#     from django.utils import timezone
#     from decimal import Decimal
#     import random
#     import uuid

#     Factura = get_model("facturacion.Factura")
#     RangoFacturacion = get_model("facturacion.RangoFacturacion")
#     Transaccion = get_model("operaciones.Transaccion")
#     Cliente = get_model("clientes.Cliente")

#     usuario_asociado = users.get("usuario_asociado")

#     if not usuario_asociado:
#         print("⚠️ No se encontró el usuario_asociado.")
#         return

#     # Buscar o crear rango de facturación del usuario_asociado
#     rango, _ = RangoFacturacion.objects.get_or_create(
#         establecimiento="001",
#         punto_expedicion="003",
#         usuario=usuario_asociado,
#         defaults={
#             "numero_inicio": 1,
#             "numero_fin": 50,
#             "numero_actual": 1,
#             "activo": True,
#         },
#     )

#     # Buscar transacciones confirmadas sin factura
#     transacciones = list(
#         Transaccion.objects.filter(estado="confirmada", factura__isnull=True)[:5]
#     )

#     if not transacciones:
#         print("⚠️ No hay transacciones confirmadas disponibles para facturar.")
#         return

#     print("🧾 Generando facturas demo...")

#     for i, t in enumerate(transacciones, 1):
#         # Obtener número de factura del rango
#         try:
#             numero_doc = rango.obtener_siguiente_numero()
#         except Exception as e:
#             print(f"⚠️ No se pudo obtener número de rango: {e}")
#             break

#         # Crear factura
#         f = Factura.objects.create(
#             cliente=t.cliente,
#             transaccion=t,
#             monto_total=t.monto,
#             moneda=t.moneda_destino.abreviacion,
#             tipo_cambio=t.tasa_usada,
#             estado="aprobado",
#             estado_sifen="APROBADO",
#             descripcion_sifen="Factura de prueba generada automáticamente",
#             fecha_emision=t.fecha_procesado or timezone.now(),
#             fecha_aprobacion=timezone.now(),
#             creado_por=usuario_asociado,
#             rango_utilizado=rango,
#             establecimiento=rango.establecimiento,
#             punto_expedicion=rango.punto_expedicion,
#             numero_documento=numero_doc,
#             cdc=str(uuid.uuid4().hex)[:44],  # genera un CDC aleatorio válido de 44 caracteres
#         )

#         print(f"✅ Factura {f.numero} generada para transacción #{t.id} ({t.tipo})")

#     print("🧾 5 facturas demo creadas correctamente.")


def ensure_segmentations_and_clients(users):
    Segmentacion = get_model("cliente_segmentacion.Segmentacion")
    Cliente = get_model("clientes.Cliente")
    UsuarioCliente = get_model("cliente_usuario.Usuario_Cliente")

    # === Segmentaciones base ===
    seg_vip, _ = Segmentacion.objects.get_or_create(nombre="VIP", defaults={"descuento": 10, "estado": "activo"})
    seg_corp, _ = Segmentacion.objects.get_or_create(nombre="CORPORATIVO", defaults={"descuento": 5, "estado": "activo"})
    seg_min, _ = Segmentacion.objects.get_or_create(nombre="MINORISTA", defaults={"descuento": 0, "estado": "activo"})

    # === Crear clientes base ===
    def crear_cliente(nombre, email, ruc, cedula, telefono, segmentacion):
        c, _ = Cliente.objects.get_or_create(
            nombre=nombre,
            defaults={
                "email": email,
                "estado": "activo",
                "segmentacion": segmentacion,
                "ruc": ruc,
                "cedula": cedula,
                "telefono": telefono,
            },
        )
        return c

    c1 = crear_cliente("Cliente VIP S.A.", "leandro.f3418@fpuna.edu.py", "12345678-0", "5209767", "0987343243", seg_vip)
    c2 = crear_cliente("Cliente Corp. Ltda.", "rodriguezmartinv02@gmail.com", "87965432-1", "5209768", "0987654321", seg_corp)
    c3 = crear_cliente("Cliente Minorista", "alanalcaraz010@gmail.com", "43218765-2", "5209769", "0987123456", seg_min)

    # === Asignaciones MANUALES de usuarios asociados ===
    usuario_asociado1 = users.get("usuario_asociado")
    usuario_asociado2 = users.get("usuario_asociado2")
    usuario_asociado3 = users.get("usuario_asociado3")

    asociaciones = [
        # usuario_asociado1 se asocia SOLO con VIP y CORPORATIVO
        (usuario_asociado1, [c1, c2]),
        # usuario_asociado2 se asocia SOLO con CORPORATIVO y MINORISTA
        (usuario_asociado2, [c2, c3]),
        # usuario_asociado3 se asocia SOLO con VIP
        (usuario_asociado3, [c1]),
    ]

    if UsuarioCliente:
        for usr, clientes in asociaciones:
            for cli in clientes:
                UsuarioCliente.objects.get_or_create(id_usuario=usr, id_cliente=cli)

    print("🤝 Asociaciones manuales de usuarios–clientes creadas correctamente.")


def ensure_currencies_and_rates():
    """
    Crea las monedas y asegura que haya AL MENOS 5 tasas por cada moneda
    extranjera (USD, EUR, BRL, ARS) contra PYG, con fechas históricas.
    NO borra tasas existentes (evita ProtectedError).
    """
    from decimal import Decimal
    from django.utils import timezone
    from datetime import timedelta
    import random, datetime
    from django.db import connection

    Moneda = get_model("monedas.Moneda")
    TasaDeCambio = get_model("cotizaciones.TasaDeCambio")

    # --- SINCRONIZAR SECUENCIA (igual que antes, si ya lo usabas) ---
    with connection.cursor() as cur:
        cur.execute("""
            SELECT setval(
                'monedas_moneda_id_seq',
                (SELECT COALESCE(MAX(id), 1) FROM monedas_moneda) + 1
            );
        """)
    print("🔄 Secuencia de ID de monedas sincronizada.")
    print("💱 Asegurando monedas y tasas base (PYG como origen)...")

    # === Monedas base ===
    monedas_def = [
        ("PYG", "Guaraní"),
        ("USD", "Dólar"),
        ("EUR", "Euro"),
    ]
    created = {}

    for abbr, nombre in monedas_def:
        moneda, _ = Moneda.objects.get_or_create(
            abreviacion=abbr,
            defaults={"nombre": nombre, "estado": True}
        )
        print(f"   ✅ Moneda existente/creada: {abbr}")
        created[abbr] = moneda

    # === Valores base (aprox actuales) ===
    base_rates = {
        "USD": 7300,
        "EUR": 7900,
    }

    hoy = timezone.now().date()

    for abbr, pb_base in base_rates.items():
        origen = created["PYG"]
        destino = created[abbr]

        qs_existentes = TasaDeCambio.objects.filter(
            moneda_origen=origen,
            moneda_destino=destino,
            estado=True,
        ).order_by("vigencia")

        existentes = qs_existentes.count()
        print(f"💹 {abbr}: ya existen {existentes} tasas.")

        if existentes >= 5:
            print(f"   🔁 {abbr}: ya tiene 5 o más tasas, no se crean nuevas.")
            continue

        faltan = 5 - existentes
        print(f"   ➕ Generando {faltan} tasas históricas adicionales para {abbr}...")

        # Creamos tasas antiguas (más viejas) para completar 5
        for i in range(faltan):
            # Distribuir en semanas hacia atrás
            # mientras más "vieja", más días atrás
            indice_global = existentes + i  # 0..4
            dias_atras = (5 - indice_global) * 7  # ej: 35, 28, 21, 14, 7
            fecha = hoy - timedelta(days=dias_atras)

            # Pequeña variación aleatoria sobre el precio base
            # Variación del precio base
            if abbr == "ARS":
                # ARS jamás negativo → variar entre +0 y +40
                delta = random.randint(0, 40)
                pb = Decimal(str(pb_base + delta))
            else:
                # Para USD / EUR variación normal ±70
                delta = random.randint(-70, 70)
                pb = Decimal(str(max(1, pb_base + delta)))  # nunca negativo
            cc = Decimal(str(random.randint(40, 80)))   # comisión compra
            cv = Decimal(str(random.randint(80, 150)))  # comisión venta

            vigencia_aware = timezone.make_aware(
                datetime.datetime.combine(fecha, datetime.time(12, 0))
            )

            TasaDeCambio.objects.create(
                moneda_origen=origen,
                moneda_destino=destino,
                precio_base=pb,
                comision_compra=cc,
                comision_venta=cv,
                vigencia=vigencia_aware,
                estado=True,
            )

            print(f"      📌 {abbr} fecha={fecha} PB={pb} cc={cc} cv={cv}")

    print("✅ Monedas y tasas históricas listas.")
    return created

def ensure_limits_per_currency(moneda_map):
    """
    Crea límites de transacción por moneda (por ahora se enfoca en PYG).
    Si el modelo existe, se asegura de no duplicar registros.
    """
    LimiteTransaccion = get_model("limite_moneda.LimiteTransaccion")
    if not LimiteTransaccion:
        print("⚠️ Modelo LimiteTransaccion no encontrado. Se omite.")
        return

    print("💰 Configurando límites por moneda...")

    # === Límite base para el Guaraní ===
    moneda_pyg = moneda_map.get("PYG")
    if moneda_pyg:
        safe_get_or_create(
            LimiteTransaccion,
            moneda=moneda_pyg,
            defaults={
                "limite_diario": Decimal("100000000"),
                "limite_mensual": Decimal("800000000"),
                "estado": "activo"
            },
        )
        print("   ✅ Límite creado/asegurado para Guaraní (PYG)")

    print("✅ Límites de transacción configurados correctamente.")

def ensure_welcome_notification(moneda_map):
    """
    Crea una notificación de ejemplo vinculada a la actualización de tasas
    (solo si el modelo notificaciones.Notificacion existe).
    """
    Notificacion = get_model("notificaciones.Notificacion")
    if not Notificacion:
        return

    # Solo crear si no existe una notificación similar
    mensaje = "Se actualizó la tasa de cambio USD/PGY a 7300 Gs."
    safe_get_or_create(
        Notificacion,
        titulo="Actualización de tasa de cambio",
        defaults={
            "mensaje": mensaje,
            "tipo": "info",
            "leido": False,
            "fecha": timezone.now(),
        },
    )


def ensure_demo_transactions_and_invoice(users, moneda_map):
    """
    Genera transacciones demo usando la lógica REAL del simulador:

    - tipo == "venta": cliente entrega PYG → compra moneda extranjera
        * monto          = monto en moneda extranjera
        * monto_recibir  = monto en PYG

    - tipo == "compra": cliente entrega moneda extranjera → recibe PYG
        * monto          = monto en PYG
        * monto_recibir  = monto en moneda extranjera

    Todas las transacciones se generan:
    - con estado = 'confirmada'
    - con fecha:
        * al menos 20 con fecha HOY
        * el resto distribuidas en los últimos 6 meses
    """

    from decimal import Decimal
    from django.utils import timezone
    from datetime import datetime, timedelta
    import random

    Transaccion = get_model("operaciones.Transaccion")
    Cliente = get_model("clientes.Cliente")
    MetodoPago = get_model("metodos_pagos.MetodoPago")
    TasaDeCambio = get_model("cotizaciones.TasaDeCambio")
    MedioAcreditacion = get_model("medio_acreditacion.MedioAcreditacion")

    usuario_asociado = users.get("usuario_asociado")
    clientes = list(Cliente.objects.all())
    metodo_efectivo = MetodoPago.objects.filter(nombre__iexact="Efectivo").first()
    tasas = list(TasaDeCambio.objects.filter(estado=True))

    if not usuario_asociado or not clientes or not metodo_efectivo or not tasas:
        print("⚠️ Faltan datos base.")
        return

    total_existentes = Transaccion.objects.count()
    OBJETIVO = 120

    if total_existentes >= OBJETIVO:
        print(f"✅ Ya existen {total_existentes} transacciones (≥ {OBJETIVO}).")
        return

    nuevos = OBJETIVO - total_existentes
    print(f"📊 Generando {nuevos} transacciones demo (hasta {OBJETIVO})...")

    operaciones = ["venta", "compra"]  # vista del cliente
    monedas_extranjeras = ["USD", "EUR"]
    hoy = timezone.now()

    from cliente_usuario.models import Usuario_Cliente
    uc = (
        Usuario_Cliente.objects
        .filter(id_usuario=usuario_asociado)
        .select_related("id_cliente__segmentacion")
        .first()
    )
    if not uc:
        print("⚠️ El usuario_asociado no tiene cliente asociado.")
        return

    cliente = uc.id_cliente
    segmento = cliente.segmentacion
    descuento = Decimal(segmento.descuento if segmento else 0)

    for i in range(nuevos):
        operacion = random.choice(operaciones)

        moneda_ext = moneda_map.get(random.choice(monedas_extranjeras))
        print("moneda_ext:", moneda_ext, flush=True)
        tasa = TasaDeCambio.objects.filter(moneda_destino=moneda_ext, estado=True).first()
        print("tasa:", tasa, flush=True)
        medio = MedioAcreditacion.objects.filter(cliente=cliente).first()

        if not tasa or not medio:
            print("⚠️ Falta tasa o medio de acreditación, se salta esta iteración.")
            continue

        PB_MONEDA = tasa.precio_base
        print("PB_MONEDA:", PB_MONEDA, flush=True)
        COMISION_VTA = tasa.comision_venta
        print("COMISION_VTA:", COMISION_VTA, flush=True)
        COMISION_COM = tasa.comision_compra
        print("COMISION_COM:", COMISION_COM, flush=True)

        # ====== FECHA ======
        h = random.randint(8, 20)
        m = random.randint(0, 59)

        if i < 20:
            # Primeras 20: HOY
            fecha_base = hoy.date()
        elif i < 30:
            # Siguientes 10: AYER
            from datetime import timedelta
            fecha_base = (hoy - timedelta(days=1)).date()
        else:
            # Resto: día aleatorio en los últimos 6 meses (desde hace 2 hasta 180 días)
            offset_dias = random.randint(2, 180)
            from datetime import timedelta
            fecha_base = (hoy - timedelta(days=offset_dias)).date()


        fecha_random = timezone.make_aware(
            datetime.combine(fecha_base, datetime.min.time())
        ).replace(hour=h, minute=m)

        estado = "confirmada"

        # ===================================================
        # CASO 1: VENTA (cliente entrega PYG → compra USD/EUR)
        # ===================================================
        if operacion == "venta":
            moneda_origen = moneda_map.get("PYG")
            moneda_destino = moneda_ext

            valor_gs = Decimal(random.randint(300_000, 800_000))
            print("valor(LO QUE ENTREGA EN GUARANIES) en poblar_datos_iniciales:", valor_gs, flush=True)

            TC_VTA = PB_MONEDA + COMISION_VTA - (COMISION_VTA * descuento / 100)
            print("TC_VTA en poblar_datos_iniciales (VENTA):", TC_VTA, flush=True)
            tasa_usada = TC_VTA

            monto_extranjero = (valor_gs / TC_VTA).quantize(Decimal("0.01"))
            print("monto_extranjero(valor_gs / TC_VTA) en poblar_datos_iniciales (VENTA):", monto_extranjero, flush=True)

            ganancia_total = round(valor_gs - (monto_extranjero * PB_MONEDA), 2)
            print("ganancia_total en poblar_datos_iniciales (VENTA):", ganancia_total, flush=True)

            monto_db = monto_extranjero      # EXTRANJERO
            monto_recibir_db = valor_gs      # GUARANÍES

        # ===================================================
        # CASO 2: COMPRA (cliente entrega USD/EUR → recibe PYG)
        # ===================================================
        else:
            moneda_origen = moneda_ext
            moneda_destino = moneda_map.get("PYG")

            valor_ext = Decimal(random.randint(50, 200))
            print("valor(LO QUE ENTREGA EN EXTRANJERO) en poblar_datos_iniciales:", valor_ext, flush=True)

            TC_COMP = PB_MONEDA - (COMISION_COM - (COMISION_COM * descuento / 100))
            print("TC_COMP en poblar_datos_iniciales (COMPRA):", TC_COMP, flush=True)
            tasa_usada = TC_COMP

            monto_gs = round(valor_ext * TC_COMP, 2)
            print("monto_gs(valor_ext * TC_COMP) en poblar_datos_iniciales:", monto_gs, flush=True)

            ganancia_total = round(
                valor_ext * (COMISION_COM * (1 - descuento / 100)),
                2
            )
            print("ganancia_total en poblar_datos_iniciales (COMPRA):", ganancia_total, flush=True)

            monto_db = monto_gs           # GUARANÍES
            monto_recibir_db = valor_ext  # EXTRANJERO

        transaccion = Transaccion.objects.create(
            usuario=usuario_asociado,
            cliente=cliente,
            monto=monto_db,
            tipo=operacion,
            estado=estado,
            ganancia=Decimal(ganancia_total),
            metodo_pago=metodo_efectivo,
            medio_acreditacion=medio,
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            tasa_usada=tasa_usada,
            tasa_ref=tasa,
            monto_recibir=monto_recibir_db,
            fecha_procesado=fecha_random,
            procesado_por=usuario_asociado,
        )

        Transaccion.objects.filter(pk=transaccion.pk).update(
            fecha=fecha_random,
            fecha_procesado=fecha_random,
        )

    print("✅ Se generaron transacciones demo con la lógica real del simulador.")





def ensure_payment_and_accreditation():
    """
    Crea métodos de pago, entidades financieras y medios de acreditación de prueba.
    Idempotente: no duplica si ya existen.
    """
    MetodoPago = get_model("metodos_pagos.MetodoPago")
    TipoEntidadFinanciera = get_model("medio_acreditacion.TipoEntidadFinanciera")
    CampoEntidadFinanciera = get_model("medio_acreditacion.CampoEntidadFinanciera")
    MedioAcreditacion = get_model("medio_acreditacion.MedioAcreditacion")
    ValorCampoMedioAcreditacion = get_model("medio_acreditacion.ValorCampoMedioAcreditacion")
    Cliente = get_model("clientes.Cliente")

    # === Métodos de pago base ===
    for nombre in ["Efectivo", "Transferencia", "Tarjeta"]:
        safe_get_or_create(MetodoPago, nombre=nombre, defaults={"estado": True})

    # === Entidades financieras base ===
    banco, _ = safe_get_or_create(
        TipoEntidadFinanciera,
        nombre="Banco",
        defaults={
            "tipo": "BANCO",
            "estado": True,
            "comision": 0.50
        }
    )
    tigo_money, _ = safe_get_or_create(
        TipoEntidadFinanciera,
        nombre="Tigo Money",
        defaults={
            "tipo": "BILLETERA",
            "estado": True,
            "comision": 0.30
        }
    )

    # === Campos requeridos para Banco ===
    nro_cta, _ = safe_get_or_create(
        CampoEntidadFinanciera,
        entidad=banco,
        nombre="nro_cuenta",
        defaults={
            "etiqueta": "Número de cuenta",
            "tipo": "numero",
            "requerido": True,
            "orden": 1,
            "ayuda": "Ingrese el número de cuenta bancaria"
        }
    )

    cedula, _ = safe_get_or_create(
        CampoEntidadFinanciera,
        entidad=banco,
        nombre="cedula",
        defaults={
            "etiqueta": "Cédula de Identidad",
            "tipo": "numero",
            "requerido": True,
            "orden": 2,
            "ayuda": "Número de documento del titular"
        }
    )

    # === Asociar medios de acreditación a los clientes demo ===
    clientes = list(Cliente.objects.all()[:3])
    if not clientes:
        print("⚠️ No hay clientes para asociar medios de acreditación.")
        return

    for i, c in enumerate(clientes):
        # Alternar: algunos con banco, otros con billetera
        entidad = banco if i % 2 == 0 else tigo_money

        medio, _ = safe_get_or_create(
            MedioAcreditacion,
            cliente=c,
            entidad=entidad,
            defaults={"estado": True}
        )

        # === Crear valores realistas ===
        numero_cuenta = str(1234567 + i)  # 👉 genera 1234567, 1234568, 1234569 ...
        nro_cuenta_valor, _ = safe_get_or_create(
            ValorCampoMedioAcreditacion,
            medio=medio,
            campo=nro_cta,
            defaults={"valor": numero_cuenta}
        )

        cedula_valor, _ = safe_get_or_create(
            ValorCampoMedioAcreditacion,
            medio=medio,
            campo=cedula,
            defaults={"valor": f"12345{c.id:02d}"}
        )

    print("🏦 Medios de acreditación y entidades creados correctamente (con números de cuenta asignados).")




@transaction.atomic
def run():
    print("▶ Iniciando carga de datos (idempotente)...")
    groups = ensure_roles_and_profiles()
    users = ensure_users(groups)

    print("… Segmentaciones y clientes")
    ensure_segmentations_and_clients(users)

    print("… Monedas y tasas")
    moneda_map = ensure_currencies_and_rates()

    print("… Métodos de pago y medios de acreditación")
    ensure_payment_and_accreditation()

    print("… Límites por moneda (si el modelo existe)")
    ensure_limits_per_currency(moneda_map)

    print("… Notificación de tasa de cambio (si modelo existe)")
    ensure_welcome_notification(moneda_map)

    print("… Transacciones demo y factura (si modelo existe)")
    ensure_demo_transactions_and_invoice(users, moneda_map)

    #print("… Facturas demo asociadas a transacciones")
    #ensure_demo_invoices(users)

    # Marcar MFA por defecto desactivado en los usuarios nuevos (si campos existen)
    for u in users.values():
        if hasattr(u, "mfa_transacciones") and u.mfa_transacciones:
            u.mfa_transacciones = False
            u.save(update_fields=["mfa_transacciones"])

    print("✅ Carga inicial completa (sin duplicar).")


# Ejecutar cuando se llama con "manage.py shell < poblar_datos_iniciales.py"
run()