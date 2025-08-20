# Imagem base oficial do Python
FROM python:3.9

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho no container
WORKDIR /app

# Copia os arquivos de requisitos para o diretório de trabalho
COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o restante dos arquivos para o diretório de trabalho
COPY . .

# Criar diretório para PDFs processados
RUN mkdir -p /app/processed_pdfs

# Define a porta na qual o Streamlit irá rodar
EXPOSE 8502

# Comando para executar a aplicação na porta 8502
CMD ["streamlit", "run", "main.py", "--server.port", "8502"]
