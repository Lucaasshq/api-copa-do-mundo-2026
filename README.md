# API-Copa-do-Mundo-2026 - Guia de Instalação e Execução do Projeto Django Rest Framework

## Criação do ambiente virtual

Na raiz do repositório, coloque o seguinte comando no terminal (o Python precisa estar instalado na sua máquina):

-**Windows:**

```bash
python -m venv (nome do ambiente virtual de preferência)
```

-**Linux:**

```bash
python3 -m venv (nome do ambiente virtual de preferência)
```

## Ativação do ambiente virtual

-**Windows:**

```bash
.\(nome do ambiente virtual de preferência)\Scripts\activate
```

-**Linux:**

```bash
source .(nome do ambiente virtual de preferência)/bin/activate
```

## Instalação de dependências

Ao ativar seu ambiente, instale as bibliotecas presentes no arquivo requirements.txt

-**Windows:**

```bash
pip install -r .\requirements.txt
```

-**Linux:**

```bash
pip install -r .\requirements.txt
```

## Execução do Projeto

Entre na raiz do projeto

-**Windows:**

```bash
cd .\copa2026
```

-**Linux:**

```bash
cd copa2026/
```

Antes de executar a aplicação Django, crie e faça as migrações do banco de dados,
para isso, certifique o seu pgAdmin está executando, crie um banco em um servidor
com o nome 'copa2026_db' e após isso, execute os seguintes comandos:

-**Windows:**

```bash
python manage.py makemigrations
python manage.py migrate
```

-**Linux:**

```bash
python manage.py makemigrations
python manage.py migrate
```

Após garantir as migrações, execute o projeto:

-**Windows:**

```bash
python manage.py runserver
```

-**Linux:**

```bash
python manage.py runserver
```
