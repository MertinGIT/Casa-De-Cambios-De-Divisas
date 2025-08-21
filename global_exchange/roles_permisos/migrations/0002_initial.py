from django.db import migrations

def crear_permisos(apps, schema_editor):
    Permiso = apps.get_model("roles_permisos", "Permiso")
    for nombre in ["Crear", "Editar", "Eliminar", "Ver", "Exportar"]:
        Permiso.objects.get_or_create(nombre=nombre)

class Migration(migrations.Migration):

    dependencies = [
        ("roles_permisos", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(crear_permisos),
    ]