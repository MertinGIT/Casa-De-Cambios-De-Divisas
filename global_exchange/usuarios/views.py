from django.shortcuts import render,redirect
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login,logout,authenticate
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import json
# Create your views here.
@login_required #con esto protejemos las rutas
def home(request):
  return render(request,'home.html')
  
def signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    eslogan_lines = ["Empieza", "ahora."]
    eslogan_spans = ["!Comienza", "ya!"]
    subtitle = "Crea tu cuenta y empieza ahora."

    if request.method == 'GET':
        return render(request, 'registrarse.html', {
            'form': UserCreationForm(),
            'eslogan_lines': eslogan_lines,
            'eslogan_spans': eslogan_spans,
            'subtitle': subtitle,
            'submit_text': "Registrarse",
            'active_tab': "register"
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(
                    username=request.POST['username'],
                    password=request.POST['password1']
                )
                user.save()
                login(request, user)
                return redirect('home')
            except:
                return render(request, 'registrarse.html', {
                    'form': UserCreationForm(),
                    'error': 'El usuario ya existe',
                    'eslogan_lines': eslogan_lines,
                    'eslogan_spans': eslogan_spans,
                    'submit_text': "Registrarse",
                    'active_tab': "register"
                })
        else:
            return render(request, 'registrarse.html', {
                'form': UserCreationForm(),
                'error': 'Las contraseñas no coinciden',
                'eslogan_lines': eslogan_lines,
                'eslogan_spans': eslogan_spans,
                'submit_text': "Registrarse",
                'active_tab': "register"
            })


@login_required
def signout(request):
  logout(request)
  return redirect('/')

def signin(request):
    if request.user.is_authenticated:
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

