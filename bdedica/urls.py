from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('api/', include('usuarios.urls')),
    path('api/processos/', include('processos.urls')),
]