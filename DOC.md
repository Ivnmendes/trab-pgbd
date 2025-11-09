# Documentação das Rotas da API

## Endpoint: Login de Usuário

Rota: *POST* `/api/login/`

Descrição: Autentica um usuário (verificando username e senha) e retorna um par de tokens (Access e Refresh) se for bem-sucedido.

Autenticação: Não necessária.

Exemplo de Requisição (JSON):

```json
{
    "username": "coordenador_admin",
    "password": "senha_admin_123"
}
```

Exemplo de Resposta (Sucesso 200 OK):

```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUz...<token>...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUz...<token>..."
}
```

O access deve ser enviado no cabeçalho `Authorization: Bearer <seu_token_de_acesso>` em todas as requisições.

## Endpoint: Criação de Usuário

Rota: *POST* `/api/criar/`

Descrição: Cria um novo usuário no sistema (Orientador, Coordenador ou JIJ).

Autenticação: Obrigatória. Requer um Access Token válido no cabeçalho `Authorization: Bearer <token>`.

Exemplo de Requisição (JSON):

```json
{
    "username": "novo_orientador",
    "nome": "Novo Orientador",
    "cargo": "ORIENTADOR",
    "password": "senha_segura_456",
    "password2": "senha_segura_456"
}
```

Exemplos de Resposta:

Sucesso (`201 CREATED`)

Ocorre quando: O usuário autenticado (via Token) é um COORDENADOR.

```json
{
    "username": "novo_orientador",
    "nome": "Novo Orientador",
    "cargo": "ORIENTADOR"
}
```

Falha de Permissão (`403 FORBIDDEN`)

Ocorre quando: O usuário autenticado (via Token) é um ORIENTADOR ou JIJ e tenta criar um usuário. O banco de dados (MySQL) bloqueia a tentativa de INSERT.

```json
{
    "detail": "Permissão negada pelo banco de dados para esta ação."
}
```

Falha de Autenticação (`401 UNAUTHORIZED`)

Ocorre quando: O Access Token não foi enviado, está expirado ou é inválido.

```json
{
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid",
    "messages": [..]
}
```

## Módulo Processos

### ViewSet: TemplateProcessoViewSet

Base URL: `/api/processos/templates/`

Descrição: API para gerenciar os templates (modelos) de processo.

#### Endpoint: Listar Templates

Rota: GET `/api/processos/templates/`

Descrição: Lista todos os templates de processo existentes.

Autenticação: Requerida.

Exemplo de Resposta (Sucesso 200 OK):

```json
[
    {
        "id": 1,
        "nome": "Relatório Mensal",
        "descricao": "Processo de envio de relatórios."
    },
    {
        "id": 2,
        "nome": "Solicitação de Férias",
        "descricao": "Fluxo para aprovação de férias."
    }
]
```

Exemplo de Resposta (Falha 500 `INTERNAL_SERVER_ERROR`):

```json
{
    "detail": "Erro de banco: ..."
}
```

#### Endpoint: Criar Template

Rota: POST `/api/processos/templates/`

Descrição: Cria um novo template de processo.

Autenticação: Requerida.

Exemplo de Requisição (JSON):

```json
{
    "nome": "Novo Template",
    "descricao": "Descrição opcional do processo."
}
```

Exemplos de Resposta:

Sucesso (201 CREATED)

```json
{
    "id": 3,
    "nome": "Novo Template",
    "descricao": "Descrição opcional do processo."
}
```

```json
{
    "id": 3,
    "nome": "Novo Template",
    "descricao": "Descrição opcional do processo."
}
{
    "id": 3,
    "nome": "Novo Template",
    "descricao": "Descrição opcional do processo."
}
```

Falha de Validação (400 BAD_REQUEST)

```json
{
    "nome": [
        "This field is required."
    ]
}
```

Falha de Permissão (403 FORBIDDEN)

```json
{
    "detail": "Permissão negada pelo banco de dados."
}
```

#### Endpoint: Detalhar Template

Rota: GET `/api/processos/templates/<pk>/`

Descrição: Busca os detalhes de um template de processo específico.

Autenticação: Requerida.

Exemplos de Resposta:

Sucesso (200 OK)

```json
{
    "id": 1,
    "nome": "Relatório Mensal",
    "descricao": "Processo de envio de relatórios."
}
```

Falha (404 NOT_FOUND)

```json
{
    "detail": "Template não encontrado."
}
```

#### Endpoint: Atualizar Template

Rota: PUT `/api/processos/templates/<pk>/`

Descrição: Atualiza um template de processo existente.

Autenticação: Requerida.

Exemplo de Requisição (JSON):

