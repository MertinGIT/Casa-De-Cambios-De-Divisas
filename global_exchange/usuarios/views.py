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

@user_required #con esto protejemos las rutas
def home(request):
    cotizaciones = [
        {'simbolo': 'ARS', 'compra': 54564, 'venta': 45645, 'logo': 'img/logoMoneda/ARS.png'},
        {'simbolo': 'USD', 'compra': 68000, 'venta': 70000, 'logo': 'img/logoMoneda/USD.svg'},
        {'simbolo': 'EUR', 'compra': 75000, 'venta': 77000, 'logo': 'img/logoMoneda/EUR.svg'},
        # agrega más monedas aquí...
    ]
    data_por_moneda = {
            "USD": [
                {"fecha": "10 Jul", "compra": 7700, "venta": 7900},
                {"fecha": "11 Jul", "compra": 7720, "venta": 7920},
                {"fecha": "12 Jul", "compra": 7750, "venta": 7950},
                {"fecha": "13 Jul", "compra": 7790, "venta": 8000},
            ],
            "EUR": [
                {"fecha": "10 Jul", "compra": 8500, "venta": 8700},
                {"fecha": "11 Jul", "compra": 8520, "venta": 8720},
                {"fecha": "12 Jul", "compra": 8550, "venta": 8750},
                {"fecha": "13 Jul", "compra": 8590, "venta": 8800},
            ],
        }
    context = {
            'cotizaciones': cotizaciones,
            'data_por_moneda': json.dumps(data_por_moneda),
            "user": request.user
        }
    return render(request,'home.html',context)

def signup(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin')
        else:
            return redirect('home')
    eslogan_lines = ["Empieza", "ahora."]
    eslogan_spans = ["!Comienza", "ya!"]
    subtitle = "Crea tu cuenta y empieza ahora."
    
    print("Correo de confirmación enviado1", flush=True)
   
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        print("Correo de confirmación enviado2", flush=True)
        
       
        if form.is_valid():
          try:
              print("entro en try", flush=True)
              # Guardar usuario inactivo
              user = form.save(commit=False)
              user.is_active = False
              # Asignamos el rol 'usuario'
              rol_usuario = Rol.objects.get(nombre="usuario")
              user.rol = rol_usuario
              user.save()
              print(user, flush=True)
              activateEmail(request, user, user.email)
              return render(request, 'registrarse.html', {
                      'form': form,
                      'messages': f"Hola {user.username} tu cuenta ha sido creada correctamente. Por favor, revisa tu correo.",
                      'eslogan_lines': eslogan_lines,
                      'eslogan_spans': eslogan_spans,
                      'submit_text': "Registrarse",
                      'active_tab': "register"
                  })
          except Exception as e:
              print("Error al guardar usuario:", e, flush=True)
              return render(request, 'registrarse.html', {
                        'form': form,
                        'error': 'El usuario ya existe',
                        'eslogan_lines': eslogan_lines,
                        'eslogan_spans': eslogan_spans,
                        'submit_text': "Registrarse",
                        'active_tab': "register"
                    })
        else:    
            return render(request, 'registrarse.html', {
                        'form': form,
                        'error': 'El usuario ya existe',
                        'eslogan_lines': eslogan_lines,
                        'eslogan_spans': eslogan_spans,
                        'submit_text': "Registrarse",
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
  logout(request)
  return redirect('pagina_aterrizaje')

def signin(request):
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
                'error': 'Usuario o contraseña incorrectos',
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
  cotizaciones = [
        {'simbolo': 'ARS', 'compra': 54564, 'venta': 45645, 'logo': 'img/logoMoneda/ARS.png'},
        {'simbolo': 'USD', 'compra': 68000, 'venta': 70000, 'logo': 'img/logoMoneda/USD.svg'},
        {'simbolo': 'EUR', 'compra': 75000, 'venta': 77000, 'logo': 'img/logoMoneda/EUR.svg'},
        # agrega más monedas aquí...
    ]
  data_por_moneda = {
        "USD": [
            {"fecha": "10 Jul", "compra": 7700, "venta": 7900},
            {"fecha": "11 Jul", "compra": 7720, "venta": 7920},
            {"fecha": "12 Jul", "compra": 7750, "venta": 7950},
            {"fecha": "13 Jul", "compra": 7790, "venta": 8000},
        ],
        "EUR": [
            {"fecha": "10 Jul", "compra": 8500, "venta": 8700},
            {"fecha": "11 Jul", "compra": 8520, "venta": 8720},
            {"fecha": "12 Jul", "compra": 8550, "venta": 8750},
            {"fecha": "13 Jul", "compra": 8590, "venta": 8800},
        ],
    }
  context = {
        'cotizaciones': cotizaciones,
        'data_por_moneda': json.dumps(data_por_moneda),
    }
  return render(request, 'pagina_aterrizaje.html',context)

def error_404_view(request, exception):
    return render(request, '404.html', status=404)

@user_required
def editarPerfil(request):
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
                return render(request, 'editarperfil.html', {'form': form, 'messages': "Perfil actualizado correctamente."} )
            else:
                return render(request, 'editarperfil.html', {'form': form, 'messages': "Corrige los errores en el formulario."} )
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

