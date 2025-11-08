from django.db import connection, IntegrityError
from django.db.utils import OperationalError
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated as iam
from rest_framework.decorators import action

from .serializers import *

class IsAuthenticated(iam):
    """
    Permite acesso apenas a usuários autenticados.
    """
    def has_permission(self, request, view):
        return True

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
        query = "SELECT id, nome, descricao FROM template_processo"
        try:
            with cursor() as cursor:
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
        query = "INSERT INTO template_processo (nome, descricao) VALUES (%s, %s)"
        
        try:
            with connection.cursor() as cursor:
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
        query = "SELECT id, nome, descricao FROM template_processo WHERE id = %s"
        try:
            with connection.cursor() as cursor:
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
        query = "UPDATE template_processo SET nome = %s, descricao = %s WHERE id = %s"

        try:
            with connection.cursor() as cursor:
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
        query = "DELETE FROM template_processo WHERE id = %s"
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Template não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            if 'foreign key constraint' in str(e).lower():
                return Response({"detail": "Não é possível deletar: este template está em uso por Etapas."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='processo-completo')
    def processo_completo(self, request, pk=None):
        """
        GET /api/processos/templates/<id_template>/processo-completo/
        Retorna a estrutura completa de um processo, incluindo etapas, fluxos e modelos de campos.
        """ 
        id_template = pk
        
        try:
            with connection.cursor() as cursor:
                query_template = "SELECT * FROM template_processo WHERE id = %s"
                cursor.execute(query_template, [id_template])
                template_data = dictfetchall(cursor)
                
                if not template_data:
                    return Response({"detail": "Template não encontrado."}, status=status.HTTP_404_NOT_FOUND)
                
                resultado = template_data[0]
                
                query_etapas = "SELECT * FROM etapa WHERE id_template = %s ORDER BY ordem"
                cursor.execute(query_etapas, [id_template])
                etapas_data = dictfetchall(cursor)
                
                query_fluxos = """
                    SELECT * FROM fluxo_execucao 
                    WHERE id_origem IN (
                        SELECT id FROM etapa WHERE id_template = %s
                    )
                """
                cursor.execute(query_fluxos, [id_template])
                fluxos_data = dictfetchall(cursor)
                
                query_campos = """
                    SELECT * FROM modelo_campo 
                    WHERE id_etapa IN (
                        SELECT id FROM etapa WHERE id_template = %s
                    )
                """
                cursor.execute(query_campos, [id_template])
                campos_data = dictfetchall(cursor)

            campos_por_etapa = {}
            for campo in campos_data:
                id_etapa_do_campo = campo['id_etapa']
                if id_etapa_do_campo not in campos_por_etapa:
                    campos_por_etapa[id_etapa_do_campo] = []
                campos_por_etapa[id_etapa_do_campo].append(campo)
            
            for etapa in etapas_data:
                etapa['campos_modelo'] = campos_por_etapa.get(etapa['id'], [])

            resultado['etapas'] = etapas_data
            resultado['fluxos'] = fluxos_data
                
            return Response(resultado, status=status.HTTP_200_OK)
            
        except Exception as e:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
        GET /api/processos/processos/<pk>/
        Busca o histórico completo de um processo específico (pk=id_processo).
        """
        id_processo = pk
        conn = None

        try:
            conn = connection
            with conn.cursor() as cursor:
                query_processo = """
                    SELECT 
                        p.id, p.status_proc, p.data_inicio,
                        t.nome as template_nome,
                        u.nome as iniciador_nome
                    FROM processo p
                    JOIN template_processo t ON p.id_template = t.id
                    JOIN usuario u ON p.id_usuario = u.id
                    WHERE p.id = %s
                """
                cursor.execute(query_processo, [id_processo])
                processo_data = dictfetchall(cursor)

                if not processo_data:
                    return Response({"detail": "Processo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
                
                resultado_processo = processo_data[0]

                query_historico = """
                    SELECT 
                        exec.id as id_execucao, 
                        exec.status, exec.data_inicio, exec.data_fim,
                        exec.observacoes,
                        et.nome as etapa_nome,
                        u.nome as executor_nome
                    FROM execucao_etapa exec
                    JOIN etapa et ON exec.id_etapa = et.id
                    JOIN usuario u ON exec.id_usuario = u.id
                    WHERE exec.id_processo = %s
                    ORDER BY exec.data_inicio ASC
                """
                cursor.execute(query_historico, [id_processo])
                historico_data = dictfetchall(cursor)

                resultado_processo['historico_etapas'] = historico_data
                
                return Response(resultado_processo, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if conn:
                conn.close()
        
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Etapa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='vincular-etapa')
    def vincular_etapa(self, request, pk=None):
        """
        POST /api/processos/etapas/<pk>/vincular-etapa/
        Cria um registro em 'fluxo_execucao' vinculando a etapa atual (pk = id_origem) a outra etapa destino.

        Body esperado:
        {
            "id_destino": <id_da_etapa_destino>
        }
        """
        id_origem = pk
        id_destino = request.data.get('id_destino')

        if not id_destino:
            return Response(
                {"detail": "O campo 'id_destino' é obrigatório no body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        query = "INSERT INTO fluxo_execucao (id_origem, id_destino) VALUES (%s, %s)"
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [id_origem, id_destino])
                new_fluxo_id = cursor.lastrowid
            
            return Response(
                {
                    "id": new_fluxo_id,
                    "id_origem": int(id_origem),
                    "id_destino": int(id_destino)
                },
                status=status.HTTP_201_CREATED
            )
        
        except IntegrityError as e:
            return Response(
                {"detail": f"Erro de integridade do banco: {e}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except (OperationalError, Exception) as e:
            return Response(
                {"detail": f"Erro de banco: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Execução não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='caixa-de-entrada')
    def caixa_de_entrada(self, request):     
        """
        GET /api/processos/execucoes/caixa-de-entrada/
        Lista as execuções de etapa na caixa de entrada do usuário.
        """
        user = request.user
        query = """
            SELECT exec.id, exec.id_processo, et.nome as nome_etapa, et.responsavel
            FROM execucao_etapa exec
            JOIN etapa et ON exec.id_etapa = et.id
            JOIN usuario user ON %s = user.id
            WHERE exec.status = 'PENDENTE' 
            AND et.responsavel = user.cargo
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [user.id])
                execucoes = dictfetchall(cursor)
            return Response(execucoes, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='detalhe_tarefa')
    def detalhe_tarefa(self, request, pk=None):
        """
        GET /api/processos/execucoes/<id_exec_etapa>/detalhe_tarefa/

        Retorna os detalhes de uma tarefa específica para executá-la.
        """
        id_exec_etapa = pk
        
        try:
            with connection.cursor() as cursor:
                query_exec = """
                    SELECT 
                        exec.id, exec.id_processo, exec.id_etapa,
                        exec.id_usuario, exec.observacoes, exec.data_inicio,
                        exec.data_fim, exec.status,
                        et.nome as nome_etapa, et.responsavel as cargo_responsavel
                    FROM execucao_etapa exec
                    JOIN etapa et ON exec.id_etapa = et.id
                    WHERE exec.id = %s
                """
                cursor.execute(query_exec, [id_exec_etapa])
                execucao_data = dictfetchall(cursor)

                if not execucao_data:
                    return Response({"detail": "Execução de etapa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
                
                resultado = execucao_data[0]
                id_etapa_atual = resultado['id_etapa']

                query_modelos = """
                    SELECT id, nome_campo, tipo, obrigatorio 
                    FROM modelo_campo
                    WHERE id_etapa = %s
                """
                cursor.execute(query_modelos, [id_etapa_atual])
                modelos_data = dictfetchall(cursor)

                query_campos_preenchidos = """
                    SELECT id, id_modelo, dados 
                    FROM campo
                    WHERE id_exec_etapa = %s
                """
                cursor.execute(query_campos_preenchidos, [id_exec_etapa])
                campos_preenchidos_data = dictfetchall(cursor)

            dados_map = {
                campo['id_modelo']: campo['dados'] 
                for campo in campos_preenchidos_data
            }
            
            formulario_campos = []
            for modelo in modelos_data:
                id_modelo_atual = modelo['id']
                modelo['dados'] = dados_map.get(id_modelo_atual, None)
                formulario_campos.append(modelo)

            resultado['formulario'] = formulario_campos
                
            return Response(resultado, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['post'], url_path='iniciar')
    def iniciar_processo(self, request):
        """
        POST /api/processos/iniciar/

        Inicia um novo processo com base em um template.
        Cria o registro 'processo' e a primeira 'execucao_etapa'.
        
        Body esperado: { "id_template": <id_do_template> }
        """
        id_template = request.data.get('id_template')
        id_usuario_iniciador = request.user.id

        if not id_template:
            return Response(
                {"detail": "O campo 'id_template' é obrigatório no body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        conn = None
        try:
            conn = connection 
            with conn.cursor() as cursor:
                cursor.execute("BEGIN;")

                query_processo = """
                    INSERT INTO processo (id_template, id_usuario)
                    VALUES (%s, %s)
                """
                cursor.execute(query_processo, [id_template, id_usuario_iniciador])
                
                processo_result = cursor.lastrowid
                if not processo_result:
                    raise Exception("Falha ao criar o processo (RETURNING id falhou).")
                new_processo_id = processo_result

                query_primeira_etapa = """
                    SELECT id FROM etapa
                    WHERE id_template = %s AND ordem = 1;
                """
                cursor.execute(query_primeira_etapa, [id_template])
                
                etapa_result = cursor.fetchone()
                if not etapa_result:
                    raise Exception(f"Template (id={id_template}) não possui uma etapa com 'ordem = 1'.")
                first_etapa_id = etapa_result[0]

                query_exec_etapa = """
                    INSERT INTO execucao_etapa (id_processo, id_etapa, id_usuario, observacoes)
                    VALUES (%s, %s, %s, %s)
                """
                
                obs_padrao = "Processo iniciado."
                cursor.execute(query_exec_etapa, [new_processo_id, first_etapa_id, id_usuario_iniciador, obs_padrao])

                new_execucao_id = cursor.lastrowid

                cursor.execute("COMMIT;")

            return Response(
                {
                    "detalhe": "Processo iniciado com sucesso.",
                    "id_processo_criado": new_processo_id,
                    "id_execucao_etapa_pendente": new_execucao_id
                },
                status=status.HTTP_201_CREATED
            )

        except IntegrityError as e:
            if conn:
                conn.rollback()
            return Response(
                {"detail": f"Erro de integridade: 'id_template' inválido? Erro: {e}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            if conn:
                conn.rollback()
            return Response(
                {"detail": f"Erro interno: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if conn:
                conn.close()

    action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar_execucao(self, request, pk=None):
        """
        POST /api/processos/execucoes/<pk>/finalizar/
        Finaliza uma execução de etapa, atualizando seu status e data_fim.
        """
        id_exec_etapa = pk
        formulario_data = request.data.get('formulario')

        if formulario_data is None:
            return Response(
                {"detail": "O body deve conter a chave 'formulario' (pode ser uma lista vazia)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        conn = None
        try:
            conn = connection
            with conn.cursor() as cursor:
                cursor.execute("BEGIN;")

                query_info = "SELECT id_etapa, id_processo FROM execucao_etapa WHERE id = %s"
                cursor.execute(query_info, [id_exec_etapa])
                info_result = cursor.fetchone()

                if not info_result:
                    conn.rollback()
                    return Response({"detail": "Execução de etapa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
                
                id_etapa_atual, id_processo_atual = info_result

                query_obrigatorios = "SELECT id FROM modelo_campo WHERE id_etapa = %s AND obrigatorio = true"
                cursor.execute(query_obrigatorios, [id_etapa_atual])
                campos_obrigatorios = {row[0] for row in cursor.fetchall()}
                
                dados_enviados = {item['id_modelo']: item.get('dados') for item in formulario_data}
                
                for id_obrigatorio in campos_obrigatorios:
                    if id_obrigatorio not in dados_enviados or not dados_enviados[id_obrigatorio]:
                        conn.rollback()
                        return Response(
                            {"detail": f"Campo obrigatório (id_modelo={id_obrigatorio}) não foi preenchido."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                cursor.execute("DELETE FROM campo WHERE id_exec_etapa = %s", [id_exec_etapa])
                
                insert_query = "INSERT INTO campo (id_modelo, id_exec_etapa, dados) VALUES (%s, %s, %s)"
                dados_para_inserir = [
                    (item['id_modelo'], id_exec_etapa, item['dados'])
                    for item in formulario_data if item.get('dados')
                ]
                if dados_para_inserir:
                    cursor.executemany(insert_query, dados_para_inserir)

                query_concluir = "UPDATE execucao_etapa SET status = 'CONCLUIDO', data_fim = NOW() WHERE id = %s"
                cursor.execute(query_concluir, [id_exec_etapa])

                query_fluxo = "SELECT id_destino FROM fluxo_execucao WHERE id_origem = %s"
                cursor.execute(query_fluxo, [id_etapa_atual])
                proxima_etapa = cursor.fetchone()

                if proxima_etapa:
                    id_etapa_destino = proxima_etapa[0]
                    id_usuario_executor = request.user.id
                    obs_padrao = "Etapa anterior concluída."
                    
                    query_nova_etapa = """
                        INSERT INTO execucao_etapa (id_processo, id_etapa, id_usuario, observacoes)
                        VALUES (%s, %s, %s, %s)
                    """
                    cursor.execute(query_nova_etapa, [id_processo_atual, id_etapa_destino, id_usuario_executor, obs_padrao])
                    
                    response_message = "Etapa concluída e processo avançado."
                else:
                    query_concluir_processo = "UPDATE processo SET status_proc = 'CONCLUIDO' WHERE id = %s"
                    cursor.execute(query_concluir_processo, [id_processo_atual])
                    
                    response_message = "Etapa final concluída. Processo finalizado."

                cursor.execute("COMMIT;")
                
                return Response({"detail": response_message}, status=status.HTTP_200_OK)

        except (IntegrityError, OperationalError, Exception) as e:
            if conn:
                conn.rollback()
            return Response(
                {"detail": f"Erro na transação: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        finally:
            if conn:
                conn.close()
        

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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
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
            with connection.cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Campo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
