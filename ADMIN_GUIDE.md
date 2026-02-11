# 🛡️ Enterprise NGFW - Administrator Guide

## 🚀 Deployment Guide

### Prerequisites
- **Docker** and **Docker Compose** installed.
- **Git** (optional, for cloning).

### 1. Configuration Setup
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and set secure values for:
   - `NGFW_SECRET_KEY`: A long random string.
   - `NGFW_ADMIN_PASSWORD`: Strong password for the `admin` user.
   - `NGFW_OPERATOR_PASSWORD`: Password for the `operator` user.
   - `NGFW_ALLOWED_ORIGINS`: Set to your dashboard domain (e.g., `https://dashboard.company.com`).

### 2. Docker Deployment
Run the following command to build and start the services:
```bash
docker-compose up -d --build
```

This will start:
- **API Server** on port `8000` (http://localhost:8000).
- **Dashboard** on port `8080` (http://localhost:8080).

### 3. Verify Installation
Check if the services are healthy:
```bash
docker-compose ps
curl http://localhost:8000/api/v1/health
```

---

## 🔐 Security Best Practices

### 1. Secret Management
- **Never** commit `.env` to version control.
- Rotate `NGFW_SECRET_KEY` periodically. Note that rotating the key will invalidate all existing user tokens.

### 2. Networking
- The default `docker-compose.yml` exposes ports `8000` and `8080` directly. In a production environment, use a reverse proxy (like Nginx or Traefik) with SSL termination in front of these services.
- Ensure the firewall (e.g., AWS Security Groups, `ufw`) restricts access to these ports.

### 3. Updates
To update the application:
```bash
git pull                   # Get latest code
docker-compose build       # Rebuild images
docker-compose up -d       # Restart containers
docker image prune -f      # Clean up old images
```

---

## 🛠️ Troubleshooting

### Logs
View logs for the API:
```bash
docker-compose logs -f ngfw-api
```

### "Token has expired" Error
The JWT tokens expire after 30 minutes by default. Users will need to re-login.

### "Rate Limit Exceeded"
The API has built-in rate limiting. If you hit the limit, wait for a minute or increase the limits in `api/rest/main.py`.
