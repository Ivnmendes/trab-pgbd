# usuarios/serializers.py
from django.db import connection
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from .models import Usuario

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['cargo'] = user.cargo 
        
        return token
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        try:
            with connection.cursor() as cursor: 
                sql_query = """
                    SELECT 
                        id, 
                        senha, 
                        cargo 
                    FROM 
                        usuario
                    WHERE 
                        username = %s;
                """
                cursor.execute(sql_query, [username])
                user_data = cursor.fetchone()
        
        except Exception as e:
            raise serializers.ValidationError({"detail": "Erro interno de autenticação."})

        if user_data:
            user_id, db_password, user_cargo = user_data

            if password == db_password:
                user = Usuario(
                    id=user_id,
                    username=username,
                    cargo=user_cargo,
                )
                
                self.user = user 
                
                refresh = self.get_token(self.user)
                
                data = {}
                data['refresh'] = str(refresh)
                data['access'] = str(refresh.access_token)

                return data
        
        raise serializers.ValidationError({"detail": "Nome de usuário ou senha inválidos."}, code='no_active_account')
    

class UsuarioCreateSerializer(serializers.Serializer):
    """
    Serializer para validar a criação de novos usuários.
    """
    username = serializers.CharField(max_length=50)
    nome = serializers.CharField(max_length=100)
    cargo = serializers.ChoiceField(choices=['ORIENTADOR', 'COORDENADOR', 'JIJ'])
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True, label="Confirmação de Senha")

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As senhas não conferem."})
        return data