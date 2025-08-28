from django.shortcuts import render

# Create your views here.
def configuracion_view(request):
    return render(request, 'base_configuracion.html')