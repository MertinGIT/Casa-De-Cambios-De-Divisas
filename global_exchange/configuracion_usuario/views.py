from django.shortcuts import render


def configuracion_view_usuario(request):
    return render(request, 'configuracion_usuario/configuracion_home_usuario.html')