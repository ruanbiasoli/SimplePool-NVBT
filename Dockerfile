# Usa a imagem base do Python
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia apenas o arquivo de dependências inicialmente
COPY requirements.txt /app/requirements.txt

# Instala as dependências da API
RUN python -m venv venv \
    && . venv/bin/activate \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Adiciona o ambiente virtual ao PATH
ENV PATH="/app/venv/bin:$PATH"

# Copia o restante do código da aplicação
COPY ./app /app

# Expõe a porta da API
EXPOSE 8000

# Comando para iniciar a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]