# 🏗 BETADVISOR - PROJECT STATUS & MEMORY
> **Last Update:** 27 Janvier 2026
> **Current Phase:** Stabilization & MVP Core Features
> **Critical Rule:** ALWAYS read this file before starting any task.

## 1. 🎯 CORE CONTEXT
- **Project:** Réseau social de paris sportifs (Creator Economy).
- **Stack Backend:** Python / Django 5 / DRF / PostgreSQL.
- **Stack Mobile:** React Native / Expo 54 / NativeWind / TypeScript.
- **AI Ops:** Gemini Flash (Low Cost) pour lecture tickets (OCR).
- **Finance:** Stripe Connect (Express accounts pour Tipsters).
- **Key Constraints:** Low cost architecture, Fail-fast, Unit Economics obsession.

## 2. 🚦 CURRENT STATE (AUDIT RESULT)

### 🟢 BACKEND (Django)
- **Status:** Fonctionnel (Architecture Saine) mais Dettes Techniques Critiques (P0).
- **Auth:** JWT opérationnel, isolation User stricte.
- **OCR:** Service Gemini actif, parsing JSON ok, Threading asynchrone en place.
- **Stripe:** Webhooks & Connect setup (Infrastructure ok), Payout non automatique.

**CRITICAL DEBT (P0 - TO FIX NOW):**
- [x] **Data Integrity:** Doublons dans le modèle BetSelection (Classe Outcome définie 2 fois).
- [x] **Business Logic:** Absence de distinction User/Tipster (Manque modèle TipsterProfile).
- [x] **Security:** Clés API Stripe non sécurisées au démarrage (Pas de Fail-fast).

### 📱 MOBILE (Expo)
- **Status:** Prototype Technique (30%).
- **Architecture:** Expo Router, NativeWind, React Query.
- **Features:** Upload Ticket -> OCR -> Résultat JSON (Fonctionnel).
- **Pending Merge:** Branche `feat/mobile-auth` (Apporte AuthContext & SecureStore) doit être mergée.

**MISSING (P0 - TO BUILD):**
- [ ] **Social:** Feed (Liste des tickets), TicketCard Component.
- [ ] **Profile:** Écran utilisateur.
- [ ] **UX:** Navigation complète post-login.

## 3. 🗺 ACTIVE ROADMAP (Immediate Next Steps)

### STEP 1: BACKEND SANITIZATION (COMPLETED)
**Goal:** Rendre la base de données propre avant d'injecter du trafic.

**Tasks:**
- Refactor `tickets/models.py` (Fix doublons).
- Create `TipsterProfile` (`users` app).
- Secure `settings.py` (Env vars checks).

### STEP 2: MOBILE AUTH MERGE (Pending)
- **Action:** Merger `feat/mobile-auth` vers `main`.
- **Verification:** Tester le login et le stockage du token.

### STEP 3: SOCIAL FEED (After Step 1 & 2)
**Goal:** Transformer le prototype OCR en réseau social.

**Tasks:**
- Create `TicketCard` component (NativeWind).
- Implement Feed Screen (`tickets/list/` endpoint).

## 4. 🧠 TECH GUIDELINES FOR AI AGENTS
- **Source of Truth:** Le Backend (`models.py`) dicte la donnée.
- **Mobile State:** Utiliser React Query pour le server state, Context pour l'auth.
- **No Regression:** Ne jamais supprimer de logique OCR ou Stripe sans audit.
- **Documentation:** Mettre à jour la section 'CURRENT STATE' de ce fichier après chaque modification majeure.
