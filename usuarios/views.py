from django.db import connections, IntegrityError, OperationalError
from django.contrib.auth.hashers import make_password
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CustomTokenObtainPairSerializer, UsuarioCreateSerializer

CARGO_TO_DB_CONNECTION = {
    'ORIENTADOR': 'orientador_db',
    'COORDENADOR': 'coordenador_db',
    'JIJ': 'jij_db',
}

class UsuarioCreateView(generics.CreateAPIView):
    """
    Endpoint para (apenas) Coordenadores criarem novos usuários.
    """
    serializer_class = UsuarioCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        validated_data = serializer.validated_data
        plain_password = validated_data['password']
        
        sql = """
            INSERT INTO usuario (username, nome, cargo, senha) 
            VALUES (%s, %s, %s, %s)
        """
        params = [
            validated_data['username'],
            validated_data['nome'],
            validated_data['cargo'],
            plain_password
        ]

        user_cargo = request.user.cargo
        connection_name = CARGO_TO_DB_CONNECTION.get(user_cargo)

        if not connection_name:
            return Response(
                {"detail": "Cargo do usuário logado não existe."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        try:
            with connections[connection_name].cursor() as cursor:
                cursor.execute(sql, params)
            
            response_data = serializer.validated_data.copy()
            response_data.pop('password')
            response_data.pop('password2')
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        
        except (OperationalError, IntegrityError) as e:
            error_message = str(e)
            
            if 'command denied' in error_message.lower():
                return Response(
                    {"detail": "Permissão negada pelo banco de dados para esta ação."}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if 'duplicate entry' in error_message.lower():
                return Response(
                    {"detail": "Este nome de usuário já existe."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(
                {"detail": f"Erro interno: {e}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class UsuarioLoginView(TokenObtainPairView):
    """
    Endpoint para login de usuários.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    permission_classes = [AllowAny]