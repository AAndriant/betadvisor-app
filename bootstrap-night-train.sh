#!/usr/bin/env bash
# =============================================================================
# bootstrap-night-train.sh — BetAdvisor Night Train V2
# Pattern validé V1 (MathPrepa — 28/02/2026 — 8 issues, ~3h30, 100%)
#
# Usage:
#   chmod +x bootstrap-night-train.sh
#   ./bootstrap-night-train.sh
#
# Prérequis:
#   - gh CLI installé (brew install gh) et authentifié (gh auth login)
#   - Être dans le repo betadvisor-app (git remote origin configuré)
# =============================================================================

set -euo pipefail

# ─── COULEURS ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

log_section() { echo -e "\n${BOLD}${BLUE}━━━ $1 ━━━${NC}"; }
log_ok()      { echo -e "${GREEN}  ✅ $1${NC}"; }
log_warn()    { echo -e "${YELLOW}  ⚠️  $1${NC}"; }
log_err()     { echo -e "${RED}  ❌ $1${NC}"; }
log_info()    { echo -e "     $1"; }

# =============================================================================
# SECTION 0 — PRÉREQUIS
# =============================================================================
log_section "PRÉREQUIS"

if ! command -v gh &>/dev/null; then
  log_err "GitHub CLI (gh) manquant. Installer: brew install gh"
  exit 1
fi
log_ok "gh CLI disponible ($(gh --version | head -1))"

if ! gh auth status &>/dev/null; then
  log_err "Non authentifié. Lancer: gh auth login"
  exit 1
fi
log_ok "gh CLI authentifié"

# Détection automatique du repo
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
  log_err "Impossible de détecter le repo GitHub."
  log_err "Vérifier: gh repo view"
  exit 1
fi
log_ok "Repo: ${REPO}"

# =============================================================================
# SECTION 1 — LABELS (idempotent)
# Pattern v1 validé : check existence avant création
# =============================================================================
log_section "LABELS"

create_label() {
  local name="$1" color="$2" description="$3"
  if gh label list --repo "$REPO" --json name -q ".[].name" 2>/dev/null | grep -qx "$name"; then
    log_warn "Label '$name' déjà existant (OK)"
  else
    gh label create "$name" --repo "$REPO" --color "$color" --description "$description" 2>/dev/null \
      && log_ok "Label créé: $name" \
      || log_warn "Problème création '$name' (peut-être race condition — OK)"
  fi
}

create_label "epic:connect-core"  "7B2FBE"  "Epic Stripe Connect Express marketplace"
create_label "agent:jules"        "6f42c1"  "Dispatches Jules on this issue"
create_label "blocked"            "d93f0b"  "Blocked by another issue"
create_label "ready"              "0e8a16"  "Completed by Jules"
create_label "needs:human"        "fbca04"  "Requires human intervention"
create_label "needs:jules-fix"    "e4e669"  "Jules needs to fix something"
create_label "security"           "B60205"  "Security-critical change"
create_label "stripe"             "635BFF"  "Stripe-related implementation"
create_label "in-progress"        "1d76db"  "Currently being worked on"

# =============================================================================
# SECTION 2 — BRANCHE JULES/TRAIN (idempotent)
# Pattern v1 validé : utiliser gh API directement
# =============================================================================
log_section "BRANCHE JULES/TRAIN"

TRAIN_BRANCH="jules/train"

if gh api "repos/${REPO}/branches/${TRAIN_BRANCH}" &>/dev/null; then
  log_warn "Branche '${TRAIN_BRANCH}' déjà existante (OK)"
else
  SHA=$(gh api "repos/${REPO}/git/ref/heads/main" --jq '.object.sha')
  gh api "repos/${REPO}/git/refs" \
    -f "ref=refs/heads/${TRAIN_BRANCH}" \
    -f "sha=${SHA}" >/dev/null
  log_ok "Branche '${TRAIN_BRANCH}' créée depuis main (${SHA:0:8})"
fi

# =============================================================================
# SECTION 3 — ISSUES CONNECT CORE (CC-01..CC-09)
# =============================================================================
log_section "CRÉATION DES ISSUES CONNECT CORE"

# ─── Helper : créer une issue (idempotent par titre) ──────────────────────────
# Retourne le numéro GitHub réel dans NUMS[]
# CRITIQUE : `gh issue create` retourne une URL complète :
#   https://github.com/owner/repo/issues/123
# On extrait le numéro avec grep -oP 'issues/\K[0-9]+'
# (PAS '#\K[0-9]+' qui ne matcherait jamais l'URL — Bug corrigé)
# =============================================================================
declare -a NUMS=()

