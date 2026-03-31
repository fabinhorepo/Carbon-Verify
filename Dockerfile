# ============================================
# STAGE 1: Build do Frontend (Node.js)
# ============================================
FROM node:22-slim AS frontend-builder

WORKDIR /frontend

# Instalar pnpm
RUN npm install -g pnpm

# Copiar arquivos de dependência primeiro (cache layer)
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# Instalar dependências
RUN pnpm install --frozen-lockfile

# Copiar código-fonte do frontend
COPY frontend/ .

# Build de produção
RUN pnpm build

# ============================================
# STAGE 2: Backend Python + Frontend estático
# ============================================
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código do backend
COPY backend/ .

# Copiar build do frontend do stage anterior
COPY --from=frontend-builder /frontend/dist ./static/

# Variável PORT lida do ambiente (Render define automaticamente)
ENV PORT=10000

# Expor porta
EXPOSE ${PORT}

# Criar script de inicialização que lê PORT do ambiente
RUN echo '#!/bin/bash\nexec uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}' > /app/start.sh && chmod +x /app/start.sh

# Iniciar servidor usando shell para expandir variável PORT
CMD ["/bin/bash", "/app/start.sh"]
