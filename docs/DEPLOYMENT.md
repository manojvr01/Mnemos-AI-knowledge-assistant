# Deployment & Infrastructure Guide — Mnemos

**Document Reference:** DEP-MNEMOS-1.0  
**Related Documents:** [ARCHITECTURE.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/ARCHITECTURE.md), [SECURITY.md](file:///c:/Users/manoj/OneDrive/Desktop/Mnemos%20AI%20Knowledge%20Assitant/mnemos/docs/SECURITY.md)

---

## 1. Local Development Architecture (Docker Compose)

For local development and testing, Mnemos runs via Docker Compose, provisioning an official PostgreSQL 16 image with the `pgvector` extension pre-installed, an API service, and a Web client.

```yaml
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    container_name: mnemos-postgres
    restart: always
    environment:
      POSTGRES_DB: mnemos_dev
      POSTGRES_USER: mnemos_user
      POSTGRES_PASSWORD: mnemos_password
    ports:
      - "5432:5432"
    volumes:
      - mnemos_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mnemos_user -d mnemos_dev"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build:
      context: ./apps/api
      dockerfile: Dockerfile
    container_name: mnemos-api
    restart: always
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://mnemos_user:mnemos_password@db:5432/mnemos_dev
      JWT_SECRET: dev_jwt_secret_change_in_production_min32chars
      STORAGE_BACKEND: local
      STORAGE_LOCAL_ROOT: /data/mnemos/storage
      EMBEDDING_PROVIDER: openai # or mock
      OPENAI_API_KEY: ${OPENAI_API_KEY}
    ports:
      - "8000:8000"
    volumes:
      - mnemos_storage:/data/mnemos/storage

  web:
    build:
      context: ./apps/web
      dockerfile: Dockerfile
    container_name: mnemos-web
    restart: always
    depends_on:
      - api
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000/api/v1

volumes:
  mnemos_pgdata:
  mnemos_storage:
```

---

## 2. Environment Configuration Matrix

### Backend (`apps/api/.env.example`)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://mnemos_user:mnemos_password@localhost:5432/mnemos_dev
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Security
JWT_SECRET=replace_with_a_secure_random_string_at_least_32_characters_long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
COOKIE_SECURE=false # Set to true in production with HTTPS

# Storage
STORAGE_BACKEND=local # 'local' or 's3'
STORAGE_LOCAL_ROOT=./data/storage
S3_BUCKET_NAME=
AWS_REGION=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# AI & Embeddings
EMBEDDING_PROVIDER=mock # 'openai', 'gemini', or 'mock'
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536
LLM_PROVIDER=mock # 'openai', 'gemini', or 'mock'
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=
GEMINI_API_KEY=

# RAG Parameters
RAG_SIMILARITY_THRESHOLD=0.70
RAG_TOP_K=5
```

### Frontend (`apps/web/.env.example`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Mnemos
```

---

## 3. Production Hosting & pgvector Compatibility

| Cloud Provider | Managed Service | pgvector Support | Notes / Cost Efficiency |
| :--- | :--- | :--- | :--- |
| **Supabase** | Managed PostgreSQL | Native (`extension vector`) | Recommended for zero-ops pgvector + connection pooling. Generous free tier. |
| **Neon.tech** | Serverless Postgres | Native (`extension vector`) | Scale-to-zero branching, free tier available. |
| **AWS RDS** | Aurora / RDS Postgres | Native (Postgres 15.3+) | Enterprise standard, requires standard EC2/RDS pricing. |
| **Render / Fly.io**| App Hosting + Docker | Native via Docker | High developer velocity, easy custom pgvector container deployment. |
