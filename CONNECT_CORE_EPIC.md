# CONNECT CORE EPIC — BetAdvisor V2
## Stripe Connect Express — Monetisation Marketplace

> **Date de création :** 2026-02-28  
> **Owner :** Product Owner → Antigravity → Jules (Night Train)  
> **Stack :** Django 5 + DRF + Postgres 15 + Expo (React Native)  
> **Epic label :** `epic:connect-core`  
> **Horizon bêta payante :** 30 jours  
> **Version :** v2 — corrections train-proof (2026-02-28)

---

## 0. DÉCISIONS STANDARDS (figées, non négociables)

| Décision | Valeur | Rationale |
|----------|--------|-----------|
| **Préfixe URL** | `/api/*` pour TOUS les nouveaux endpoints | L'app `finance` existante garde `finance/` sans modification |
| **Subscribe URL** | `POST /api/subscriptions/subscribe/` | Évite collision avec `finance/` |
| **Webhook URL** | `POST /api/stripe/webhook/` | Hors DRF parsers — raw body requis |
| **Fee plateforme** | `application_fee_percent=20` en constante | `settings.PLATFORM_FEE_PERCENT` par défaut = 10 → dangereux |
| **Source of truth DB** | Webhook CC-07 uniquement crée/modifie `Subscription` | CC-06 ne write jamais en DB |
| **Events webhook gérés** | `checkout.session.completed`, `invoice.paid`, `invoice.payment_failed`, `customer.subscription.deleted`, `account.updated` | Cycle de vie complet |
| **Numérotation GitHub** | Les `Blocked by` dans les issues utilisent les numéros GitHub réels (ex: `#42`) | Le bootstrap.sh gère le mapping CC-xx → numéro réel |

---

## 1. PÉRIMÈTRE DE L'EPIC

Le modèle économique de BetAdvisor repose sur :

| Acteur | Rôle Stripe | Flux |
|--------|-------------|------|
| BetAdvisor Platform | Platform Account | Collecte 20% sur chaque abonnement |
| Tipster | Connected Account (Express) | Reçoit 80% via `transfer_data` |
| Follower | Customer | Paie un abonnement mensuel récurrent |

**Split automatique** via `application_fee_percent=20` sur chaque `checkout.session` en mode `subscription`.

---

## 2. LISTE COMPLÈTE DES ISSUES ATOMIQUES

### ISSUE #CC-01 — App Django `connect` : scaffold et ConnectedAccount model

**Label :** `epic:connect-core` `ready` `stripe`  
**Estimated complexity :** S (1 migration, pas de dépendances)

#### Goal
Créer l'app Django `connect/` et le model `ConnectedAccount` qui lie un `CustomUser` à son compte Stripe Express.

#### Acceptance Criteria
- [ ] App `connect` créée et enregistrée dans `INSTALLED_APPS`
- [ ] Model `ConnectedAccount` avec champs :
  - `user` → `OneToOneField(CustomUser, on_delete=CASCADE, related_name='connected_account')`
  - `stripe_account_id` → `CharField(max_length=64, unique=True)`
  - `charges_enabled` → `BooleanField(default=False)`
  - `payouts_enabled` → `BooleanField(default=False)`
  - `onboarding_completed` → `BooleanField(default=False)`
  - `created_at` → `DateTimeField(auto_now_add=True)`
  - `updated_at` → `DateTimeField(auto_now=True)`
- [ ] Migration générée et propre (`0001_initial.py` uniquement)
- [ ] `__str__` retourne `f"{self.user.username} — {self.stripe_account_id}"`
- [ ] Admin Django enregistré pour inspection
- [ ] `python manage.py check` passe sans erreur

#### Definition of Done
Migration `connect/0001_initial.py` appliquée proprement. Admin accessible. Aucun autre fichier modifié.

---

### ISSUE #CC-02 — Service Stripe : `StripeConnectService` (création account + onboarding link)

