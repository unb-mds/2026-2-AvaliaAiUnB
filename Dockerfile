# Usa a versão oficial e leve do Python (slim)
FROM python:3.11-slim

# Define a pasta de trabalho lá dentro
WORKDIR /app

# Copia apenas as dependências primeiro (otimiza o build)
COPY requirements.txt .

# Instala as dependências da aplicação
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código da aplicação (ignorando o que está no .dockerignore)
COPY . .

# Expõe a porta para o servidor
EXPOSE 8000

# Roda o servidor de produção Gunicorn, escutando em todas as interfaces
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]