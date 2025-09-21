from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from .forms import CustomUserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
# Para enviar correos
from django.core.mail import send_mail
# Para renderizar templates a string
from django.template.loader import render_to_string
# Para codificar el ID de usuario en base64
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.core.mail import EmailMessage
from usuarios.forms import CustomUserChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .tokens import account_activation_token
import json
from collections import namedtuple
from django.urls import reverse
from django.utils.http import urlencode
from django.http import JsonResponse
from django.utils.timezone import now
from monedas.models import Moneda
from cotizaciones.models import TasaDeCambio
from datetime import datetime
from .models import CustomUser
from .forms import UserRolePermissionForm
import sys
from clientes.models import Cliente, Segmentacion
from cliente_usuario.models import Usuario_Cliente

User = get_user_model()
# Create your views here.

# Solo usuarios normales (no superadmin)


def user_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.has_perm('session.view_panel_admin'):
                print("Entra", flush=True)
                # Si es superadmin, lo redirige al panel de admin
                return redirect('admin_dashboard')
            else:
                return view_func(request, *args, **kwargs)
        # Si no está logueado, redirige a login
        return redirect('login')
    return _wrapped_view

# Solo superadmin



# views.py - home
"""
Vista principal para usuarios normales.

Muestra las cotizaciones de distintas monedas y los datos del usuario
autenticado en el contexto del template `home.html`.
"""
@user_required  # con esto protejemos las rutas
def home(request):
    
    # === DATOS DESDE LA BD ===
    monedas = list(Moneda.objects.filter(estado=True).values("abreviacion", "nombre"))

    # Tasas de cambio vigentes (por simplicidad: tomo la más reciente por cada moneda_destino)
    tasas = (
        TasaDeCambio.objects
        .filter(estado=True)
        .select_related("moneda_origen", "moneda_destino")
        .order_by("moneda_destino", "-vigencia")
    )
    print("tasas:", tasas, flush=True)


    # Reorganizar datos en un dict similar a tu data_por_moneda
    data_por_moneda = {}
    for tasa in tasas:
        abrev = tasa.moneda_destino.abreviacion
        if abrev not in data_por_moneda:
            data_por_moneda[abrev] = []
        # Insertar al inicio para que el primero sea el más reciente
        data_por_moneda[abrev].insert(0, {
            "fecha": tasa.vigencia.strftime("%d %b"),
            "compra": float(tasa.monto_compra),
            "venta": float(tasa.monto_venta),
            "comision_compra": float(tasa.comision_compra),
            "comision_venta": float(tasa.comision_venta)
        })

    print("data_por_moneda:", data_por_moneda, flush=True)

    
    # === SEGMENTACIÓN SEGÚN USUARIO ===
    descuento = 0
    segmento_nombre = "Sin Clientes"

    # === SEGMENTACIÓN SEGÚN USUARIO ===
    clientes_asociados, cliente_operativo = obtener_clientes_usuario(request.user,request)

    if cliente_operativo and cliente_operativo.segmentacion and cliente_operativo.segmentacion.estado == "activo":
        descuento = float(cliente_operativo.segmentacion.descuento)
        segmento_nombre = cliente_operativo.segmentacion.nombre

    print("Clientes asociados:", [c.nombre for c in clientes_asociados])
    print("Cliente operativo:", cliente_operativo.nombre if cliente_operativo else "Ninguno")
    print("Descuento:", descuento)
    print("Segmento:", segmento_nombre)

    
    
    # Variables iniciales
    resultado = ""
    ganancia_total = 0
    valor_input = ""
    moneda_seleccionada = ""
    operacion = "venta"
    origen = ""
    destino = ""
    COMISION_VTA = None
    COMISION_COM = None
    
    if request.method == "POST":
        valor_input = request.POST.get("valor", "").strip()
        operacion = request.POST.get("operacion")
        origen = request.POST.get("origen", "")
        destino = request.POST.get("destino", "")

        # Determinar moneda relevante según operación
        if operacion == "venta":
            moneda_seleccionada = destino
        else:
            moneda_seleccionada = origen

        try:
            valor = float(valor_input)
            if valor <= 0:
                resultado = "Monto inválido"
                COMISION_VTA = 0
                COMISION_COM = 0
            else:
                # === OBTENER PB_MONEDA DE LA FECHA MÁS RECIENTE ===
                registros = data_por_moneda.get(moneda_seleccionada, [])
                if not registros:
                    resultado = "No hay cotización disponible" # no hay cotización, no mostrar nada
                    ganancia_total = 0
                    COMISION_VTA = 0
                    COMISION_COM = 0
                else:
                    if registros:
                        print("entro",registros, flush=True)
                        registros_ordenados = sorted(
                            registros,
                            key=lambda x: datetime.strptime(x["fecha"] + " 2025", "%d %b %Y"),
                            reverse=True
                        )
                        ultimo = registros_ordenados[0]
                        print(f"Registros ordenados: {registros_ordenados}", flush=True)
                        print(f"Ultimo {ultimo}", flush=True)
                        print("registrohome:", registros_ordenados, flush=True)
                        PB_MONEDA = ultimo["venta"] if operacion == "venta" else ultimo["compra"]
                        COMISION_VTA = ultimo["comision_venta"]
                        COMISION_COM = ultimo["comision_compra"]
                    else:
                        PB_MONEDA = 0
                        COMISION_VTA = 0
                        COMISION_COM = 0
                    print("PB_MONEDA:", PB_MONEDA,flush=True)
                    print("COMISION_VTA:", COMISION_VTA,flush=True)
                    print("COMISION_COM:", COMISION_COM,flush=True)
                    # === CÁLCULOS ===
                    print("operacion:", operacion,flush=True)
                    if operacion == "venta":  # Vender PYG → otra moneda
                        TC_VTA = PB_MONEDA + COMISION_VTA - (COMISION_VTA * descuento / 100)
                        resultado = round(valor / TC_VTA, 2)
                        ganancia_total = round(valor - (resultado * PB_MONEDA), 2)
                        print("COMISION_VTA:", COMISION_VTA, flush=True)
                        print("descuento:", descuento, flush=True)
                    else:  # Compra: otra moneda → PYG
                        TC_COMP = PB_MONEDA - (COMISION_COM - (COMISION_COM * descuento / 100))
                        print("TC_COMP:", TC_COMP, flush=True)
                        print("PB_MONEDA:", PB_MONEDA, flush=True)
                        print("COMISION_COM:", COMISION_COM, flush=True)
                        print("descuento:", descuento, flush=True)
                        resultado = round(valor * TC_COMP, 2)
                        ganancia_total = round(valor * (COMISION_COM * (1 - descuento / 100)), 2)
        except ValueError:
            resultado = "Monto inválido"
            COMISION_VTA = 0
            COMISION_COM = 0

        # Respuesta AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                "resultado": resultado,
                "ganancia_total": ganancia_total,
                "segmento": segmento_nombre,
                "descuento": descuento,
                "comision_compra": COMISION_COM if operacion != "venta" else None,
                "comision_venta": COMISION_VTA if operacion == "venta" else None,
            })

    
    context = {
        'monedas': monedas,
        'resultado': resultado,
        'ganancia_total': ganancia_total,
        'valor_input': valor_input,
        'moneda_seleccionada': moneda_seleccionada,
        'operacion': operacion,
        "user": request.user,
        "origen": origen,
        "destino": destino,
        'data_por_moneda': data_por_moneda,
        "segmento": segmento_nombre,
        "descuento": descuento,
        "clientes_asociados": clientes_asociados,
        "cliente_operativo": cliente_operativo,
        "comision_compra": COMISION_COM if operacion != "venta" else None,
        "comision_venta": COMISION_VTA if operacion == "venta" else None,
    }
    return render(request, 'home.html', context)