**Label :** `epic:connect-core` `ready` `stripe` `security`  
**Blocked by :** #CC-01  
**Estimated complexity :** S

#### Goal
Créer `connect/services.py` avec la logique Stripe isolée (pas dans les vues). Deux fonctions : création d'un Express Account et génération d'un Account Link.

#### Acceptance Criteria
- [ ] Fichier `connect/services.py` créé
- [ ] Fonction `create_express_account(user)` :
  - Appelle `stripe.Account.create(type='express', ...)`
  - Sauvegarde `ConnectedAccount` avec le `stripe_account_id` retourné
  - Retourne l'instance `ConnectedAccount`
  - Lève `StripeConnectError` (exception custom) si l'account existe déjà
- [ ] Fonction `create_onboarding_link(stripe_account_id, return_url, refresh_url)` :
  - Appelle `stripe.AccountLink.create(...)`
  - Retourne l'URL d'onboarding
- [ ] Aucune clé Stripe en dur — utilise `settings.STRIPE_SECRET_KEY`
- [ ] Log structuré sur erreur Stripe (pas de `print`)
- [ ] `python manage.py check` passe

#### Definition of Done
`connect/services.py` testable via shell Django. Aucune migration. Aucune vue.

---

### ISSUE #CC-03 — Endpoints REST : `POST /api/connect/create-account/` et `GET /api/connect/onboarding-link/`

**Label :** `epic:connect-core` `ready` `stripe`  
**Blocked by :** #CC-02  
**Estimated complexity :** S

#### Goal
Exposer les deux endpoints Connect via DRF. Authentification JWT requise. Logique déléguée au service.

#### Acceptance Criteria
- [ ] `connect/views.py` avec :
  - `CreateConnectedAccountView(APIView)` → `POST /api/connect/create-account/`
    - Retourne `{"stripe_account_id": "...", "onboarding_completed": false}` avec HTTP 201
    - Retourne HTTP 400 si account déjà existant
  - `OnboardingLinkView(APIView)` → `GET /api/connect/onboarding-link/`
    - Retourne `{"url": "https://connect.stripe.com/..."}` avec HTTP 200
    - Retourne HTTP 404 si l'utilisateur n'a pas de `ConnectedAccount`
- [ ] `connect/urls.py` créé avec les deux routes
- [ ] `config/urls.py` mis à jour : `path('api/connect/', include('connect.urls'))`
- [ ] Permission : `IsAuthenticated` enforced
- [ ] Serializers dans `connect/serializers.py`
- [ ] `python manage.py check` passe

#### Definition of Done
Endpoints testables via `curl` authentifié. Aucune migration. Logique métier absente des vues.

---

### ISSUE #CC-04 — App Django `subscriptions` : models `Subscription` et `StripeEvent`

**Label :** `epic:connect-core` `ready` `stripe`  
**Blocked by :** #CC-01  
**Estimated complexity :** M (2 models, 1 migration, critique pour idempotence)

#### Goal
Créer l'app `subscriptions/` avec les deux models fondamentaux : `Subscription` (état de l'abonnement follower→tipster) et `StripeEvent` (garde-fou idempotence webhook).

#### Acceptance Criteria
- [ ] App `subscriptions` créée et dans `INSTALLED_APPS`
- [ ] Model `Subscription` :
  - `follower` → `ForeignKey(CustomUser, related_name='subscriptions_as_follower')`
  - `tipster` → `ForeignKey(CustomUser, related_name='subscriptions_as_tipster')`
  - `stripe_subscription_id` → `CharField(max_length=128, unique=True)`
  - `stripe_customer_id` → `CharField(max_length=64, blank=True)`
  - `status` → `CharField(choices=['active','past_due','canceled','incomplete'], max_length=20)`
  - `current_period_end` → `DateTimeField(null=True, blank=True)`
  - `created_at` → `DateTimeField(auto_now_add=True)`
  - `updated_at` → `DateTimeField(auto_now=True)`
  - Contrainte `unique_together = ('follower', 'tipster')`
