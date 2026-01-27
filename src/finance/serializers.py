from rest_framework import serializers
from .models import Plan

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'titre', 'description', 'price_amount', 'tipster', 'is_active', 'stripe_product_id', 'stripe_price_id']
        read_only_fields = ['tipster', 'stripe_product_id', 'stripe_price_id']
