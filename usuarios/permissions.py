from rest_framework.permissions import BasePermission

class IsCoordenador(BasePermission):
    """
    Permissão personalizada que permite acesso apenas a usuários com o papel de 'Coordenador'.
    """

    def has_permission(self, request, view):
        print(request.user.cargo)
        return request.user.is_authenticated and request.user.cargo == 'COORDENADOR'