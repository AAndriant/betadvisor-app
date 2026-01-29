from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Sum
from bets.models import BetTicket

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()
    wallet_balance = serializers.DecimalField(source='wallet.balance', max_digits=12, decimal_places=2, read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'stats', 'wallet_balance', 'avatar_url']

    def get_avatar_url(self, obj):
        return f"https://ui-avatars.com/api/?name={obj.username}&background=10b981&color=fff"

    def get_stats(self, obj):
        """ Calcul dynamique des Unit Economics (ROI, Winrate) """
        bets = BetTicket.objects.filter(author=obj).exclude(status='PENDING')
        total_bets = bets.count()

        if total_bets == 0:
            return {"roi": 0, "win_rate": 0, "total_bets": 0, "total_profit": 0}

        wins = bets.filter(status='WON').count()
        win_rate = (wins / total_bets) * 100

        # Calcul du ROI (Simplifié pour MVP : Somme des (Gains - Mises) / Somme des Mises)
        # Note : En prod, utiliser des agrégations SQL (Sum) pour la performance
        total_stake = 0
        net_profit = 0

        for bet in bets:
            total_stake += bet.stake
            if bet.status == 'WON':
                gain = (bet.stake * bet.odds) - bet.stake
                net_profit += gain
            elif bet.status == 'LOST':
                net_profit -= bet.stake

        roi = (net_profit / total_stake * 100) if total_stake > 0 else 0

        return {
            "roi": round(roi, 2),
            "win_rate": round(win_rate, 1),
            "total_bets": total_bets,
            "total_profit": round(net_profit, 2)
        }
