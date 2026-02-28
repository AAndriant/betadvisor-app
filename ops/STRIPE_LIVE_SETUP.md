# Stripe Connect Live — Guide de Configuration Production

> **Criticité :** Business-critique. Ne pas rushier ces étapes.  
> **Pré-requis :** Avoir terminé et validé les issues CC-01..CC-09 en staging/test.  
> **Date de référence :** 2026-02-28

---

## ⚠️ AVERTISSEMENT DE SÉCURITÉ

**JAMAIS** stocker une clé Stripe Live dans :
- le code source
- un fichier `.env` commité
- les logs CI
- un message de chat, email, ou document partagé

**TOUJOURS** utiliser GitHub Secrets :
```bash
gh secret set STRIPE_LIVE_SECRET_KEY --repo AAndriant/betadvisor-app
gh secret set STRIPE_LIVE_WEBHOOK_SECRET --repo AAndriant/betadvisor-app
gh secret set STRIPE_PLATFORM_ACCOUNT_ID --repo AAndriant/betadvisor-app
```

---

## ÉTAPE 1 — Créer et configurer le compte Stripe Platform

### 1.1 Accès Dashboard
1. Aller sur [dashboard.stripe.com](https://dashboard.stripe.com)
2. S'assurer d'être sur le compte **Platform** (pas un compte tipster)
3. Passer en mode **Live** (toggle en haut à droite du dashboard)

### 1.2 Identifiants à récupérer
- **Secret Key** : `Developers → API Keys → Secret key` (commence par `sk_live_`)
- **Platform Account ID** : `Settings → Account details → Account ID` (commence par `acct_`)

```bash
# Stocker immédiatement après récupération
gh secret set STRIPE_LIVE_SECRET_KEY --repo AAndriant/betadvisor-app
# Coller la valeur sk_live_... quand demandé

gh secret set STRIPE_PLATFORM_ACCOUNT_ID --repo AAndriant/betadvisor-app
# Coller la valeur acct_... quand demandé
```

---

## ÉTAPE 2 — Activer Stripe Connect Express

### 2.1 Activation
1. `Connect → Settings → Get started`
2. Choisir **Express** (pas Custom, pas Standard)
3. Configurer les pays acceptés (France minimum)

### 2.2 Branding Checkout (obligatoire pour Express)
1. `Connect → Settings → Branding`
2. Uploader logo BetAdvisor (512x512px, fond blanc recommandé)
3. Définir la couleur de marque (hex)
4. Nom légal de la plateforme : **BetAdvisor**

### 2.3 URL de redirection onboarding
Dans `Connect → Settings → Redirect URLs` :
- Success : `betadvisor://connect/onboarding-complete`
- Refresh : `betadvisor://connect/onboarding-refresh`

---

## ÉTAPE 3 — Configurer le Webhook Live

### 3.1 Créer l'endpoint
1. `Developers → Webhooks → Add endpoint`
2. URL : `https://<VOTRE_DOMAINE_PRODUCTION>/api/stripe/webhook/`
3. Version d'API Stripe : **dernière version stable** (ex: 2024-06-20)

### 3.2 Events à écouter (obligatoires — implémentés dans CC-07)
```
✅ checkout.session.completed
✅ invoice.paid
✅ invoice.payment_failed
✅ customer.subscription.deleted
✅ account.updated
```

### 3.3 Récupérer le Webhook Secret
1. Cliquer sur l'endpoint créé → `Reveal signing secret`
2. Copier la valeur `whsec_...`

```bash
gh secret set STRIPE_LIVE_WEBHOOK_SECRET --repo AAndriant/betadvisor-app
# Coller la valeur whsec_... quand demandé
```

---

## ÉTAPE 4 — Configurer les Variables d'Environnement Production

### 4.1 GitHub Secrets (CI/CD)
```bash
# Live Stripe
gh secret set STRIPE_LIVE_SECRET_KEY --repo AAndriant/betadvisor-app
gh secret set STRIPE_LIVE_WEBHOOK_SECRET --repo AAndriant/betadvisor-app
gh secret set STRIPE_PLATFORM_ACCOUNT_ID --repo AAndriant/betadvisor-app

# App
gh secret set APP_BASE_URL --repo AAndriant/betadvisor-app
# Valeur : https://api.betadvisor.app (ou votre domaine)

gh secret set EXPO_APP_SCHEME --repo AAndriant/betadvisor-app
# Valeur : betadvisor
```

### 4.2 Variables d'environnement PaaS (Railway, Render, etc.)
```bash
# Django Production Settings
DEBUG=False
SECRET_KEY=<générer avec: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
ALLOWED_HOSTS=api.betadvisor.app
DATABASE_URL=postgres://...

# Stripe Live
STRIPE_LIVE_SECRET_KEY=sk_live_...
STRIPE_LIVE_WEBHOOK_SECRET=whsec_...
STRIPE_PLATFORM_ACCOUNT_ID=acct_...

# Checkout Deep Links (Expo)
CHECKOUT_SUCCESS_URL=betadvisor://checkout/success?session_id={CHECKOUT_SESSION_ID}
CHECKOUT_CANCEL_URL=betadvisor://checkout/cancel

# Platform Fee (CONSTANTE — toujours 20, jamais modifiable sans code review)
STRIPE_PLATFORM_FEE_PERCENT=20
```

### 4.3 .env.example à mettre à jour
```bash
# Ajouter dans apps/backend/.env.example :
STRIPE_LIVE_SECRET_KEY=sk_live_your-live-secret-key-here
STRIPE_LIVE_WEBHOOK_SECRET=whsec_your-live-webhook-secret-here
STRIPE_PLATFORM_ACCOUNT_ID=acct_your-platform-account-id-here
CHECKOUT_SUCCESS_URL=betadvisor://checkout/success?session_id={CHECKOUT_SESSION_ID}
CHECKOUT_CANCEL_URL=betadvisor://checkout/cancel
STRIPE_PLATFORM_FEE_PERCENT=20
```

---

## ÉTAPE 5 — Produits et Prix Dynamiques par Tipster

### 5.1 Architecture recommandée
Chaque tipster dispose d'un `Price ID` Stripe créé à son onboarding :

```
Stripe Product: "Abonnement Tipster — <username>"
Stripe Price:   recurring, monthly, amount défini par le tipster
```

### 5.2 Création via API (à implémenter dans un service futur)
```python
# Exemple (à ne PAS implémenter dans CC-01..CC-09, scope futur)
product = stripe.Product.create(
    name=f"Abonnement {tipster.username}",
    metadata={"tipster_id": str(tipster.id)}
)
price = stripe.Price.create(
    product=product.id,
    unit_amount=999,  # en centimes — 9.99€
    currency="eur",
    recurring={"interval": "month"},
)
```

### 5.3 Pour la bêta (V2 scope actuel)
Créer manuellement 1 prix fixe de test sur le Dashboard Stripe :
- Montant : 9,99€/mois
- Récupérer le `price_id` (commence par `price_`)
- L'utiliser comme `price_id` dans `POST /api/subscriptions/subscribe/`

---

## ÉTAPE 6 — Test via Stripe CLI

### 6.1 Installation
```bash
brew install stripe/stripe-cli/stripe
stripe login
```

### 6.2 Écouter les webhooks localement
```bash
stripe listen \
  --forward-to localhost:8000/api/stripe/webhook/ \
  --events checkout.session.completed,invoice.paid,invoice.payment_failed,customer.subscription.deleted,account.updated
```

### 6.3 Déclencher des events de test
```bash
# Simuler checkout réussi
stripe trigger checkout.session.completed

# Simuler renouvellement mensuel
stripe trigger invoice.paid

# Simuler échec paiement
stripe trigger invoice.payment_failed

# Simuler résiliation
stripe trigger customer.subscription.deleted
```

### 6.4 Test Express Account onboarding
```bash
# Créer un compte Express de test
stripe accounts create --type express --country FR

# Puis appeler votre endpoint
curl -X POST http://localhost:8000/api/connect/create-account/ \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json"
```

---

## CHECKLIST GO-LIVE STRIPE (10 items max)

- [ ] **1.** Compte Stripe Live activé avec KYC vérifié
- [ ] **2.** Connect Express activé + branding configuré
- [ ] **3.** `STRIPE_LIVE_SECRET_KEY` stocké dans GitHub Secrets  
- [ ] **4.** `STRIPE_LIVE_WEBHOOK_SECRET` stocké dans GitHub Secrets
- [ ] **5.** `STRIPE_PLATFORM_ACCOUNT_ID` stocké dans GitHub Secrets
- [ ] **6.** Webhook endpoint Live créé avec les 5 events requis
- [ ] **7.** `CHECKOUT_SUCCESS_URL` et `CHECKOUT_CANCEL_URL` configurés (deep links `betadvisor://`)
- [ ] **8.** `DEBUG=False` et `ALLOWED_HOSTS` non-vides en production
- [ ] **9.** `application_fee_percent=20` vérifié dans le code (pas settings)
- [ ] **10.** Test End-to-End : tipster onboarding → follower subscribe → webhook reçu → Subscription active en DB

---

## CONTACTS ET RESSOURCES

| Ressource | URL |
|-----------|-----|
| Stripe Dashboard | https://dashboard.stripe.com |
| Stripe Connect Docs | https://stripe.com/docs/connect |
| Stripe Connect Express | https://stripe.com/docs/connect/express-accounts |
| Stripe Webhooks | https://stripe.com/docs/webhooks |
| Stripe CLI | https://stripe.com/docs/stripe-cli |
| Stripe Test Cards | https://stripe.com/docs/testing#cards |
