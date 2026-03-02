# QA Steps for Token Refresh Interceptor (Issue #39)

Ce document décrit la procédure de test manuel pour valider le comportement du rafraîchissement de token (refresh token interceptor).

## Prérequis
- Avoir un compte utilisateur valide avec lequel se connecter sur l'app mobile.
- L'application mobile connectée à un serveur backend local (assurez-vous que `EXPO_PUBLIC_API_URL` pointe bien vers le backend).

## Scénarios de Test

### Scénario 1 : Rafraîchissement automatique réussi
1. Lancez l'application et connectez-vous avec vos identifiants.
2. Interagissez avec l'application (ex: visitez le Feed) pour vous assurer que les appels réseau fonctionnent (statut 200 OK).
3. Connectez-vous à la base de données du backend ou forcez l'expiration de votre Access Token via le shell Django (ou modifiez les paramètres DRF `SIMPLE_JWT` pour un `ACCESS_TOKEN_LIFETIME` très court, ex: 1 minute).
4. Attendez l'expiration de l'Access Token (ou forcez son invalidation).
5. Interagissez à nouveau avec l'application (ex: rechargez le Feed).
6. **Résultat attendu :**
   - L'appel original échoue (401 Unauthorized).
   - L'intercepteur intercepte l'erreur 401 et appelle `/api/auth/token/refresh/` avec le Refresh Token.
   - Le refresh réussit (200 OK).
   - L'appel original est rejoué avec succès et la vue (Feed) se recharge de manière transparente, sans vous déconnecter.

### Scénario 2 : Blocage des requêtes concurrentes (Mutex)
1. Configurez un Access Token expiré comme dans le Scénario 1.
2. Dans l'application, déclenchez plusieurs requêtes réseau en même temps (ex: navigation rapide ou montage d'un composant déclenchant plusieurs fetch simultanés).
3. Observez les logs réseau (via React Native Debugger ou l'inspecteur web si sur web).
4. **Résultat attendu :**
   - Une seule requête `/api/auth/token/refresh/` doit être effectuée.
   - Les autres requêtes bloquées attendent que le token soit rafraîchi avant d'être rejouées avec le nouveau token.

### Scénario 3 : Refresh Token expiré / invalidé (Déconnexion propre)
1. Connectez-vous normalement.
2. Forcez l'expiration ou supprimez **à la fois** votre Access Token et votre Refresh Token via le backend (ou réduisez `REFRESH_TOKEN_LIFETIME` à une valeur minimale).
3. Interagissez avec l'application pour déclencher une requête nécessitant une authentification.
4. **Résultat attendu :**
   - L'appel échoue (401).
   - L'intercepteur tente un rafraîchissement avec le Refresh Token expiré ou invalide.
   - L'appel de rafraîchissement échoue (401 / 403).
   - L'application efface correctement les tokens stockés (SecureStore/localStorage) et redirige immédiatement l'utilisateur vers l'écran de Login.

### Scénario 4 : Vérification du Logout manuel
1. Connectez-vous à l'application.
2. Utilisez le bouton/action de déconnexion.
3. Vérifiez que vous êtes bien redirigé vers l'écran de Login.
4. Tentez de revenir en arrière (back navigation) pour vous assurer que l'accès au contenu protégé est impossible sans nouvelle connexion.
