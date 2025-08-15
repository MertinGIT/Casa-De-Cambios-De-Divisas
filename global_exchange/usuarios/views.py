from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login,logout,authenticate
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
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
# Create your views here.
@login_required #con esto protejemos las rutas
def home(request):
  return render(request,'home.html')


def signup(request):
    #if request.user.is_authenticated:
    #    return redirect('home')
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
              user.save()
              activateEmail(request, user, user.email)
              return render(request, 'email_confirm.html', {'email': user.email})
          except Exception as e:
              print("Error al guardar usuario:", e, flush=True)
              return render(request, 'registrarse.html', {
                  'form': form,
                  'error': 'El usuario ya existe'
              })
          
        else:    
            print("Formulario no válido", flush=True)
            return render(request, 'registrarse.html', {
                'form': form,
                'error': 'Corrige los errores en el formulario'
            })
        
    else:
        form = CustomUserCreationForm()
        return render(request, 'registrarse.html', {
            'form': form
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
        'user': user.username,
        'domain': get_current_site(request).domain,
        'uid64': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'protocol': 'https' if request.is_secure() else 'http'
    })

    email = EmailMessage(mail_subject, message, to=[to_email])
    email.content_subtype = 'html'  # Esto indica que el cuerpo es HTML
    email.send()
        
    
@login_required
def signout(request):
  logout(request)
  return redirect('/')

def signin(request):
  if request.user.is_authenticated:
      return redirect('home')
  if request.method == 'GET':
    return render(request,'login.html',{
    'form':AuthenticationForm
  })
  else:
    user=authenticate(username=request.POST['username'],password=request.POST['password'])
    print(user)
    if user is None:
      return render(request,'login.html',{
    'form':AuthenticationForm,
    'error':'El usuario o contraseña es incorrecto'
  })
    else:
      login(request,user)
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


def editarPerfil(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        
        if form.is_valid():
            user = request.user
            cd = form.cleaned_data
            #Si escribió algo en contraseña actual, obligar nueva y confirmación
            if cd.get('password_actual'):
              print("Intentando cambiar contraseña", flush=True)
              #Verificar si se quiere cambiar contraseña
              if cd['password_nuevo'] or cd['password_confirmacion']:
                  print("tiene pass nuevo o confirmacion", flush=True)
                  # Revisar que la contraseña actual sea correcta
                  if not user.check_password(cd['password_actual']):
                      messages.success(request,"La contraseña actual no es correcta.")
                      return render(request, 'editarperfil.html', {'form': form})

                  # Revisar que las contraseñas nuevas coincidan
                  if cd['password_nuevo'] != cd['password_confirmacion']:
                      messages.success(request,"La nueva contraseña y su confirmación no coinciden.")
                      return render(request, 'editarperfil.html', {'form': form})

                  # Guardar la nueva contraseña
                  user.set_password(cd['password_nuevo'])
                  update_session_auth_hash(request, user)  # Mantener sesión activa
              else:
                messages.success(request,"Para cambiar la contraseña debes escribir la contraseña nueva y de confirmacion") 
                return render(request, 'editarperfil.html', {'form': form})
          
              # Verificar si se quiere cambiar username
              if User.objects.filter(username=cd['username']).exclude(pk=user.pk).exists():
                  messages.success(request, "El nombre de usuario ya está en uso.")
                  return render(request, 'editarperfil.html', {'form': form})

              # Guardar cambios
              user.save()
              messages.success(request, "Perfil actualizado correctamente.")
              return redirect('home')
            else:
              # si no escribió la actual pero sí alguna de las nuevas, marcar error
              if cd.get('password_nuevo') or cd.get('password_confirmacion'):
                  messages.success(request,"Para cambiar la contraseña debes escribir la contraseña actual.")
                  return render(request, 'editarperfil.html', {'form': form})
    else:
        form = CustomUserChangeForm(instance=request.user)

    return render(request, 'editarperfil.html', {'form': form})

@login_required
def eliminarPerfil(request):
    if request.method == 'POST':
        password = request.POST.get('password_actual')

        # Verificar que puso la contraseña actual
        if not password:
          messages.error(request, "Debes ingresar tu contraseña para eliminar la cuenta.")
          return render(request, 'eliminarperfil.html')

        user = request.user
        if not user.check_password(password):
          messages.error(request, "La contraseña no es correcta.")
          return render(request, 'eliminarperfil.html')

        # Eliminar usuario
        user.delete()
        logout(request)  # Cerrar sesión
        messages.success(request, "Tu cuenta ha sido eliminada correctamente.")
        return redirect('home')

    return render(request, 'eliminarperfil.html')