```json
{
    "nome": "Nome Atualizado",
    "descricao": "Descrição atualizada."
}
```

Exemplos de Resposta:

Sucesso (200 OK)

```json
{
    "id": 1,
    "nome": "Nome Atualizado",
    "descricao": "Descrição atualizada."
}
```

Falha (404 NOT_FOUND)

```json
{
    "detail": "Template não encontrado."
}
```

#### Endpoint: Deletar Template

Rota: DELETE `/api/processos/templates/<pk>/`

Descrição: Deleta um template de processo.

Autenticação: Requerida.

Exemplos de Resposta:

Sucesso (204 NO_CONTENT)
(Sem corpo de resposta)

Falha (404 NOT_FOUND)

```json
{
    "detail": "Template não encontrado."
}
```

#### Endpoint: Obter Template Completo (Ação)

Rota: GET `/api/processos/templates/<pk>/processo-completo/`

Descrição: Busca o design completo do template, incluindo suas etapas (ordenadas) e fluxos associados.

Autenticação: Requerida.

Exemplos de Resposta:

Sucesso (200 OK)

```json
{
    "id": 1,
    "nome": "Relatório Mensal",
    "descricao": "Processo de envio de relatórios.",
    "etapas": [
        {
            "id": 1,
            "id_template": 1,
            "nome": "Elaboração do Relatório",
            "ordem": 1,
            "responsavel": "ORIENTADOR"
        },
        {
            "id": 2,
            "id_template": 1,
            "nome": "Correção (Coordenador)",
            "ordem": 2,
            "responsavel": "COORDENADOR"
        }
    ],
    "fluxos": [
        {
            "id": 1,
            "id_origem": 1,
            "id_destino": 2
        }
    ]
}
```

Falha (404 NOT_FOUND)

```json
{
    "detail": "Template não encontrado."
}
```

### ViewSet: ProcessoViewSet

Base URL: `/api/processos/processos/`
Descrição: API para gerenciar as instâncias de processos (processos em andamento ou concluídos).

#### Endpoint: Listar Processos (com Filtros)

Rota: GET `/api/processos/processos/`

Descrição: Lista todas as instâncias de processos. O resultado é filtrado automaticamente com base no cargo do usuário (Coordenador/JIJ veem tudo; Orientador vê apenas processos onde ele é o id_usuario). Permite filtros adicionais por query parameters.

Autenticação: Requerida.

Query Parameters (Filtros Opcionais):

`?status_proc=<STATUS>`: Filtra por PENDENTE ou CONCLUIDO.

`?id_template=<id>`: Filtra por ID do template de processo.

`?id_usuario=<id>`: Filtra por ID do usuário que iniciou o processo (disponível apenas para Coordenador/JIJ).

Exemplo de Requisição (Coordenador filtrando):
GET `/api/processos/processos/?status_proc=PENDENTE&id_template=1`

Exemplo de Resposta (Sucesso 200 OK):

```json
[
    {
        "id": 1,
        "tipo_processo": "Relatório Mensal",
        "iniciado_por": "Nome do Orientador",
        "status_proc": "PENDENTE",
        "data_inicio": "2025-11-09T18:00:00Z"
    }
]
```

#### Endpoint: Obter Histórico do Processo

Rota: GET `/api/processos/processos/<pk>/`

Descrição: Busca o histórico completo de um processo específico, listando todas as suas etapas de execução, quem as executou e quando.

Autenticação: Requerida.

Exemplos de Resposta:

Sucesso (200 OK)

```json
{
    "historico_etapas": [
        {
            "Etapa": "Elaboração do Relatório",
            "Encaminhado por": "Nome do Orientador",
            "Status": "CONCLUIDO",
            "Data Início": "2025-11-09T18:00:00Z",
            "Data Fim": "2025-11-10T10:00:00Z",
            "Mensagem": "Relatório enviado."
        },
        {
            "Etapa": "Correção (Coordenador)",
            "Encaminhado por": "Nome do Orientador",
            "Status": "PENDENTE",
            "Data Início": "2025-11-10T10:00:00Z",
            "Data Fim": null,
            "Mensagem": "Etapa anterior concluída."
        }
    ]
}
```

Falha (404 NOT_FOUND)
Ocorre quando: O <pk> do processo não existe.

```json
{
    "detail": "Processo não encontrado."
}
```

### ViewSet: EtapaViewSet

Base URL: `/api/processos/etapas/`
Descrição: API para gerenciar as etapas (passos) de um template de processo.

#### Endpoint: Listar Etapas

Rota: GET `/api/processos/etapas/`

Descrição: Lista todas as etapas de todos os templates.

