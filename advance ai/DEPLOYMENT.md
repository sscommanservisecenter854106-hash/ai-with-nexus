# 🚀 NEXUS-AI: Production & Cloud Deployment Guide

Nexus-AI is designed to run seamlessly in any cloud or on-premise environment with zero external database requirements (self-contained SQLite + in-memory BM25 vector index).

---

## 📋 Table of Contents
1. [Deployment Options Overview](#-deployment-options-overview)
2. [Option 1: Render.com (Recommended Free Cloud Hosting)](#option-1-rendercom-recommended-free-cloud-hosting)
3. [Option 2: Docker & Docker Compose](#option-2-docker--docker-compose)
4. [Option 3: Railway.app](#option-3-railwayapp)
5. [Option 4: Hugging Face Spaces (Docker)](#option-4-hugging-face-spaces-docker)
6. [Option 5: Self-Hosted Linux VPS (Ubuntu/Debian + Nginx + Systemd)](#option-5-self-hosted-linux-vps-ubuntudebian--nginx--systemd)
7. [Environment Variables Reference](#-environment-variables-reference)

---

## 🌐 Deployment Options Overview

| Platform | Cost | Configuration Required | Health Check |
|---|---|---|---|
| **Render** | Free tier available | 1-Click (`render.yaml` included) | `/api/status` |
| **Docker Compose** | Free / Local / VPS | Zero-config (`docker-compose.yml`) | Built-in container healthcheck |
| **Railway** | Free trial / Pay-as-you-go | `Procfile` included | Auto-detected |
| **Hugging Face** | Free CPU tier | Docker SDK (`Dockerfile` included) | Built-in |
| **Self-Hosted VPS** | $3.50 - $5 / mo (Hetzner/DigitalOcean) | Systemd + Nginx | Complete control & privacy |

---

## Option 1: Render.com (Recommended Free Cloud Hosting)

Render provides free hosting for web services with automatic TLS/SSL and Git-based continuous deployment.

### Steps:
1. Push this repository to GitHub or GitLab.
2. Log into [Render.com](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Connect your GitHub repository.
5. Render will automatically detect [`render.yaml`](file:///c:/Users/Raghu/Downloads/advance%20ai/render.yaml) and configure:
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server.app:app --host 0.0.0.0 --port $PORT`
6. Click **Apply Blueprint**.
7. Once deployed, Render will provide your public URL (e.g. `https://nexus-ai.onrender.com`).

---

## Option 2: Docker & Docker Compose

Nexus-AI comes pre-configured with a production-grade multi-stage Dockerfile and Docker Compose definition.

### Single-Command Run:
```bash
docker compose up -d --build
```

### Inspect Container:
```bash
docker compose ps
docker compose logs -f
```

### Access Platform:
Open your browser at **`http://localhost:8000`**.

### Persistent Volumes:
Data, SQLite conversation history, and uploaded knowledge base documents are stored in the persistent volume `nexus_data` mapped to `/app/data`.

---

## Option 3: Railway.app

1. Fork or push this repository to GitHub.
2. In [Railway.app](https://railway.app), click **New Project** -> **Deploy from GitHub repo**.
3. Railway detects [`Procfile`](file:///c:/Users/Raghu/Downloads/advance%20ai/Procfile):
   ```procfile
   web: uvicorn server.app:app --host 0.0.0.0 --port $PORT
   ```
4. In Railway Settings -> Networking, click **Generate Domain**.
5. Your application is live immediately!

---

## Option 4: Hugging Face Spaces (Docker)

1. Create a new Space on [Hugging Face](https://huggingface.co/new-space).
2. Select **Space SDK**: `Docker` -> **Blank**.
3. Push your repository code to the Hugging Face Space Git remote:
   ```bash
   git remote add space https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
   git push space main
   ```
4. Hugging Face will automatically build and run the provided [`Dockerfile`](file:///c:/Users/Raghu/Downloads/advance%20ai/Dockerfile) on free cloud compute.

---

## Option 5: Self-Hosted Linux VPS (Ubuntu/Debian + Nginx + Systemd)

For complete privacy and control, run Nexus-AI as a systemd service behind Nginx reverse proxy.

### 1. Install System Dependencies & Python 3.11+:
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv nginx git
```

### 2. Clone & Setup Virtual Environment:
```bash
git clone <your-repo-url> /opt/nexus-ai
cd /opt/nexus-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Create Systemd Service (`/etc/systemd/system/nexus-ai.service`):
```ini
[Unit]
Description=Nexus-AI Autonomous Platform
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/nexus-ai
Environment="PATH=/opt/nexus-ai/venv/bin"
ExecStart=/opt/nexus-ai/venv/bin/uvicorn server.app:app --host 127.0.0.1 --port 8000 --workers 2

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nexus-ai
sudo systemctl status nexus-ai
```

### 4. Configure Nginx Reverse Proxy with WebSocket Support (`/etc/nginx/sites-available/nexus-ai`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        
        # WebSocket headers
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }
}
```

Enable site and secure with free Let's Encrypt SSL:
```bash
sudo ln -s /etc/nginx/sites-available/nexus-ai /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🔑 Environment Variables Reference

All settings can be configured via environment variables in cloud dashboards:

| Variable | Default | Description |
|---|---|---|
| `PORT` | `8000` | Port for ASGI Uvicorn server |
| `ACTIVE_PROVIDER` | `local` | Active LLM engine (`local`, `ollama`, `gemini`, `openai`, `groq`) |
| `GEMINI_API_KEY` | `""` | Google Gemini API Key (Optional) |
| `OPENAI_API_KEY` | `""` | OpenAI API Key (Optional) |
| `GROQ_API_KEY` | `""` | Groq API Key (Optional) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama local endpoint URL |
| `TEMPERATURE` | `0.7` | Model creativity temperature (0.0 - 1.0) |
| `PYTHONUNBUFFERED` | `1` | Stream console logs without buffering |
