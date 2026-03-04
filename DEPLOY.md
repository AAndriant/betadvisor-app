# BetAdvisor — Production Deployment Guide

## Architecture Overview

```
┌───────────────┐   HTTPS    ┌───────────┐      ┌──────────────┐
│   Mobile App  │ ──────────▶│   Caddy   │─────▶│  Django API  │
│  (Expo/RN)    │            │  (HTTPS)  │      │  (Gunicorn)  │
└───────────────┘            └───────────┘      └──────┬───────┘
                                                       │
                              ┌─────────────┐          │
                              │ PostgreSQL  │◀─────────┘
                              │   15        │
                              └─────────────┘
```

## Prerequisites

- Docker & Docker Compose v2+
- A VPS with at least 2GB RAM, 2 vCPU
- A domain name (e.g., `api.betadvisor.app`)
- DNS pointed to your server's IP

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/AAndriant/betadvisor-app.git
cd betadvisor-app
cp apps/backend/.env.example apps/backend/.env.prod
```

### 2. Edit `.env.prod` with production values

```bash
# Required production values:
DEBUG=False
SECRET_KEY=<generate-with-python-secrets>
ALLOWED_HOSTS=api.betadvisor.app
DATABASE_URL=postgres://betadvisor:<strong-password>@postgres:5432/betadvisor

# Stripe LIVE keys
STRIPE_LIVE_SECRET_KEY=sk_live_...
STRIPE_LIVE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_PLATFORM_ACCOUNT_ID=acct_...

# Sports API
API_SPORTS_KEY=<your-api-sports-key>

# Email (use SendGrid, Mailgun, etc.)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<sendgrid-api-key>
EMAIL_USE_TLS=True

# CORS
CORS_ALLOWED_ORIGINS=https://betadvisor.app
```

### 3. Configure Caddy for HTTPS

Edit `Caddyfile`:
```
api.betadvisor.app {
    reverse_proxy backend:8000
    handle_path /media/* {
        root * /srv/media
        file_server
    }
}
```

### 4. Generate a strong SECRET_KEY

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 5. Deploy

```bash
# Set PostgreSQL password
export POSTGRES_PASSWORD=<strong-db-password>

# Build and start
docker compose -f docker-compose.prod.yml up -d --build

# Check logs
docker compose -f docker-compose.prod.yml logs -f backend

# Create superuser
docker compose -f docker-compose.prod.yml exec backend \
    python src/manage.py createsuperuser
```

### 6. Set up Stripe webhook

Point your Stripe webhook to:
```
https://api.betadvisor.app/api/stripe/webhook/
```

Events to listen for:
- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

### 7. Set up the settlement cron

```bash
# Add to crontab on the server
*/10 * * * * docker compose -f /path/to/docker-compose.prod.yml exec -T backend \
    python src/manage.py settle_predictions >> /var/log/betadvisor-settle.log 2>&1
```

## Health Check

```bash
curl https://api.betadvisor.app/api/health/
# Expected: {"status": "ok"}
```

## Maintenance

### View logs
```bash
docker compose -f docker-compose.prod.yml logs -f --tail=100
```

### Database backup
```bash
docker compose -f docker-compose.prod.yml exec postgres \
    pg_dump -U betadvisor betadvisor > backup_$(date +%Y%m%d).sql
```

### Update deployment
```bash
git pull origin main
docker compose -f docker-compose.prod.yml up -d --build
```

## Recommended VPS Providers

| Provider | Plan | Price | Notes |
|----------|------|-------|-------|
| **Railway** | Pro | ~$20/mo | Easiest Docker deploy, auto-scaling |
| **Render** | Standard | ~$25/mo | Good DX, managed PostgreSQL available |
| **DigitalOcean** | Droplet 2GB | $18/mo | Full control, affordable |
| **Fly.io** | 2x shared-cpu | ~$15/mo | Edge deploy, good latency |
| **Hetzner** | CPX21 | €7.99/mo | Best price/perf in EU |

**Recommendation for BetAdvisor startup**: Start with **Hetzner CPX21** (2 vCPU, 4GB RAM, €7.99/mo) or **DigitalOcean $18/mo** for best value. Move to Railway/Render for zero-ops once revenue grows.
