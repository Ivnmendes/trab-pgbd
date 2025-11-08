from django.db import connections, IntegrityError
from django.db.utils import OperationalError
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .serializers import *

# Essa parte de conexão é temporária, até eu souber como vão ficar definidas as permissões de cada usuário.
CARGO_TO_DB_CONNECTION = {
    'ORIENTADOR': 'orientador_db',
    'COORDENADOR': 'coordenador_db',
    'JIJ': 'jij_db',
}

def get_admin_connection():
    """Retorna a conexão com privilégios de escrita (Coordenador)."""
    return connections['coordenador_db']

def get_read_connection():
    """Retorna a conexão de leitura com privilégios baixos (Autenticação)."""
    return connections['autenticacao_db'] 

def dictfetchall(cursor):
    """
    Retorna todos os resultados de um cursor como uma lista de dicionários.
    Essencial para converter dados SQL brutos em JSON.
    """
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

class TemplateProcessoViewSet(viewsets.ViewSet):
    """
    API para gerenciar Templates de Processo (CRUD).
    Apenas Coordenadores podem Criar, Atualizar ou Deletar.
    Todos os usuários autenticados podem Listar/Ver.
    """
    
    def get_permissions(self):
        self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def list(self, request):
        """
        GET /api/processos/templates/
        Lista todos os templates de processo.
        """
        query = "SELECT id, nome, descricao FROM templateProcesso"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query)
                templates = dictfetchall(cursor)
            return Response(templates, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        """
        POST /api/processos/templates/
        Cria um novo template de processo. (Apenas Coordenador)
        """
        serializer = TemplateProcessoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "INSERT INTO templateProcesso (nome, descricao) VALUES (%s, %s)"
        
        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [data['nome'], data.get('descricao')])
                new_id = cursor.lastrowid
            
            return Response({"id": new_id, **data}, status=status.HTTP_201_CREATED)
        
        except (OperationalError, IntegrityError) as e:
            if 'command denied' in str(e).lower():
                return Response({"detail": "Permissão negada pelo banco de dados."}, status=status.HTTP_403_FORBIDDEN)
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        """
        GET /api/processos/templates/<pk>/
        Busca um template específico.
        """
        query = "SELECT id, nome, descricao FROM templateProcesso WHERE id = %s"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                template = cursor.fetchone()
            
            if not template:
                return Response({"detail": "Template não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            data = {'id': template[0], 'nome': template[1], 'descricao': template[2]}
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
        """
        PUT /api/processos/templates/<pk>/
        Atualiza um template. (Apenas Coordenador)
        """
        serializer = TemplateProcessoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "UPDATE templateProcesso SET nome = %s, descricao = %s WHERE id = %s"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [data['nome'], data.get('descricao'), pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Template não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"id": pk, **data}, status=status.HTTP_200_OK)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        DELETE /api/processos/templates/<pk>/
        Deleta um template. (Apenas Coordenador)
        """
        # TODO: Verificar se há etapas vinculadas antes de deletar
        query = "DELETE FROM templateProcesso WHERE id = %s"
        
        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Template não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            if 'foreign key constraint' in str(e).lower():
                return Response({"detail": "Não é possível deletar: este template está em uso por Etapas."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ProcessoViewSet(viewsets.ViewSet):
    """
    API para gerenciar Processos.
    Apenas Coordenadores podem Criar, Atualizar ou Deletar.
    Outros usuários autenticados podem Listar/Ver processos inativo.
    """
    
    def get_permissions(self):
        self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def list(self, request):
        """
        GET /api/processos/
        Lista todos os processos.
        """
        query = "SELECT id, id_template, id_usuario, status_proc, data_inicio FROM processo"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query)
                processos = dictfetchall(cursor)
            return Response(processos, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def create(self, request):
        """
        POST /api/processos/
        Cria um novo processo. (Apenas Coordenador)
        """
        serializer = ProcessoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "INSERT INTO processo (id_template, id_usuario, status_proc, data_inicio) VALUES (%s, %s, %s, %s)"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_template'],
                    data['id_usuario'],
                    data['status_proc'],
                    data['data_inicio']
                ])
                new_id = cursor.lastrowid
            
            return Response({"id": new_id, **data}, status=status.HTTP_201_CREATED)
        
        except (OperationalError, IntegrityError) as e:
            if 'command denied' in str(e).lower():
                return Response({"detail": "Permissão negada pelo banco de dados."}, status=status.HTTP_403_FORBIDDEN)
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def retrieve(self, request, pk=None):
        """
        GET /api/processos/<pk>/
        Busca um processo específico.
        """
        query = "SELECT id, id_template, id_usuario, status_proc, data_inicio FROM processo WHERE id = %s"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                processo = cursor.fetchone()
            
            if not processo:
                return Response({"detail": "Processo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            data = {
                'id': processo[0],
                'id_template': processo[1],
                'id_usuario': processo[2],
                'status_proc': processo[3],
                'data_inicio': processo[4]
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def update(self, request, pk=None):
        """
        PUT /api/processos/<pk>/
        Atualiza um processo. (Apenas Coordenador)
        """
        serializer = ProcessoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "UPDATE processo SET id_template = %s, id_usuario = %s, status_proc = %s, data_inicio = %s WHERE id = %s"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_template'],
                    data['id_usuario'],
                    data['status_proc'],
                    data['data_inicio'],
                    pk
                ])
                if cursor.rowcount == 0:
                    return Response({"detail": "Processo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"id": pk, **data}, status=status.HTTP_200_OK)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, pk=None):
        """
        DELETE /api/processos/<pk>/
        Deleta um processo. (Apenas Coordenador) 
        """
        query = "DELETE FROM processo WHERE id = %s"
        
        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Processo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class EtapaViewSet(viewsets.ViewSet):
    """
    API para gerenciar Etapas.
    """
    
    def get_permissions(self):
        self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def list(self, request):
        """
        GET /api/processos/etapas/
        Lista todas as etapas.
        """
        query = "SELECT id, id_template, nome, ordem, responsavel FROM etapa"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query)
                etapas = dictfetchall(cursor)
            return Response(etapas, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def create(self, request):
        """
        POST /api/processos/etapas/
        Cria uma nova etapa.
        """
        serializer = EtapaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "INSERT INTO etapa (id_template, nome, ordem, responsavel) VALUES (%s, %s, %s, %s)"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_template'],
                    data['nome'],
                    data['ordem'],
                    data['responsavel']
                ])
                new_id = cursor.lastrowid
            
            return Response({"id": new_id, **data}, status=status.HTTP_201_CREATED)
        
        except (OperationalError, IntegrityError) as e:
            if 'command denied' in str(e).lower():
                return Response({"detail": "Permissão negada pelo banco de dados."}, status=status.HTTP_403_FORBIDDEN)
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def retrieve(self, request, pk=None):
        """
        GET /api/processos/etapas/<pk>/
        Busca uma etapa específica.
        """
        query = "SELECT id, id_template, nome, ordem, responsavel FROM etapa WHERE id = %s"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                etapa = cursor.fetchone()
            
            if not etapa:
                return Response({"detail": "Etapa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
            data = {
                'id': etapa[0],
                'id_template': etapa[1],
                'nome': etapa[2],
                'ordem': etapa[3],
                'responsavel': etapa[4]
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def update(self, request, pk=None):
        """
        PUT /api/processos/etapas/<pk>/
        Atualiza uma etapa.
        """
        serializer = EtapaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "UPDATE etapa SET id_template = %s, nome = %s, ordem = %s, responsavel = %s WHERE id = %s"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_template'],
                    data['nome'],
                    data['ordem'],
                    data['responsavel'],
                    pk
                ])
                if cursor.rowcount == 0:
                    return Response({"detail": "Etapa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"id": pk, **data}, status=status.HTTP_200_OK)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, pk=None):
        """
        DELETE /api/processos/etapas/<pk>/
        Deleta uma etapa.
        """
        query = "DELETE FROM etapa WHERE id = %s"
        
        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Etapa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class FluxoExecucaoViewSet(viewsets.ViewSet):
    """
    API para gerenciar Fluxos de Execução.
    """
    
    def get_permissions(self):
        self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def list(self, request):
        """
        GET /api/processos/fluxos/
        Lista todos os fluxos de execução.
        """
        query = "SELECT id, id_origem, id_destino FROM fluxo_execucao"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query)
                fluxos = dictfetchall(cursor)
            return Response(fluxos, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def create(self, request):
        """
        POST /api/processos/fluxos/
        Cria um novo fluxo de execução.
        """
        serializer = FluxoExecucaoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "INSERT INTO fluxo_execucao (id_origem, id_destino) VALUES (%s, %s)"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_origem'],
                    data['id_destino']
                ])
                new_id = cursor.lastrowid
            
            return Response({"id": new_id, **data}, status=status.HTTP_201_CREATED)
        
        except (OperationalError, IntegrityError) as e:
            if 'command denied' in str(e).lower():
                return Response({"detail": "Permissão negada pelo banco de dados."}, status=status.HTTP_403_FORBIDDEN)
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def retrieve(self, request, pk=None):
        """
        GET /api/processos/fluxos/<pk>/
        Busca um fluxo de execução específico.
        """
        query = "SELECT id, id_origem, id_destino FROM fluxo_execucao WHERE id = %s"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                fluxo = cursor.fetchone()
            
            if not fluxo:
                return Response({"detail": "Fluxo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            data = {
                'id': fluxo[0],
                'id_origem': fluxo[1],
                'id_destino': fluxo[2]
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def update(self, request, pk=None):
        """
        PUT /api/processos/fluxos/<pk>/
        Atualiza um fluxo de execução.
        """
        serializer = FluxoExecucaoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "UPDATE fluxo_execucao SET id_origem = %s, id_destino = %s WHERE id = %s"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_origem'],
                    data['id_destino'],
                    pk
                ])
                if cursor.rowcount == 0:
                    return Response({"detail": "Fluxo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"id": pk, **data}, status=status.HTTP_200_OK)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, pk=None):
        """
        DELETE /api/processos/fluxos/<pk>/
        Deleta um fluxo de execução.
        """
        query = "DELETE FROM fluxo_execucao WHERE id = %s"
        
        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Fluxo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ExecucaoEtapaViewSet(viewsets.ViewSet):
    """
    API para gerenciar Execuções de Etapas.
    """
    
    def get_permissions(self):
        self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def list(self, request):
        """
        GET /api/processos/execucoes/
        Lista todas as execuções de etapas.
        """
        query = "SELECT id, id_processo, id_etapa, id_usuario, observacoes, data_inicio, data_fim, status FROM execucao_etapa"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query)
                execucoes = dictfetchall(cursor)
            return Response(execucoes, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def create(self, request):
        """
        POST /api/processos/execucoes/
        Cria uma nova execução de etapa.
        """
        serializer = ExecucaoEtapaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "INSERT INTO execucao_etapa (id_processo, id_etapa, id_usuario, observacoes, data_inicio, data_fim, status) VALUES (%s, %s, %s, %s, %s, %s, %s)"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_processo'],
                    data['id_etapa'],
                    data['id_usuario'],
                    data['observacoes'],
                    data['data_inicio'],
                    data['data_fim'],
                    data['status']
                ])
                new_id = cursor.lastrowid
            
            return Response({"id": new_id, **data}, status=status.HTTP_201_CREATED)
        
        except (OperationalError, IntegrityError) as e:
            if 'command denied' in str(e).lower():
                return Response({"detail": "Permissão negada pelo banco de dados."}, status=status.HTTP_403_FORBIDDEN)
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def retrieve(self, request, pk=None):
        """
        GET /api/processos/execucoes/<pk>/
        Busca uma execução de etapa específica.
        """
        query = "SELECT id, id_processo, id_etapa, id_usuario, observacoes, data_inicio, data_fim, status FROM execucao_etapa WHERE id = %s"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                execucao = cursor.fetchone()
            
            if not execucao:
                return Response({"detail": "Execução não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
            data = {
                'id': execucao[0],
                'id_processo': execucao[1],
                'id_etapa': execucao[2],
                'id_usuario': execucao[3],
                'observacoes': execucao[4],
                'data_inicio': execucao[5],
                'data_fim': execucao[6],
                'status': execucao[7]
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def update(self, request, pk=None):
        """
        PUT /api/processos/execucoes/<pk>/
        Atualiza uma execução de etapa.
        """
        serializer = ExecucaoEtapaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "UPDATE execucao_etapa SET id_processo = %s, id_etapa = %s, id_usuario = %s, observacoes = %s, data_inicio = %s, data_fim = %s, status = %s WHERE id = %s"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_processo'],
                    data['id_etapa'],
                    data['id_usuario'],
                    data['observacoes'],
                    data['data_inicio'],
                    data['data_fim'],
                    data['status'],
                    pk
                ])
                if cursor.rowcount == 0:
                    return Response({"detail": "Execução não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"id": pk, **data}, status=status.HTTP_200_OK)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, pk=None):
        """
        DELETE /api/processos/execucoes/<pk>/
        Deleta uma execução de etapa.
        """
        query = "DELETE FROM execucao_etapa WHERE id = %s"
        
        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Execução não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ModeloCampoViewSet(viewsets.ViewSet):
    """
    API para gerenciar Modelos de Campos.
    """
    
    def get_permissions(self):
        self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def list(self, request):
        """
        GET /api/processos/modelos_campos/
        Lista todos os modelos de campos.
        """
        query = "SELECT id, id_etapa, nome_campo, tipo, obrigatorio FROM modelo_campo"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query)
                modelos = dictfetchall(cursor)
            return Response(modelos, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def create(self, request):
        """
        POST /api/processos/modelos_campos/
        Cria um novo modelo de campo.
        """
        serializer = ModeloCampoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "INSERT INTO modelo_campo (id_etapa, nome_campo, tipo, obrigatorio) VALUES (%s, %s, %s, %s)"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_etapa'],
                    data['nome_campo'],
                    data['tipo'],
                    data['obrigatorio']
                ])
                new_id = cursor.lastrowid
            
            return Response({"id": new_id, **data}, status=status.HTTP_201_CREATED)
        
        except (OperationalError, IntegrityError) as e:
            if 'command denied' in str(e).lower():
                return Response({"detail": "Permissão negada pelo banco de dados."}, status=status.HTTP_403_FORBIDDEN)
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def retrieve(self, request, pk=None):
        """
        GET /api/processos/modelos_campos/<pk>/
        Busca um modelo de campo específico.
        """
        query = "SELECT id, id_etapa, nome_campo, tipo, obrigatorio FROM modelo_campo WHERE id = %s"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                modelo = cursor.fetchone()
            
            if not modelo:
                return Response({"detail": "Modelo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            data = {
                'id': modelo[0],
                'id_etapa': modelo[1],
                'nome_campo': modelo[2],
                'tipo': modelo[3],
                'obrigatorio': modelo[4]
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def update(self, request, pk=None):
        """
        PUT /api/processos/modelos_campos/<pk>/
        Atualiza um modelo de campo.
        """
        serializer = ModeloCampoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "UPDATE modelo_campo SET id_etapa = %s, nome_campo = %s, tipo = %s, obrigatorio = %s WHERE id = %s"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_etapa'],
                    data['nome_campo'],
                    data['tipo'],
                    data['obrigatorio'],
                    pk
                ])
                if cursor.rowcount == 0:
                    return Response({"detail": "Modelo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"id": pk, **data}, status=status.HTTP_200_OK)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, pk=None):
        """
        DELETE /api/processos/modelos_campos/<pk>/
        Deleta um modelo de campo.
        """
        query = "DELETE FROM modelo_campo WHERE id = %s"
        
        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Modelo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CampoViewSet(viewsets.ViewSet):
    """
    API para gerenciar Campos.
    """
    
    def get_permissions(self):
        self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def list(self, request):
        """
        GET /api/processos/campos/
        Lista todos os campos.
        """
        query = "SELECT id, id_modelo, dados FROM campo"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query)
                campos = dictfetchall(cursor)
            return Response(campos, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def create(self, request):
        """
        POST /api/processos/campos/
        Cria um novo campo.
        """
        serializer = CampoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "INSERT INTO campo (id_modelo, dados) VALUES (%s, %s)"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_modelo'],
                    data['dados']
                ])
                new_id = cursor.lastrowid
            
            return Response({"id": new_id, **data}, status=status.HTTP_201_CREATED)
        
        except (OperationalError, IntegrityError) as e:
            if 'command denied' in str(e).lower():
                return Response({"detail": "Permissão negada pelo banco de dados."}, status=status.HTTP_403_FORBIDDEN)
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def retrieve(self, request, pk=None):
        """
        GET /api/processos/campo/<pk>/
        Busca um campo específico.
        """
        query = "SELECT id, id_modelo, dados FROM campo WHERE id = %s"
        try:
            with get_read_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                campo = cursor.fetchone()
            
            if not campo:
                return Response({"detail": "Campo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            data = {
                'id': campo[0],
                'id_modelo': campo[1],
                'dados': campo[2]
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def update(self, request, pk=None):
        """
        PUT /api/processos/campo/<pk>/
        Atualiza um campo preenchido.
        """
        serializer = CampoSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "UPDATE campo SET id_modelo = %s, dados = %s WHERE id = %s"

        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [
                    data['id_modelo'],
                    data['dados'],
                    pk
                ])
                if cursor.rowcount == 0:
                    return Response({"detail": "Campo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"id": pk, **data}, status=status.HTTP_200_OK)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, pk=None):
        """
        DELETE /api/processos/campo/<pk>/
        Deleta um campo.
        """
        query = "DELETE FROM campo WHERE id = %s"
        
        try:
            with get_admin_connection().cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Campo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
