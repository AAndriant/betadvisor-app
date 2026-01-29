#!/usr/bin/env python
"""
Script pour créer des données de test pour la v1
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import sys
sys.path.insert(0, '/app/src')

django.setup()

from users.models import CustomUser
from bets.models import BetTicket
from social.models import Like, Comment
from decimal import Decimal

# Créer des utilisateurs
print("📝 Création des utilisateurs...")

users_data = [
    {"username": "champion1", "email": "champ1@test.com", "password": "test123"},
    {"username": "probet", "email": "pro@test.com", "password": "test123"},
    {"username": "tipster_king", "email": "king@test.com", "password": "test123"},
]

users = []
for user_data in users_data:
    user, created = CustomUser.objects.get_or_create(
        username=user_data["username"],
        defaults={"email": user_data["email"]}
    )
    if created:
        user.set_password(user_data["password"])
        user.save()
        print(f"✅ {user.username} créé")
    else:
        print(f"ℹ️  {user.username} existe déjà")
    users.append(user)

# Créer des paris pour chaque utilisateur
print("\n📊 Création des paris...")

bets_data = [
    # Champion1 - ROI positif
    {
        "author": users[0],
        "match_title": "PSG vs OM",
        "selection": "PSG gagne",
        "odds": Decimal("1.85"),
        "stake": Decimal("100"),
        "status": BetTicket.BetStatus.WON,
    },
    {
        "author": users[0],
        "match_title": "Real Madrid vs Barcelona",
        "selection": "Plus de 2.5 buts",
        "odds": Decimal("2.10"),
        "stake": Decimal("50"),
        "status": BetTicket.BetStatus.WON,
    },
    {
        "author": users[0],
        "match_title": "Lakers vs Celtics",
        "selection": "Lakers +5.5",
        "odds": Decimal("1.90"),
        "stake": Decimal("75"),
        "status": BetTicket.BetStatus.LOST,
    },
    # Probet - ROI moyennement positif
    {
        "author": users[1],
        "match_title": "Manchester City vs Liverpool",
        "selection": "Draw",
        "odds": Decimal("3.20"),
        "stake": Decimal("100"),
        "status": BetTicket.BetStatus.WON,
    },
    {
        "author": users[1],
        "match_title": "Tennis - Nadal vs Djokovic",
        "selection": "Nadal en 3 sets",
        "odds": Decimal("2.50"),
        "stake": Decimal("80"),
        "status": BetTicket.BetStatus.LOST,
    },
    # Tipster King - ROI faible
    {
        "author": users[2],
        "match_title": "Formula 1 - Monaco GP",
        "selection": "Verstappen victoire",
        "odds": Decimal("1.50"),
        "stake": Decimal("200"),
        "status": BetTicket.BetStatus.WON,
    },
    {
        "author": users[2],
        "match_title": "NFL - Chiefs vs Cowboys",
        "selection": "Chiefs -7",
        "odds": Decimal("1.95"),
        "stake": Decimal("100"),
        "status": BetTicket.BetStatus.LOST,
    },
    {
        "author": users[2],
        "match_title": "NBA - Warriors vs Bucks",
        "selection": "Over 225.5",
        "odds": Decimal("1.85"),
        "stake": Decimal("150"),
        "status": BetTicket.BetStatus.LOST,
    },
]

for bet_data in bets_data:
    bet = BetTicket.objects.create(**bet_data)
    print(f"✅ Pari créé: {bet.match_title} pour {bet.author.username} ({bet.status})")

print("\n🎉 Données de test créées avec succès!")
print(f"👥 {len(users)} utilisateurs")
print(f"🎲 {len(bets_data)} paris")
