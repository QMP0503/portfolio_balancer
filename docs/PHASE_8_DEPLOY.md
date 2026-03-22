# Phase 8 — Deploy + Monitoring

> Orchestration guide for Claude Code. Work through each task in order.
> Do not skip verification steps. Commit after each working task.

---

## Pre-flight Check

Before starting, verify your current state:

```bash
docker compose up -d
docker compose ps          # all services healthy
curl http://localhost:8000/health   # backend responds
curl http://localhost:5173          # frontend responds
```

If anything is broken, fix it before proceeding.

---

## Task 8A: Nginx Reverse Proxy

**Goal:** Single entry point on port 80. Nginx serves built React static files and proxies `/api/*` to FastAPI.

### 8A-1: Check if FastAPI routes use /api prefix

**Prompt for Claude Code:**
```
Read backend/main.py and list all route prefixes.
Do any routes start with /api? Just tell me, don't change anything.
```

**Why:** Nginx is configured to proxy `/api/*` to the backend. If your routes are currently `/quotes/latest` instead of `/api/quotes/latest`, we need to add a router prefix first.

**If routes do NOT have /api prefix, run this next:**
```
Add an /api prefix to all routes in the FastAPI app.

Option A (preferred): If routes use APIRouter, add prefix="/api" to the router.
Option B: If routes are on the app directly, create a router with prefix="/api",
move all routes to it, and include it in the app.

Do NOT change the route logic — only add the prefix.
Update any frontend fetch calls that hit these endpoints to include /api.
```

**Verify:**
```bash
docker compose up -d --build
curl http://localhost:8000/api/health   # should work
curl http://localhost:8000/health       # should 404 now
```

**Commit:** `git add -A && git commit -m "phase8: add /api prefix to all routes"`

---

### 8A-2: Create Nginx config

**Prompt for Claude Code:**
```
Create nginx/nginx.conf with this exact content:

upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    # API requests → FastAPI
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check (no /api prefix for monitoring tools)
    location /health {
        proxy_pass http://backend;
    }

    # Prometheus metrics scrape endpoint
    location /metrics {
        proxy_pass http://backend;
    }

    # React SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Verify:** File exists at `nginx/nginx.conf`. No syntax to test yet.

**Commit:** `git add -A && git commit -m "phase8: add nginx config"`

---

### 8A-3: Create Nginx Dockerfile (multi-stage build)

**Prompt for Claude Code:**
```
Create nginx/Dockerfile with a multi-stage build:

Stage 1 ("build"):
- FROM node:20-alpine
- WORKDIR /app
- COPY frontend/package.json and frontend/package-lock.json
- RUN npm ci
- COPY frontend/ .
- RUN npm run build

Stage 2:
- FROM nginx:alpine
- Remove /etc/nginx/conf.d/default.conf
- COPY nginx/nginx.conf to /etc/nginx/conf.d/default.conf
- COPY --from=build /app/dist to /usr/share/nginx/html
- EXPOSE 80
- CMD nginx -g "daemon off;"

The build context will be the project root (not nginx/),
so COPY paths are relative to etf-intelligence/.
```

**Verify:** File exists at `nginx/Dockerfile`.

**Commit:** `git add -A && git commit -m "phase8: add nginx multi-stage dockerfile"`

---

### 8A-4: Create docker-compose.prod.yml

**Prompt for Claude Code:**
```
Create docker-compose.prod.yml as an override file for production.

It should:
1. Override the backend service:
   - Remove ports (Nginx handles external traffic)
   - Remove volume mount (no hot-reload in prod)
   - Set command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
   - Keep the DATABASE_URL environment variable

2. Disable the frontend service:
   - Set profiles: ["disabled"] so it doesn't start

3. Add an nginx service:
   - Build from context: . with dockerfile: nginx/Dockerfile
   - Expose port 80:80
   - depends_on: backend
   - restart: unless-stopped

Usage will be:
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

**Verify:**
```bash
# Build and run production stack
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Check all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Test through Nginx
curl http://localhost              # should return React index.html
curl http://localhost/api/health   # should return {"status":"ok"}

# Test from another device via Tailscale
curl http://<tailscale-ip>         # same results
```

**If something breaks:** check `docker compose logs nginx` first. Common issues:
- `upstream not found` → backend service name mismatch in nginx.conf
- `403 forbidden` → React build failed, /usr/share/nginx/html is empty
- `502 bad gateway` → backend isn't running or wrong port

**Commit:** `git add -A && git commit -m "phase8: add production compose with nginx"`

---

### 8A-5: Update .gitignore

**Prompt for Claude Code:**
```
Check .gitignore exists and includes these entries (add any that are missing):
.env
node_modules/
__pycache__/
*.pyc
dist/
```

**Commit:** `git add -A && git commit -m "phase8: update gitignore"`

---

## Task 8B: Prometheus + Grafana Monitoring

**Goal:** Instrument FastAPI with metrics, add Prometheus + Grafana + node_exporter to Docker Compose.

### 8B-1: Add Prometheus metrics to FastAPI

