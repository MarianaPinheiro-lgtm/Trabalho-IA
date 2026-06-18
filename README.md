# Chatbot Inteligente para Agendamento de Compromissos

## Sobre o Projeto

Este projeto consiste em um chatbot inteligente desenvolvido para o Telegram, com o objetivo de auxiliar usuários no agendamento, consulta e cancelamento de compromissos por meio de linguagem natural.

O sistema utiliza Inteligência Artificial com a API da Groq para interpretar as mensagens enviadas pelo usuário e identificar a intenção da solicitação. Após interpretar a mensagem, o chatbot registra o compromisso no banco de dados PostgreSQL e também cria o evento no Google Calendar.


## Objetivo

Desenvolver um assistente virtual capaz de:

* Interpretar mensagens em linguagem natural;
* Identificar se o usuário deseja marcar, consultar ou cancelar um compromisso;
* Solicitar informações quando a mensagem estiver incompleta;
* Armazenar histórico de conversa;
* Registrar compromissos no banco de dados;
* Criar eventos no Google Calendar;
* Responder ao usuário diretamente pelo Telegram.


## Tecnologias Utilizadas

* Python
* Flask
* FastAPI
* PostgreSQL
* Groq API
* Telegram Bot API
* Google Calendar API
* Pydantic
* Requests
* Psycopg2
* Python Dotenv


## Estrutura do Projeto

```text
projeto/
│
├── app.py
├── main.py
├── database.py
├── google_calendar.py
├── requirements.txt
├── .env
├── credentials.json
└── README.md
```


## Descrição dos Arquivos

### app.py

Responsável por receber as mensagens enviadas pelo Telegram através do webhook e encaminhá-las para a API principal desenvolvida em FastAPI.

### main.py

Arquivo principal da aplicação. Ele recebe a mensagem do usuário, busca o histórico da conversa, chama a IA da Groq, interpreta a intenção, monta a resposta e envia a mensagem de volta para o Telegram.

### database.py

Responsável pela conexão com o PostgreSQL e pelas operações de banco de dados, como salvar mensagens, buscar histórico, salvar eventos, listar compromissos e cancelar eventos.

### google_calendar.py

Responsável pela autenticação com a API do Google Calendar e pela criação de eventos diretamente na agenda do usuário.


## Funcionalidades

* Marcar compromissos;
* Consultar compromissos cadastrados;
* Cancelar compromissos;
* Interpretar mensagens com linguagem natural;
* Armazenar histórico de conversa;
* Criar eventos no Google Calendar;
* Enviar respostas automáticas pelo Telegram.


## Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes informações:

```env
GROQ_API_KEY=sua_chave_groq
DATABASE_URL=postgresql://usuario:senha@localhost:5432/seubanco
TELEGRAM_BOT_TOKEN=seu_token_do_telegram
```


## Configuração do Google Calendar

Para utilizar a integração com o Google Calendar, é necessário:

1. Criar um projeto no Google Cloud;
2. Ativar a Google Calendar API;
3. Criar credenciais OAuth;
4. Baixar o arquivo `credentials.json`;
5. Colocar o arquivo na raiz do projeto.

Na primeira execução, o sistema abrirá uma janela do navegador para autorização da conta Google. Após a autorização, será criado automaticamente o arquivo `token.pickle`.


## Equipe

> Hugo Martins Nobrega de Oliveira
>
> João Marcos Lopes de Oliveira
>
> Karine Araujo dos Santos
>
> Mariana Nascimento Pinheiro


## Licença

Projeto desenvolvido exclusivamente para fins acadêmicos.
