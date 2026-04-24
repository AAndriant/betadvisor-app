# 📱 BETADVISOR MOBILE — PROJECT STATUS
> **Last Update:** 12 avril 2026
> **Current Phase:** Code Complete — Pending EAS Build
> **Source of Truth:** `.agents/PROJECT_MEMORY.md` (racine repo)

## Status: ✅ CODE COMPLET

L'app mobile est **entièrement fonctionnelle** pour la bêta privée.

### Stack
- **Framework:** React Native + Expo (expo-router)
- **Styling:** NativeWind (Tailwind CSS)
- **State:** React Query (server state) + Context (auth)
- **Types:** TypeScript — 0 erreurs

### Screens (17+)
- Auth: Login, Signup, Forgot Password
- Feed: Home (global feed), Leaderboard
- Betting: Create Ticket (OCR), My Tickets
- Social: User Profile, Comments, My Subscriptions
- Tipster: Tipster Onboarding (WebView), Dashboard
- Stripe: Subscribe (WebView), Checkout Success/Cancel
- Settings: Edit Profile, Security, Legal

### Assets app.json
- Icon: `./assets/icon.png` (placeholder — custom recommandé)
- Splash: `./assets/splash-icon.png` (placeholder)
- Scheme: `betadvisor://` (deep links configurés)

### Ce qui reste (0 code)
- `EXPO_PUBLIC_API_URL` → pointer vers API prod
- `eas build` iOS (TestFlight) + Android (Internal)
- Visuels custom (App Icon, Splash) — optionnel mais recommandé

### ⚠️ Ne pas modifier ce fichier
Toute mise à jour d'avancement doit être faite dans `.agents/PROJECT_MEMORY.md`.