**Prompt for Claude Code:**
```
Add prometheus-fastapi-instrumentator to the backend.

1. Add "prometheus-fastapi-instrumentator" to backend/requirements.txt

2. In backend/main.py:
   - Import Instrumentator from prometheus_fastapi_instrumentator
   - After creating the FastAPI app, add:
     Instrumentator().instrument(app).expose(app)
   - This auto-exposes a /metrics endpoint

Do NOT change any existing endpoints or logic.
```

**Verify:**
```bash
docker compose up -d --build
curl http://localhost:8000/metrics
# Should return Prometheus-format text with http_request_duration_seconds etc.
```

**Commit:** `git add -A && git commit -m "phase8: add prometheus metrics to fastapi"`

---

### 8B-2: Add custom ingestion metrics

**Prompt for Claude Code:**
```
Add custom Prometheus metrics to the ingestion pipeline.

In backend/ingestion/scheduler.py (or wherever the fetch cycle runs):

1. Import prometheus_client:
   from prometheus_client import Counter, Histogram, Gauge

2. Define these metrics at module level:
   FETCH_LATENCY = Histogram(
       "etf_fetch_latency_seconds",
       "Time to fetch quote data from yfinance",
       labelnames=["ticker"]
   )
   FETCH_SUCCESS = Counter(
       "etf_fetch_success_total",
       "Successful fetches",
       labelnames=["ticker"]
   )
   FETCH_FAILURE = Counter(
       "etf_fetch_failure_total",
       "Failed fetches",
       labelnames=["ticker"]
   )
   ROWS_INSERTED = Counter(
       "etf_rows_inserted_total",
       "Rows inserted into TimescaleDB",
       labelnames=["ticker"]
   )
   LAST_FETCH_TIME = Gauge(
       "etf_last_fetch_timestamp",
       "Unix timestamp of last successful fetch",
       labelnames=["ticker"]
   )

3. Wrap the existing fetch logic:
   - Time each fetch with FETCH_LATENCY.labels(ticker=t).observe(duration)
   - Increment FETCH_SUCCESS or FETCH_FAILURE on result
   - Increment ROWS_INSERTED after DB insert
   - Set LAST_FETCH_TIME after success

Do NOT restructure the fetch logic. Just wrap the existing code
with metric calls.
```

**Verify:**
```bash
docker compose up -d --build
# Trigger a fetch cycle (or wait for scheduler)
curl http://localhost:8000/metrics | grep etf_
# Should see etf_fetch_latency_seconds, etf_fetch_success_total, etc.
```

**Commit:** `git add -A && git commit -m "phase8: add custom prometheus metrics to ingestion"`

---

### 8B-3: Create Prometheus config

**Prompt for Claude Code:**
```
Create monitoring/prometheus.yml:

global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "fastapi"
    static_configs:
      - targets: ["backend:8000"]

  - job_name: "node"
    static_configs:
      - targets: ["node-exporter:9100"]
```

**Verify:** File exists at `monitoring/prometheus.yml`.

**Commit:** `git add -A && git commit -m "phase8: add prometheus config"`

---

### 8B-4: Create Grafana provisioning

**Prompt for Claude Code:**
```
Create two Grafana provisioning files:

1. monitoring/grafana/provisioning/datasources/prometheus.yml:

apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

2. monitoring/grafana/provisioning/dashboards/dashboard.yml:

apiVersion: 1
providers:
  - name: Default
    orgId: 1
    folder: ''
    type: file
    options:
      path: /var/lib/grafana/dashboards

These auto-configure Grafana on first boot so you don't have to
click through the UI to add Prometheus as a data source.
```

**Verify:** Both files exist in the right paths.

**Commit:** `git add -A && git commit -m "phase8: add grafana provisioning"`

---

### 8B-5: Add monitoring services to docker-compose.prod.yml

**Prompt for Claude Code:**
```
Add three services to docker-compose.prod.yml:

1. prometheus:
   - image: prom/prometheus:latest
   - volumes: ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
   - ports: 9090:9090 (we'll remove this later, just for debugging)
   - restart: unless-stopped

2. grafana:
   - image: grafana/grafana:latest
   - volumes:
     - grafana_data:/var/lib/grafana
     - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
   - ports: 3000:3000
   - environment:
     - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
   - depends_on: prometheus
   - restart: unless-stopped

3. node-exporter:
   - image: prom/node-exporter:latest
   - restart: unless-stopped
   (no ports needed — Prometheus scrapes it internally)

Also add grafana_data to the volumes section.

Do NOT modify any existing services.
```

**Verify:**
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Check all services running
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Test Prometheus targets
curl http://localhost:9090/api/v1/targets
# Both "fastapi" and "node" jobs should show state: "up"

# Test Grafana
# Open http://localhost:3000 (or Tailscale IP)
# Login: admin / admin (or whatever GRAFANA_PASSWORD is set to)
# Go to Explore → select Prometheus → query: up
# Should show 2 targets
```

**Commit:** `git add -A && git commit -m "phase8: add prometheus, grafana, node-exporter to prod compose"`

---

### 8B-6: Add Nginx routes for monitoring (optional)

**Prompt for Claude Code:**
```
Add these location blocks to nginx/nginx.conf, BEFORE the
React SPA catch-all location / block:

    # Grafana dashboard
    location /grafana/ {
        proxy_pass http://grafana:3000/;
        proxy_set_header Host $host;
    }

