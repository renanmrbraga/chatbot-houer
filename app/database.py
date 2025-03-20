import os
import psycopg2
import logging
from dotenv import load_dotenv, find_dotenv

# Carregar variáveis de ambiente
load_dotenv(find_dotenv())

# Configurar o logging
logging.basicConfig(
    level=logging.INFO,  # Em produção, considere usar WARNING ou ERROR
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def conectar_banco():
    """
    Cria e retorna a conexão com o banco de dados PostgreSQL.
    
    Retorna:
        conn (psycopg2.extensions.connection): conexão com o banco de dados, ou
        uma string de erro se ocorrer uma exceção.
    """
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT")
        )
        logger.info("Conexão com o banco de dados estabelecida com sucesso.")
        return conn
    except Exception as e:
        error_message = f"Erro ao conectar ao banco: {e}"
        logger.error(error_message)
        return error_message

def salvar_mensagem(usuario, resposta):
    """
    Salva a interação (pergunta do usuário e resposta do chatbot) no banco de dados.
    
    Parâmetros:
        usuario (str): A pergunta ou identificação do usuário.
        resposta (str): A resposta gerada pelo chatbot.
        
    Retorna:
        None se a operação for bem-sucedida, ou uma string de erro em caso de falha.
    """
    conn = conectar_banco()
    if isinstance(conn, str):
        logger.error("Não foi possível conectar ao banco para salvar a mensagem.")
        return conn
    try:
        cur = conn.cursor()
        # Insere a mensagem na tabela chatbot_logs
        cur.execute(
            "INSERT INTO chatbot_logs (user_query, bot_response) VALUES (%s, %s);",
            (usuario, resposta)
        )
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Mensagem salva com sucesso no banco.")
    except Exception as e:
        error_message = f"Erro ao salvar no banco: {e}"
        logger.error(error_message)
        return error_message

def buscar_ultima_resposta(usuario):
    """
    Busca a última resposta registrada para uma dada consulta no banco de dados.
    
    Parâmetros:
        usuario (str): A consulta do usuário.
        
    Retorna:
        str: A resposta encontrada ou uma mensagem padrão se nenhuma resposta for encontrada,
             ou uma string de erro em caso de falha.
    """
    conn = conectar_banco()
    if isinstance(conn, str):
        logger.error("Não foi possível conectar ao banco para buscar a mensagem.")
        return conn
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT bot_response FROM chatbot_logs WHERE user_query = %s ORDER BY created_at DESC LIMIT 1;",
            (usuario,)
        )
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        if resultado:
            logger.info("Resposta encontrada no banco.")
            return resultado[0]
        else:
            logger.info("Nenhuma resposta encontrada para a consulta.")
            return "Nenhuma resposta encontrada."
    except Exception as e:
        error_message = f"Erro ao buscar do banco: {e}"
        logger.error(error_message)
        return error_message
