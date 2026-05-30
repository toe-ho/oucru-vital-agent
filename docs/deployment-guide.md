# Deployment Guide

**Last Updated:** 2026-05-29  
**Current Version:** v0.7.0 (Phases 1-7 Complete)

## Local Development with Docker Compose

### Prerequisites

- Docker 25+ and Compose v2
- Google OAuth client credentials (for auth flow)
- ~10 GB disk space (PostgreSQL + Ollama models)

### Quick Start

#### 1. Clone & Configure

```bash
git clone <repo_url>
cd oucru-capstone

# Root .env (Docker network, ports)
cp .env.example .env
# Edit as needed; defaults work for localhost development

# Backend .env (secrets)
cp backend/.env.example backend/.env
# REQUIRED: Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET_KEY

# Frontend .env.local (secrets)
cp frontend/.env.example frontend/.env.local
# OPTIONAL: Override NEXT_PUBLIC_API_BASE_URL if backend port differs
```

#### 2. Start Services

```bash
# Without LLM (deterministic fallback only)
docker compose up -d

# With LLM (full agentic assessment)
docker compose --profile ollama up -d
docker compose exec ollama ollama pull qwen3:8b
```

#### 3. Initialize Database

```bash
# Run Alembic migrations
docker compose exec backend alembic upgrade head

# Seed initial roles and default settings
docker compose exec backend python -m app.scripts.seed
```

#### 4. Verify Services

```bash
# Check all services running
docker compose ps

# Verify backend health
curl http://localhost:8000/health

# Open frontend
open http://localhost:3000
```

#### 5. Inspect Logs

```bash
# All services
docker compose logs -f

# Backend only
docker compose logs -f backend

# Frontend only
docker compose logs -f frontend
```

### Environment File Structure

#### Root `.env` (Docker Compose)

```bash
# Ports (change if conflicts)
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
OLLAMA_PORT=11434

# Database
POSTGRES_DB=oucru_vital
POSTGRES_USER=postgres
POSTGRES_PASSWORD=example_password_change_in_production

# Ollama (if using --profile ollama)
OLLAMA_HOST=0.0.0.0:11434
```

**Loaded by:** `docker-compose.yml` (interpolates variables)

#### Backend `.env` (Secrets)

```bash
# Database connection (async)
DATABASE_URL=postgresql+asyncpg://postgres:example_password_change_in_production@postgres:5432/oucru_vital

# Google OAuth (from Google Cloud Console)
GOOGLE_CLIENT_ID=<your_google_client_id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<your_google_client_secret>

# JWT signing key (generate: `openssl rand -hex 32`)
JWT_SECRET_KEY=<random_32_byte_hex>

# Storage
STORAGE_ROOT=/app/storage

# Ollama (if using)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=qwen3:8b

# Optional: LiteLLM for cloud LLMs (post-MVP)
# LITELLM_LOG=debug
```

**Loaded by:** Backend Docker entrypoint (uvicorn app.main:app)

#### Frontend `.env.local` (Secrets)

```bash
# Backend API base URL (change if backend port differs)
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**Loaded by:** Next.js build/runtime

### Docker Compose Services

#### PostgreSQL

```yaml
postgres:
  image: postgres:15-alpine
  ports:
    - "${POSTGRES_PORT}:5432"
  environment:
    POSTGRES_DB: ${POSTGRES_DB}
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

**Access:** `psql -h localhost -U postgres -d oucru_vital`

#### Backend (FastAPI)

```yaml
backend:
  build: ./backend
  ports:
    - "${BACKEND_PORT}:8000"
  depends_on:
    - postgres
  environment:
    DATABASE_URL: ${DATABASE_URL}
    GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
    GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
    JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    STORAGE_ROOT: ${STORAGE_ROOT}
  volumes:
    - ./backend:/app
    - ${STORAGE_ROOT}:/app/storage
  command: uvicorn app.main:app --host 0.0.0.0 --reload
```

**Features:**
- Code volume-mounted (hot reload)
- Depends on postgres (waits for connection)
- Stores files in `storage/` volume

#### Frontend (Next.js)

```yaml
frontend:
  build:
    context: ./frontend
    args:
      NEXT_PUBLIC_API_BASE_URL: http://localhost:${BACKEND_PORT}
  ports:
    - "${FRONTEND_PORT}:3000"
  depends_on:
    - backend
  environment:
    NEXT_PUBLIC_API_BASE_URL: http://localhost:${BACKEND_PORT}
```

**Note:** Rebuild required if `NEXT_PUBLIC_*` env changes; restart sufficient for other changes.

