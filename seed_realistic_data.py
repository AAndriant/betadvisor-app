#!/usr/bin/env python
"""
Script pour créer des données de test réalistes avec des personas détaillés
"""
import os
import django
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import sys
sys.path.insert(0, '/app/src')

django.setup()

from users.models import CustomUser
from bets.models import BetTicket

# 10 Personas Détaillés
PERSONAS = [
    {
        "username": "probet_king",
        "email": "probet@betadvisor.com",
        "password": "test123",
        "bio": "Tipster professionnel depuis 2018. Spécialisé dans les paris sportifs européens (foot, tennis). ROI constant de +15% sur 3 ans. Analyse technique et statistiques avancées.",
        "bets": [
            {"match": "Real Madrid vs Barcelona", "selection": "BTTS", "odds": "1.75", "stake": "200", "status": "WON"},
            {"match": "PSG vs Bayern Munich", "selection": "Over 2.5", "odds": "1.90", "stake": "150", "status": "WON"},
            {"match": "Liverpool vs Man City", "selection": "Draw", "odds": "3.50", "stake": "100", "status": "LOST"},
            {"match": "Djokovic vs Nadal (Roland Garros)", "selection": "Djokovic en 4 sets", "odds": "2.20", "stake": "180", "status": "WON"},
            {"match": "Juventus vs Inter Milan", "selection": "Under 2.5", "odds": "2.00", "stake": "120", "status": "WON"},
        ]
    },
    {
        "username": "nba_expert_mike",
        "email": "mike@betadvisor.com",
        "password": "test123",
        "bio": "Analyste NBA depuis 10 ans. Ancien joueur universitaire. Expertise dans les spreads et les totaux. Focus sur les playoffs et les matchs à enjeux. ROI: +22% cette saison.",
        "bets": [
            {"match": "Lakers vs Celtics", "selection": "Lakers -5.5", "odds": "1.91", "stake": "250", "status": "WON"},
            {"match": "Warriors vs Suns", "selection": "Over 225.5", "odds": "1.87", "stake": "200", "status": "WON"},
            {"match": "Bucks vs Nets", "selection": "Bucks ML", "odds": "1.65", "stake": "300", "status": "WON"},
            {"match": "Heat vs 76ers", "selection": "Under 215", "odds": "1.95", "stake": "150", "status": "LOST"},
            {"match": "Nuggets vs Clippers", "selection": "Nuggets +3.5", "odds": "1.88", "stake": "180", "status": "LOST"},
        ]
    },
    {
        "username": "tennis_ace_laura",
        "email": "laura@betadvisor.com",
        "password": "test123",
        "bio": "Passionnée de tennis WTA/ATP. Ancienne joueuse semi-pro. Je suis les tournois du Grand Chelem et Masters 1000. Approche value betting sur les outsiders. ROI moyen: +12%.",
        "bets": [
            {"match": "Alcaraz vs Sinner (US Open)", "selection": "Alcaraz en 4 sets", "odds": "2.10", "stake": "100", "status": "WON"},
            {"match": "Swiatek vs Sabalenka (Wimbledon)", "selection": "Over 22.5 jeux", "odds": "1.85", "stake": "120", "status": "WON"},
            {"match": "Medvedev vs Zverev", "selection": "Medvedev ML", "odds": "1.70", "stake": "150", "status": "LOST"},
            {"match": "Rune vs Tsitsipas", "selection": "Tsitsipas -3.5 jeux", "odds": "1.95", "stake": "80", "status": "WON"},
        ]
    },
    {
        "username": "value_hunter_tom",
        "email": "tom@betadvisor.com",
        "password": "test123",
        "bio": "Value bettor mathématique. Je ne parie que sur des cotes avec EV+ confirmé par mes modèles statistiques. Multi-sports (foot, basket, tennis). Patience et discipline avant tout.",
        "bets": [
            {"match": "Atalanta vs Napoli", "selection": "Atalanta +0.5", "odds": "2.30", "stake": "100", "status": "WON"},
            {"match": "Bayer Leverkusen vs Dortmund", "selection": "BTTS", "odds": "1.65", "stake": "200", "status": "WON"},
            {"match": "Spurs vs Knicks", "selection": "Under 218", "odds": "2.05", "stake": "120", "status": "LOST"},
            {"match": "Monaco vs Lyon", "selection": "Draw HT", "odds": "2.80", "stake": "90", "status": "LOST"},
            {"match": "Federer vs Murray (Exhibition)", "selection": "Murray +4.5 jeux", "odds": "1.75", "stake": "110", "status": "WON"},
        ]
    },
    {
        "username": "ligue1_insider",
        "email": "insider@betadvisor.com",
        "password": "test123",
        "bio": "Spécialiste Ligue 1 & Ligue 2. Journaliste sportif de formation. Accès privilégié aux infos vestiaires. Focus sur les blessures, compos probables et dynamiques d'équipes.",
        "bets": [
            {"match": "PSG vs Marseille", "selection": "PSG -1.5", "odds": "1.80", "stake": "250", "status": "WON"},
            {"match": "Monaco vs Nice", "selection": "Over 2.5", "odds": "1.92", "stake": "150", "status": "WON"},
            {"match": "Lens vs Lille", "selection": "BTTS", "odds": "1.70", "stake": "180", "status": "LOST"},
            {"match": "Rennes vs Strasbourg", "selection": "Draw", "odds": "3.20", "stake": "100", "status": "LOST"},
            {"match": "Toulouse vs Auxerre", "selection": "Under 2.5", "odds": "2.10", "stake": "120", "status": "WON"},
        ]
    },
    {
        "username": "safe_bettor_emma",
        "email": "emma@betadvisor.com",
        "password": "test123",
        "bio": "Approche conservative. Je privilégie les cotes entre 1.50 et 2.00 avec un taux de réussite de 68%. Gestion stricte de bankroll (max 5% par pari). ROI stable de +8%.",
        "bets": [
            {"match": "Man United vs Chelsea", "selection": "BTTS", "odds": "1.60", "stake": "100", "status": "WON"},
            {"match": "Arsenal vs Tottenham", "selection": "Over 2.5", "odds": "1.75", "stake": "100", "status": "WON"},
            {"match": "Bayern vs Leipzig", "selection": "Bayern -1", "odds": "1.85", "stake": "100", "status": "WON"},
            {"match": "Atletico vs Sevilla", "selection": "Under 2.5", "odds": "1.95", "stake": "100", "status": "LOST"},
            {"match": "Inter vs AC Milan", "selection": "Draw", "odds": "3.00", "stake": "50", "status": "LOST"},
        ]
    },
    {
        "username": "combo_master_alex",
        "email": "alex@betadvisor.com",
        "password": "test123",
        "bio": "Roi du pari combiné ! Je construis des combos à 3-5 sélections avec cotes entre @3 et @8. Taux de réussite: 35%, mais les gains compensent largement. Spécialité: foot européen.",
        "bets": [
            {"match": "Combo: Real ML + Liverpool ML + Bayern ML", "selection": "Triplé", "odds": "3.80", "stake": "100", "status": "WON"},
            {"match": "Combo: PSG -1 + Man City -1.5 + Barça ML", "selection": "Triplé", "odds": "5.20", "stake": "80", "status": "LOST"},
            {"match": "Combo: Over 2.5 (4 matchs de Liga)", "selection": "Quadruplé", "odds": "7.50", "stake": "60", "status": "WON"},
            {"match": "Combo: BTTS (Roma + Napoli + Lazio)", "selection": "Triplé", "odds": "4.10", "stake": "90", "status": "LOST"},
        ]
    },
    {
        "username": "esport_legend_kai",
        "email": "kai@betadvisor.com",
        "password": "test123",
        "bio": "Ancien joueur pro CS:GO. Tipster esport (LoL, Valorant, Dota2). Connaissance approfondie des metas, rosters et synergies d'équipes. ROI: +18% sur les majors.",
        "bets": [
            {"match": "T1 vs Gen.G (LoL Worlds)", "selection": "T1 ML", "odds": "1.85", "stake": "200", "status": "WON"},
            {"match": "FaZe vs Vitality (CS2 Major)", "selection": "Vitality +1.5 maps", "odds": "1.70", "stake": "150", "status": "WON"},
            {"match": "Sentinels vs 100T (Valorant)", "selection": "Over 2.5 maps", "odds": "2.00", "stake": "120", "status": "LOST"},
            {"match": "OG vs Liquid (Dota2 TI)", "selection": "OG ML", "odds": "2.20", "stake": "100", "status": "WON"},
        ]
    },
    {
        "username": "underdog_lover_sam",
        "email": "sam@betadvisor.com",
        "password": "test123",
        "bio": "Je ne parie que sur les outsiders (cotes @3 minimum). Approche contrarian. ROI négatif certains mois, mais les coups gagnants payent énormément. Pour les audacieux !",
        "bets": [
            {"match": "Brentford vs Man City", "selection": "Brentford ML", "odds": "9.00", "stake": "50", "status": "LOST"},
            {"match": "Burnley vs Liverpool", "selection": "Draw", "odds": "5.50", "stake": "60", "status": "LOST"},
            {"match": "Getafe vs Real Madrid", "selection": "Getafe +1", "odds": "3.80", "stake": "80", "status": "WON"},
            {"match": "Southampton vs Arsenal", "selection": "Southampton ML", "odds": "7.20", "stake": "50", "status": "LOST"},
            {"match": "Nice vs PSG", "selection": "Nice +0.5", "odds": "3.20", "stake": "100", "status": "LOST"},
        ]
    },
    {
        "username": "stats_wizard_leo",
        "email": "leo@betadvisor.com",
        "password": "test123",
        "bio": "Data scientist appliqué aux paris sportifs. Modèles ML (XGBoost, Random Forest) pour prédire les résultats. Je partage mes plays algorithmiques. ROI sur 500+ paris: +11.3%.",
        "bets": [
            {"match": "Brighton vs Newcastle", "selection": "BTTS", "odds": "1.72", "stake": "180", "status": "WON"},
            {"match": "Fulham vs West Ham", "selection": "Over 2.5", "odds": "1.88", "stake": "150", "status": "WON"},
            {"match": "Everton vs Aston Villa", "selection": "Villa ML", "odds": "2.10", "stake": "140", "status": "WON"},
            {"match": "Crystal Palace vs Wolves", "selection": "Under 2.5", "odds": "1.95", "stake": "120", "status": "LOST"},
            {"match": "Bournemouth vs Nottingham", "selection": "Draw", "odds": "3.40", "stake": "90", "status": "LOST"},
        ]
    },
]

print("🎭 Création des personas détaillés...")

users_created = []

for persona in PERSONAS:
    # Créer l'utilisateur
    user, created = CustomUser.objects.get_or_create(
        username=persona["username"],
        defaults={
            "email": persona["email"],
        }
    )
    
    if created:
        user.set_password(persona["password"])
        user.save()
        print(f"✅ {user.username} créé")
    else:
        print(f"ℹ️  {user.username} existe déjà")
    
    users_created.append(user)
    
    # Créer les paris pour ce persona
    for bet_data in persona["bets"]:
        bet = BetTicket.objects.create(
            author=user,
            match_title=bet_data["match"],
            selection=bet_data["selection"],
            odds=Decimal(bet_data["odds"]),
            stake=Decimal(bet_data["stake"]),
            status=bet_data["status"],
        )
        print(f"   📊 Pari: {bet.match_title} ({bet.status})")

print("\n✨ Données réalistes créées avec succès!")
print(f"👥 {len(users_created)} tipsters avec leurs historiques")
print(f"🎲 {sum(len(p['bets']) for p in PERSONAS)} paris au total")
print("\nTous les comptes utilisent le mot de passe: test123")
