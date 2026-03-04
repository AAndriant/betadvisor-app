"""
seed_demo — Populate the database with realistic demo data for design testing.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --flush   # Wipe and re-seed

Creates:
    - 2 tipster users (with TipsterProfile + ConnectedAccount + GlobalStats + Badges)
    - 3 punter users (with GlobalStats)
    - 10 sports
    - 20+ bets across multiple sports and statuses
    - Likes, comments, follows
    - Notifications
    - Subscriptions (mock)
"""
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import CustomUser, TipsterProfile
from bets.models import BetTicket
from sports.models import Sport
from social.models import Like, Comment, Follow
from notifications.models import Notification
from subscriptions.models import Subscription
from gamification.models import UserGlobalStats, UserSportStats, UserBadge
from connect.models import ConnectedAccount


DEMO_SPORTS = [
    'Football', 'Tennis', 'Basketball', 'Rugby', 'Handball',
    'Volleyball', 'Hockey', 'Baseball', 'Formula 1', 'MMA',
]

DEMO_BETS = [
    # (match_title, selection, odds, stake, status, sport, is_premium)
    ("PSG vs Real Madrid", "PSG Win", "2.10", "50.00", "WON", "Football", True),
    ("Barcelona vs Bayern Munich", "Over 2.5 Goals", "1.75", "30.00", "WON", "Football", False),
    ("Man City vs Liverpool", "BTTS Yes", "1.85", "25.00", "LOST", "Football", True),
    ("Djokovic vs Nadal", "Djokovic Win", "1.65", "40.00", "WON", "Tennis", True),
    ("Alcaraz vs Sinner", "Over 3.5 Sets", "2.20", "20.00", "PENDING", "Tennis", False),
    ("Lakers vs Celtics", "Lakers +5.5", "1.90", "35.00", "WON", "Basketball", True),
    ("Warriors vs Bucks", "Under 230.5", "1.80", "30.00", "LOST", "Basketball", False),
    ("France vs England", "France Win", "1.55", "50.00", "PENDING", "Rugby", True),
    ("Verstappen P1", "Verstappen Win", "1.40", "60.00", "WON", "Formula 1", False),
    ("PSG Handball vs Nantes", "PSG Handball Win", "1.30", "45.00", "WON", "Handball", False),
    ("Olympique Lyon vs Monaco", "Draw", "3.50", "15.00", "LOST", "Football", True),
    ("Medvedev vs Tsitsipas", "Tsitsipas Win", "2.40", "20.00", "PENDING", "Tennis", True),
    ("Heat vs 76ers", "Heat ML", "2.15", "25.00", "WON", "Basketball", False),
    ("McGregor vs Poirier", "McGregor KO R1", "3.80", "10.00", "LOST", "MMA", True),
    ("Nantes vs Montpellier", "Nantes Win", "1.95", "30.00", "PENDING", "Volleyball", False),
    ("Rangers vs Bruins", "Over 5.5", "2.05", "20.00", "WON", "Hockey", False),
    ("Yankees vs Red Sox", "Yankees Win", "1.70", "40.00", "WON", "Baseball", False),
    ("Marseille vs Lens", "1X", "1.35", "50.00", "WON", "Football", True),
    ("Atletico vs Inter", "Under 2.5", "1.90", "25.00", "LOST", "Football", False),
    ("Rublev vs Ruud", "Rublev Win", "1.80", "30.00", "PENDING", "Tennis", True),
]

DEMO_COMMENTS = [
    "Excellent pick ! 🔥",
    "Je suis entièrement d'accord avec cette analyse",
    "Un peu risqué mais je follow quand même",
    "Belle cote, bien vu !",
    "J'aurais plutôt pris l'over perso",
    "Toujours pertinent, merci pour le partage 💪",
    "Ça passe easy, confiance !",
    "First time following, let's go !",
]


