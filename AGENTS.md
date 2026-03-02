# AGENTS.md — betadvisor-app Repository Rules

> Ce fichier est la loi pour tout agent IA (Jules) opérant sur ce repo.
> **Violation d'une règle = PR refusée sans discussion.**

---

## Project

- **Stack** : Django 5 + DRF + Postgres 15 (backend) · Expo 54 + React Native 0.81 + TypeScript (mobile)
- **Monorepo** : `apps/backend/` (Python) · `apps/mobile/` (Node)
- **Python** : 3.11 — `apps/backend/requirements.txt`
- **Node** : 20 — `apps/mobile/package-lock.json`
- **manage.py** : situé dans `apps/backend/src/`

---

## Scripts CI (à exécuter avant toute PR)

### Backend
| Commande | But | Bloquant |
|----------|-----|----------|
| `python -m compileall apps/backend/src -q` | Syntax check | ✅ OUI |
| `cd apps/backend/src && python manage.py check` | System check Django | ✅ OUI |
| `cd apps/backend/src && python manage.py migrate --noinput` | Appliquer migrations | ✅ OUI |
| `cd apps/backend/src && python manage.py showmigrations` | État migrations | ✅ OUI |

### Mobile
| Commande | But | Bloquant |
|----------|-----|----------|
| `cd apps/mobile && npm ci` | Install deps | ✅ OUI |
| `cd apps/mobile && npx tsc --noEmit` | Typecheck TS | ⚠️ NON (continue-on-error) |

---

## Night Train v3 — Jules Workflow

- Jules démarre **toujours** depuis `main` (via `startingBranch: main`).
- Branches de travail : `jules/<issue-number>-<short-slug>` (ex: `jules/42-connect-account-model`).
- PRs ciblent **`main`** directement (squash merge).
- Après CI success sur une branche Jules → autoqueue valide, merge squash → main, chaîne l'issue suivante.
- **Matin** : Antigravity review les commits sur `main` + issues fermées. Pas de merge manuel nécessaire.

---

## Coding Rules

### 🔴 ENV VARS (CRITIQUE — identique à Night Train v1)

**JAMAIS** de `raise` / `throw` au top-level de module pour une env var manquante :

```python
# ✅ CORRECT — guard au niveau du handler
def my_view(request):
    key = settings.STRIPE_SECRET_KEY
    if not key:
        return Response({'error': 'Misconfigured'}, status=500)

# ❌ WRONG — casse les imports au démarrage
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
if not stripe.api_key:
    raise ValueError("Missing STRIPE_SECRET_KEY")  # ← interdit au top-level
```

### 🔴 MIGRATIONS (règle absolue)

1. **1 migration maximum par issue/PR.** Jamais 2 migrations dans la même app.
2. Ne jamais modifier une migration déjà mergée dans `main` ou `jules/train`.
3. Format : `app_name/migrations/000N_description_courte.py`
4. Si l'issue requiert 2 apps avec migration → ouvrir 2 issues séparées.

### 🔴 STRIPE (architecture)

1. **Toute logique Stripe dans `services.py` ou `webhooks.py` uniquement.** Jamais dans `views.py`.
2. Aucune clé Stripe en clair. Toujours `settings.STRIPE_SECRET_KEY`.
3. **Vérification de signature webhook OBLIGATOIRE** : `stripe.Webhook.construct_event(request.body, sig_header, settings.STRIPE_WEBHOOK_SECRET)`.
4. **Idempotence obligatoire** : `StripeEvent.objects.select_for_update().get_or_create(stripe_event_id=event['id'])` dans `transaction.atomic`.
5. **`application_fee_percent = 20` en constante explicite.** Ne pas lire depuis `settings.PLATFORM_FEE_PERCENT` (valeur par défaut incorrecte = 10).
6. CC-07 est la **seule** source de vérité pour les objets `Subscription` en DB.

### 🔴 SÉCURITÉ