create_issue() {
  local title="$1"
  local body="$2"
  local labels="${3:-}"

  # Idempotence : vérifier si une issue avec ce titre existe déjà
  local existing
  existing=$(gh issue list \
    --repo "$REPO" \
    --state all \
    --search "\"${title}\" in:title" \
    --json number \
    -q '.[0].number' 2>/dev/null || echo "")

  if [[ -n "$existing" && "$existing" != "null" ]]; then
    NUMS+=("$existing")
    log_warn "Issue #${existing} existe déjà: ${title}"
    return
  fi

  local url number
  url=$(gh issue create \
    --repo "$REPO" \
    --title "${title}" \
    --body "${body}" \
    --label "${labels}" \
    2>/dev/null || echo "")

  # Extraire le numéro depuis l'URL retournée
  number=$(echo "${url}" | grep -oP 'issues/\K[0-9]+' || echo "")

  if [[ -n "$number" && "$number" != "0" ]]; then
    NUMS+=("$number")
    log_ok "Issue #${number} créée: ${title}"
    log_info "→ ${url}"
  else
    log_err "ÉCHEC création: ${title}"
    log_err "  Réponse gh: ${url}"
    log_err "  → Vérifier labels existants, permissions, gh auth"
    NUMS+=("0")
  fi
}

# ─────────────────────────────────────────────────────────────────────────────
# CC-01 — ConnectedAccount model (PREMIER, pas de dépendance)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
log_info "Création CC-01..."
create_issue \
  "[CC-01] feat: ConnectedAccount model + connect app scaffold" \
  '## Goal
Créer app Django `connect/` et model `ConnectedAccount`.

## Acceptance Criteria
- [ ] App `connect` créée et dans `INSTALLED_APPS`
- [ ] Model `ConnectedAccount` avec champs :
  - `user` → `OneToOneField(CustomUser, on_delete=CASCADE, related_name="connected_account")`
  - `stripe_account_id` → `CharField(max_length=64, unique=True)`
  - `charges_enabled` → `BooleanField(default=False)`
  - `payouts_enabled` → `BooleanField(default=False)`
  - `onboarding_completed` → `BooleanField(default=False)`
  - `created_at` → `DateTimeField(auto_now_add=True)`
  - `updated_at` → `DateTimeField(auto_now=True)`
- [ ] Migration `connect/migrations/0001_initial.py` uniquement (1 migration max)
- [ ] `__str__` retourne `f"{self.user.username} — {self.stripe_account_id}"`
- [ ] Admin Django enregistré (`admin.site.register(ConnectedAccount)`)
- [ ] `python manage.py check` passe sans erreur

## Migration
`connect/migrations/0001_initial.py`

## Definition of Done
Migration appliquée proprement. Admin accessible. Aucun autre fichier modifié.' \
  "epic:connect-core,stripe,agent:jules"

CC01="${NUMS[-1]}"

# ─────────────────────────────────────────────────────────────────────────────
# CC-02 — StripeConnectService (blocked by CC-01)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
log_info "Création CC-02..."
create_issue \
  "[CC-02] feat: StripeConnectService (create_express_account + onboarding_link)" \
"Blocked by #${CC01}

