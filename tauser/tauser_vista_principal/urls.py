from django.urls import path
from . import views

urlpatterns = [   # página principal
    path('login/', views.login_view, name='login'),  # login API

]