def signup(request):
    """
    Vista para registrar nuevos usuarios.

    - GET: Muestra el formulario de registro.
    - POST: Valida el formulario, crea un usuario inactivo, asigna el rol 'usuario'
      y envía un correo de activación.
    """
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.groups.filter(name='ADMIN').exists():
            return redirect('admin')
        else:
            return redirect('home')
    eslogan_lines = ["Empieza", "ahora."]
    eslogan_spans = ["!Comienza", "ya!"]
    subtitle = "Crea tu cuenta y empieza ahora."

    print("Fuera del POST", flush=True)

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        print("Entra en POST", flush=True)
        if form.is_valid():
            try:
                print("entro en try", flush=True)
                # Guardar usuario inactivo
                user = form.save(commit=False)
                user.is_active = False
                # Asignamos el rol 'usuario'
                rol_usuario = Group.objects.get(name="Usuario")
                user.save()
                user.groups.add(rol_usuario)
                print(user, flush=True)
                activateEmail(request, user, user.email)
                return render(request, 'registrarse.html', {
                    'form': form,
                    'subtitle': f"Hola {user.username} tu cuenta ha sido creada correctamente. Por favor, revisa tu correo.",
                    'eslogan_lines': eslogan_lines,
                    'eslogan_spans': eslogan_spans,
                    'submit_text': "Registrarse",
                    'active_tab': "register"
                })
            except Exception as e:
                print("Error al guardar usuario:", e, flush=True)
                return render(request, 'registrarse.html', {
                    'form': form,
                    'eslogan_lines': eslogan_lines,
                    'eslogan_spans': eslogan_spans,
                    'submit_text': "Registrarse",
                    'active_tab': "register"
                })
        else:
            return render(request, 'registrarse.html', {
                'form': form,
                'eslogan_lines': eslogan_lines,
                'eslogan_spans': eslogan_spans,
                'submit_text': "Registrarse",
                'subtitle': subtitle,
                'active_tab': "register"
            })
    else:
        storage = messages.get_messages(request)
        storage.used = True  # limpia todos los mensajes previos
        form = CustomUserCreationForm()
    return render(request, 'registrarse.html', {
        'form': form,
        'eslogan_lines': eslogan_lines,
        'eslogan_spans': eslogan_spans,
        'subtitle': subtitle,
        'submit_text': "Registrarse",
        'active_tab': "register"
    })


