# Bloom Deployment Guide

This guide covers deploying Bloom in production environments, including prerequisites, configuration, monitoring, and troubleshooting.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Database Configuration](#database-configuration)
- [Integration Setup](#integration-setup)
- [Running in Production](#running-in-production)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Troubleshooting](#troubleshooting)
- [Security Checklist](#security-checklist)

## Prerequisites

### System Requirements

**Minimum (Development)**:
- CPU: 4 cores
- RAM: 8 GB
- Disk: 50 GB SSD
- Network: 100 Mbps

**Recommended (Production)**:
- CPU: 16+ cores
- RAM: 32+ GB
- Disk: 500+ GB NVMe SSD
- Network: 1+ Gbps

### Software Dependencies

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.9+ | Application runtime |
| PostgreSQL | 14+ | DocumentStore |
| Redis | 6.2+ | Caching, pub/sub |
| Neo4j | 4.4+ | GraphStore |
| InfluxDB | 2.0+ | TimeSeriesStore |
| Nginx | 1.20+ | Reverse proxy (optional) |
| Docker | 20.10+ | Containerization (optional) |
| Kubernetes | 1.24+ | Orchestration (optional) |

### API Keys & Credentials

Required integrations:
- **Slack**: Bot token, signing secret, app token
- **Email**: SMTP credentials
- **Calendar**: Google/Microsoft OAuth credentials
- **Jira**: API token
- **GitHub/GitLab**: Personal access token
- **LLM Provider**: OpenAI or Anthropic API key

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd apps/bloom
```

### 2. Create Virtual Environment

```bash
python3.9 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 4. Environment Variables

Create `.env` file:

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env
```

**`.env` Configuration**:

```bash
# ============================================
# Application Settings
# ============================================
BLOOM_ENV=production  # development, staging, production
BLOOM_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
BLOOM_SECRET_KEY=your-secret-key-here-minimum-32-chars
ENCRYPTION_KEY=your-encryption-key-base64-encoded

# ============================================
# Database - PostgreSQL (DocumentStore)
# ============================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=bloom
POSTGRES_USER=bloom_user
POSTGRES_PASSWORD=secure-password-here
POSTGRES_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Connection pooling
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=10

# ============================================
# Redis (Caching & Pub/Sub)
# ============================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis-password-here
REDIS_DB=0
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}

# ============================================
# Neo4j (GraphStore)
# ============================================
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j-password-here

# ============================================
# InfluxDB (TimeSeriesStore)
# ============================================
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=influxdb-token-here
INFLUXDB_ORG=bloom-org
INFLUXDB_BUCKET=bloom-metrics

# ============================================
# Vector Database (for RAG)
# ============================================
VECTOR_DB_TYPE=pinecone  # or weaviate, qdrant, milvus
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=bloom-embeddings

# ============================================
# Slack Integration
# ============================================
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ

# ============================================
# Email Integration
# ============================================
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=bloom@company.com
EMAIL_SMTP_PASSWORD=your-app-password
EMAIL_FROM_ADDRESS=bloom@company.com
EMAIL_FROM_NAME=Bloom Evaluation System

# ============================================
# Calendar Integration
# ============================================
CALENDAR_PROVIDER=google  # or microsoft
GOOGLE_CALENDAR_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_CALENDAR_SCOPES=https://www.googleapis.com/auth/calendar

# ============================================
# Jira Integration
# ============================================
JIRA_URL=https://company.atlassian.net
JIRA_USER=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token

# ============================================
# Git Integration
# ============================================
GITHUB_TOKEN=ghp_your-github-token
GITHUB_ORG=your-organization
# Or for GitLab:
# GITLAB_TOKEN=glpat-your-gitlab-token
# GITLAB_URL=https://gitlab.com

# ============================================
# LLM Provider
# ============================================
LLM_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Anthropic (alternative)
# ANTHROPIC_API_KEY=sk-ant-your-key
# ANTHROPIC_MODEL=claude-3-opus-20240229

# ============================================
# Bloom Configuration
# ============================================
BLOOM_NUM_SCRIBES=2
BLOOM_NUM_CONTEXT_MINERS=1
BLOOM_NUM_CHASERS=1

BLOOM_ENABLE_AUTONOMOUS_MODE=true
BLOOM_ENABLE_RAG=true
BLOOM_ENABLE_VOICE_SYNTHESIS=true

BLOOM_MAX_CONCURRENT_EVALUATIONS=100
BLOOM_HEALTH_CHECK_INTERVAL_MINUTES=5

# Deadlines (in days)
BLOOM_PEER_SELECTION_DEADLINE_DAYS=7
BLOOM_PEER_FEEDBACK_DEADLINE_DAYS=14
BLOOM_SELF_EVAL_DEADLINE_DAYS=14
BLOOM_MANAGER_EVAL_DEADLINE_DAYS=21
BLOOM_CALIBRATION_DAYS=7

# ============================================
# Monitoring & Observability
# ============================================
SENTRY_DSN=https://xxx@sentry.io/xxx
DATADOG_API_KEY=your-datadog-api-key
PROMETHEUS_PORT=9090

# ============================================
# Security
# ============================================
ALLOWED_HOSTS=bloom.company.com,localhost
CORS_ALLOWED_ORIGINS=https://bloom.company.com
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
```

## Database Configuration

### PostgreSQL Setup

```bash
# Install PostgreSQL
sudo apt-get install postgresql-14

# Create database and user
sudo -u postgres psql

postgres=# CREATE DATABASE bloom;
postgres=# CREATE USER bloom_user WITH PASSWORD 'secure-password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE bloom TO bloom_user;
postgres=# \q

# Run migrations
python scripts/migrate_database.py
```

**Initialize Schema**:

```bash
# Run schema initialization script
python scripts/init_databases.py

# Verify tables created
psql -U bloom_user -d bloom -c "\dt"
```

### Redis Setup

```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf

# Set password
requirepass your-redis-password

# Restart Redis
sudo systemctl restart redis-server

# Test connection
redis-cli -a your-redis-password ping
```

### Neo4j Setup

```bash
# Install Neo4j (using Docker)
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -v $HOME/neo4j/data:/data \
  neo4j:4.4

# Access browser UI
# http://localhost:7474

# Create indexes
cypher-shell -u neo4j -p your-password <<EOF
CREATE INDEX employee_id FOR (e:Employee) ON (e.id);
CREATE INDEX collaboration_weight FOR ()-[r:COLLABORATION]-() ON (r.weight);
EOF
```

### InfluxDB Setup

```bash
# Install InfluxDB (using Docker)
docker run -d \
  --name influxdb \
  -p 8086:8086 \
  -v $HOME/influxdb/data:/var/lib/influxdb2 \
  influxdb:2.0

# Setup organization and bucket
influx setup \
  --username admin \
  --password secure-password \
  --org bloom-org \
  --bucket bloom-metrics \
  --retention 90d \
  --force

# Get auth token
influx auth list
```

## Integration Setup

### Slack Integration

1. **Create Slack App**:
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name: "Bloom"
   - Workspace: Select your workspace

2. **Configure Bot Permissions**:
   - Navigate to "OAuth & Permissions"
   - Add Bot Token Scopes:
     - `chat:write`
     - `chat:write.public`
     - `users:read`
     - `users:read.email`
     - `channels:read`
     - `groups:read`
     - `im:write`

3. **Install App to Workspace**:
   - Click "Install to Workspace"
   - Copy "Bot User OAuth Token" (starts with `xoxb-`)

4. **Enable Socket Mode** (for events):
   - Navigate to "Socket Mode"
   - Enable Socket Mode
   - Generate App-Level Token with `connections:write` scope
   - Copy token (starts with `xapp-`)

5. **Configure Event Subscriptions**:
   - Navigate to "Event Subscriptions"
   - Enable Events
   - Subscribe to bot events:
     - `message.im`
     - `app_mention`

6. **Add to `.env`**:
   ```bash
   SLACK_BOT_TOKEN=xoxb-...
   SLACK_APP_TOKEN=xapp-...
   SLACK_SIGNING_SECRET=...
   ```

### Email Integration (Gmail Example)

1. **Enable 2-Factor Authentication** on Gmail account

2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and "Other (Custom name)"
   - Name: "Bloom"
   - Copy generated password

3. **Configure `.env`**:
   ```bash
   EMAIL_SMTP_HOST=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_SMTP_USER=bloom@company.com
   EMAIL_SMTP_PASSWORD=generated-app-password
   ```

### Calendar Integration (Google Calendar)

1. **Create Google Cloud Project**:
   - Go to https://console.cloud.google.com
   - Create new project: "Bloom"

2. **Enable Calendar API**:
   - Navigate to "APIs & Services" → "Library"
   - Search "Google Calendar API"
   - Click "Enable"

3. **Create OAuth Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Download JSON

4. **Place credentials file**:
   ```bash
   mkdir -p /etc/bloom/credentials
   mv ~/Downloads/credentials.json /etc/bloom/credentials/google-calendar.json
   ```

5. **First-time authorization**:
   ```bash
   python scripts/authorize_calendar.py
   # Follow browser prompt to authorize
   ```

### Jira Integration

1. **Generate API Token**:
   - Go to https://id.atlassian.com/manage/api-tokens
   - Click "Create API token"
   - Label: "Bloom"
   - Copy token

2. **Configure `.env`**:
   ```bash
   JIRA_URL=https://company.atlassian.net
   JIRA_USER=your-email@company.com
   JIRA_API_TOKEN=your-token
   ```

3. **Test connection**:
   ```bash
   python scripts/test_jira_connection.py
   ```

## Running in Production

### Systemd Service

Create `/etc/systemd/system/bloom.service`:

```ini
[Unit]
Description=Bloom Evaluation System
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=bloom
Group=bloom
WorkingDirectory=/opt/bloom
Environment="PATH=/opt/bloom/venv/bin"
ExecStart=/opt/bloom/venv/bin/python main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
LimitNOFILE=65535
MemoryLimit=4G
CPUQuota=400%

[Install]
WantedBy=multi-user.target
```

**Enable and start**:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bloom
sudo systemctl start bloom
sudo systemctl status bloom
```

### Supervisor (Alternative)

Create `/etc/supervisor/conf.d/bloom.conf`:

```ini
[program:bloom]
command=/opt/bloom/venv/bin/python main.py
directory=/opt/bloom
user=bloom
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/bloom/bloom.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/bloom/venv/bin"
```

**Start**:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start bloom
```

## Docker Deployment

### Dockerfile

```dockerfile
# Multi-stage build
FROM python:3.9-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.9-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 bloom && chown -R bloom:bloom /app
USER bloom

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "main.py"]
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bloom:
    build: .
    container_name: bloom-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - BLOOM_ENV=production
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
      - neo4j
      - influxdb
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - bloom-network

  postgres:
    image: postgres:14-alpine
    container_name: bloom-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: bloom
      POSTGRES_USER: bloom_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - bloom-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U bloom_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:6.2-alpine
    container_name: bloom-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - bloom-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  neo4j:
    image: neo4j:4.4
    container_name: bloom-neo4j
    restart: unless-stopped
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
    volumes:
      - neo4j-data:/data
    networks:
      - bloom-network
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  influxdb:
    image: influxdb:2.0
    container_name: bloom-influxdb
    restart: unless-stopped
    environment:
      DOCKER_INFLUXDB_INIT_MODE: setup
      DOCKER_INFLUXDB_INIT_USERNAME: admin
      DOCKER_INFLUXDB_INIT_PASSWORD: ${INFLUXDB_PASSWORD}
      DOCKER_INFLUXDB_INIT_ORG: bloom-org
      DOCKER_INFLUXDB_INIT_BUCKET: bloom-metrics
    volumes:
      - influxdb-data:/var/lib/influxdb2
    networks:
      - bloom-network

volumes:
  postgres-data:
  redis-data:
  neo4j-data:
  influxdb-data:

networks:
  bloom-network:
    driver: bridge
```

**Deploy**:

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f bloom

# Check status
docker-compose ps
```

## Kubernetes Deployment

### Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: bloom
```

### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: bloom-config
  namespace: bloom
data:
  BLOOM_ENV: "production"
  BLOOM_LOG_LEVEL: "INFO"
  BLOOM_NUM_SCRIBES: "2"
  BLOOM_NUM_CONTEXT_MINERS: "1"
  BLOOM_NUM_CHASERS: "1"
```

### Secret

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: bloom-secrets
  namespace: bloom
type: Opaque
stringData:
  POSTGRES_PASSWORD: "your-postgres-password"
  REDIS_PASSWORD: "your-redis-password"
  SLACK_BOT_TOKEN: "xoxb-your-token"
  OPENAI_API_KEY: "sk-your-key"
```

### Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bloom-app
  namespace: bloom
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bloom
  template:
    metadata:
      labels:
        app: bloom
    spec:
      containers:
      - name: bloom
        image: bloom:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: bloom-config
        - secretRef:
            name: bloom-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 5
```

### Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: bloom-service
  namespace: bloom
spec:
  selector:
    app: bloom
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Deploy**:

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Check status
kubectl get pods -n bloom
kubectl logs -f -n bloom deployment/bloom-app
```

## Monitoring & Logging

### Prometheus Metrics

Bloom exposes Prometheus metrics at `/metrics`:

```python
# Key metrics
bloom_evaluations_total{cycle="Q4 2024"}
bloom_evaluations_active
bloom_agent_task_duration_seconds{agent="Scribe"}
bloom_agent_workload{agent="ContextMiner"}
bloom_rag_generation_duration_seconds
bloom_deadline_violations_total
bloom_system_health_score
```

**Prometheus Configuration**:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'bloom'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
    metrics_path: '/metrics'
```

### Grafana Dashboard

Import dashboard from `dashboards/grafana-bloom.json`:

**Key Panels**:
- Active evaluations over time
- Agent workload distribution
- RAG generation latency (P50, P95, P99)
- Deadline compliance rate
- System health score
- Agent failure rate

### Logging

**Structured Logging with Loguru**:

```python
from loguru import logger

# Configure logging
logger.add(
    "/var/log/bloom/bloom.log",
    rotation="500 MB",
    retention="30 days",
    compression="gz",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level="INFO"
)
```

**Log Aggregation (ELK Stack)**:

```yaml
# filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/bloom/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "bloom-%{+yyyy.MM.dd}"
```

## Backup & Recovery

### Database Backups

**PostgreSQL**:

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backup/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

pg_dump -U bloom_user -d bloom -F c -f "$BACKUP_DIR/bloom_$DATE.dump"

# Compress and upload to S3
gzip "$BACKUP_DIR/bloom_$DATE.dump"
aws s3 cp "$BACKUP_DIR/bloom_$DATE.dump.gz" s3://bloom-backups/postgres/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.dump.gz" -mtime +30 -delete
```

**Neo4j**:

```bash
neo4j-admin dump --database=neo4j --to=/backup/neo4j/bloom_$(date +%Y%m%d).dump
```

**Redis**:

```bash
# Configure Redis persistence
# In redis.conf:
save 900 1
save 300 10
save 60 10000

# Backup RDB file
cp /var/lib/redis/dump.rdb /backup/redis/dump_$(date +%Y%m%d).rdb
```

### Recovery

**PostgreSQL**:

```bash
# Restore from backup
pg_restore -U bloom_user -d bloom -c /backup/postgres/bloom_20241201.dump
```

**Neo4j**:

```bash
neo4j-admin load --from=/backup/neo4j/bloom_20241201.dump --database=neo4j --force
```

## Troubleshooting

### Common Issues

#### 1. Agent Not Starting

**Symptoms**: Agent shows as "FAILED" in orchestrator status

**Debug**:
```bash
# Check agent logs
grep "ERROR" /var/log/bloom/bloom.log | grep "agent_id"

# Check database connectivity
python scripts/test_database_connections.py

# Verify environment variables
python -c "import os; print(os.getenv('POSTGRES_URL'))"
```

**Solution**: Ensure all database connections are healthy and environment variables are set.

#### 2. RAG Generation Slow

**Symptoms**: Draft generation takes > 60 seconds

**Debug**:
```bash
# Check vector DB latency
python scripts/benchmark_vector_db.py

# Check LLM API latency
curl -w "@curl-format.txt" -o /dev/null -s https://api.openai.com/v1/models
```

**Solution**:
- Increase Scribe instance count
- Use faster embedding model
- Implement result caching

#### 3. Deadline Notifications Not Sending

**Symptoms**: Users not receiving reminders

**Debug**:
```bash
# Check Chaser agent status
curl http://localhost:8000/api/v1/agents/chaser/status

# Check notification queue
redis-cli -a $REDIS_PASSWORD LLEN notification_queue

# Test Slack connection
python scripts/test_slack_connection.py
```

**Solution**: Verify Slack credentials, check network connectivity.

#### 4. High Memory Usage

**Symptoms**: Orchestrator using > 4GB RAM

**Debug**:
```bash
# Profile memory usage
python -m memory_profiler main.py

# Check cache sizes
redis-cli -a $REDIS_PASSWORD INFO memory
```

**Solution**:
- Reduce cache TTL
- Limit concurrent evaluations
- Implement memory limits per agent

### Health Checks

**System Health Endpoint**:

```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 86400,
  "agents": {
    "watchkeeper": "IDLE",
    "scribes": [{"id": "...", "status": "IDLE", "workload": 0.2}],
    ...
  },
  "databases": {
    "postgres": "connected",
    "redis": "connected",
    "neo4j": "connected",
    "influxdb": "connected"
  }
}
```

## Security Checklist

Before going to production:

- [ ] Change all default passwords
- [ ] Generate unique `BLOOM_SECRET_KEY` and `ENCRYPTION_KEY`
- [ ] Enable HTTPS/TLS for all external connections
- [ ] Configure firewall rules (allow only necessary ports)
- [ ] Set up VPN for database access
- [ ] Enable database encryption at rest
- [ ] Configure RBAC policies
- [ ] Set up audit logging to immutable storage
- [ ] Enable rate limiting on API endpoints
- [ ] Configure CORS to allow only trusted origins
- [ ] Set up automated security scanning (Snyk, Dependabot)
- [ ] Implement secrets rotation schedule
- [ ] Configure backup encryption
- [ ] Set up intrusion detection (fail2ban, OSSEC)
- [ ] Enable 2FA for all admin accounts
- [ ] Review and minimize IAM permissions
- [ ] Configure network segmentation
- [ ] Set up DDoS protection (Cloudflare, AWS Shield)
- [ ] Implement content security policy (CSP)
- [ ] Enable security headers (HSTS, X-Frame-Options)
- [ ] Configure secure session management

---

## Next Steps

After deployment:
1. Review [API.md](./API.md) for API integration
2. Set up monitoring dashboards
3. Configure alerting rules
4. Train team on system operations
5. Establish on-call rotation
6. Document runbooks for common incidents

For development, see [DEVELOPMENT.md](./DEVELOPMENT.md).
For architecture details, see [ARCHITECTURE.md](./ARCHITECTURE.md).