Also add to the grafana service environment in docker-compose.prod.yml:
    - GF_SERVER_ROOT_URL=http://localhost/grafana
    - GF_SERVER_SERVE_FROM_SUB_PATH=true

This lets you access Grafana at http://<your-ip>/grafana
instead of remembering port 3000.
```

**Verify:**
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
curl http://localhost/grafana/login   # should return Grafana login page HTML
```

**Commit:** `git add -A && git commit -m "phase8: route grafana through nginx"`

---

## Task 8C: Public Access (do when ready to share)

Two options. Pick one.

### Option 1: Tailscale Funnel (simpler, 2 commands)

```bash
# On your server
sudo tailscale funnel 80
```

That's it. Tailscale gives you a public URL like `https://your-machine.tailnet-name.ts.net`.
Free, auto-HTTPS, zero DNS config. Downside: URL isn't customizable.

### Option 2: DuckDNS + Let's Encrypt (better resume story)

**Step 1:** Go to duckdns.org, create a subdomain (e.g. `quang-etf.duckdns.org`).

**Step 2:** Prompt for Claude Code:
```
Create a DuckDNS update script at scripts/duckdns-update.sh:

#!/bin/bash
DOMAIN="YOUR_SUBDOMAIN"
TOKEN="YOUR_DUCKDNS_TOKEN"
curl -s "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip="

Add a cron job that runs this every 5 minutes to keep the DNS updated.
```

**Step 3:** Prompt for Claude Code:
```
Add HTTPS to the Nginx setup using certbot.

1. Add a certbot service to docker-compose.prod.yml:
   - image: certbot/certbot
   - volumes:
     - certbot_etc:/etc/letsencrypt
     - certbot_var:/var/lib/letsencrypt
     - ./nginx/webroot:/var/www/certbot

2. Update nginx/nginx.conf:
   - Add a location /.well-known/acme-challenge/ block
     that serves from /var/www/certbot
   - Add a second server block listening on 443 with:
     ssl_certificate /etc/letsencrypt/live/YOUR_DOMAIN/fullchain.pem
     ssl_certificate_key /etc/letsencrypt/live/YOUR_DOMAIN/privkey.pem
   - Redirect port 80 to 443

3. Add certbot volumes to the nginx service too.
```

**Step 4:** Run certbot:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm certbot \
  certonly --webroot --webroot-path=/var/www/certbot \
  -d your-subdomain.duckdns.org --email your@email.com --agree-tos

# Restart nginx to pick up the cert
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart nginx
```

---

## Task 8D: README + Benchmarks

**Prompt for Claude Code:**
```
Read MASTER_PLAN.md, then create/update README.md at the project root.

Include these sections:
1. One-line description (from MASTER_PLAN.md)
2. Screenshot placeholder (we'll add later)
3. Architecture overview — the three layers
4. Tech stack table
5. Performance benchmarks section with placeholder values:
   - Ingestion latency per cycle
   - Dashboard load time (cached)
   - Historical query time (2M rows)
   - Rebalancer compute time
6. Setup instructions:
   - Prerequisites (Docker, Docker Compose)
   - Clone, create .env, docker compose up
   - Access URLs (localhost, Tailscale, public if configured)
7. Project structure (from MASTER_PLAN.md file tree)

Keep it concise. No fluff. Write it like a senior engineer's README.
```

**Verify:** Read the README. Make sure setup instructions actually work by following them on a clean checkout.

**Commit:** `git add -A && git commit -m "phase8: add README with benchmarks"`

---

## Final File Structure After Phase 8

```
etf-intelligence/
├── nginx/
│   ├── nginx.conf
│   └── Dockerfile
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
│       └── provisioning/
│           ├── datasources/prometheus.yml
│           └── dashboards/dashboard.yml
├── scripts/
│   └── duckdns-update.sh          # only if using DuckDNS
├── docker-compose.yml              # dev (unchanged)
├── docker-compose.prod.yml         # production overlay
├── README.md
└── ... (existing project files)
```

---

## Status Checklist

```
[ ] 8A-1  FastAPI routes prefixed with /api
[ ] 8A-2  nginx.conf created
[ ] 8A-3  Nginx Dockerfile created
[ ] 8A-4  docker-compose.prod.yml working — app accessible on port 80
[ ] 8A-5  .gitignore updated
[ ] 8B-1  FastAPI /metrics endpoint working
[ ] 8B-2  Custom ingestion metrics emitting
[ ] 8B-3  Prometheus config created
[ ] 8B-4  Grafana provisioning created
[ ] 8B-5  Monitoring stack running — Prometheus targets up
[ ] 8B-6  Grafana accessible through Nginx (optional)
[ ] 8C    Public access configured (when ready)
[ ] 8D    README written
```