def activate(request, uidb64, token):
    """
      **activate(request, uidb64, token)**: Activa la cuenta de un usuario a través del enlace de activación enviado por email.

      - **Parámetros**:
          - request: objeto HttpRequest.
          - uidb64: UID del usuario codificado en base64.
          - token: token de activación generado para el usuario.

      - **Funcionamiento**:
          - Decodifica el UID y busca el usuario correspondiente.
          - Verifica que el token sea válido.
          - Si es válido, activa al usuario y redirige al login.
          - Si no es válido, redirige a la página principal.
      """
    print('Activando cuenta', flush=True)
    try:
        print("Intentando activar cuenta", flush=True)
        # Decodificar el UID
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        print("Error al activar cuenta", flush=True)
        user = None

    # Validar que el token sea correcto
    print(user)
    if user is not None and account_activation_token.check_token(user, token):
        print("Token válido, activando cuenta", flush=True)
        user.is_active = True
        user.save()
        print(request, 'Tu cuenta ha sido activada con éxito. Ahora puedes iniciar sesión.')
        return redirect('login')
    else:
        print("Token inválido", flush=True)
        print('El enlace de activación no es válido o ha expirado.')
        return redirect('home')


def activateEmail(request, user, to_email):
    """
    **activateEmail(request, user, to_email)**  
    Envía un correo electrónico de activación al usuario recién registrado.

    - **Parámetros**:
        - request: objeto HttpRequest.
        - user: instancia del usuario a activar.
        - to_email: dirección de correo electrónico del destinatario.

    - **Funcionamiento**:
        - Renderiza el template `email_confirm.html`.
        - Genera el token de activación.
        - Envía el email en formato HTML.
    """
    mail_subject = 'Activate your user account.'
    message = render_to_string('email_confirm.html', {
        'user': user,
        'domain': get_current_site(request).domain,
        'uid64': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })

    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = 'html'
    email.send()

# cierra sesion tanto usuarios como admins


def signout(request):
    """
      **signout(request)**: Cierra la sesión del usuario y lo redirige a la página de aterrizaje.

      - **Parámetros**:
          - request: objeto HttpRequest.
      """
    logout(request)
    return redirect('pagina_aterrizaje')


