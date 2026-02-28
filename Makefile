# =============================================================
# BetAdvisor Monorepo — Makefile root
# =============================================================
# Usage : make <commande>
# Pré-requis : Docker, Node.js 20+, npm
# =============================================================

.PHONY: help up down logs migrate backend-sh mobile ci-mobile ci-backend

# Aide par défaut
help:
	@echo ""
	@echo "BetAdvisor Monorepo — Commandes disponibles :"
	@echo ""
	@echo "  Docker / Backend :"
	@echo "    make up            Démarrer postgres + backend (build incl.)"
	@echo "    make down          Arrêter tous les services"
	@echo "    make logs          Suivre les logs en temps réel (200 lignes)"
	@echo "    make migrate       Appliquer les migrations Django"
	@echo "    make backend-sh    Ouvrir un shell dans le container backend"
	@echo ""
	@echo "  Mobile :"
	@echo "    make mobile        Installer les deps + démarrer Expo"
	@echo ""
	@echo "  CI locaux :"
	@echo "    make ci-mobile     npm ci + tsc --noEmit (mobile)"
	@echo "    make ci-backend    compileall + manage.py check (backend, SQLite)"
	@echo ""

# ─── Docker / Backend ───────────────────────────────────────

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose exec backend sh -c "cd src && python manage.py migrate"

backend-sh:
	docker compose exec backend sh

# ─── Mobile ─────────────────────────────────────────────────

mobile:
	cd apps/mobile && npm ci && npx expo start

# ─── CI locaux ──────────────────────────────────────────────

ci-mobile:
	cd apps/mobile && npm ci && npx tsc --noEmit

ci-backend:
	pip install -r apps/backend/requirements.txt && \
	python -m compileall apps/backend/src -q && \
	cd apps/backend/src && \
	DEBUG=True \
	SECRET_KEY=local-ci-dummy-key \
	DATABASE_URL=sqlite:///tmp/ci.db \
	STRIPE_PUBLISHABLE_KEY=pk_test_dummy \
	STRIPE_SECRET_KEY=sk_test_dummy \
	STRIPE_WEBHOOK_SECRET=whsec_dummy \
	GEMINI_API_KEY=dummy \
	python manage.py check
