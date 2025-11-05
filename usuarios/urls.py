from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import UsuarioLoginView, UsuarioCreateView

urlpatterns = [
    path('login/', UsuarioLoginView.as_view(), name='token_obtain_pair'),
    path('criar/', UsuarioCreateView.as_view(), name='usuario_create'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]