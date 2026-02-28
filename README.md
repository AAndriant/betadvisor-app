# BetAdvisor — Monorepo

Monorepo consolidant le backend Django et l'application mobile React Native/Expo pour la plateforme BetAdvisor.

## Architecture

```
betadvisor-app/
├── apps/
│   ├── backend/          # API Django REST Framework
│   │   ├── src/          # Code source Django (apps, config, manage.py)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.example
│   │   └── docker-compose.backend.yml  # Compose isolé (dev backend seul)
│   └── mobile/           # Application React Native / Expo
│       ├── app/          # Écrans (expo-router file-based)
│       ├── src/          # Services, hooks, composants
│       ├── package.json
│       └── .env.example
├── docker-compose.yml    # Orchestration root (postgres + backend)
├── .github/
│   └── workflows/
│       ├── backend.yml   # CI backend (path filter: apps/backend/**)
│       └── mobile.yml    # CI mobile  (path filter: apps/mobile/**)
└── README.md
```

## Démarrage rapide

### Backend (via Docker)

```bash
# 1. Configurer l'environnement backend
cp apps/backend/.env.example apps/backend/.env
# Éditer apps/backend/.env avec vos clés réelles

# 2. Lancer postgres + backend
docker compose up --build

# L'API est disponible sur : http://localhost:8000
# Admin Django : http://localhost:8000/admin
```

### Mobile (React Native / Expo)

```bash
# 1. Configurer l'environnement mobile
cp apps/mobile/.env.example apps/mobile/.env
# Éditer apps/mobile/.env si nécessaire

# 2. Installer les dépendances
cd apps/mobile
npm install

# 3. Démarrer le bundler Expo
npx expo start
```

## Variables d'Environnement

### Backend (`apps/backend/.env`)

Basé sur `apps/backend/.env.example` :

| Variable | Description |
|----------|-------------|
| `DEBUG` | `True` en dev, `False` en prod |
| `SECRET_KEY` | Clé secrète Django (longue et aléatoire) |
| `DATABASE_URL` | URL PostgreSQL complète |
| `GEMINI_API_KEY` | Clé Google Gemini AI (OCR tickets) |
| `STRIPE_SECRET_KEY` | Clé secrète Stripe |
| `STRIPE_PUBLISHABLE_KEY` | Clé publique Stripe |
| `STRIPE_WEBHOOK_SECRET` | Secret webhook Stripe |

### Mobile (`apps/mobile/.env`)

Basé sur `apps/mobile/.env.example` :

| Variable | Description |
|----------|-------------|
| `EXPO_PUBLIC_API_URL` | URL de base de l'API backend |

> **Note :** Les variables `EXPO_PUBLIC_*` sont intégrées dans le bundle Expo et visibles côté client. Ne jamais y placer de secrets.

## CI / CD

Les workflows GitHub Actions utilisent du **path filtering** :

- **`backend.yml`** : déclenché uniquement si `apps/backend/**` ou le workflow lui-même change
- **`mobile.yml`** : déclenché uniquement si `apps/mobile/**` ou le workflow lui-même change

## Notes techniques

### Historique Git

Le monorepo conserve l'**historique complet** des deux dépôts source via `git merge --allow-unrelated-histories`. Les commits originaux sont visibles via `git log --graph --all`.

### Migrations Django — Note de migration

Le conflit de migrations `tickets/0002` (deux branches parallèles de migration créées par Jules agent) a été résolu **avant la migration monorepo** via `--fake` apply de la branche non appliquée. Toutes les migrations sont marquées `[X]` en DB. Voir le rapport d'audit pré-monorepo pour les détails.

### Mac Silicon (M1/M2/M3)

Le `docker-compose.yml` root inclut `security_opt: seccomp:unconfined` pour permettre aux threads de la librairie Google AI de fonctionner correctement sur architecture ARM.

## Accès API principaux

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/token/` | Obtenir JWT |
| `POST /api/auth/token/refresh/` | Rafraîchir JWT |
| `GET /api/bets/` | Feed global des paris |
| `GET /api/me/` | Profil utilisateur connecté |
| `GET /api/users/leaderboard/` | Classement des tipsters |
| `POST /api/tickets/upload/` | Upload ticket image (OCR async) |
| `GET /api/tickets/<uuid>/status/` | Statut OCR ticket |