#### Ollama (Optional Profile)

```yaml
ollama:
  image: ollama/ollama:latest
  ports:
    - "${OLLAMA_PORT}:11434"
  profiles:
    - ollama
  volumes:
    - ollama_data:/root/.ollama
```

**Usage:**
```bash
docker compose --profile ollama up ollama
docker compose exec ollama ollama pull qwen3:8b
```

### Makefile Shortcuts

```bash
make up          # docker compose up -d
make down        # docker compose down
make migrate     # alembic upgrade head
make seed        # python -m app.scripts.seed
make test        # run tests
make lint        # ruff + eslint
make logs        # docker compose logs -f
```

## Local Development Without Docker

For rapid iteration (backend + frontend separately):

### Backend (FastAPI)

#### Prerequisites
- Python 3.11+
- PostgreSQL 15 running locally

#### Setup

```bash
cd backend

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edit: DATABASE_URL, GOOGLE_*, JWT_SECRET_KEY, etc.

# Initialize database (local postgres)
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/oucru_vital"
createdb -U postgres oucru_vital  # One-time
alembic upgrade head
python -m app.scripts.seed

# Start server
export GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... JWT_SECRET_KEY=...
uvicorn app.main:app --reload --port 8000
```

**API available at:** http://localhost:8000/docs (Swagger UI)

### Frontend (Next.js)

#### Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure .env.local
cp .env.example .env.local
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Start dev server
npm run dev
```

**App available at:** http://localhost:3000

## Database Migrations

### Create New Migration

```bash
cd backend
alembic revision --autogenerate -m "Add new table"
# Edit alembic/versions/NNNN_add_new_table.py to verify

# Apply migration
alembic upgrade head
```

### Rollback

```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# View current version
alembic current

# View migration history
alembic history
```

### In Docker

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
```

## Seeding Data

### Initial Seed (One-Time)

```bash
# Docker
docker compose exec backend python -m app.scripts.seed

# Local
python -m app.scripts.seed
```

**Seeded:**
- Roles: admin, researcher, reviewer, readonly
- Default SQI thresholds
- Initial settings

### Custom Seed Script

Edit `backend/app/scripts/seed.py` to add initial data:

```python
async def seed_db():
    async with get_db() as db:
        # Create roles
        admin_role = Role(name="admin")
        db.add(admin_role)
        
        # Create default settings
        setting = Setting(key="sqi_hr_threshold", value=0.7)
        db.add(setting)
        
        await db.commit()
```

## Testing Before Deployment

### Backend Tests

```bash
# In Docker
docker compose exec backend pytest

# Local
cd backend && pytest -v

# With coverage
pytest --cov=app tests/
```

**Location:** `backend/tests/unit/`, `backend/tests/integration/`

### Frontend Tests

```bash
# In Docker
docker compose exec frontend npm test

# Local
cd frontend && npm test

# With coverage
npm test -- --coverage
```

**Location:** `frontend/__tests__/`

### Integration Testing

```bash
# Start all services
make up

# Run all tests
make test

# Lint all code
make lint
```

## Production Deployment (Post-MVP)

### Cloud Platforms

#### AWS (ECS + RDS)

```bash
# Push Docker images to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <ecr_url>
docker build -t <ecr_url>/oucru-backend:latest backend/
docker push <ecr_url>/oucru-backend:latest

# Deploy to ECS (CloudFormation or Terraform)
# See AWS deployment guide (post-MVP)
```

#### Google Cloud (Cloud Run + Cloud SQL)

```bash
# Push to Container Registry
gcloud builds submit backend/ --tag gcr.io/<project>/oucru-backend
gcloud run deploy oucru-backend \
  --image gcr.io/<project>/oucru-backend \
  --set-env-vars DATABASE_URL=<cloud_sql_proxy_url>
```

#### Azure (App Service + Azure Database)

```bash
# Push to ACR
az acr build -r <registry> -t oucru-backend:latest backend/

# Deploy to App Service
az container create --resource-group <group> --name oucru-backend \
  --image <acr_url>/oucru-backend:latest \
  --environment-variables DATABASE_URL=<connection_string>
```