def signin(request):
    """
    **signin(request)**  
    Maneja el inicio de sesión de usuarios y superadmins.

    - **GET**: Muestra el formulario de login.
    - **POST**: Autentica al usuario con `username` y `password`.
        - Si las credenciales son correctas:
            - Redirige a `admin_dashboard` si es superadmin.
            - Redirige a `home` si es usuario normal.
        - Si las credenciales son incorrectas, vuelve a mostrar el formulario con mensaje de error.
    - **Parámetros**:
        - request: objeto HttpRequest.
    """
    if request.user.is_authenticated:
        # Redirige según tipo de usuario
        if request.user.groups.filter(name='ADMIN').exists():
            print("PRIMER IF:", flush=True)
            return redirect('admin_dashboard')
        else:
            return redirect('home')

    eslogan_lines = ["Tu éxito", "comienza", "aqui."]
    eslogan_spans = ["¡Accede", "ahora!"]
    subtitle = "¡Bienvenido de nuevo! Inicia sesión para continuar."

    if request.method == 'GET':
        return render(request, 'login.html', {
            'form': AuthenticationForm(),
            'eslogan_lines': eslogan_lines,
            'eslogan_spans': eslogan_spans,
            'subtitle': subtitle,
            'submit_text': "Acceder",
            'active_tab': "login"
        })
    else:
        user = authenticate(
            username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'login.html', {
                'form': AuthenticationForm(),
                'subtitle': "Usuario o contraseña incorrectos. Inténtalo de nuevo.",
                'eslogan_lines': eslogan_lines,
                'eslogan_spans': eslogan_spans,
                'submit_text': "Acceder",
                'active_tab': "login"
            })
        else:
            login(request, user)
            if request.user.groups.filter(name='ADMIN').exists():
                return redirect('admin_dashboard')
            else:
                return redirect('home')
      
def pagina_aterrizaje(request):
    """
    Renderiza la página de aterrizaje mostrando cotizaciones reales
    con tasas más recientes, hasta 6 monedas y datos para gráfico.
    """
    """
      **pagina_aterrizaje(request)**  
      Renderiza la página principal de aterrizaje mostrando cotizaciones reales
      con tasas más recientes, hasta 6 monedas y datos para gráfico.

      - **Parámetros**:
          - request: objeto HttpRequest.

      - **Funcionamiento**:
          - Define una lista de cotizaciones de monedas con compra, venta y logo.
          - Define datos históricos de ejemplo por moneda en `data_por_moneda`.
          - Convierte `data_por_moneda` a JSON y lo pasa al contexto.
          - Renderiza el template `pagina_aterrizaje.html` con el contexto.
      """

    # === Obtener monedas activas ===
    monedas = Moneda.objects.filter(estado=True)

    # === Obtener tasas de cambio ordenadas por moneda_destino y vigencia desc ===
    tasas = (
        TasaDeCambio.objects
        .filter(estado=True)
        .select_related("moneda_origen", "moneda_destino")
        .order_by("moneda_destino__abreviacion", "-vigencia")
    )

    # === Reorganizar datos en dict por moneda_destino ===
    data_por_moneda = {}
    for tasa in tasas:
        abrev = tasa.moneda_destino.abreviacion
        if abrev not in data_por_moneda:
            data_por_moneda[abrev] = []
        # Insertar al inicio para que el primero sea el más reciente
        data_por_moneda[abrev].insert(0, {
            "fecha": tasa.vigencia.strftime("%d %b"),
            "compra": float(tasa.monto_compra),
            "venta": float(tasa.monto_venta),
        })
    print("data_por_moneda aterrizaje:", data_por_moneda, flush=True)
    
    # === Preparar cotizaciones para mostrar en landing (solo más reciente por moneda) ===
    cotizaciones = []
    for abrev, registros in data_por_moneda.items():
        ultimo = registros[-1]  # el más reciente
        # Intentar buscar logo PNG primero, si no, SVG
        if f'static/img/logoMoneda/{abrev}.png':
            logo = f'img/logoMoneda/{abrev}.png'
        else:
            logo = f'img/logoMoneda/{abrev}.svg'
        cotizaciones.append({
            'simbolo': abrev,
            'compra': ultimo['compra'],
            'venta': ultimo['venta'],
            'logo': logo
        })
    print("registros22", registros, flush=True)
    # Limitar a máximo 6 monedas
    cotizaciones = cotizaciones[:6]
    print("cotizaciones aterrizaje:", cotizaciones, flush=True)

    context = {
        'cotizaciones': cotizaciones,
        'data_por_moneda': data_por_moneda,  # para gráfico JS
    }
    return render(request, 'pagina_aterrizaje.html', context)