- [ ] Model `StripeEvent` :
  - `stripe_event_id` → `CharField(max_length=64, unique=True)` ← clé d'idempotence
  - `event_type` → `CharField(max_length=64)`
  - `processed_at` → `DateTimeField(auto_now_add=True)`
  - `payload` → `JSONField()`
- [ ] Migration `subscriptions/0001_initial.py` uniquement
- [ ] Admin enregistré pour les deux models
- [ ] `python manage.py check` passe

#### Definition of Done
Migration appliquée. Admin accessible. `StripeEvent` prêt à garantir l'idempotence.

---

### ISSUE #CC-05 — Service Stripe : `SubscriptionService` (checkout session + customer management)

**Label :** `epic:connect-core` `ready` `stripe` `security`  
**Blocked by :** #CC-04, #CC-01  
**Estimated complexity :** M

#### Goal
Créer `subscriptions/services.py` avec la logique de création de checkout session Stripe (mode subscription, split 80/20, customer upsert).

#### Acceptance Criteria
- [ ] Fonction `get_or_create_stripe_customer(user)` :
  - Recherche un customer existant via `stripe.Customer.list(email=user.email)`
  - Crée si absent, retourne `stripe_customer_id` (string)
- [ ] Fonction `create_subscription_checkout(follower, tipster, price_id, success_url, cancel_url)` :
  - Récupère `ConnectedAccount` du tipster
  - Lève `TipsterNotOnboardedError` si `charges_enabled=False` ou `onboarding_completed=False`
  - Crée `stripe.checkout.Session.create(...)` avec :
    - `mode='subscription'`
    - `customer=stripe_customer_id`
    - **`application_fee_percent=20`** ← CONSTANTE EXPLICITE (voir note)
    - `transfer_data={'destination': connected_account.stripe_account_id}`
    - `subscription_data={'metadata': {'follower_id': str(follower.id), 'tipster_id': str(tipster.id)}}`
  - Retourne `session.url`
- [ ] Aucune clé Stripe en dur — `settings.STRIPE_SECRET_KEY` uniquement
- [ ] Log structuré sur erreur Stripe (pas de `print`)
- [ ] `python manage.py check` passe

> ⚠️ **Fee critique :** Ne PAS utiliser `settings.PLATFORM_FEE_PERCENT` (défaut = `10.0` dans `settings.py`, **incorrect** pour Connect V2). La valeur `20` doit être une constante visible dans le code du service. Alternative acceptée : `STRIPE_PLATFORM_FEE_PERCENT = env.int('STRIPE_PLATFORM_FEE_PERCENT', default=20)` dans settings + `.env.example`.

#### Definition of Done
`subscriptions/services.py` testable via shell Django. `application_fee_percent=20` visible dans le code. Aucune migration. Aucune vue.

---

### ISSUE #CC-06 — Endpoint REST : `POST /api/subscriptions/subscribe/`

**Label :** `epic:connect-core` `ready` `stripe`  
**Blocked by :** #CC-05, #CC-03  
**Estimated complexity :** S

#### Goal
Exposer l'endpoint de souscription qui orchestre la création de la Checkout Session Stripe et retourne l'URL de paiement au mobile. **Cette vue ne write jamais en base de données.**

#### Acceptance Criteria
- [ ] `subscriptions/views.py` avec `SubscribeView(APIView)` :
  - **`POST /api/subscriptions/subscribe/`** (préfixe `api/subscriptions/` — décision figée)
  - Body : `{"tipster_id": <int>, "price_id": "price_xxx"}`
  - Retourne HTTP 200 : `{"checkout_url": "https://checkout.stripe.com/..."}`
  - Retourne HTTP 400 si tipster non onboardé (`TipsterNotOnboardedError`)
  - Retourne HTTP 404 si tipster inexistant
  - Retourne HTTP 409 si abonnement actif déjà existant (requête DB avant appel Stripe)
  - **AUCUN write en base.** La vue appelle uniquement `SubscriptionService.create_subscription_checkout()` et retourne l'URL
