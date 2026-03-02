1. **Ajouter la fonction `createSubscriptionCheckout` dans `apps/mobile/src/services/api.ts`**
   - Fonction qui appelle `POST /api/subscriptions/subscribe/` avec `tipster_id`.
   - Optionnellement avec `success_url` et `cancel_url`.
2. **Ajouter la fonction `getMySubscriptions` dans `apps/mobile/src/services/api.ts`**
   - Fonction qui appelle `GET /api/me/subscriptions/`.
3. **Mettre à jour `apps/mobile/src/components/ProfileHeader.tsx` et `apps/mobile/app/user/[id].tsx`**
   - Modifier `UserProfile` dans `users.ts` pour inclure un champ `is_subscribed` (optionnel, ou on le déduit de getMySubscriptions).
   - Dans `ProfileHeader.tsx`, ajouter un bouton "S'abonner" à côté de ou remplaçant "Suivre" si c'est un tipster et qu'on n'est pas abonné.
   - Ce bouton fera un `router.push({ pathname: '/subscribe', params: { tipsterId: id } })`.
4. **Créer l'écran `apps/mobile/app/subscribe.tsx`**
   - Récupère `tipsterId` via `useLocalSearchParams`.
   - Appelle `createSubscriptionCheckout` pour récupérer `checkout_url`.
   - Affiche une `WebView` avec `checkout_url`.
   - Intercepte la navigation dans la `WebView` pour détecter les URL de retour (ex: `/success` ou `/cancel`).
   - Sur succès, on peut appeler `getMySubscriptions` pour rafraîchir l'état local ou utiliser React Query pour invalider les queries liées aux abonnements/profil, puis faire un `router.replace` vers le profil.
5. **Vérifier les types TypeScript**
   - `npm install typescript --no-save` et `npx tsc --noEmit`
6. **Pre-commit steps**
   - Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.
