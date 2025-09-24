from django.shortcuts import render
import requests

def menu_principal(request):
    # Recibimos token desde querystring o cabecera
    token = request.GET.get("token")
    if token:
        request.session["access_token"] = token
    return render(request, "menu.html")

from django.shortcuts import render
import requests
from rest_framework_simplejwt.authentication import JWTAuthentication
def mostrar_saldo(request):
    # Tomar token desde cookie segura
    nombre=""
    token = request.COOKIES.get("access_token")
    print("Token en sesión:", token)
    if not token:
        return render(request, "saldo.html", {"saldo": "No has iniciado sesión"})

    try:
        headers = {"Authorization": f"Bearer {token}"}
        # Llamada al endpoint de clientes en global_exchange
        response = requests.get("http://127.0.0.1:8001/clientes/", headers=headers)
        print("Respuesta del servicio de clientes:", response.status_code, response.text)
    

        if response.status_code != 200:
            saldo = f"Error al obtener saldo: {response.status_code}"
        else:
            data = response.json()
            saldo = data.get("saldo", "Cuenta no encontrada")
            nombre = data.get("nombre", "Usuario")
            print("Nombre: "+ nombre)
    except Exception as e:
        saldo = f"Error al obtener saldo: {e}"

    return render(request, "saldo.html", {"saldo": saldo, "nombre": nombre})