Autenticação: Requerida.

Exemplo de Resposta (Sucesso 200 OK):

```json
[
    {
        "id": 1,
        "id_template": 1,
        "nome": "Elaboração do Relatório",
        "ordem": 1,
        "responsavel": "ORIENTADOR",
        "campo_anexo": true
    },
    {
        "id": 2,
        "id_template": 1,
        "nome": "Correção (Coordenador)",
        "ordem": 2,
        "responsavel": "COORDENADOR",
        "campo_anexo": false
    }
]
```

#### Endpoint: Criar Etapa

Rota: POST `/api/processos/etapas/`

Descrição: Cria uma nova etapa vinculada a um template.

Autenticação: Requerida.

Exemplo de Requisição (JSON):

```json
{
    "id_template": 1,
    "nome": "Etapa de Aprovação Final",
    "ordem": 3,
    "responsavel": "JIJ",
    "campo_anexo": false
}
```

Exemplos de Resposta:

Sucesso (201 CREATED)

```json
{
    "id": 3,
    "id_template": 1,
    "nome": "Etapa de Aprovação Final",
    "ordem": 3,
    "responsavel": "JIJ",
    "campo_anexo": false
}
```

Falha de Validação (400 BAD_REQUEST)
Ocorre quando: O EtapaSerializer falha (ex: id_template ausente).

```json
{
    "id_template": ["This field is required."],
    "nome": ["This field is required."]
}
```

#### Endpoint: Detalhar Etapa

Rota: GET `/api/processos/etapas/<pk>/`

Descrição: Busca os detalhes de uma etapa específica.

Autenticação: Requerida.

Exemplos de Resposta:

Sucesso (200 OK)

```json
{
    "id": 1,
    "id_template": 1,
    "nome": "Elaboração do Relatório",
    "ordem": 1,
    "responsavel": "ORIENTADOR",
    "campo_anexo": true
}
```

Falha (404 NOT_FOUND)

```json
{
    "detail": "Etapa não encontrada."
}
```

#### Endpoint: Atualizar Etapa

Rota: PUT `/api/processos/etapas/<pk>/`

Descrição: Atualiza uma etapa existente.

Autenticação: Requerida.

Exemplo de Requisição (JSON):

```json
{
    "id_template": 1,
    "nome": "Elaboração (Anexo Obrigatório)",
    "ordem": 1,
    "responsavel": "ORIENTADOR",
    "campo_anexo": true
}
```

Exemplos de Resposta:

Sucesso (200 OK)

```json
{
    "id": 1,
    "id_template": 1,
    "nome": "Elaboração (Anexo Obrigatório)",
    "ordem": 1,
    "responsavel": "ORIENTADOR",
    "campo_anexo": true
}
```

Falha (404 NOT_FOUND)

```json
{
    "detail": "Etapa não encontrada."
}
```

#### Endpoint: Deletar Etapa

Rota: DELETE `/api/processos/etapas/<pk>/`

Descrição: Deleta uma etapa.

Autenticação: Requerida.

Exemplos de Resposta:

Sucesso (204 NO_CONTENT)
(Sem corpo de resposta)

Falha (404 NOT_FOUND)

```json
{
    "detail": "Etapa não encontrada."
}
```

#### Endpoint: Vincular Etapa (Ação)

Rota: POST `/api/processos/etapas/<pk>/vincular-etapa/`

Descrição: Cria um fluxo_execucao da etapa `<pk>` (origem) para uma etapa de destino.

Autenticação: Requerida.

Exemplo de Requisição (JSON):

```json
{
    "id_destino": 2
}
```

Exemplos de Resposta:

Sucesso (201 CREATED)
Onde `<pk>` da URL era 1 e o body era `{"id_destino": 2}`

```json
{
    "id": 1,
    "id_origem": 1,
    "id_destino": 2
}
```

Falha (400 BAD_REQUEST)
Ocorre quando: O body está vazio ou o id_destino não existe (erro de FK).

```json
{
    "detail": "O campo 'id_destino' é obrigatório no body."
}
```

### ViewSet: FluxoExecucaoViewSet

Base URL: `/api/processos/fluxos/`
Descrição: API (CRUD) para gerenciar o fluxo_execucao (as "setas" que ligam as etapas).

#### Endpoint: Listar Fluxos

Rota: GET `/api/processos/fluxos/`

Descrição: Lista todos os vínculos de fluxo (origem -> destino).

Autenticação: Requerida.

Exemplo de Resposta (Sucesso 200 OK):

```json
[
    {
        "id": 1,
        "id_origem": 1,
        "id_destino": 2
    },
    {
        "id": 2,
        "id_origem": 2,
        "id_destino": 3
    }
]
```

