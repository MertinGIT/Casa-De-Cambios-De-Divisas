from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError

from monedas.models import Moneda
from .models import LimiteTransaccion
from .forms import LimiteTransaccionForm


def lista_limites(request):
    """
    Muestra la lista de límites globales de transacciones.

    Obtiene todas las instancias de `LimiteTransaccion`, ordenadas por estado,
    y renderiza la plantilla `limite_moneda/lista.html` junto con el formulario
    de creación de nuevos límites.

    Parámetros:
        request (HttpRequest): Objeto de solicitud HTTP.

    Retorna:
        HttpResponse: Página renderizada con la lista de límites y el formulario.
    """
    form = LimiteTransaccionForm()
    limites = LimiteTransaccion.objects.all().order_by('-estado')
    return render(request, "limite_moneda/lista.html", {
        "limites": limites,
        "form": form,
    })


def  crear_limite(request):
    """
    Crea un nuevo límite de transacción global.

    Procesa los datos enviados mediante POST utilizando `LimiteTransaccionForm`.
    Si el formulario es válido, crea un nuevo límite asociado a una moneda
    específica (actualmente se usa la moneda con id=1). Si ocurre un error de
    validación, se re-renderiza la página mostrando el modal con los errores.

    Parámetros:
        request (HttpRequest): Objeto de solicitud HTTP.

    Retorna:
        HttpResponse: Redirección a la lista de límites o página renderizada con errores.
    """
    if request.method == "POST":
        form = LimiteTransaccionForm(request.POST)
        print("POST DATA:", request.POST)  # Para ver qué llega
        print("Form is valid?", form.is_valid())
        print("Form errors:", form.errors)  # Esto te dice por qué no guarda

        if form.is_valid():
            limite = form.save(commit=False)
            limite.moneda = Moneda.objects.get(id=1)
            limite.save()
            print("Guardado:", limite.id, limite.limite_diario, limite.limite_mensual, limite.moneda)

            messages.success(request, "Límite creado")
            return redirect("lista-limites")
        else:
            return render(request, "limite_moneda/lista.html", {
                "form": form,
                "limites": LimiteTransaccion.objects.all(),
                "show_modal": True,
                "modal_type": "create",
            })
    return redirect("lista-limites")



def editar_limite(request, pk):
    """
    Edita un límite de transacción existente.

    Permite modificar los valores de un límite global identificado por su `pk`.
    Soporta tanto peticiones normales como AJAX, devolviendo respuestas JSON
    en caso de solicitudes asincrónicas.

    Parámetros:
        request (HttpRequest): Objeto de solicitud HTTP.
        pk (int): Identificador del límite de transacción a editar.

    Retorna:
        HttpResponse | JsonResponse:
            - Página renderizada con el formulario o redirección a la lista de límites.
            - JSON con el resultado si la petición es AJAX.

    Excepciones:
        Http404: Si el límite con la clave primaria especificada no existe.
    """
    limite = get_object_or_404(LimiteTransaccion, pk=pk)

    if request.method == "POST":
        form = LimiteTransaccionForm(request.POST, instance=limite)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if form.is_valid():
            try:
                limite_actualizado = form.save()
                messages.success(request, 'Límite global actualizado exitosamente.')
                if is_ajax:
                    return JsonResponse({
                        "success": True,
                        "message": "Límite actualizado exitosamente",
                        "limite": {
                            "id": limite_actualizado.id,
                            "limite_diario": float(limite_actualizado.limite_diario),
                            "limite_mensual": float(limite_actualizado.limite_mensual),
                            "moneda": limite_actualizado.moneda.nombre if limite_actualizado.moneda else None,
                        }
                    })
                return redirect("lista-limites")
            except Exception as e:
                error_msg = f'Error al actualizar el límite: {str(e)}'
                messages.error(request, error_msg)
                if is_ajax:
                    return JsonResponse({"success": False, "message": error_msg})
        else:
            if is_ajax:
                return JsonResponse({"success": False, "errors": form.errors})

        limites = LimiteTransaccion.objects.all()
        return render(request, "limite_moneda/lista.html", {
            "limites": limites,
            "form": form,
            "modal_title": "Editar Límite",
            "form_action": request.path,
            "modal_type": "edit",
            "obj_id": limite.id,
            "show_modal": True,
        })
    else:
        form = LimiteTransaccionForm(instance=limite)
        limites = LimiteTransaccion.objects.all()
        return render(request, "limite_moneda/lista.html", {
            "limites": limites,
            "form": form,
            "modal_title": "Editar Límite",
            "form_action": request.path,
            "obj_id": limite.id,
            "show_modal": True,
            "modal_type": "edit",
        })


def limite_detalle(request, pk):
    """
    Devuelve los detalles de un límite en formato JSON.

    Busca el límite de transacción por su clave primaria y devuelve sus
    atributos principales, como límite diario, mensual y moneda asociada.

    Parámetros:
        request (HttpRequest): Objeto de solicitud HTTP.
        pk (int): Identificador del límite.

    Retorna:
        JsonResponse: Diccionario con los datos del límite.
    """
    limite = get_object_or_404(LimiteTransaccion, pk=pk)
    return JsonResponse({
        "id": limite.id,
        "limite_diario": float(limite.limite_diario),
        "limite_mensual": float(limite.limite_mensual),
        "moneda": limite.moneda.nombre if limite.moneda else None,
    })
def cambiar_estado_limite(request, pk):
    """
    Cambia el estado de un límite entre 'activo' e 'inactivo'.

    Si se activa un límite, cualquier otro límite activo de la misma moneda
    se desactiva automáticamente para mantener una única configuración activa
    por moneda. Soporta peticiones AJAX.

    Parámetros:
        request (HttpRequest): Objeto de solicitud HTTP.
        pk (int): Identificador del límite de transacción.

    Retorna:
        HttpResponse | JsonResponse:
            - JSON con el nuevo estado si la petición es AJAX.
            - Redirección a la lista de límites en solicitudes normales.

    Excepciones:
        Http404: Si el límite no existe.
        Exception: Si ocurre un error al guardar los cambios.
    """
    limite = get_object_or_404(LimiteTransaccion, pk=pk)
    response = {}

    if request.method == "POST":
        try:
            # Alterna el estado
            nuevo_estado = "inactivo" if limite.estado == "activo" else "activo"

            if nuevo_estado == "activo":
                # Desactivar cualquier otro límite activo de la misma moneda
                LimiteTransaccion.objects.filter(
                    moneda=limite.moneda,
                    estado='activo'
                ).exclude(pk=limite.pk).update(estado='inactivo')

            limite.estado = nuevo_estado
            limite.save()

            response = {
                "success": True,
                "nuevo_estado": limite.estado,
                "message": f"Límite {limite.estado} correctamente"
            }

        except Exception as e:
            response = {"success": False, "errors": [str(e)]}

        # Respuesta AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(response)

    # Para requests normales
    return redirect("lista-limites")
