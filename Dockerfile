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

# Expor porta (Render usa 10000 por padrão)
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:10000/api/health || exit 1

# Iniciar servidor
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
