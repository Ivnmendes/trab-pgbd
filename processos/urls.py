from django.urls import path, include
from rest_framework import routers
from .views import *

router = routers.DefaultRouter()
router.register(r'templates', TemplateProcessoViewSet, basename='templateprocesso')
router.register(r'etapas', EtapaViewSet, basename='etapa')
router.register(r'fluxos', FluxoExecucaoViewSet, basename='fluxoexecucao')
router.register(r'processos', ProcessoViewSet, basename='processo')
router.register(r'campos_modelo', ModeloCampoViewSet, basename='modelocampo')
router.register(r'campo', CampoViewSet, basename='campo')
router.register(r'exec_etapas', ExecucaoEtapaViewSet, basename='execucaoetapa')

urlpatterns = [
    path('', include(router.urls)),
]