def error_404_view(request, exception):
    """
    **error_404_view(request, exception)**  
    Muestra una página personalizada cuando se produce un error 404 (página no encontrada).

    - **Parámetros**:
        - request: objeto HttpRequest.
        - exception: objeto de excepción.

    - **Funcionamiento**:
        Renderiza el template `404.html` con código de estado 404.
    """
    return render(request, '404.html', status=404)


@user_required
def editarPerfil(request):
    """
    **editarPerfil(request)**  
    Permite a un usuario autenticado editar su perfil.

    - **Parámetros**:
        - request: objeto HttpRequest.

    - **Funcionamiento**:
        - Limpia mensajes previos.
        - Si el método es POST:
            - Guarda cambios si `action` es 'guardar' y el formulario es válido.
            - Mantiene la sesión activa si cambia contraseña.
            - Devuelve mensajes de error si el formulario no es válido.
        - Si el método es GET:
            - Crea un formulario con los datos actuales del usuario.
        - Renderiza `editarperfil.html` con el formulario y mensajes.
    """
    segmento_nombre = "Sin Segmentación"
    descuento=0
    storage = messages.get_messages(request)
    storage.used = True  # Limpia todos los mensajes previos
    # === SEGMENTACIÓN SEGÚN USUARIO ===
    clientes_asociados, cliente_operativo = obtener_clientes_usuario(request.user,request)
    if cliente_operativo and cliente_operativo.segmentacion and cliente_operativo.segmentacion.estado == "activo":
        segmento_nombre = cliente_operativo.segmentacion.nombre
        if cliente_operativo.segmentacion.descuento:
            descuento = float(cliente_operativo.segmentacion.descuento)

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        action = request.POST.get('action')
        # Guardar cambios
        if action == 'guardar':
            if form.is_valid():
                user = form.save()
                print(user, flush=True)
                # Mantiene sesión si cambia contraseña
                update_session_auth_hash(request, user)
                return render(request, 'editarperfil.html', {'form': form,  'success': True,
        "segmento": segmento_nombre,
        "clientes_asociados": clientes_asociados,
        "cliente_operativo": cliente_operativo,'descuento': descuento,})
            else:
                return render(request, 'editarperfil.html', {'form': form,"segmento": segmento_nombre,
        "clientes_asociados": clientes_asociados,
        "cliente_operativo": cliente_operativo,'descuento': descuento,})
        """
        # Eliminar cuenta
        elif action == 'eliminar':
            password = request.POST.get('password_actual')
            if not password:
                return render(request, 'editarperfil.html', {'form': form, 'messages': "Debes ingresar tu contraseña para eliminar la cuenta."} )
            elif not request.user.check_password(password):
                return render(request, 'editarperfil.html', {'form': form, 'messages': "La contraseña no es correcta."} )
            else:
                request.user.delete()
                logout(request)
                return render(request, 'pagina_aterrizaje.html', {'form': form, 'messages': "Tu cuenta ha sido eliminada correctamente."} )
        """
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'editarperfil.html', {'form': form,"segmento": segmento_nombre,
        "clientes_asociados": clientes_asociados,
        "cliente_operativo": cliente_operativo,'descuento': descuento,})


"""
def editarperfilDesing (request):
# Creamos un usuario temporal para la vista
    mock_user = User(
        username='usuario_ejemplo',
        email='usuario@example.com',
        first_name='Juan',
        last_name='Pérez',
    )
    # Agregamos atributos extra dinámicamente
    mock_user.role = 'Superadmin'
    mock_user.avatar = None  # o URL de imagen
    mock_user.clientes_asociados = [
        {"id": 1, "nombre": "Cliente A"},
        {"id": 2, "nombre": "Cliente B"},
        {"id": 3, "nombre": "Cliente C"},
    ]
    

    # Instanciamos el formulario con ese usuario ficticio
    form = CustomUserChangeForm(instance=mock_user)

    return render(request, 'editarperfil.html', {'form': form,'user_fake': mock_user})
"""