## Goal
Créer \`connect/services.py\` avec la logique Stripe isolée.

## Acceptance Criteria
- [ ] Fonction \`create_express_account(user)\` :
  - Appelle \`stripe.Account.create(type='express', ...)\`
  - Sauvegarde \`ConnectedAccount\` avec le \`stripe_account_id\` retourné
  - Lève \`StripeConnectError\` (exception custom) si l'account existe déjà
- [ ] Fonction \`create_onboarding_link(stripe_account_id, return_url, refresh_url)\` :
  - Appelle \`stripe.AccountLink.create(...)\`
  - Retourne l'URL d'onboarding
- [ ] Aucune clé Stripe en dur — \`settings.STRIPE_SECRET_KEY\` uniquement
- [ ] Logging structuré (pas de \`print\`)
- [ ] \`python manage.py check\` passe

## Migration
N/A

## Definition of Done
\`connect/services.py\` testable via shell Django. Aucune migration. Aucune vue." \
  "epic:connect-core,stripe,security,blocked"

CC02="${NUMS[-1]}"

# ─────────────────────────────────────────────────────────────────────────────
# CC-04 — Subscription + StripeEvent models (blocked by CC-01, parallèle CC-02)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
log_info "Création CC-04..."
create_issue \
  "[CC-04] feat: Subscription + StripeEvent models + subscriptions app" \
"Blocked by #${CC01}

## Goal
Créer app Django \`subscriptions/\` avec models \`Subscription\` et \`StripeEvent\`.

## Acceptance Criteria
- [ ] App \`subscriptions\` dans \`INSTALLED_APPS\`
- [ ] Model \`Subscription\` :
  - \`follower\` → \`ForeignKey(CustomUser, related_name='subscriptions_as_follower')\`
  - \`tipster\` → \`ForeignKey(CustomUser, related_name='subscriptions_as_tipster')\`
  - \`stripe_subscription_id\` → \`CharField(max_length=128, unique=True)\`
  - \`stripe_customer_id\` → \`CharField(max_length=64, blank=True)\`
  - \`status\` → \`CharField(choices=['active','past_due','canceled','incomplete'], max_length=20)\`
  - \`current_period_end\` → \`DateTimeField(null=True, blank=True)\`
  - \`created_at\`, \`updated_at\` → auto
  - \`unique_together = ('follower', 'tipster')\`
- [ ] Model \`StripeEvent\` :
  - \`stripe_event_id\` → \`CharField(max_length=64, unique=True)\` ← clé d'idempotence
  - \`event_type\` → \`CharField(max_length=64)\`
  - \`processed_at\` → \`DateTimeField(auto_now_add=True)\`
  - \`payload\` → \`JSONField()\`
- [ ] Migration \`subscriptions/migrations/0001_initial.py\` uniquement
- [ ] Admin enregistré pour les deux models
- [ ] \`python manage.py check\` passe

## Migration
\`subscriptions/migrations/0001_initial.py\`

## Definition of Done
Migration appliquée. \`StripeEvent\` prêt à garantir l'idempotence." \
  "epic:connect-core,stripe,blocked"

CC04="${NUMS[-1]}"

# ─────────────────────────────────────────────────────────────────────────────
# CC-03 — REST endpoints Connect (blocked by CC-02)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
log_info "Création CC-03..."
create_issue \
  "[CC-03] feat: REST endpoints /api/connect/create-account/ + /api/connect/onboarding-link/" \
"Blocked by #${CC02}

## Goal
Exposer les deux endpoints REST Connect via DRF.

## Acceptance Criteria
- [ ] \`CreateConnectedAccountView(APIView)\` → \`POST /api/connect/create-account/\`
  - Retourne HTTP 201 : \`{\"stripe_account_id\": \"...\", \"onboarding_completed\": false}\`
  - Retourne HTTP 400 si account déjà existant
- [ ] \`OnboardingLinkView(APIView)\` → \`GET /api/connect/onboarding-link/\`
  - Retourne HTTP 200 : \`{\"url\": \"https://connect.stripe.com/...\"}\`
  - Retourne HTTP 404 si \`ConnectedAccount\` absent
- [ ] \`connect/urls.py\` créé avec les deux routes
- [ ] \`config/urls.py\` mis à jour : \`path('api/connect/', include('connect.urls'))\`
- [ ] Permission : \`IsAuthenticated\` enforced
- [ ] Serializers dans \`connect/serializers.py\`
- [ ] \`python manage.py check\` passe

## Migration
N/A

## Definition of Done
Endpoints testables via curl authentifié. Logique dans services.py, pas dans views.py." \
  "epic:connect-core,stripe,blocked"

CC03="${NUMS[-1]}"

# ─────────────────────────────────────────────────────────────────────────────
# CC-05 — SubscriptionService (blocked by CC-04 + CC-01)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
log_info "Création CC-05..."
create_issue \
  "[CC-05] feat: SubscriptionService (checkout session + customer upsert)" \
"Blocked by #${CC04}
Blocked by #${CC01}

## Goal
Créer \`subscriptions/services.py\` avec logique checkout Stripe.

## Acceptance Criteria
- [ ] Fonction \`get_or_create_stripe_customer(user)\` :
  - Recherche customer existant via \`stripe.Customer.list(email=user.email)\`
  - Crée si absent, retourne \`stripe_customer_id\` (string)
- [ ] Fonction \`create_subscription_checkout(follower, tipster, price_id, success_url, cancel_url)\` :
  - Récupère \`ConnectedAccount\` du tipster
  - Lève \`TipsterNotOnboardedError\` si \`charges_enabled=False\` ou \`onboarding_completed=False\`
  - Crée \`stripe.checkout.Session.create(...)\` avec :
    - \`mode='subscription'\`
    - \`customer=stripe_customer_id\`
    - \`application_fee_percent=20\` ← CONSTANTE EXPLICITE (pas settings.PLATFORM_FEE_PERCENT qui vaut 10)
    - \`transfer_data={'destination': connected_account.stripe_account_id}\`
    - \`subscription_data={'metadata': {'follower_id': str(follower.id), 'tipster_id': str(tipster.id)}}\`
  - Retourne \`session.url\`
- [ ] Aucune clé Stripe en dur — \`settings.STRIPE_SECRET_KEY\` uniquement
- [ ] Logging structuré, pas de print
- [ ] \`python manage.py check\` passe

## Migration
N/A

## Definition of Done
Testable via shell Django. \`application_fee_percent=20\` visible dans le code. Aucune migration. Aucune vue." \
  "epic:connect-core,stripe,security,blocked"

CC05="${NUMS[-1]}"

# ─────────────────────────────────────────────────────────────────────────────
# CC-06 — Endpoint subscribe (blocked by CC-03 + CC-05)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
log_info "Création CC-06..."
create_issue \
  "[CC-06] feat: POST /api/subscriptions/subscribe/ checkout endpoint" \
"Blocked by #${CC03}
Blocked by #${CC05}

## Goal
Exposer \`POST /api/subscriptions/subscribe/\` qui retourne une Checkout URL Stripe.
Cette vue NE WRITE PAS en DB — la source de vérité est le webhook CC-07.

## URL Standard (figé)
\`POST /api/subscriptions/subscribe/\` (pas /api/finance/ — conflit évité)
\`config/urls.py\` : \`path('api/subscriptions/', include('subscriptions.urls'))\`

## Acceptance Criteria
- [ ] \`SubscribeView(APIView)\` → \`POST /api/subscriptions/subscribe/\`
- [ ] Body : \`{\"tipster_id\": <int>, \"price_id\": \"price_xxx\"}\`
- [ ] Retourne HTTP 200 : \`{\"checkout_url\": \"https://checkout.stripe.com/...\"}\`
- [ ] Retourne HTTP 400 si tipster non onboardé (\`TipsterNotOnboardedError\`)
- [ ] Retourne HTTP 404 si tipster inexistant
- [ ] Retourne HTTP 409 si abonnement actif déjà existant (vérification DB avant appel Stripe)
- [ ] **AUCUN write en base** — cette vue appelle uniquement \`SubscriptionService.create_subscription_checkout()\`
- [ ] \`subscriptions/urls.py\` créé
- [ ] \`config/urls.py\` mis à jour : \`path('api/subscriptions/', include('subscriptions.urls'))\`
- [ ] Permission : \`IsAuthenticated\`
- [ ] \`python manage.py check\` passe

## Migration
N/A

## Definition of Done
Retourne une checkout_url. Aucun objet Subscription créé par cette vue. Aucune migration." \
  "epic:connect-core,stripe,blocked"

CC06="${NUMS[-1]}"

# ─────────────────────────────────────────────────────────────────────────────
# CC-07 — Webhook Stripe sécurisé (blocked by CC-04 + CC-05)
# NUIT CRITIQUE — source de vérité DB
# ─────────────────────────────────────────────────────────────────────────────
echo ""
log_info "Création CC-07..."
create_issue \
  "[CC-07] feat: Stripe webhook sécurisé + 4 handlers idempotents (checkout.session.completed, invoice.paid, invoice.payment_failed, customer.subscription.deleted)" \
"Blocked by #${CC04}
Blocked by #${CC05}

## Goal
Webhook Stripe avec signature HMAC obligatoire et idempotence.
CC-07 est la SOURCE DE VÉRITÉ UNIQUE pour les objets Subscription en DB.
CC-06 ne write jamais en DB.

## Acceptance Criteria

### Sécurité
- [ ] Endpoint : \`POST /api/stripe/webhook/\`
- [ ] \`@csrf_exempt\` — raw body requis (\`request.body\`), ne pas passer par DRF parsers
- [ ] Vérification signature obligatoire : \`stripe.Webhook.construct_event(request.body, sig_header, settings.STRIPE_WEBHOOK_SECRET)\`
- [ ] HTTP 400 si signature invalide, absente ou payload corrompu. JAMAIS HTTP 200 sur erreur.

### Idempotence
- [ ] Pattern : \`StripeEvent.objects.select_for_update().get_or_create(stripe_event_id=event['id'])\` dans \`transaction.atomic\`
- [ ] Si \`created=False\` → HTTP 200 immédiat, handler non appelé
- [ ] \`StripeEvent\` créé avant le handler, dans la même transaction

### Handler 1 — \`checkout.session.completed\`
- [ ] Lit \`session['metadata']['follower_id']\` et \`session['metadata']['tipster_id']\`
- [ ] \`Subscription.objects.update_or_create(follower=..., tipster=..., defaults={'stripe_subscription_id': session['subscription'], 'stripe_customer_id': session['customer'], 'status': 'active'})\`

### Handler 2 — \`invoice.paid\`
- [ ] Récupère \`Subscription\` via \`stripe_subscription_id = invoice['subscription']\`
- [ ] Met à jour \`current_period_end\` (datetime UTC)
- [ ] Status → \`'active'\`

### Handler 3 — \`invoice.payment_failed\`
- [ ] Récupère \`Subscription\` via \`stripe_subscription_id = invoice['subscription']\`
- [ ] Status → \`'past_due'\`

### Handler 4 — \`customer.subscription.deleted\`
- [ ] Récupère \`Subscription\` via \`stripe_subscription_id = subscription['id']\`
- [ ] Status → \`'canceled'\`

### Routing
- [ ] \`config/urls.py\` : \`path('api/stripe/webhook/', StripeWebhookView.as_view())\`
- [ ] Router dans \`subscriptions/webhooks.py\` via dict handlers
- [ ] Aucune logique Stripe dans \`views.py\`
- [ ] \`python manage.py check\` passe

## Migration
N/A

## Definition of Done
HTTP 400 sur signature invalide. Idempotence garantie. 4 events couverts. Testé via \`stripe listen --forward-to localhost:8000/api/stripe/webhook/\`" \
  "epic:connect-core,stripe,security,blocked"

CC07="${NUMS[-1]}"

# ─────────────────────────────────────────────────────────────────────────────
# CC-08 — HasActiveSubscription + /api/me/subscriptions/ (blocked by CC-07)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
log_info "Création CC-08..."
create_issue \
  "[CC-08] feat: HasActiveSubscription permission + GET /api/me/subscriptions/" \
"Blocked by #${CC07}

## Goal
Exposer l'état des abonnements et créer la permission premium backend-enforced.

## Acceptance Criteria
- [ ] \`subscriptions/permissions.py\` avec \`HasActiveSubscription(BasePermission)\` :
  - Vérifie \`Subscription.objects.filter(follower=request.user, status='active').exists()\`
  - HTTP 403 si non abonné
  - Logique 100% backend — jamais d'override mobile
- [ ] \`MySubscriptionsView(ListAPIView)\` → \`GET /api/me/subscriptions/\`
  - Retourne liste des abonnements actifs du request.user (follower)
  - Serializer : champs \`tipster\`, \`status\`, \`current_period_end\`
- [ ] Route ajoutée dans \`subscriptions/urls.py\` et \`config/urls.py\`
- [ ] Permission : \`IsAuthenticated\`
- [ ] \`python manage.py check\` passe

## Migration
N/A

## Definition of Done
\`/api/me/subscriptions/\` retourne la liste correcte. \`HasActiveSubscription\` utilisable comme permission DRF standard." \
  "epic:connect-core,stripe,blocked"

CC08="${NUMS[-1]}"

# ─────────────────────────────────────────────────────────────────────────────
# CC-09 — account.updated sync (blocked by CC-07 + CC-01)
# ─────────────────────────────────────────────────────────────────────────────
echo ""
log_info "Création CC-09..."
create_issue \
  "[CC-09] feat: account.updated webhook handler (sync onboarding status)" \
"Blocked by #${CC07}
Blocked by #${CC01}

## Goal
Synchroniser automatiquement \`charges_enabled\` et \`payouts_enabled\` sur \`ConnectedAccount\` via l'event \`account.updated\`.

## Acceptance Criteria
- [ ] Handler \`handle_account_updated(account)\` dans le webhook :
  - Met à jour \`ConnectedAccount.charges_enabled\`, \`payouts_enabled\`
  - Si les deux \`True\` → \`onboarding_completed=True\`
- [ ] Event \`account.updated\` routé dans \`StripeWebhookView\`
- [ ] Idempotence via \`StripeEvent\`
- [ ] \`python manage.py check\` passe

## Migration
N/A

## Definition of Done
Après onboarding Stripe Express, \`ConnectedAccount\` reflète automatiquement le statut réel sans intervention manuelle." \
  "epic:connect-core,stripe,security,blocked"

CC09="${NUMS[-1]}"

# =============================================================================
# SECTION 4 — VALIDATION INTÉGRITÉ
# Fail-fast si un numéro est 0 ou vide
# =============================================================================
log_section "VALIDATION INTÉGRITÉ"

declare -A ISSUE_MAP=(
  ["CC-01"]="${CC01}"
  ["CC-02"]="${CC02}"
  ["CC-03"]="${CC03}"
  ["CC-04"]="${CC04}"
  ["CC-05"]="${CC05}"
  ["CC-06"]="${CC06}"
  ["CC-07"]="${CC07}"
  ["CC-08"]="${CC08}"
  ["CC-09"]="${CC09}"
)

FAILED=0
for key in CC-01 CC-02 CC-03 CC-04 CC-05 CC-06 CC-07 CC-08 CC-09; do
  val="${ISSUE_MAP[$key]}"
  if [[ "${val}" == "0" || -z "${val}" ]]; then
    log_err "Issue ${key} n'a pas de numéro GitHub valide (valeur: '${val}')"
    FAILED=1
  fi
done

if [[ "${FAILED}" == "1" ]]; then
  echo ""
  log_err "BOOTSTRAP INCOMPLET — chaînage Blocked by sera cassé."
  log_err "→ Vérifier les permissions gh, les labels, et relancer."
  exit 1
fi

log_ok "Toutes les issues ont des numéros GitHub valides"

# =============================================================================
# SECTION 5 — RÉSUMÉ FINAL
# =============================================================================
log_section "RÉSUMÉ FINAL"

echo ""
echo -e "${BOLD}Mapping CC-xx → GitHub #NUM (chaînage réel) :${NC}"
echo -e "  CC-01 → GitHub #${CC01} ${GREEN}[ready + agent:jules — PREMIER]${NC}"
echo -e "  CC-02 → GitHub #${CC02} ${YELLOW}[blocked by #${CC01}]${NC}"
echo -e "  CC-04 → GitHub #${CC04} ${YELLOW}[blocked by #${CC01}] (parallèle CC-02)${NC}"
echo -e "  CC-03 → GitHub #${CC03} ${YELLOW}[blocked by #${CC02}]${NC}"
echo -e "  CC-05 → GitHub #${CC05} ${YELLOW}[blocked by #${CC04} + #${CC01}]${NC}"
echo -e "  CC-06 → GitHub #${CC06} ${YELLOW}[blocked by #${CC03} + #${CC05}]${NC}"
echo -e "  CC-07 → GitHub #${CC07} ${YELLOW}[blocked by #${CC04} + #${CC05}]${NC}"
echo -e "  CC-08 → GitHub #${CC08} ${YELLOW}[blocked by #${CC07}]${NC}"
echo -e "  CC-09 → GitHub #${CC09} ${YELLOW}[blocked by #${CC07} + #${CC01}]${NC}"

echo ""
echo -e "${BOLD}Décisions standards figées :${NC}"
echo -e "  • Préfixe API    : ${GREEN}/api/*${NC}"
echo -e "  • Subscribe URL  : ${GREEN}POST /api/subscriptions/subscribe/${NC}"
echo -e "  • Webhook URL    : ${GREEN}POST /api/stripe/webhook/${NC}"
echo -e "  • Fee plateforme : ${GREEN}application_fee_percent=20${NC} (constante — pas settings.PLATFORM_FEE_PERCENT)"
echo -e "  • Source DB      : ${GREEN}webhook CC-07 uniquement${NC}"
echo -e "  • Events gérés   : checkout.session.completed, invoice.paid, invoice.payment_failed,"
echo -e "                     customer.subscription.deleted, account.updated"

echo ""
echo -e "${BOLD}Séquence de lancement :${NC}"
echo -e "  1. ${YELLOW}gh secret set JULES_API_KEY --repo ${REPO}${NC}"
echo -e "  2. Ouvrir GitHub → Issue #${CC01}"
echo -e "  3. Appliquer le label ${GREEN}agent:jules${NC} (manuellement — humain seulement)"
echo -e "  4. 🚂 Night Train démarre automatiquement"
echo -e "  5. Chaque matin : review jules/train → merge → reset train"

echo ""
log_ok "Night Train V2 bootstrapped pour BetAdvisor CONNECT CORE"
echo ""
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${PURPLE}  CONNECT CORE READY FOR NIGHT TRAIN  🚂⚡️                    ${NC}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
