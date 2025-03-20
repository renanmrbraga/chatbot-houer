import logging
import streamlit as st
import requests
import os
from dotenv import load_dotenv, find_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from database import conectar_banco, salvar_mensagem, buscar_ultima_resposta
import psycopg2

# 1. Configurar Logging com Handler para o Banco
class DatabaseLogHandler(logging.Handler):
    """
    Logging handler que insere logs na tabela app_logs do PostgreSQL.
    """
    def __init__(self):
        super().__init__()
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT")
            )
            self.conn.autocommit = True
        except Exception as e:
            print(f"Erro ao conectar ao banco para logs: {e}")
            self.conn = None

    def emit(self, record):
        if not self.conn:
            return
        try:
            log_entry = self.format(record)
            level = record.levelname
            context = record.name
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO app_logs (log_level, message, context) VALUES (%s, %s, %s)",
                (level, log_entry, context)
            )
            cursor.close()
        except Exception as e:
            print(f"Erro ao registrar log no banco: {e}")

# Configuração básica dos logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ChatbotApp")

# Adiciona handler para console
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# Adiciona handler para o banco de dados (tabela app_logs)
db_handler = DatabaseLogHandler()
db_handler.setLevel(logging.INFO)
db_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(db_handler)

# 2. Carregar variáveis de ambiente
load_dotenv(find_dotenv())
logger.info("Variáveis de ambiente carregadas.")

# 3. Configurar o modelo Groq
groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(
    model="Gemma2-9b-It",
    groq_api_key=groq_api_key,
)
parser = StrOutputParser()

generic_template = """
Você é um chatbot altamente eficiente, estratégico e analítico para o Grupo Houer. Sua missão é fornecer respostas precisas e fundamentadas utilizando dados públicos e informações oficiais.

Ao responder as consultas, siga estas diretrizes:
- Utilize dados atualizados e verificados, priorizando informações de fontes oficiais como o IBGE.
- Ao tratar de localidades, inclua indicadores demográficos, socioeconômicos e dados regionais relevantes.
- Para questões sobre educação, saúde, saneamento, rodovias e iluminação pública, apresente informações claras e contextualizadas, com dados numéricos e tendências que embasem decisões estratégicas.
- Integre dados de múltiplas fontes oficiais para oferecer uma visão completa e precisa.
- Se os dados forem insuficientes, explique as limitações e sugira fontes ou ações para obtenção de mais informações.
- Mantenha um tom claro, direto e orientado a resultados, auxiliando o Grupo Houer a tomar decisões informadas.

Sua resposta deve ser precisa, fundamentada e mostrar uma visão estratégica dos dados públicos.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", generic_template),
    ("user", "{text}")
])
chain = prompt | llm | parser

# 4. Funções para consulta à API do IBGE
def get_ibge_data(endpoint):
    base_url = "https://servicodados.ibge.gov.br/api/v1"
    url = f"{base_url}/{endpoint}"
    logger.info(f"Consultando IBGE: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        logger.info("Resposta do IBGE recebida com sucesso.")
        return response.json()
    else:
        error_msg = f"Erro {response.status_code} na consulta ao IBGE."
        logger.error(error_msg)
        return {"error": error_msg}

def listar_estados():
    dados = get_ibge_data("localidades/estados")
    if "error" not in dados:
        estados = [estado["nome"] for estado in dados]
        return estados
    else:
        return dados["error"]

# 5. Definição dos Agents
class BaseAgent:
    def handle_query(self, query: str) -> str:
        raise NotImplementedError("Método handle_query() precisa ser implementado.")

class IBGEAgent(BaseAgent):
    def __init__(self, nome: str = "IBGEAgent"):
        self.nome = nome

    def handle_query(self, query: str) -> str:
        query_lower = query.lower()
        if "população" in query_lower:
            return f"{self.nome}: Dados populacionais específicos não encontrados."
        elif "estados" in query_lower:
            estados = listar_estados()
            if isinstance(estados, list):
                return f"{self.nome}: Estados do Brasil: " + ", ".join(estados)
            else:
                return estados
        else:
            return f"{self.nome} não encontrou uma correspondência para sua consulta."

class DefaultAgent(BaseAgent):
    def handle_query(self, query: str) -> str:
        return chain.invoke({'text': query})

class RouterAgent(BaseAgent):
    def __init__(self, ibge_agents: list, default_agent: BaseAgent):
        self.ibge_agents = ibge_agents
        self.default_agent = default_agent
        self.ibge_keywords = ["população", "estados", "ibge", "cidade", "município", "municipal"]

    def handle_query(self, query: str) -> str:
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in self.ibge_keywords):
            respostas_especializadas = []
            for agent in self.ibge_agents:
                resposta = agent.handle_query(query)
                if resposta and "não encontrou" not in resposta.lower():
                    respostas_especializadas.append(resposta)
            if respostas_especializadas:
                return "\n".join(respostas_especializadas)
            else:
                return self.default_agent.handle_query(query)
        else:
            return self.default_agent.handle_query(query)

# 6. Inicialização dos Agents
ibge_agent_especializado = IBGEAgent(nome="Especializado")
ibge_agent_geral = IBGEAgent(nome="Geral")
default_agent = DefaultAgent()
router_agent = RouterAgent(
    ibge_agents=[ibge_agent_especializado, ibge_agent_geral],
    default_agent=default_agent
)

# 7. Interface com Streamlit
st.title("Testando Conexão com PostgreSQL")
conn = conectar_banco()
if isinstance(conn, str):
    logger.error("Falha na conexão com o PostgreSQL.")
    st.error(conn)
else:
    logger.info("Conexão com o PostgreSQL estabelecida com sucesso.")
    st.success("Banco conectado com sucesso!")

st.title("Chatbot Grupo Houer com Agents")
st.markdown("Integração com Dados Públicos e Insights Estratégicos usando uma arquitetura de Agents")

user_question = st.text_input("Digite sua pergunta:")
logger.info(f"Usuário digitou a pergunta: {user_question}")

st.sidebar.title("Consultas Rápidas")
opcao = st.sidebar.selectbox("Selecione uma opção", ["Nenhuma", "Lista de Estados", "Lista de Municípios"])
if opcao == "Lista de Estados":
    user_question = "Lista de Estados"
elif opcao == "Lista de Municípios":
    user_question = "Lista de Municípios"

if st.button("Enviar"):
    with st.spinner("Processando..."):
        logger.info("Processamento da pergunta iniciado.")
        # Primeiro, tenta buscar uma resposta já salva no banco
        resposta = buscar_ultima_resposta(user_question)
        if resposta == "Nenhuma resposta encontrada.":
            logger.info("Nenhuma resposta salva no banco. Gerando nova resposta.")
            resposta = router_agent.handle_query(user_question)
            salvar_mensagem(user_question, resposta)
        else:
            logger.info("Resposta recuperada do banco.")
    st.subheader("Resposta:")
    st.write(resposta)
    logger.info("Resposta exibida ao usuário.")
