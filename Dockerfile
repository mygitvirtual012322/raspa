FROM python:3.9-slim

WORKDIR /app

# Copia todos os arquivos do projeto
COPY . .

# Comando para iniciar o servidor na porta definida pelo Railway ($PORT)
# Se PORT não estiver definida, usa 8000
CMD sh -c "python3 -m http.server ${PORT:-8000}"
