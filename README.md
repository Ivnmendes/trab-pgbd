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

No terminal MySQL, execute o seguinte comando para criar o banco de dados:

```sql
CREATE DATABASE bdedica;
```

#### 5.2 Criar o usuário dedicado

No terminal MySQL, execute o seguinte comando para criar o usuário e conceder as permissões necessárias:

```sql
CREATE USER 'bdedica_user'@'localhost' IDENTIFIED WITH mysql_native_password BY 'senha';
GRANT ALL PRIVILEGES ON bdedica.* TO 'bdedica_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 5.3 Atualizar o settings.py

No arquivo `settings.py`, atualize as configurações do banco de dados com as credenciais do usuário criado:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'projeto_db',            # O nome do DB que você criou
        'USER': 'django_user',           # O novo usuário que você criou
        'PASSWORD': 'sua_senha_forte',   # A senha do novo usuário
        'HOST': 'localhost',             # Onde o MySQL está rodando
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

### 7. Desenvolvimento

#### 7.1 Criar migrations

```bash
python manage.py makemigrations
```

Execute sempre que houver mudanças nos modelos.

#### 7.3 Criar um superusuário

```bash
python manage.py createsuperuser
```

Necessário para acessar o painel admin do Django.

#### 7.4 Rodar o Servidor de Desenvolvimento

```bash
python manage.py runserver
```

#### 7.5 Criar novos módulos no projeto

```bash
python manage.py startapp nome_do_modulo
```
