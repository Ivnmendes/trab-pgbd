from django.db import models

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        raise NotImplementedError("Método create_user não implementado para autenticação.")

    def create_superuser(self, username, password=None, **extra_fields):
        raise NotImplementedError("Método create_superuser não implementado para autenticação.")
    

class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)
    cargo = models.CharField(max_length=50) 
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Campos do usuário padrão do django remapeados/desativados
    password = models.CharField(max_length=255, db_column='senha')
    last_login = None
    is_superuser = None
    is_staff = None
    is_active = True

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['cargo'] 

    objects = UsuarioManager()

    class Meta:
        db_table = 'usuario'
        managed = False

    def __str__(self):
        return self.username

    @property
    def is_authenticated(self):
        return True
    
    def has_perm(self, perm, obj=None):
        return True 
    
    def has_module_perms(self, app_label):
        return True 