# Usa a imagem oficial do Python
FROM python:3.13.2

# Cria um usuário não-root para segurança
RUN useradd -m myuser

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia apenas os arquivos necessários
COPY --chown=myuser:myuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos da aplicação
COPY --chown=myuser:myuser . .

# Alterna para o usuário seguro
USER myuser

# Expondo a porta do Streamlit
EXPOSE 8501

# Verifica se o Streamlit está instalado corretamente antes de iniciar
RUN pip list | grep streamlit

# Corrige o caminho do `app.py`
CMD ["streamlit", "run", "app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