def crud_empleados(request):
    """
    **crud_empleados(request)**  
    Muestra un ejemplo de gestión de empleados con datos ficticios.

    - **Parámetros**:
        - request: objeto HttpRequest.

    - **Funcionamiento**:
        - Crea un namedtuple `Empleado` para simular un modelo de empleado.
        - Define una lista de empleados de ejemplo con id, nombre, cédula, email y cargo.
        - Renderiza `empleados.html` pasando los empleados al template.
    """
    # Creamos un "Empleado" ficticio usando namedtuple
    Empleado = namedtuple(
        'Empleado', ['id', 'nombre', 'cedula', 'email', 'cargo'])

    # Datos de ejemplo
    empleados = [
        Empleado(id=1, nombre="Juan Pérez", cedula="12345678",
                 email="juan.perez@email.com", cargo="Administrador"),
        Empleado(id=2, nombre="María Gómez", cedula="87654321",
                 email="maria.gomez@email.com", cargo="Supervisor"),
        Empleado(id=3, nombre="Carlos López", cedula="11223344",
                 email="carlos.lopez@email.com", cargo="Empleado"),
    ]

    # Pasamos los datos al template
    return render(request, 'empleados.html', {'empleados': empleados})


def user_roles_lista(request):
    """
    Lista de usuarios con buscador básico.
    Optimizada para mostrar grupos sin problema N+1.
    """
    q = request.GET.get("q", "")
    campo = request.GET.get("campo", "")

    # Usar prefetch_related para optimizar la carga de grupos
    usuarios = CustomUser.objects.prefetch_related('groups').all().order_by("-id")
    form = UserRolePermissionForm()

    if q and campo:
        if campo == "groups__name":
            # Búsqueda por nombre de grupo
            usuarios = usuarios.filter(groups__name__icontains=q).distinct()
        else:
            # Búsqueda por otros campos
            filtro = {f"{campo}__icontains": q}
            usuarios = usuarios.filter(**filtro)

    # Implementar paginación si es necesario
    from django.core.paginator import Paginator
    
    paginator = Paginator(usuarios, 10)  # 10 usuarios por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "user_roles_lista.html", {
        "usuarios": page_obj,
        "page_obj": page_obj,
        "q": q,
        "campo": campo,
        "form": form
    })


def user_roles_edit(request, pk):
    """
    Editar roles y permisos de un usuario via AJAX (para modal).
    """
    usuario = get_object_or_404(CustomUser, pk=pk)

    if request.method == "POST":
        # DEBUG: Imprimir todos los datos recibidos
        print("=== DEBUG POST DATA ===", file=sys.stdout, flush=True)
        print(f"request.POST: {request.POST}", file=sys.stdout, flush=True)
        print(f"request.FILES: {request.FILES}", file=sys.stdout, flush=True)
        print(f"Headers: {dict(request.headers)}", file=sys.stdout, flush=True)
        
        # Verificar si hay datos de grupos y permisos
        groups_data = request.POST.getlist('groups')
        perms_data = request.POST.getlist('user_permissions')
        
        print(f"Grupos recibidos directamente: {groups_data}", file=sys.stdout, flush=True)
        print(f"Permisos recibidos directamente: {perms_data}", file=sys.stdout, flush=True)
        
        form = UserRolePermissionForm(request.POST, instance=usuario)
        
        print(f"Form is_valid: {form.is_valid()}", file=sys.stdout, flush=True)
        print(f"Form errors: {form.errors}", file=sys.stdout, flush=True)
        print(f"Form cleaned_data: {form.cleaned_data if form.is_valid() else 'No valid'}", file=sys.stdout, flush=True)
        
        if form.is_valid():
            # Limpiar grupos y permisos actuales
            usuario.groups.clear()
            usuario.user_permissions.clear()
            
            # Asignar nuevos grupos
            groups = form.cleaned_data.get('groups')
            if groups:
                usuario.groups.set(groups)
                print(f"Grupos asignados: {list(groups)}", file=sys.stdout, flush=True)
            else:
                print("No se asignaron grupos.", file=sys.stdout, flush=True)

            # Asignar nuevos permisos
            permissions = form.cleaned_data.get('user_permissions')
            if permissions:
                usuario.user_permissions.set(permissions)
                print(f"Permisos asignados: {list(permissions)}", file=sys.stdout, flush=True)
            else:
                print("No se asignaron permisos.", file=sys.stdout, flush=True)

            usuario.save()
            
            # Si es AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Usuario {usuario.username} actualizado correctamente.'
                })
            else:
                messages.success(request, f'Usuario {usuario.username} actualizado correctamente.')
                return redirect("user_roles_lista")
        else:
            print("Errores del formulario:", form.errors, file=sys.stdout, flush=True)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
            else:
                messages.error(request, "Error al actualizar el usuario. Revisa los datos.")
                return render(request, "user_roles_form.html", {
                    "form": form,
                    "usuario": usuario
                })

    # Si no es POST, mostrar el formulario de edición
    form = UserRolePermissionForm(instance=usuario)
    return render(request, "user_roles_form.html", {
        "form": form,
        "usuario": usuario
    })

