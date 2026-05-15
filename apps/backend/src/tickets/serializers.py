"""
Production-grade serializers for Ticket Upload & Listing API.
Includes validation, status mapping, and nested bet selection details.
"""
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import FileExtensionValidator
from django.urls import reverse
from decimal import Decimal

from .models import Ticket, BetSelection


def validate_file_size(value):
    """
    Validates that uploaded file does not exceed 5MB.
    """
    limit_mb = 5
    limit_bytes = limit_mb * 1024 * 1024
    if value.size > limit_bytes:
        raise DjangoValidationError(
            f"La taille du fichier ne doit pas dépasser {limit_mb}MB. "
            f"Taille actuelle: {value.size / (1024 * 1024):.2f}MB"
        )


class BetSelectionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for BetSelection with match name and outcome.
    Used in nested representation for ticket upload response.
    """
    match_name = serializers.SerializerMethodField()
    
    class Meta:
        model = BetSelection
        fields = ['id', 'match_name', 'selection', 'odds', 'outcome']
        read_only_fields = ['id', 'match_name', 'selection', 'odds', 'outcome']
    
    def get_match_name(self, obj):
        """Returns the match display name."""
        return str(obj.match) if obj.match else "Match inconnu"


class TicketStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for status polling endpoint.
    Used by mobile to check if OCR processing is complete.
    """
    bet_selections = BetSelectionDetailSerializer(source='selections', many=True, read_only=True)
    status = serializers.SerializerMethodField()
    warning_message = serializers.SerializerMethodField()
    ticket_id = serializers.UUIDField(source='id', read_only=True)
    ocr_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_id', 'status', 'bet_selections', 'ocr_data', 'warning_message']
        read_only_fields = ['id', 'ticket_id', 'status', 'bet_selections', 'ocr_data', 'warning_message']
    
    def get_status(self, obj):
        """Maps internal statuses to mobile-friendly codes."""
        MOBILE_STATUS_MAPPING = {
            'REVIEW_NEEDED': 'FAILED_OCR',
            'REJECTED': 'FAILED_OCR',
        }
        return MOBILE_STATUS_MAPPING.get(obj.status, obj.status)
    
    def get_warning_message(self, obj):
        """Returns error message for failed OCR."""
        if obj.status in ['REVIEW_NEEDED', 'REJECTED']:
            if obj.ocr_error_log:
                return obj.ocr_error_log
            return "Analyse automatique échouée. Vérification manuelle en cours."
        return None

    def get_ocr_data(self, obj):
        """
        Mobile-friendly OCR summary for the legacy post form.

        The raw OCR payload is preserved in `ocr_raw_data`, while this shape
        gives React Native stable keys for autofill.
        """
        raw = obj.ocr_raw_data or {}
        first_bet = {}
        if isinstance(raw.get('bets'), list) and raw['bets']:
            first_bet = raw['bets'][0] or {}
        elif isinstance(raw.get('predictions'), list) and raw['predictions']:
            prediction = raw['predictions'][0] or {}
            first_bet = {
                'match_name': prediction.get('match_name'),
                'selection': prediction.get('prediction_value'),
                'odds': prediction.get('odds'),
                'stake': prediction.get('stake'),
            }

        first_selection = obj.selections.first()
        return {
            'match': first_bet.get('match_name') or (
                str(first_selection.match) if first_selection else ''
            ),
            'selection': first_bet.get('selection') or (
                first_selection.selection if first_selection else ''
            ),
            'odds': first_bet.get('odds') or (
                str(first_selection.odds) if first_selection else None
            ),
            'stake': first_bet.get('stake') or (
                str(first_selection.stake) if first_selection else None
            ),
            'bets': raw.get('bets') or [],
            'predictions': raw.get('predictions') or [],
        }


class TicketUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for async ticket upload.
    
    Features:
    - Image validation (format & size)
    - Returns status_url for polling
    - Immediate response (202 Accepted)
    """
    image = serializers.ImageField(
        write_only=True,
        required=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png'],
                message="Seuls les fichiers JPG, JPEG et PNG sont acceptés."
            ),
            validate_file_size
        ]
    )
    status_url = serializers.SerializerMethodField()
    ticket_id = serializers.UUIDField(source='id', read_only=True)
    created_at = serializers.DateTimeField(source='created', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_id',
            'image',
            'status',
            'created_at',
            'status_url'
        ]
        read_only_fields = ['id', 'ticket_id', 'status', 'created_at', 'status_url']
    
    def get_status_url(self, obj):
        """
        Returns the absolute URL for status polling.
        Mobile will use this to check OCR completion.
        """
        request = self.context.get('request')
        url = reverse('tickets:ticket-status', kwargs={'pk': obj.id})
        return request.build_absolute_uri(url) if request else url


class TicketListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for ticket list view.
    Optimized for performance with minimal data.
    """
    thumbnail_url = serializers.SerializerMethodField()
    estimated_roi = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(source='created', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id',
            'status',
            'status_display',
            'created_at',
            'thumbnail_url',
            'estimated_roi'
        ]
    
    def get_thumbnail_url(self, obj):
        """Returns the image URL from storage (S3 or media)."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_estimated_roi(self, obj):
        """
        Calculates potential return on investment based on bet selections.
        Formula: Product of all odds - 1 (assuming €1 stake).
        """
        selections = obj.selections.all()
        if not selections:
            return Decimal('0.00')
        
        # Calculate combined odds (parlay/accumulator)
        combined_odds = Decimal('1.00')
        for selection in selections:
            combined_odds *= selection.odds
        
        # ROI = (combined_odds - 1) * 100%
        roi = (combined_odds - Decimal('1.00')) * Decimal('100.00')
        return round(roi, 2)
