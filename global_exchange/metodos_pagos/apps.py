from django.apps import AppConfig

class MetodosPagosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'metodos_pagos'
    
    def ready(self):
        import metodos_pagos.signals as _  # Importa los signals al iniciar la app