from django.db import connection, IntegrityError, transaction
from django.db.utils import OperationalError
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from .serializers import *
from usuarios.permissions import IsCoordenador

def dictfetchall(cursor):
    """
    Retorna todos os resultados de um cursor como uma lista de dicionários.
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
    """
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'processo_completo']:
            self.permission_classes = [IsAuthenticated, IsCoordenador]
        else: # list, retrieve
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def list(self, request):
        query = "SELECT id, nome, descricao FROM template_processo"
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                templates = dictfetchall(cursor)
            return Response(templates, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
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
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        query = "SELECT id, nome, descricao FROM template_processo WHERE id = %s"
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [pk])
                template = dictfetchall(cursor)
            
            if not template:
                return Response({"detail": "Template não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(template[0], status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, pk=None):
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
        Deleta um template.
        ON DELETE CASCADE (no SQL) cuidará da limpeza das etapas/fluxos.
        """
        query = "DELETE FROM template_processo WHERE id = %s"
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [pk])
                if cursor.rowcount == 0:
                    return Response({"detail": "Template não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='processo-completo')
    def processo_completo(self, request, pk=None):
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

            resultado['etapas'] = etapas_data
            resultado['fluxos'] = fluxos_data
                
            return Response(resultado, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EtapaViewSet(viewsets.ViewSet):
    """
    API para gerenciar Etapas (CRUD) e suas ações (Vincular).
    """
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'vincular_etapa']:
            self.permission_classes = [IsAuthenticated, IsCoordenador]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()
    
    def list(self, request):
        id_template = request.query_params.get('id_template')
        
        query = "SELECT id, id_template, nome, ordem, responsavel, campo_anexo FROM etapa"
        params = []
        
        if id_template:
            query += " WHERE id_template = %s"
            params.append(id_template)
            
        query += " ORDER BY ordem"

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                etapas = dictfetchall(cursor)
            return Response(etapas, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def create(self, request):
        serializer = EtapaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "INSERT INTO etapa (id_template, nome, ordem, responsavel, campo_anexo) VALUES (%s, %s, %s, %s, %s)"

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [
                    data['id_template'],
                    data['nome'],
                    data['ordem'],
                    data['responsavel'],
                    data.get('campo_anexo', False) 
                ])
                new_id = cursor.lastrowid
            
            return Response({"id": new_id, **data}, status=status.HTTP_201_CREATED)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def retrieve(self, request, pk=None):
        query = "SELECT id, id_template, nome, ordem, responsavel, campo_anexo FROM etapa WHERE id = %s"
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [pk])
                etapa = dictfetchall(cursor)
            
            if not etapa:
                return Response({"detail": "Etapa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(etapa[0], status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def update(self, request, pk=None):
        serializer = EtapaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        query = "UPDATE etapa SET id_template = %s, nome = %s, ordem = %s, responsavel = %s, campo_anexo = %s WHERE id = %s"

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [
                    data['id_template'],
                    data['nome'],
                    data['ordem'],
                    data['responsavel'],
                    data.get('campo_anexo', False),
                    pk
                ])
                if cursor.rowcount == 0:
                    return Response({"detail": "Etapa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"id": pk, **data}, status=status.HTTP_200_OK)
        except (OperationalError, IntegrityError) as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
    def destroy(self, request, pk=None):
        """
        Deleta uma etapa.
        ON DELETE CASCADE (no SQL) cuidará da limpeza dos fluxos/execuções.
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


class FluxoExecucaoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para visualizar Fluxos de Execução.
    A criação/deleção é feita pelo EtapaViewSet (vincular_etapa)
    ou manualmente no banco.
    """
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        id_template = request.query_params.get('id_template')
        
        query = """
            SELECT f.id, f.id_origem, f.id_destino 
            FROM fluxo_execucao f
        """
        params = []

        if id_template:
            query += """
                JOIN etapa e ON f.id_origem = e.id
                WHERE e.id_template = %s
            """
            params.append(id_template)

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                fluxos = dictfetchall(cursor)
            return Response(fluxos, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def retrieve(self, request, pk=None):
        query = "SELECT id, id_origem, id_destino FROM fluxo_execucao WHERE id = %s"
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [pk])
                fluxo = dictfetchall(cursor)
            
            if not fluxo:
                return Response({"detail": "Fluxo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(fluxo[0], status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcessoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para visualizar Processos e seu histórico.
    Processos são criados/gerenciados pelo ExecucaoEtapaViewSet.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cargo_usuario = request.user.cargo
        id_usuario = request.user.id

        params = []
        if cargo_usuario in ['COORDENADOR', 'JIJ']:
            query_base = """
                SELECT p.id, tp.nome as tipo_processo, u.nome as iniciado_por, 
                    p.status_proc, p.data_inicio
                FROM processo p 
                JOIN template_processo tp ON p.id_template = tp.id
                JOIN usuario u ON p.id_usuario = u.id
                WHERE 1=1 
            """
        else:
            query_base = """
                SELECT p.id, tp.nome as tipo_processo, u.nome as iniciado_por, 
                    p.status_proc, p.data_inicio
                FROM processo p 
                JOIN template_processo tp ON p.id_template = tp.id
                JOIN usuario u ON p.id_usuario = u.id
                WHERE p.id IN (SELECT id_processo FROM execucao_etapa WHERE id_usuario = %s)
                AND 1=1
            """
            params.append(id_usuario)

        filtro_status = request.query_params.get('status_proc')
        if filtro_status:
            query_base += " AND p.status_proc = %s"
            params.append(filtro_status)

        filtro_template = request.query_params.get('id_template')
        if filtro_template:
            query_base += " AND tp.id = %s"
            params.append(filtro_template)

        filtro_usuario = request.query_params.get('id_usuario')
        if filtro_usuario and cargo_usuario in ['COORDENADOR', 'JIJ']:
            query_base += " AND u.id = %s"
            params.append(filtro_usuario)

        query_base += " ORDER BY p.data_inicio DESC"

        try:
            with connection.cursor() as cursor:
                cursor.execute(query_base, params)
                processos = dictfetchall(cursor)
            return Response(processos, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def retrieve(self, request, pk=None):
        """
        GET /api/processos/processos/<pk>/
        Busca o histórico de um processo (Implementação da Query 2).
        """
        id_processo = pk
        try:
            with connection.cursor() as cursor:
                query_processo = "SELECT * FROM processo WHERE id = %s"
                cursor.execute(query_processo, [id_processo])
                processo_data = dictfetchall(cursor)

                if not processo_data:
                    return Response({"detail": "Processo não encontrado."}, status=status.HTTP_404_NOT_FOUND)
                
                resultado_processo = processo_data[0]

                query_historico = """
                    SELECT 
                        e.nome as 'Etapa', 
                        u.nome as 'Encaminhado_por', 
                        ee.status_exec as 'Status', 
                        ee.data_inicio as 'Data_Inicio',
                        ee.data_fim as 'Data_Fim', 
                        ee.observacoes as 'Mensagem' 
                    FROM etapa e 
                    JOIN execucao_etapa ee ON e.id = ee.id_etapa
                    JOIN usuario u ON u.id = ee.id_usuario 
                    WHERE ee.id_processo = %s
                    ORDER BY ee.data_inicio ASC, ee.status_exec DESC
                """
                cursor.execute(query_historico, [id_processo])
                historico_data = dictfetchall(cursor)
                
                resultado_processo['historico_etapas'] = historico_data
                
                return Response(resultado_processo, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ExecucaoEtapaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API para executar o workflow (Caixa de Entrada, Iniciar, Finalizar).
    Não expõe CRUD, apenas ações de negócio.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='caixa-de-entrada')
    def caixa_de_entrada(self, request):     
        """
        GET /api/processos/execucoes/caixa-de-entrada/
        Implementação da Query 1.3 (Tarefas pendentes do usuário)
        """
        id_usuario = request.user.id
        
        query = """
            SELECT p.id as 'Id_Processo', tp.nome as 'Tipo_Processo', 
                   u.nome as 'Processo_iniciado_por', p.status_proc as 'Status',
                   p.data_inicio as 'Iniciado_em', e.nome as 'Etapa_Pendente' 
            FROM processo p 
            JOIN template_processo tp ON p.id_template = tp.id
            JOIN usuario u ON p.id_usuario = u.id 
            JOIN execucao_etapa ee ON ee.id_processo = p.id 
            JOIN etapa e ON e.id = ee.id_etapa
            WHERE ee.id_usuario = %s AND ee.status_exec = 'PENDENTE'
            AND p.id IN (
                SELECT id_processo 
                FROM execucao_etapa 
                WHERE id_usuario = %s AND status_exec = 'PENDENTE'
            )
        """
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, [id_usuario, id_usuario])
                execucoes = dictfetchall(cursor)
            return Response(execucoes, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='detalhe-tarefa')
    def detalhe_tarefa(self, request, pk=None):
        """
        GET /api/processos/execucoes/<pk>/detalhe_tarefa/
        Retorna os detalhes de uma tarefa específica (execucao_etapa).
        """
        id_exec_etapa = pk
        
        try:
            with connection.cursor() as cursor:
                query_exec = """
                    SELECT 
                        exec.id, exec.id_processo, exec.id_etapa,
                        exec.id_usuario, exec.observacoes, exec.data_inicio,
                        exec.data_fim, exec.anexo, exec.status_exec,
                        et.nome as nome_etapa, et.responsavel as cargo_responsavel,
                        et.campo_anexo
                    FROM execucao_etapa exec
                    JOIN etapa et ON exec.id_etapa = et.id
                    WHERE exec.id = %s
                """
                cursor.execute(query_exec, [id_exec_etapa])
                execucao_data = dictfetchall(cursor)

                if not execucao_data:
                    return Response({"detail": "Execução de etapa não encontrada."}, status=status.HTTP_404_NOT_FOUND)
                
                return Response(execucao_data[0], status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"detail": f"Erro de banco: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
        
    @action(detail=False, methods=['post'], url_path='iniciar')
    def iniciar_processo(self, request):
        """
        POST /api/processos/execucoes/iniciar/
        Inicia um novo processo chamando a Stored Procedure 'criacaoProcessoEtapa'.
        
        Body esperado: 
        { 
            "id_template": <id>,
            "observacoes": "...", (Opcional)
            "anexo": "..." (Opcional)
        }
        """
        id_template = request.data.get('id_template')
        id_usuario_iniciador = request.user.id
        observacoes = request.data.get('observacoes', 'Processo iniciado.')
        anexo = request.data.get('anexo', None)

        if not id_template:
            return Response(
                {"detail": "O campo 'id_template' é obrigatório no body."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with connection.cursor() as cursor:
                query_primeira_etapa = """
                    SELECT id FROM etapa
                    WHERE id_template = %s AND ordem = 1;
                """
                cursor.execute(query_primeira_etapa, [id_template])
                etapa_result = cursor.fetchone()
                
                if not etapa_result:
                    raise Exception(f"Template (id={id_template}) não possui uma etapa com 'ordem = 1'.")
                
                first_etapa_id = etapa_result[0]

                cursor.callproc('criacaoProcessoEtapa', [
                    id_template,
                    id_usuario_iniciador,
                    first_etapa_id,
                    observacoes,
                    anexo
                ])
                
                cursor.execute("""
                    SELECT id FROM processo 
                    WHERE id_usuario = %s 
                    ORDER BY data_inicio DESC 
                    LIMIT 1
                """, [id_usuario_iniciador])
                
                processo_criado = cursor.fetchone()
                new_processo_id = processo_criado[0] if processo_criado else None

            return Response(
                {
                    "detalhe": "Processo iniciado com sucesso.",
                    "id_processo_criado": new_processo_id
                },
                status=status.HTTP_201_CREATED
            )
        
        except (IntegrityError, OperationalError, Exception) as e:
            return Response(
                {"detail": f"Erro do banco de dados: {e}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar_execucao(self, request, pk=None):
        """
        POST /api/processos/execucoes/<pk>/finalizar/
        (Rota 7) Avança o workflow chamando a Stored Procedure 'validacaoEtapas'.
        
        Body esperado:
        {
            "observacoes": "...",
            "anexo": "..." (Opcional)
        }
        """
        id_exec_etapa_atual = pk
        
        observacoes = request.data.get('observacoes', 'Etapa anterior concluída.')
        anexo = request.data.get('anexo', None)
        id_usuario_executor = request.user.id

        try:
            with connection.cursor() as cursor:
                query_info = "SELECT id_etapa, id_processo FROM execucao_etapa WHERE id = %s AND status_exec = 'PENDENTE'"
                cursor.execute(query_info, [id_exec_etapa_atual])
                info_result = cursor.fetchone()

                if not info_result:
                    return Response({"detail": "Execução de etapa não encontrada ou já concluída."}, status=status.HTTP_404_NOT_FOUND)
                
                id_etapa_atual, id_processo_atual = info_result[0], info_result[1]

                query_fluxo = "SELECT id_destino FROM fluxo_execucao WHERE id_origem = %s"
                cursor.execute(query_fluxo, [id_etapa_atual])
                proxima_etapa = cursor.fetchone()

                if not proxima_etapa:
                    return Response({"detail": "Fluxo não definido. Esta etapa é um beco sem saída."}, status=status.HTTP_400_BAD_REQUEST)
                
                id_etapa_destino = proxima_etapa[0]

                cursor.callproc('validacaoEtapas', [
                    id_processo_atual,
                    id_etapa_destino,
                    id_usuario_executor,
                    observacoes,
                    anexo
                ])
        
                return Response({"detail": "Etapa avançada com sucesso."}, status=status.HTTP_200_OK)

        except (IntegrityError, OperationalError, Exception) as e:
            return Response(
                {"detail": f"Erro do banco de dados: {e}"},
                status=status.HTTP_400_BAD_REQUEST
            )