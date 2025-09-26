from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db import IntegrityError
from django.views.decorators.http import require_http_methods
from .models import LimiteTransaccion
from .forms import LimiteTransaccionForm
from clientes.models import Cliente
from monedas.models import Moneda

def check_nombre_cliente(request):
    """
    Verifica si un cliente ya tiene un límite activo para una moneda específica.
    Retorna False si el cliente ya tiene un límite activo para esa moneda, True si puede asignarse.
    """
    if request.method == 'POST':
        cliente_id = request.POST.get('cliente')
        moneda_id = request.POST.get('moneda')
        obj_id = request.POST.get('obj_id')  # ID del límite actual si es edición

        # Debug log para verificar parámetros recibidos
        print(f"🔍 DEBUG - check_nombre_cliente:")
        print(f"   - cliente_id: '{cliente_id}'")
        print(f"   - moneda_id: '{moneda_id}'")
        print(f"   - obj_id: '{obj_id}' (type: {type(obj_id)})")
        print(f"   - POST data: {dict(request.POST)}")

        if not cliente_id or not moneda_id:
            print("❌ Cliente ID o Moneda ID faltante, retornando False")
            return JsonResponse(False, safe=False)

        # Filtramos por cliente y moneda
        query = LimiteTransaccion.objects.filter(
            cliente_id=cliente_id,
            moneda_id=moneda_id,
            estado='activo'  # Solo consideramos los activos
        )
        print(f"🔎 Query inicial encontró: {query.count()} registros activos")

        # Excluimos el propio registro si estamos editando
        if obj_id and obj_id != 'null' and obj_id != '' and obj_id != 'None':
            try:
                obj_id_int = int(obj_id)
                query_before = query.count()
                query = query.exclude(pk=obj_id_int)
                query_after = query.count()
                print(f"✅ Excluyendo registro con ID: {obj_id_int}")
                print(f"   - Registros antes de excluir: {query_before}")
                print(f"   - Registros después de excluir: {query_after}")
            except (ValueError, TypeError) as e:
                print(f"❌ Error al convertir obj_id a int: {obj_id} - Error: {e}")
        else:
            print(f"⚠️  No se excluyó ningún registro (obj_id: {obj_id})")

        # Si existe al menos uno activo, no se puede asignar
        exists = query.exists()
        can_assign = not exists
        
        print(f"📊 RESULTADO:")
        print(f"   - Query exists: {exists}")
        print(f"   - Can assign: {can_assign}")
        print(f"   - Retornando: {can_assign}")
        print("=" * 50)

        return JsonResponse(can_assign, safe=False)

    print("❌ Método no es POST")
    return JsonResponse(False, safe=False)


from django.shortcuts import render
from .models import LimiteTransaccion
from .forms import LimiteTransaccionForm

def lista_limites(request):
    """
    Listado de límites con búsqueda opcional.
    Permite filtrar por cliente o moneda.
    """
    form = LimiteTransaccionForm()
    q = request.GET.get("q", "")
    campo = request.GET.get("campo", "")

    # Obtener todos los límites con cliente y moneda para optimizar consultas
    limites = LimiteTransaccion.objects.select_related('cliente', 'moneda').all()

    if q and campo:
        if campo == "nombre":  # Coincide con el value del select del template
            limites = limites.filter(cliente__nombre__icontains=q)
        elif campo == "moneda":
            limites = limites.filter(moneda__nombre__icontains=q)
        # Se pueden agregar más filtros en el futuro

    return render(request, "limite_moneda/lista.html", {
        "limites": limites,
        "form": form,
        "q": q,
        "campo": campo,
    })


def crear_limite(request):
    """Crear un nuevo límite de transacción"""
    if request.method == "POST":
        form = LimiteTransaccionForm(request.POST)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if form.is_valid():
            limite = form.save(commit=False)
            try:
                limite.save()
                messages.success(request, 'Límite de transacción creado exitosamente.')
                if is_ajax:
                    return JsonResponse({
                        "success": True,
                        "message": "Límite creado exitosamente",
                        "limite": {
                            "id": limite.id,
                            "cliente": limite.cliente.nombre,
                            "cliente_id": limite.cliente.id,
                            "moneda": limite.moneda.nombre,
                            "moneda_id": limite.moneda.id,
                            "limite_diario": float(limite.limite_diario),
                            "limite_mensual": float(limite.limite_mensual),
                            "estado": limite.estado
                        }
                    })
                return redirect("lista-limites")
            except IntegrityError:
                error_msg = "Ya existe un límite para este cliente y moneda."
                messages.error(request, error_msg)
                if is_ajax:
                    return JsonResponse({"success": False, "message": error_msg})
            except Exception as e:
                error_msg = f'Error al crear el límite: {str(e)}'
                messages.error(request, error_msg)
                if is_ajax:
                    return JsonResponse({"success": False, "message": error_msg})
        else:
            if is_ajax:
                return JsonResponse({"success": False, "errors": form.errors})

        # Si hay errores, renderizamos el listado con modal abierto
        limites = LimiteTransaccion.objects.select_related('cliente', 'moneda').all()
        return render(request, "limite_moneda/lista.html", {
            "limites": limites,
            "form": form,
            "show_modal": True,
            "modal_type": "create",
        })
    return redirect("lista-limites")

