# BDedica

## Pré-requisitos

Para rodar este projeto, você precisará ter o seguinte instalado em sua máquina:

* **Python (versão 3.x recomendada)**
* **pip** (gerenciador de pacotes do Python)

## Instalação e Configuração

Siga os passos abaixo para configurar o ambiente e iniciar o projeto.

### 1. Clonar o Repositório

```bash
git clone https://github.com/Ivnmendes/trab-pgbd
cd trab-pgbd
```

### 2. Criar um Ambiente Virtual

É recomendado criar um ambiente virtual para isolar as dependências do projeto. Você pode fazer isso com o seguinte comando:

```bash
python -m venv venv
```

Use `source venv/bin/activate` para ativar o ambiente virtual.

### 3. Instalar as Dependências

Com o ambiente virtual ativado, você pode instalar as dependências do projeto usando o `pip`. Execute o seguinte comando:

```bash
pip install -r requirements.txt
```

### 4. Configurar o settings.py

Usando o arquivo `settings_base.py` como base, crie um novo arquivo chamado `settings.py` na mesma pasta e ajuste as configurações conforme necessário, especialmente as relacionadas ao banco de dados.

### 5. Configurar o Banco de Dados

#### 5.1 Criar o Banco de Dados

Use o arquivo `scripts/trab1-pgbd.sql` para criar o banco de dados e os usuários necessários. Você pode executar o script SQL usando o cliente MySQL:

```bash
mysql -u root -p < scripts/trab1-pgbd.sql
```

#### 5.2 Atualizar o settings.py

No arquivo `settings.py`, atualize as configurações do banco de dados com as credenciais do usuário criado (normalmente só copiar e colar de `settings_base.py`):

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'projeto_db',            
        'USER': 'django_user',           
        'PASSWORD': 'sua_senha_forte',   
        'HOST': 'localhost',             
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}
```

### 6. Aplicar as Migrações do Banco de Dados

```bash
python manage.py migrate
```

Execute sempre que houver mudanças nos modelos/no início do projeto. Sempre após criar as migrations.

### 7. Desenvolvimento

#### 7.1 Criar migrations

```bash
python manage.py makemigrations
```

Execute sempre que houver mudanças nos modelos/no início do projeto.

#### 7.4 Rodar o Servidor de Desenvolvimento

```bash
python manage.py runserver
```

#### 7.5 Criar novos módulos no projeto

```bash
python manage.py startapp nome_do_modulo
```

### 8. Doc da api

[Clique aqui](DOC.md)
