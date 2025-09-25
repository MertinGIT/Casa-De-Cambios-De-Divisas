# global_exchange/middleware.py
from django.shortcuts import render

class Custom404Middleware:
    """
    Middleware personalizado para manejar errores 404 (página no encontrada).

    Este middleware intercepta todas las respuestas de la aplicación Django y,
    si detecta que el código de estado HTTP es 404, renderiza una plantilla 
    personalizada llamada '404.html'. 

    De esta manera, en lugar de mostrar el error genérico de Django, el usuario 
    verá una página de error definida por el desarrollador.

    Atributos
    ---------
    get_response : function
        Función que procesa la solicitud y devuelve una respuesta HTTP.

    Métodos
    -------
    __call__(request):
        Procesa la solicitud entrante, obtiene la respuesta y, si el estado es 
        404, retorna la plantilla personalizada.
    """
    def __init__(self, get_response):
        """
        Inicializa el middleware con la función de respuesta de Django.

        Parámetros
        ----------
        get_response : function
            Función que maneja la solicitud y retorna la respuesta.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Procesa cada solicitud entrante y verifica el estado de la respuesta.

        Si la respuesta tiene un código 404, devuelve la plantilla '404.html'.
        En caso contrario, retorna la respuesta original.

        Parámetros
        ----------
        request : HttpRequest
            Objeto de la solicitud HTTP entrante.

        Retorna
        -------
        HttpResponse
            Respuesta original o la página personalizada de error 404.
        """
        response = self.get_response(request)
        if response.status_code == 404:
            return render(request, '404.html', status=404)
        return response
