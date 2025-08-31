from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth import get_user_model
from django.contrib.auth import login,logout,authenticate
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from roles_permisos.models import Rol
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

User = get_user_model()
# Create your views here.
from functools import wraps

# Solo usuarios normales (no superadmin)
def user_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                # Si es superadmin, lo redirige al panel de admin
                return redirect('admin_dashboard')
            else:
                return view_func(request, *args, **kwargs)
        # Si no está logueado, redirige a login
        return redirect('login')
    return _wrapped_view

# Solo superadmin
def superadmin_required(view_func):
    """
    Decorador que limita el acceso únicamente a usuarios superadministradores.

    - Si el usuario no está autenticado, se lo redirige a ``login``.
    - Si el usuario está autenticado pero no es superadmin, se lo redirige a ``home``.
    - Si el usuario es superadmin, se ejecuta la vista original.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                # Usuario normal no tiene acceso
                return redirect('home')
        return redirect('login')
    return _wrapped_view

# views.py - home
"""
Vista principal para usuarios normales.

Muestra las cotizaciones de distintas monedas y los datos del usuario
autenticado en el contexto del template `home.html`.
"""
@user_required #con esto protejemos las rutas
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
            "venta": float(tasa.monto_venta)
        })

    
    print("data_por_moneda:", data_por_moneda, flush=True)

    # Comisiones y segmentos
    COMISION_VTA = 100
    COMISION_COM = 50
    segmentos = {"VIP": 10, "Corporativo": 5, "Minorista": 0}

    # Variables iniciales
    resultado = ""
    ganancia_total = 0
    valor_input = ""
    moneda_seleccionada = ""
    operacion = "venta"
    segmento = "Minorista"
    origen = ""
    destino = ""

    if request.method == "POST":
        valor_input = request.POST.get("valor", "").strip()
        operacion = request.POST.get("operacion")
        segmento = request.POST.get("segmento", "Corporativo")
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
            else:
                descuento = segmentos.get(segmento, 0)

                # === OBTENER PB_MONEDA DE LA FECHA MÁS RECIENTE ===
                registros = data_por_moneda.get(moneda_seleccionada, [])
                if not registros:
                    resultado = "No hay cotización disponible" # no hay cotización, no mostrar nada
                    ganancia_total = 0
                else:
                    if registros:
                        print("entro",registros, flush=True)
                        registros_ordenados = sorted(
                            registros,
                            key=lambda x: datetime.strptime(x["fecha"] + " 2025", "%d %b %Y"),
                            reverse=True
                        )
                        ultimo = registros_ordenados[0]
                        PB_MONEDA = ultimo["venta"] if operacion == "venta" else ultimo["compra"]
                    else:
                        PB_MONEDA = 0

                    # === CÁLCULOS ===
                    if operacion == "venta":  # Vender PYG → otra moneda
                        TC_VTA = PB_MONEDA + COMISION_VTA - (COMISION_VTA * descuento / 100)
                        resultado = round(valor / TC_VTA, 2)
                        ganancia_total = round(valor - (resultado * PB_MONEDA), 2)
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

        # Respuesta AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"resultado": resultado, "ganancia_total": ganancia_total})

    
    context = {
        'monedas': monedas,
        'resultado': resultado,
        'ganancia_total': ganancia_total,
        'valor_input': valor_input,
        'moneda_seleccionada': moneda_seleccionada,
        'operacion': operacion,
        'segmento': segmento,
        "user": request.user,
        "origen": origen,
        "destino": destino,
        'data_por_moneda': data_por_moneda,
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
        if request.user.is_superuser:
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
              rol_usuario = Rol.objects.get(id=1)
              user.rol = rol_usuario
              user.save()
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
        storage.used = True  #limpia todos los mensajes previos
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
      print( 'El enlace de activación no es válido o ha expirado.')
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
        
#cierra sesion tanto usuarios como admins
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
        if request.user.is_superuser:
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
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
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
            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('home')
      
def pagina_aterrizaje(request):
    """
    Renderiza la página de aterrizaje mostrando cotizaciones reales
    con tasas más recientes, hasta 6 monedas y datos para gráfico.
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
    storage = messages.get_messages(request)
    storage.used = True  # Limpia todos los mensajes previos
    
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        action = request.POST.get('action')
        # Guardar cambios
        if action == 'guardar':
            if form.is_valid():
                user = form.save()
                print(user, flush=True)
                update_session_auth_hash(request, user)  # Mantiene sesión si cambia contraseña
                return render(request, 'editarperfil.html', {'form': form,  'success': True} )
            else:
                return render(request, 'editarperfil.html', {'form': form} )
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

    return render(request, 'editarperfil.html', {'form': form})

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
    Empleado = namedtuple('Empleado', ['id', 'nombre', 'cedula', 'email', 'cargo'])
    
    # Datos de ejemplo
    empleados = [
        Empleado(id=1, nombre="Juan Pérez", cedula="12345678", email="juan.perez@email.com", cargo="Administrador"),
        Empleado(id=2, nombre="María Gómez", cedula="87654321", email="maria.gomez@email.com", cargo="Supervisor"),
        Empleado(id=3, nombre="Carlos López", cedula="11223344", email="carlos.lopez@email.com", cargo="Empleado"),
    ]
    
    # Pasamos los datos al template
    return render(request, 'empleados.html', {'empleados': empleados})