### Kubernetes (Optional)

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oucru-backend
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: backend
        image: gcr.io/project/oucru-backend:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: oucru-secrets
              key: database-url
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
```

### Environment Variables (Production)

**Backend:**

```bash
# Use secure secret management (AWS Secrets Manager, Google Secret Manager, etc.)
DATABASE_URL=postgresql+asyncpg://user:pass@cloud-sql.example.com:5432/oucru_vital
GOOGLE_CLIENT_ID=<production_oauth_client_id>
GOOGLE_CLIENT_SECRET=<production_oauth_secret>
JWT_SECRET_KEY=<production_jwt_key>
STORAGE_ROOT=/mnt/gcs  # or S3 path
OLLAMA_BASE_URL=http://ollama-service:11434  # or cloud LLM endpoint
```

**Frontend:**

```bash
NEXT_PUBLIC_API_BASE_URL=https://api.example.com  # Production API URL
```

### SSL/TLS

```bash
# Nginx reverse proxy (example)
server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Authorization $http_authorization;
        proxy_pass_request_headers on;
    }
}
```

## Monitoring & Troubleshooting

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health
# Response: {"status": "ok"}

# Database
docker compose exec postgres psql -U postgres -c "SELECT 1"

# Check logs
docker compose logs backend | grep -i error
```

### Common Issues

#### `Connection refused` (Backend can't reach DB)

```bash
# Verify postgres is running
docker compose ps postgres

# Check environment variable
docker compose exec backend env | grep DATABASE_URL

# Test connection
docker compose exec backend python -c \
  "from sqlalchemy import create_engine; create_engine('$DATABASE_URL').connect()"
```

#### `Ollama not found` (LLM unavailable)

```bash
# Verify Ollama is running (if using --profile ollama)
docker compose --profile ollama ps ollama

# Check Ollama has model pulled
docker compose exec ollama ollama list

# Test Ollama endpoint
curl http://localhost:11434/api/tags
```

#### Frontend can't reach backend

```bash
# Check NEXT_PUBLIC_API_BASE_URL
docker compose logs frontend | grep API_BASE_URL

# Verify backend is accessible from frontend container
docker compose exec frontend curl http://backend:8000/health
```

### Database Inspection

```bash
# Connect to postgres
docker compose exec postgres psql -U postgres -d oucru_vital

# List tables
\dt

# Count recordings
SELECT COUNT(*) FROM recordings;

# View audit events
SELECT user_id, action, resource_type FROM audit_events LIMIT 10;

# Quit
\q
```

### Log Levels

**Backend (FastAPI):**

```bash
# Set in .env (local) or environment (Docker)
LOG_LEVEL=DEBUG
```

**Frontend (Next.js):**

```bash
# Enable debug logs
DEBUG=oucru:* npm run dev
```

## Backup & Recovery

### Database Backup

```bash
# Dump database
docker compose exec postgres pg_dump -U postgres oucru_vital > backup.sql

# Restore from dump
docker compose exec -T postgres psql -U postgres oucru_vital < backup.sql
```

### File Storage Backup

```bash
# Docker volume
docker volume inspect oucru-capstone_postgres_data

# Local filesystem
tar -czf storage-backup.tar.gz backend/storage/
```

### Automated Backup (Production)

Use cloud provider's backup service:
- **AWS RDS:** Automated snapshots every 24 hours
- **Google Cloud SQL:** Automated backups + point-in-time recovery
- **Azure:** Geo-redundant backups

## Upgrade Path

### From v0.6 to v0.7

```bash
# Pull latest code
git pull origin main

# Rebuild images
docker compose build

# Apply any new migrations
docker compose exec backend alembic upgrade head

# Restart services
docker compose down
docker compose up -d
```

No breaking changes from v0.6 to v0.7.

### Database Migration Strategy

1. Run migration in staging environment first
2. Backup production database
3. Apply migration during low-traffic window
4. Verify data integrity
5. Monitor for errors in logs

## Performance Tuning

### PostgreSQL

```bash
# In .env or cloud settings
shared_buffers = 256MB (25% of RAM)
effective_cache_size = 1GB (50-75% of RAM)
work_mem = 4MB
```

### Backend

```bash
# Increase Uvicorn workers
uvicorn app.main:app --workers 4

# Add gunicorn wrapper (production)
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

### Frontend

```bash
# Build optimization
npm run build

# Enable SWR caching
staleTime: 60000  # TanStack Query default
```

## Post-MVP Roadmap

- [ ] Cloud deployment (AWS/GCP/Azure)
- [ ] Kubernetes orchestration
- [ ] Autoscaling (horizontal pod autoscaler)
- [ ] CDN for frontend (CloudFront/Cloudflare)
- [ ] Redis caching layer
- [ ] Message queue (RabbitMQ/SQS) for assessment jobs
- [ ] Prometheus monitoring + alerting
- [ ] Automated CI/CD deployment (GitHub Actions)
