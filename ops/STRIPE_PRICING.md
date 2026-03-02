# Configuration du Prix de Souscription Stripe (Beta)

Ce document explique comment créer et configurer le prix fixe pour les souscriptions (Closed Beta). Le système utilise actuellement un prix unique configuré via la variable d'environnement `STRIPE_SUBSCRIPTION_PRICE_ID`.

## 1. Créer le Produit et le Prix dans Stripe

1. Connectez-vous à votre [Dashboard Stripe](https://dashboard.stripe.com/).
2. Vérifiez si vous êtes en **Mode Test** (recommandé pour le développement) ou **Mode Live**.
3. Naviguez vers la section **Catalogue de produits (Product Catalog)**.
4. Cliquez sur **Ajouter un produit (Add product)**.
5. Remplissez les informations du produit :
   - **Nom** : ex. "Abonnement BetAdvisor"
   - **Description** : (optionnel) "Accès premium aux pronostics d'un tipster"
6. Dans la section **Détails des tarifs (Pricing details)** :
   - **Modèle tarifaire** : Tarif standard (Standard pricing)
   - **Prix** : Saisissez le montant (ex. `10.00` €)
   - **Devise** : EUR (ou autre devise choisie)
   - **Type de facturation** : Récurrent (Recurring)
   - **Période de facturation** : Mensuelle (Monthly)
7. Cliquez sur **Enregistrer le produit (Save product)**.

## 2. Récupérer l'ID du Prix

Une fois le produit créé :
1. Sur la page des détails du produit, descendez jusqu'à la section **Tarifs (Pricing)**.
2. Repérez la ligne correspondant au prix que vous venez de créer.
3. Copiez l'ID de l'API (API ID), qui devrait commencer par `price_...` (ex: `price_1QxYxZ...`).

## 3. Configurer l'environnement

Ajoutez cet ID dans le fichier d'environnement `.env` du backend.

### Pour le développement (Test Mode) :
Modifiez `apps/backend/.env` :
```env
STRIPE_SUBSCRIPTION_PRICE_ID=price_test_xxxxxxxxxx
```

### Pour la production (Live Mode) :
Configurez la variable d'environnement sur votre plateforme de déploiement (Heroku, AWS, etc.) avec l'ID du prix de production :
```env
STRIPE_SUBSCRIPTION_PRICE_ID=price_live_xxxxxxxxxx
```

## Remarques importantes

- **Mode Test vs Live** : Les Price IDs sont différents entre l'environnement de Test et le Live de Stripe. Assurez-vous d'utiliser l'ID correspondant à l'environnement.
- **Beta fermée** : Cette configuration permet d'avoir un prix unique fixe pour tous les tipsters pendant la beta. Les évolutions futures permettront la gestion dynamique des prix par chaque tipster.