#### Endpoint: Detalhar Fluxo

Rota: GET `/api/processos/fluxos/<pk>/`

Descrição: Busca os detalhes de um vínculo de fluxo.

Autenticação: Requerida.

Exemplos de Resposta:

Sucesso (200 OK)

```json
{
    "id": 1,
    "id_origem": 1,
    "id_destino": 2
}
```

Falha (404 NOT_FOUND)

```json
{
    "detail": "Fluxo não encontrado."
}
```

### ViewSet: ExecucaoEtapaViewSet

Base URL: `/api/processos/exec_etapa/`
Descrição: API para gerenciar as instâncias de execução de etapas (as tarefas do workflow).

#### Endpoint: Iniciar Processo (Ação)

Rota: POST `/api/processos/exec_etapa/iniciar/`

Descrição: Inicia uma nova instância de processo com base em um template. Cria o processo e a primeira execucao_etapa.

Autenticação: Requerida.

Exemplo de Requisição (JSON):

```json
{
    "id_template": 1,
    "observacoes": "Iniciando o relatório de Novembro.",
    "anexo": null
}
```

Exemplos de Resposta:

Sucesso (201 CREATED)

```json
{
    "detalhe": "Processo iniciado com sucesso.",
    "id_processo_criado": 1
}
```

Falha (400 BAD_REQUEST)
Ocorre quando: O id_template não é enviado.

```json
{
    "detail": "O campo 'id_template' é obrigatório no body."
}
```

Falha (500 INTERNAL_SERVER_ERROR)
Ocorre quando: O template não tem uma etapa com ordem = 1.

```json
{
    "detail": "Erro interno: Exception: Template (id=1) não possui uma etapa com 'ordem = 1'."
}
```

#### Endpoint: Caixa de Entrada (Ação)

Rota: GET `/api/processos/exec_etapa/caixa-de-entrada/`

Descrição: Lista todas as etapas de execução (execucao_etapa) que estão com status_exec = 'PENDENTE' e atribuídas ao id_usuario do usuário autenticado.

Autenticação: Requerida.

Exemplo de Resposta (Sucesso 200 OK):

```json
[
    {
        "Id_Processo": 1,
        "Tipo_Processo": "Relatório Mensal",
        "Processo_iniciado_por": "Nome do Orientador",
        "Status": "PENDENTE",
        "Iniciado_em": "2025-11-09T18:00:00Z",
        "Etapa_Pendente": "Correção (Coordenador)"
    }
]
```


#### Endpoint: Detalhe da Tarefa (Ação)

Rota: GET `/api/processos/exec_etapa/<pk>/detalhe_tarefa/`

Descrição: Busca os detalhes de uma execucao_etapa específica (a "tarefa") para que o usuário possa visualizá-la ou executá-la.

Autenticação: Requerida.

Exemplos de Resposta:

Sucesso (200 OK)

```json
{
    "id": 2,
    "id_processo": 1,
    "id_etapa": 2,
    "id_usuario": 1,
    "observacoes": "Etapa anterior concluída.",
    "data_inicio": "2025-11-10T10:00:00Z",
    "data_fim": null,
    "anexo": null,
    "status_exec": "PENDENTE",
    "nome_etapa": "Correção (Coordenador)",
    "cargo_responsavel": "COORDENADOR"
}
```

Falha (404 NOT_FOUND)

```json
{
    "detail": "Execução de etapa não encontrada."
}
```

#### Endpoint: Finalizar Etapa (Ação)

Rota: POST `/api/processos/exec_etapa/<pk>/finalizar/`

Descrição: Marca a execucao_etapa (`<pk>`) como 'CONCLUIDO', salva as observacoes e/ou anexo enviados no body e avança o fluxo para a próxima etapa (se houver) ou finaliza o processo.

Autenticação: Requerida.

Exemplo de Requisição (JSON):

```json
{
    "observacoes": "Relatório revisado. Tudo certo.",
    "anexo": "[http://link.para/documento_assinado.pdf](http://link.para/documento_assinado.pdf)"
}
```

Exemplos de Resposta:

Sucesso (Avançou) (200 OK)

```json
{
    "detail": "Etapa avançada com sucesso."
}
```

Sucesso (Finalizou) (200 OK)

```json
{
    "detail": "Etapa final concluída. Processo finalizado."
}
```

Falha (404 NOT_FOUND)
Ocorre quando: A etapa `<pk>` não existe ou já foi concluída.

```json
{
    "detail": "Execução de etapa não encontrada ou já concluída."
}
```