class Command(BaseCommand):
    help = 'Seed database with realistic demo data for design testing'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Delete all demo data before seeding')

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING("Flushing demo data..."))
            for model in [UserBadge, UserSportStats, UserGlobalStats, ConnectedAccount,
                          Notification, Subscription, Comment, Like, Follow, BetTicket]:
                model.objects.all().delete()
            CustomUser.objects.filter(username__startswith='demo_').delete()
            self.stdout.write(self.style.SUCCESS("Flushed."))

        # 1. Sports
        self.stdout.write("Creating sports...")
        sports = {}
        for name in DEMO_SPORTS:
            sport, _ = Sport.objects.get_or_create(name=name)
            sports[name] = sport
        self.stdout.write(f"  → {len(sports)} sports")

        # 2. Users
        self.stdout.write("Creating users...")
        tipster1 = self._create_user('demo_tipster1', 'tipster1@betadvisor.test', is_tipster=True,
                                      bio="🏆 Pro tipster, Football & Tennis specialist. +34% ROI sur 500+ paris.")
        tipster2 = self._create_user('demo_tipster2', 'tipster2@betadvisor.test', is_tipster=True,
                                      bio="🎯 Multi-sport analyst. Data-driven picks since 2022.")
        punter1 = self._create_user('demo_punter1', 'punter1@betadvisor.test',
                                     bio="Just a casual bettor having fun 🎲")
        punter2 = self._create_user('demo_punter2', 'punter2@betadvisor.test',
                                     bio="Football addict ⚽")
        punter3 = self._create_user('demo_punter3', 'punter3@betadvisor.test', bio="")

        all_users = [tipster1, tipster2, punter1, punter2, punter3]
        tipsters = [tipster1, tipster2]

        # 3. Bets
        self.stdout.write("Creating bets...")
        bets = []
        for i, (title, sel, odds, stake, status, sport_name, is_premium) in enumerate(DEMO_BETS):
            author = tipsters[i % 2] if is_premium else random.choice(all_users)
            bet = BetTicket.objects.create(
                author=author,
                match_title=title,
                selection=sel,
                odds=Decimal(odds),
                stake=Decimal(stake),
                status=status,
                is_premium=is_premium,
                payout=Decimal(odds) * Decimal(stake) if status == 'WON' else None,
                settled_at=timezone.now() - timedelta(hours=random.randint(1, 72)) if status != 'PENDING' else None,
                created_at=timezone.now() - timedelta(hours=random.randint(1, 168)),
            )
            # Force created_at since auto_now_add
            BetTicket.objects.filter(pk=bet.pk).update(
                created_at=timezone.now() - timedelta(hours=random.randint(1, 168))
            )
            bets.append(bet)
        self.stdout.write(f"  → {len(bets)} bets")

        # 4. Social (likes, comments, follows)
        self.stdout.write("Creating social interactions...")
        like_count = 0
        comment_count = 0
        for bet in bets:
            # Random likes from non-authors
            likers = [u for u in all_users if u != bet.author]
            for u in random.sample(likers, k=min(random.randint(1, 4), len(likers))):
                Like.objects.get_or_create(user=u, bet=bet)
                like_count += 1

            # Random comments
            if random.random() > 0.4:
                commenter = random.choice([u for u in all_users if u != bet.author])
                Comment.objects.create(
                    user=commenter,
                    bet=bet,
                    content=random.choice(DEMO_COMMENTS),
                )
                comment_count += 1

        # Follows
        follow_pairs = [
            (punter1, tipster1), (punter2, tipster1), (punter3, tipster1),
            (punter1, tipster2), (punter2, tipster2),
            (punter3, punter1),
        ]
        for follower, followed in follow_pairs:
            Follow.objects.get_or_create(follower=follower, followed=followed)
        self.stdout.write(f"  → {like_count} likes, {comment_count} comments, {len(follow_pairs)} follows")

        # 5. Gamification
        self.stdout.write("Creating gamification data...")
        for user in all_users:
            user_bets = BetTicket.objects.filter(author=user)
            wins = user_bets.filter(status='WON').count()
            losses = user_bets.filter(status='LOST').count()
            total = user_bets.exclude(status='PENDING').count()

            halo = 'none'
            if wins >= 8:
                halo = 'gold'
            elif wins >= 5:
                halo = 'silver'
            elif wins >= 3:
                halo = 'bronze'

            gs, _ = UserGlobalStats.objects.update_or_create(
                user=user,
                defaults={
                    'total_bets': total,
                    'wins': wins,
                    'losses': losses,
                    'current_streak': min(wins, 3),
                    'max_streak': min(wins, 5),
                    'reputation_score': wins * 10,
                    'profile_halo_color': halo,
                    'units_returned': Decimal(str(wins * 1.5)),
                }
            )

            # Sport stats for tipsters
            if user in tipsters:
                for sport_name in ['Football', 'Tennis', 'Basketball']:
                    sport_bets = user_bets.filter(match_title__icontains=sport_name.lower()[:4])
                    s_wins = sport_bets.filter(status='WON').count()
                    s_total = sport_bets.exclude(status='PENDING').count()
                    if s_total > 0:
                        UserSportStats.objects.update_or_create(
                            user=user, sport=sports[sport_name],
                            defaults={
                                'total_bets': s_total,
                                'wins': s_wins,
                                'losses': s_total - s_wins,
                                'units_returned': Decimal(str(s_wins * 1.3)),
                            }
                        )

        # Badges
        badge_assignments = [
            (tipster1, 'First Win', 'Remporté le premier pari'),
            (tipster1, 'Hot Streak 3', '3 paris gagnés d\'affilée'),
            (tipster1, 'Hot Streak 5', '5 paris gagnés d\'affilée'),
            (tipster1, 'Sharp Shooter', 'Winrate > 60%'),
            (tipster2, 'First Win', 'Remporté le premier pari'),
            (tipster2, 'Hot Streak 3', '3 paris gagnés d\'affilée'),
            (punter1, 'First Win', 'Remporté le premier pari'),
        ]
        for user, badge, desc in badge_assignments:
            UserBadge.objects.get_or_create(
                user=user, badge_name=badge,
                defaults={'description': desc}
            )
        self.stdout.write(f"  → {len(badge_assignments)} badges")

        # 6. Notifications
        self.stdout.write("Creating notifications...")
        notifs = [
            (punter1, tipster1, 'NEW_FOLLOWER', "Nouveau follower", "demo_tipster1 vous suit maintenant 🔥"),
            (punter2, tipster1, 'PREDICTION_RESOLVED', "Pari gagné !", "demo_tipster1 a gagné son dernier pari ✅"),
            (punter1, punter2, 'NEW_LIKE', "Like", "demo_punter2 a aimé votre pari"),
            (tipster1, punter1, 'NEW_FOLLOWER', "Nouvel abonné", "demo_punter1 s'est abonné à vos pronostics 🎉"),
            (tipster1, punter3, 'NEW_COMMENT', "Commentaire", "demo_punter3 a commenté votre pari"),
            (punter2, tipster2, 'NEW_LIKE', "Like", "demo_tipster2 a publié un nouveau pari"),
        ]
        for recipient, sender, notif_type, title, body in notifs:
            Notification.objects.create(
                recipient=recipient, sender=sender,
                notification_type=notif_type,
                title=title, body=body,
                is_read=random.random() > 0.5,
            )
        self.stdout.write(f"  → {len(notifs)} notifications")

        # 7. Subscriptions (mock — no real Stripe)
        self.stdout.write("Creating mock subscriptions...")
        Subscription.objects.get_or_create(
            follower=punter1, tipster=tipster1,
            defaults={
                'stripe_subscription_id': 'sub_demo_001',
                'stripe_customer_id': 'cus_demo_001',
                'status': 'active',
                'current_period_end': timezone.now() + timedelta(days=25),
            }
        )
        Subscription.objects.get_or_create(
            follower=punter2, tipster=tipster1,
            defaults={
                'stripe_subscription_id': 'sub_demo_002',
                'stripe_customer_id': 'cus_demo_002',
                'status': 'active',
                'current_period_end': timezone.now() + timedelta(days=15),
            }
        )

        self.stdout.write(self.style.SUCCESS("\n✅ Demo data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("   Accounts (password: demo1234):"))
        for u in all_users:
            role = "TIPSTER" if u in tipsters else "PUNTER"
            self.stdout.write(f"     → {u.username} ({role})")

    def _create_user(self, username, email, is_tipster=False, bio=""):
        user, created = CustomUser.objects.get_or_create(
            username=username,
            defaults={'email': email, 'bio': bio}
        )
        if created:
            user.set_password('demo1234')
            user.save()

        if is_tipster and not hasattr(user, 'tipster_profile'):
            TipsterProfile.objects.create(
                user=user,
                subscription_price=Decimal('9.99'),
            )
            # Mock connected account
            ConnectedAccount.objects.get_or_create(
                user=user,
                defaults={
                    'stripe_account_id': f'acct_demo_{username}',
                    'charges_enabled': True,
                    'payouts_enabled': True,
                    'onboarding_completed': True,
                }
            )

        return user
