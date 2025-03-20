
# Chatbot Houer

![Versão](https://img.shields.io/badge/Versão-1.0-blue)

## Descrição

O **Chatbot Houer** é um assistente virtual desenvolvido para o Grupo Houer, com o objetivo de fornecer respostas precisas e fundamentadas utilizando dados públicos e informações oficiais. O chatbot integra dados de fontes como o IBGE para oferecer insights estratégicos em áreas como educação, saúde, saneamento, rodovias e iluminação pública.

## Funcionalidades

- **Consultas Demográficas**: Fornece indicadores demográficos e socioeconômicos de localidades específicas.
- **Informações Setoriais**: Apresenta dados atualizados sobre educação, saúde, saneamento, rodovias e iluminação pública.
- **Integração com Fontes Oficiais**: Utiliza dados de fontes oficiais, priorizando informações do IBGE.
- **Respostas Estratégicas**: Oferece respostas claras e orientadas a resultados, auxiliando na tomada de decisões informadas.

## Tecnologias Utilizadas

- [Streamlit](https://streamlit.io/): Framework para criação de aplicações web interativas em Python.
- [LangChain](https://python.langchain.com/): Biblioteca para construção de aplicações de linguagem natural.
- [ChatGroq](https://groq.com/): Modelo de linguagem utilizado para processamento e geração de respostas.
- [PostgreSQL](https://www.postgresql.org/): Banco de dados relacional utilizado para armazenar logs e mensagens.

## Pré-requisitos

- Python 3.8 ou superior
- [Docker](https://www.docker.com/) (opcional, recomendado para executar PostgreSQL)

## Instalação

1. **Clone o repositório:**

```bash
git clone https://github.com/renanmrbraga/chatbot-houer.git
```

2. **Navegue até o diretório do projeto:**

```bash
cd chatbot-houer
```

3. **Crie e ative um ambiente virtual usando venv:**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux ou MacOS
source venv/bin/activate
```

4. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

5. **Configure as variáveis de ambiente:**

Crie um arquivo `.env` na raiz do projeto com:

```env
POSTGRES_DB=chatbot
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

GROQ_API_KEY=sua_api_key
```

6. **Configure o banco de dados (com Docker):**

```bash
docker run --name chatbot_postgres -e POSTGRES_DB=chatbot -e POSTGRES_USER=seu_usuario -e POSTGRES_PASSWORD=sua_senha -p 5432:5432 -d postgres
```

Crie a tabela `app_logs`:

```sql
CREATE TABLE app_logs (
    id SERIAL PRIMARY KEY,
    log_level VARCHAR(50),
    message TEXT,
    context VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Uso

Inicie a aplicação:

```bash
streamlit run app.py
```

Acesse via navegador em `http://localhost:8501`.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## Licença

Este projeto está licenciado sob a Licença [APACHE](LICENSE).