- [ ] `subscriptions/urls.py` créé
- [ ] `config/urls.py` mis à jour : `path('api/subscriptions/', include('subscriptions.urls'))`  
  *(L'app `finance` existante conserve son préfixe `finance/` sans modification)*
- [ ] Permission : `IsAuthenticated`
- [ ] `python manage.py check` passe

> ⚠️ **Règle critique — source of truth = webhook :** La création d'objets `Subscription` en DB est du **seul ressort de CC-07**. Flux : vue → Stripe Checkout → webhook `checkout.session.completed` → DB. Écrire en DB ici casserait l'idempotence.

#### Definition of Done
`POST /api/subscriptions/subscribe/` retourne une `checkout_url`. Aucun objet `Subscription` créé ou modifié par cette vue. Aucune migration.

---

### ISSUE #CC-07 — Webhook Stripe sécurisé + 4 handlers idempotents

**Label :** `epic:connect-core` `ready` `stripe` `security`  
**Blocked by :** #CC-04, #CC-05  
**Estimated complexity :** L (critique sécurité — vérification signature + idempotence)

#### Goal
Implémenter le webhook Stripe avec vérification de signature HMAC obligatoire et traitement idempotent via `StripeEvent`. **CC-07 est la source de vérité unique pour les objets `Subscription` en base de données.**

#### Acceptance Criteria

**Sécurité (non négociable)**
- [ ] Endpoint : `POST /api/stripe/webhook/`
- [ ] `@csrf_exempt` — raw body brut requis (`request.body`), ne pas passer par DRF parsers
- [ ] **Vérification signature obligatoire** : `stripe.Webhook.construct_event(request.body, sig_header, settings.STRIPE_WEBHOOK_SECRET)`
- [ ] Retourne HTTP 400 si signature invalide, absente, ou payload corrompu — jamais HTTP 200 sur erreur signature

**Idempotence (non négociable)**
- [ ] Pattern : `StripeEvent.objects.select_for_update().get_or_create(stripe_event_id=event['id'])` dans `transaction.atomic`
- [ ] Si `created=False` (déjà traité) → HTTP 200 immédiatement, handler non appelé
- [ ] `StripeEvent` créé **avant** le handler, dans la même transaction

**Handler 1 — `checkout.session.completed`** ← crée la Subscription en DB
- [ ] Lit `session['metadata']['follower_id']` et `session['metadata']['tipster_id']`
- [ ] `Subscription.objects.update_or_create(follower=..., tipster=..., defaults={'stripe_subscription_id': session['subscription'], 'stripe_customer_id': session['customer'], 'status': 'active'})`

**Handler 2 — `invoice.paid`**
- [ ] Récupère `Subscription` via `stripe_subscription_id = invoice['subscription']`
- [ ] Met à jour `current_period_end` (datetime UTC depuis `invoice`)
- [ ] Status → `'active'`

**Handler 3 — `invoice.payment_failed`**
- [ ] Récupère `Subscription` via `stripe_subscription_id = invoice['subscription']`
- [ ] Status → `'past_due'`

**Handler 4 — `customer.subscription.deleted`**
- [ ] Récupère `Subscription` via `stripe_subscription_id = subscription['id']`
- [ ] Status → `'canceled'`

**Routing**
- [ ] `config/urls.py` : `path('api/stripe/webhook/', StripeWebhookView.as_view())`
- [ ] Router Stripe dans `subscriptions/webhooks.py` via dict : `{'checkout.session.completed': handle_checkout_session_completed, ...}`
- [ ] Aucune logique Stripe dans `views.py`
- [ ] `python manage.py check` passe

#### Definition of Done
Webhook rejette toute requête sans signature valide (HTTP 400). Aucun double-traitement possible. Les 4 events couvrent le lifecycle complet. Testé via `stripe listen --forward-to localhost:8000/api/stripe/webhook/`.

---

### ISSUE #CC-08 — Middleware premium backend-enforced + endpoint `/api/me/subscriptions/`

**Label :** `epic:connect-core` `ready` `stripe`  
**Blocked by :** #CC-07  
**Estimated complexity :** S

#### Goal
Exposer l'état des abonnements d'un utilisateur et créer un helper de permission premium utilisable dans toute l'API.

#### Acceptance Criteria
- [ ] `subscriptions/permissions.py` avec `HasActiveSubscription(BasePermission)` :
  - Vérifie `Subscription.objects.filter(follower=request.user, tipster=tipster, status='active').exists()`
  - Retourne HTTP 403 si non abonné
  - **Jamais** d'override côté mobile — logique 100% backend
- [ ] `subscriptions/views.py` : ajout de `MySubscriptionsView(ListAPIView)` :
  - `GET /api/me/subscriptions/`
  - Retourne la liste des abonnements actifs du `request.user` (en tant que follower)
  - Serializer : `SubscriptionSerializer` avec champs `tipster`, `status`, `current_period_end`
- [ ] `config/urls.py` ou `subscriptions/urls.py` mis à jour
- [ ] Permission : `IsAuthenticated`
- [ ] `python manage.py check` passe

#### Definition of Done
`/api/me/subscriptions/` retourne la liste correcte. `HasActiveSubscription` utilisable comme classe de permission DRF standard.

---

### ISSUE #CC-09 — Onboarding webhook : sync `charges_enabled` + `payouts_enabled`

**Label :** `epic:connect-core` `ready` `stripe` `security`  
**Blocked by :** #CC-07, #CC-01  
**Estimated complexity :** S

#### Goal
Gérer l'événement `account.updated` du webhook pour mettre à jour automatiquement les flags `charges_enabled` et `payouts_enabled` sur `ConnectedAccount`.

#### Acceptance Criteria
- [ ] Handler `handle_account_updated(account)` ajouté dans le webhook :
  - Met à jour `ConnectedAccount.charges_enabled`, `payouts_enabled`
  - Si `charges_enabled=True` et `payouts_enabled=True` → `onboarding_completed=True`
- [ ] L'événement `account.updated` est routé dans `StripeWebhookView`
- [ ] Idempotence respectée via `StripeEvent`
- [ ] `python manage.py check` passe

#### Definition of Done
Après onboarding Stripe Express, le `ConnectedAccount` reflète automatiquement le statut réel sans intervention manuelle.

---

## 3. ARBRE DE DÉPENDANCES

```
#CC-01 (ConnectedAccount model)
├── #CC-02 (StripeConnectService)
│   └── #CC-03 (Endpoints create-account + onboarding-link)
│       └── #CC-06 (POST /api/finance/subscribe/)
│           └── [accès premium actif]
└── #CC-04 (Subscription + StripeEvent models)
    ├── #CC-05 (SubscriptionService)
    │   └── #CC-06 (POST /api/finance/subscribe/) ← blocked by #CC-03 + #CC-05
    └── #CC-07 (Webhook sécurisé + handlers)
        ├── #CC-08 (Middleware premium + /api/me/subscriptions/)
        └── #CC-09 (account.updated sync)
```

### Vue linéaire (ordre d'exécution Night Train)

| Nuit | Issue | Dépend de | Statut initial |
|------|-------|-----------|----------------|
| N1 | #CC-01 | — | `ready` |
| N2 | #CC-02 | #CC-01 | `blocked` |
| N2 | #CC-04 | #CC-01 | `ready` (parallèle) |
| N3 | #CC-03 | #CC-02 | `blocked` |
| N3 | #CC-05 | #CC-04 + #CC-01 | `blocked` |
| N4 | #CC-06 | #CC-03 + #CC-05 | `blocked` |
| N5 | #CC-07 | #CC-04 + #CC-05 | `blocked` |
| N6 | #CC-08 | #CC-07 | `blocked` |
| N6 | #CC-09 | #CC-07 + #CC-01 | `blocked` |

> **N2** : #CC-02 et #CC-04 peuvent être traités la même nuit (pas de conflit d'app ni de migration).  
> **N3** : #CC-03 et #CC-05 peuvent être traités la même nuit si Jules les prend séquentiellement.  
> **N6** : #CC-08 et #CC-09 peuvent être traités la même nuit (apps distinctes, pas de migration supplémentaire).

**Total estimé : 6 nuits Night Train.**

---

## 4. LABELS À CRÉER SUR GITHUB

```
epic:connect-core   → couleur #7B2FBE  (violet)
agent:jules         → couleur #0075CA  (bleu)
blocked             → couleur #E4E669  (jaune)
ready               → couleur #0E8A16  (vert)
needs:human         → couleur #D93F0B  (rouge)
security            → couleur #B60205  (rouge foncé)
stripe              → couleur #635BFF  (indigo Stripe)
```

---

## 5. ANALYSE DES RISQUES

| # | Risque | Sévérité | Mitigation |
|---|--------|----------|------------|
| R1 | **Conflit `finance/` prefix** — L'app `finance` existante utilise `finance/` sans `api/`. `POST /api/finance/subscribe/` peut collider | HIGH | Audit `config/urls.py` avant #CC-06. Fallback vers `/api/subscriptions/` si conflit |
| R2 | **Webhook raw body** — Django consomme le body avant la vue si un middleware le lit | HIGH | `@csrf_exempt` + lecture `request.body` directement. Vérifier middleware order |
| R3 | **`STRIPE_WEBHOOK_SECRET` absent en CI** — Le CI utilise `whsec_dummy` qui ne valide pas les vrais events | MEDIUM | Secret de test Stripe CLI pour les tests d'intégration. Ne jamais exposer le vrai secret |
| R4 | **Double migration** — Jules pourrait générer `0001` + `0002` dans la même PR | HIGH | Contrainte AGENTS.md : 1 migration max par issue. CI `showmigrations` doit valider |
| R5 | **Connected Account sans onboarding complet** — Le tipster peut avoir un `stripe_account_id` mais `charges_enabled=False` | HIGH | `TipsterNotOnboardedError` dans `SubscriptionService`. Guard dans le webhook |
| R6 | **Race condition sur `StripeEvent`** — Deux webhooks identiques reçus simultanément | MEDIUM | `get_or_create` avec `select_for_update()` dans `transaction.atomic` |
| R7 | **`PLATFORM_FEE_PERCENT` hardcodé** — settings.py a `default=10.0` mais le business model est 20% | MEDIUM | S'assurer que `PLATFORM_FEE_PERCENT=20` dans `.env` production. Ne pas lire depuis settings dans le service, passer explicitement `20` |
| R8 | **Expo deep link return_url** — L'onboarding Stripe redirige via URL. Expo doit avoir un scheme configuré | LOW | Note pour issue mobile future. Backend retourne l'URL, la gestion du deep link est mobile |

---

## 6. ESTIMATION NOMBRE DE NUITS

| Nuit | Issues traitées | Complexité cumulée |
|------|-----------------|--------------------|
| N1 | #CC-01 | S |
| N2 | #CC-02 + #CC-04 | S + M |
| N3 | #CC-03 + #CC-05 | S + M |
| N4 | #CC-06 | S |
| N5 | #CC-07 | L (nuit critique) |
| N6 | #CC-08 + #CC-09 | S + S |

**Total : 6 nuits Night Train**  
**Avec révision humaine matinale + reset train : 6 jours calendaires**  
**Marge buffer (re-runs, hotfix) : +2 nuits**  
**Horizon réaliste bêta payante : J+8 à J+10**