1. `DEBUG=False` en production. Ne jamais committer `DEBUG=True` hors CI.
2. Pas de `ALLOWED_HOSTS = ['*']` en production.
3. Aucun secret dans le code. Toujours via `django-environ` + `.env` (jamais commité).
4. Pas de logique premium côté mobile. Contrôle d'accès = backend only via `HasActiveSubscription`.

### 🔴 CODE STYLE

1. Pas de `print()` → utiliser `import logging; logger = logging.getLogger(__name__)`.
2. Exceptions typées : `class StripeConnectError(Exception): pass` — pas de `raise Exception(...)`.
3. Chaque `services.py` est testable isolément (pas de side-effects au module-level).

---

## API Standards (Connect Core)

Tous les nouveaux endpoints sont sous `/api/*` :

| Endpoint | Issue |
|----------|-------|
| `POST /api/connect/create-account/` | CC-03 |
| `GET /api/connect/onboarding-link/` | CC-03 |
| `POST /api/subscriptions/subscribe/` | CC-06 |
| `POST /api/stripe/webhook/` | CC-07 |
| `GET /api/me/subscriptions/` | CC-08 |

L'app `finance` existante conserve son préfixe `finance/` sans modification.

---

## PR Conventions

### Titre
```
[CC-0N] feat: description courte
```
Exemple : `[CC-01] feat: ConnectedAccount model + connect app scaffold`

### Body obligatoire
```markdown
## Summary
[2-3 phrases résumant la PR]

## Issue
Closes #[NUMÉRO_GITHUB]    ← OBLIGATOIRE — l'autoqueue en dépend

## Changes
- app_name/models.py : ...
- app_name/migrations/0001_initial.py : ...

## Migration
N/A  (ou nom exact de la migration)

## CI Checklist
- [ ] python manage.py check ✅
- [ ] python manage.py migrate --noinput ✅
- [ ] python -m compileall apps/backend/src -q ✅
```

### Règle de liaison
`Closes #N` doit être présent dans le body. L'autoqueue parse ce pattern pour chaîner.
La PR doit **cibler `main`** (et non une autre branche).

---

## Issue Conventions

La première ligne d'une issue bloquée doit contenir :
```
Blocked by #<NUMÉRO_GITHUB_RÉEL>
```
**Jamais** un identifiant interne comme `CC-01` — uniquement le numéro GitHub.

---

## Interdictions absolues pour Jules

- Ne jamais push directement sur `main`
- Ne jamais modifier les fichiers `.github/workflows/`
- Ne jamais créer plus d'une migration par PR
- Ne jamais implémenter des features non décrites dans l'issue assignée
- Ne jamais appeler `stripe.*` depuis une vue (`views.py`)
- Ne jamais commiter un fichier `.env` ou tout secret

---

## Morning Review (Antigravity)

Avec Night Train v3, tout est mergé directement sur `main` (squash merge).
Pas besoin de merger un train branch ni de le reset.

```bash
# 1. Voir les commits de la nuit sur main
git fetch origin
git log --since="12 hours ago" --oneline origin/main

# 2. Issues fermées cette nuit
gh issue list --repo AAndriant/betadvisor-app --state closed \
  --json number,title,labels,closedAt \
  --jq '.[] | select(.closedAt > (now - 43200 | strftime("%Y-%m-%dT%H:%M:%SZ"))) | "#\(.number) | \(.title)"'

# 3. Issues encore ouvertes (restantes)
gh issue list --repo AAndriant/betadvisor-app --state open \
  --json number,title,labels \
  --jq '.[] | "#\(.number) | \([.labels[].name] | join(", ")) | \(.title)"'

# 4. Vérifier la queue
cat ops/night-queue.json
```

**Si Jules s'arrête en cours de nuit :**
```bash
# Re-dispatcher le train (kick le prochain issue open de la queue)
gh workflow run "Start Night Train" --ref main
```
