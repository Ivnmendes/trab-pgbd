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