def user_roles_detalle(request, pk):
    """
    Obtener detalles de un usuario para el modal de edición.
    """
    from django.contrib.auth.models import Group, Permission

    User = get_user_model()
    user = User.objects.prefetch_related('groups', 'user_permissions').get(pk=pk)

    # Obtener todos los grupos disponibles
    all_groups = Group.objects.all()

    # Obtener todos los permisos disponibles
    all_permissions = Permission.objects.all()

    # Crear una lista de grupos del usuario con información adicional
    user_groups = []
    for group in user.groups.all():
        user_groups.append({
            "id": group.id,
            "name": group.name
        })

    return JsonResponse({
        "username": user.username,
        "cedula": getattr(user, 'cedula', ''),
        "groups": list(user.groups.values_list('id', flat=True)),
        "user_permissions": list(user.user_permissions.values_list('id', flat=True)),
        "modal_title": f"Editar Usuario: {user.username}",
        "user_groups_info": user_groups,

        # Agregar todos los grupos y permisos disponibles
        "all_groups": [{"id": g.id, "name": g.name} for g in all_groups],
        "all_permissions": [{"id": p.id, "name": p.name} for p in all_permissions],
    })

def obtener_clientes_usuario(user,request):
    """
    Devuelve:
        - clientes_asociados: lista de todos los clientes asociados al usuario
        - cliente_operativo: cliente actualmente seleccionado (desde sesión si existe)
    """

     # Solo clientes activos
    usuarios_clientes = (
        Usuario_Cliente.objects
        .select_related("id_cliente__segmentacion")
        .filter(id_usuario=user, id_cliente__estado="activo")
    )
    
    clientes_asociados = [uc.id_cliente for uc in usuarios_clientes if uc.id_cliente]
    cliente_operativo = None

    # Tomar de la sesión si existe
    if request and request.session.get('cliente_operativo_id'):
        cliente_operativo = next((c for c in clientes_asociados if c.id == request.session['cliente_operativo_id']), None)

    # Si no hay sesión o ID no válido, tomar el primero
    if not cliente_operativo and clientes_asociados:
        cliente_operativo = clientes_asociados[0]

    return clientes_asociados, cliente_operativo


@login_required
def set_cliente_operativo(request):
    """
    Guarda en sesión el cliente operativo seleccionado y devuelve JSON
    con segmento y descuento para actualizar el front sin recargar.
    """
    cliente_id = request.POST.get('cliente_id')

    if cliente_id:
        try:
            cliente = Cliente.objects.select_related("segmentacion").get(
                pk=cliente_id, estado="activo"
            )
            # Guardar en sesión
            request.session['cliente_operativo_id'] = cliente.id

            # Datos a devolver
            segmento_nombre = None
            descuento = 0
            if cliente.segmentacion and cliente.segmentacion.estado == "activo":
                segmento_nombre = cliente.segmentacion.nombre
                descuento = float(cliente.segmentacion.descuento or 0)

            return JsonResponse({
                "success": True,
                "segmento": segmento_nombre,
                "descuento": descuento,
                "cliente_nombre": cliente.nombre
            })

        except Cliente.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Cliente no encontrado"}, status=404
            )

    return JsonResponse({"success": False, "error": "Petición inválida"}, status=400)
	