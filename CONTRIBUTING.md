# Contributing — BetAdvisor Monorepo

Bienvenue dans le monorepo BetAdvisor. Ce document définit les règles de collaboration pour les équipes humaines et les agents IA (Antigravity, Jules).

---

## 1. Architecture du monorepo

```
betadvisor-app/
├── apps/
│   ├── backend/     # API Django REST Framework (Python 3.11)
│   └── mobile/      # Application React Native / Expo 54
├── .github/
│   └── workflows/   # CI path-filtered (backend.yml / mobile.yml)
├── docker-compose.yml   # Orchestration dev root
├── Makefile             # Raccourcis commandes
└── CONTRIBUTING.md      # Ce fichier
```

### Règle fondamentale

> Chaque app est **autonome**. Le code de `apps/backend/` ne doit jamais importer de `apps/mobile/` et vice-versa.

---

## 2. Conventions Git

### Branches

| Préfixe | Usage |
|---------|-------|
| `feat/` | Nouvelle fonctionnalité |
| `fix/` | Correction de bug |
| `chore/` | Tâche technique (CI, deps, config) |
| `docs/` | Documentation uniquement |
| `test/` | Ajout ou modification de tests |

**Règles :**
- Branches courtes et atomiques (1 PR = 1 objectif)
- Nommer clairement : `feat/leaderboard-pagination`, `fix/cors-port-8083`
- PR obligatoire vers `main` — pas de push direct sur `main`
- Supprimer la branche après merge

### Commits

Format : `<type>(<scope>): <description courte>`

```
feat(backend): add ROI caching on UserGlobalStats
fix(mobile): correct pollTicketStatus endpoint prefix
chore(ci): add postgres service to backend workflow
docs(readme): add dev vs prod section
```

Types valides : `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `ci`

Scopes courants : `backend`, `mobile`, `ci`, `docker`, `readme`, `deps`

---

## 3. Règles Migrations Django

> ⚠️ Les migrations mal gérées sont l'une des sources d'incidents les plus courantes.

### Règle absolue

**1 branche de feature = 1 série linéaire de migrations.**

Ne jamais créer deux migrations `0002_*` en parallèle sur deux branches simultanées (cf. incident tickets/0002 documenté dans le rapport d'audit pré-monorepo).

### Procédure standard

```bash
# 1. Vérifier l'état avant de créer une migration
make migrate  # ou : docker compose exec backend sh -c "cd src && python manage.py showmigrations"

# 2. Créer la migration depuis le container
docker compose exec backend sh -c "cd src && python manage.py makemigrations <app_name>"

# 3. Vérifier le fichier généré AVANT de committer
# 4. Appliquer en dev et vérifier showmigrations
# 5. Committer migration + code ensemble dans le même commit
```

### En cas de conflit de migration

1. **Ne pas supprimer** les migrations conflictuelles
2. Créer une migration de merge : `python manage.py makemigrations --merge`
3. Documenter dans le message de commit : `fix(backend): merge migration conflict on tickets/0002`
4. Vérifier `showmigrations` affiche `[X]` pour toutes les migrations

---

## 4. CI Path-Filtering

La CI ne se déclenche que si les fichiers concernés sont modifiés :

| Workflow | Déclenché si |
|----------|-------------|
| `backend.yml` | `apps/backend/**` ou `.github/workflows/backend.yml` |
| `mobile.yml` | `apps/mobile/**` ou `.github/workflows/mobile.yml` |

**Implication :** une PR qui modifie uniquement `README.md` ou `Makefile` ne déclenche aucun workflow CI. C'est intentionnel pour optimiser les ressources GitHub Actions.

---

## 5. Workflow Agents IA

### Antigravity (jour — pair programming)

- Implémentation de features complexes
- Refactorisation architecturale
- Mise en place CI/CD, Docker, infra
- Revue de code et corrections structurelles
- Documentation technique

### Jules (nuit — issues atomiques)

- Issues courtes et bien définies
- Tests unitaires (+1 test par issue)
- Documentation inline (docstrings)
- Petites corrections de bugs documentées
- **Interdit :** modifier `settings.py`, `docker-compose.yml`, les workflows CI, ou les migrations existantes sans validation humaine

### Règles communes aux deux agents

- ❌ **Jamais committer de secrets réels** (clés API, mots de passe)
- ❌ **Jamais modifier les fichiers `.env`** (créer/modifier `.env.example` uniquement)
- ❌ **Jamais de force push** sur `main` ou sur une branche ouverte
- ✅ **Toujours travailler via issues** (référencer le numéro dans le commit)
- ✅ **Toujours vérifier** `git status` avant commit
- ✅ **Toujours vérifier** que les migrations sont cohérentes avant PR

---

## 6. Commandes locales rapides

```bash
# Voir toutes les commandes disponibles
make help

# Lancer le backend en local
make up

# Lancer le mobile
make mobile

# Vérification CI backend en local (sans Docker)
make ci-backend

# Vérification CI mobile en local
make ci-mobile

# Ouvrir un shell dans le backend
make backend-sh

# Appliquer les migrations
make migrate
```

---

## 7. Environnement local

### Backend

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/backend/.env.db.example apps/backend/.env.db
# Éditer les deux fichiers avec vos valeurs réelles
```

### Mobile

```bash
cp apps/mobile/.env.example apps/mobile/.env
# Éditer EXPO_PUBLIC_API_URL si nécessaire
```

---

## 8. Sécurité

- Les fichiers `.env` et `.env.db` sont dans `.gitignore` — ils ne doivent **jamais** apparaître dans un diff
- Les fichiers `.env.example` et `.env.db.example` sont la seule référence committée
- En cas de commit accidentel d'un secret : contacter immédiatement l'équipe et invalider la clé

---

*Document maintenu par Antigravity & l'équipe BetAdvisor — 28/02/2026*
