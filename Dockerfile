# Imagem base oficial do Python
FROM python:3.9

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos de requisitos para o diretório de trabalho
COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o restante dos arquivos para o diretório de trabalho
COPY . .

# Define a porta na qual o Streamlit irá rodar
EXPOSE 8502

# Comando para executar a aplicação na porta 8502
CMD ["streamlit", "run", "main.py", "--server.port", "8502"]