def editar_limite(request, pk):
    """Editar un límite existente"""
    limite = get_object_or_404(LimiteTransaccion, pk=pk)
    if request.method == "POST":
        form = LimiteTransaccionForm(request.POST, instance=limite)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        if form.is_valid():
            limite_actualizado = form.save(commit=False)
            try:
                limite_actualizado.save()
                messages.success(request, 'Límite de transacción actualizado exitosamente.')
                if is_ajax:
                    return JsonResponse({
                        "success": True,
                        "message": "Límite actualizado exitosamente",
                        "limite": {
                            "id": limite_actualizado.id,
                            "cliente": limite_actualizado.cliente.nombre,
                            "cliente_id": limite_actualizado.cliente.id,
                            "moneda": limite_actualizado.moneda.nombre,
                            "moneda_id": limite_actualizado.moneda.id,
                            "limite_diario": float(limite_actualizado.limite_diario),
                            "limite_mensual": float(limite_actualizado.limite_mensual),
                            "estado": limite_actualizado.estado
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

        limites = LimiteTransaccion.objects.select_related('cliente', 'moneda').all()
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
        limites = LimiteTransaccion.objects.select_related('cliente', 'moneda').all()
        return render(request, "limite_moneda/lista.html", {
            "limites": limites,
            "form": form,
            "modal_title": "Editar Límite",
            "form_action": request.path,
            "obj_id": limite.id,
            "show_modal": True,
            "modal_type": "edit",
        })
from django.core.exceptions import ValidationError
def cambiar_estado_limite(request, pk):
    """Alterna el estado entre activo/inactivo de un límite"""
    limite = get_object_or_404(LimiteTransaccion, pk=pk)
    response = {}

    if request.method == "POST":
        try:
            nuevo_estado = "inactivo" if limite.estado == "activo" else "activo"

            # Solo validar si vamos a activar
            if nuevo_estado == "activo":
                existe_activo = LimiteTransaccion.objects.filter(
                    cliente=limite.cliente,
                    moneda=limite.moneda,
                    estado='activo'
                ).exclude(pk=limite.pk).exists()
                if existe_activo:
                    raise ValidationError("Este cliente ya tiene un límite activo para esta moneda.")

            limite.estado = nuevo_estado
            limite.save()

            response = {
                "success": True,
                "nuevo_estado": limite.estado,
                "message": f"Límite {limite.estado} correctamente"
            }

        except ValidationError as e:
            response = {"success": False, "errors": e.messages}
        except Exception as e:
            response = {"success": False, "errors": [str(e)]}

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(response)

    # Para requests normales (no AJAX) redirigir a la lista
    return redirect("lista-limites")


def limite_detalle(request, pk):
    """Devuelve los detalles de un límite en formato JSON"""
    limite = get_object_or_404(LimiteTransaccion, pk=pk)
    return JsonResponse({
        "id": limite.id,
        "cliente": limite.cliente.id,
        "moneda": limite.moneda.id,
        "limite_diario": float(limite.limite_diario),
        "limite_mensual": float(limite.limite_mensual),
        "estado": limite.estado
    })
@require_http_methods(["GET"])
def get_clientes(request):
    """
    Devuelve la lista de clientes activos en formato JSON.
    Útil para llenar dinámicamente selects en formularios vía AJAX.
    """
    try:
        clientes = Cliente.objects.filter(estado='activo')
        clientes_data = [
            {
                'id': c.id,
                'nombre': c.nombre,
                'email': c.email,
                'cedula': c.cedula,
                'telefono': c.telefono
            }
            for c in clientes
        ]
        return JsonResponse(clientes_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_monedas(request):
    """
    Devuelve la lista de monedas activas en formato JSON.
    Útil para llenar dinámicamente selects en formularios vía AJAX.
    """
    try:
        monedas = Moneda.objects.filter(estado=True)
        monedas_data = [
            {
                'id': m.id,
                'nombre': m.nombre,
                'abreviacion': m.abreviacion
            }
            for m in monedas
        ]
        return JsonResponse(monedas_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)