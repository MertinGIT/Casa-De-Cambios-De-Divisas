from django.shortcuts import render

from usuarios.forms import UserRolePermissionForm
from usuarios.models import CustomUser
from django.core.paginator import Paginator


# Create your views here.
def configuracion_view(request):
    return render(request, 'configuracion_home.html')

"""
def seguridad_hub(request):
    Hub principal de seguridad con tabs para usuarios y roles
    active_tab = request.GET.get('tab', 'usuarios')
    
    context = {
        'active_tab': active_tab
    }
    
    if active_tab == 'usuarios':
        # Lógica para usuarios (reutilizar de user_roles_lista)
        q = request.GET.get("q", "")
        campo = request.GET.get("campo", "")
        
        usuarios = CustomUser.objects.all().order_by("-id")
        form = UserRolePermissionForm()
        
        if q and campo:
            filtro = {f"{campo}__icontains": q}
            usuarios = usuarios.filter(**filtro)
        
        # Paginación
        paginator = Paginator(usuarios, 10)  # 10 usuarios por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context.update({
            "usuarios": usuarios,
            "page_obj": page_obj,
            "q": q,
            "campo": campo,
            "form": form
        })
        
    elif active_tab == 'roles':
        # Lógica para roles (adaptar según tu vista de roles existente)
        from django.contrib.auth.models import Group
        
        q = request.GET.get("q", "")
        campo = request.GET.get("campo", "")
        
        roles = Group.objects.all().order_by("name")
        
        if q and campo:
            if campo == "name":
                roles = roles.filter(name__icontains=q)
        
        # Paginación
        paginator = Paginator(roles, 10)  # 10 roles por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context.update({
            "roles": roles,
            "page_obj": page_obj,
            "q": q,
            "campo": campo,
        })
    
    return render(request, "security_hub.html", context)
"""