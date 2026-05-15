from django.contrib.auth import get_user_model
from django.test import TestCase

from tickets.logic import normalize_ocr_bets
from tickets.models import Ticket
from tickets.serializers import TicketStatusSerializer

User = get_user_model()


class OCRContractTests(TestCase):
    def test_normalize_ocr_bets_keeps_legacy_bets_payload(self):
        payload = {
            'bets': [{
                'match_name': 'PSG vs OM',
                'selection': 'PSG gagne',
                'odds': 1.8,
                'stake': 10,
            }]
        }

        self.assertEqual(normalize_ocr_bets(payload), payload['bets'])

    def test_normalize_ocr_bets_converts_predictions_payload(self):
        payload = {
            'predictions': [{
                'match_name': 'Djokovic vs Nadal',
                'prediction_value': 'Djokovic',
                'match_date': '2026-05-15',
            }]
        }

        bets = normalize_ocr_bets(payload)

        self.assertEqual(len(bets), 1)
        self.assertEqual(bets[0]['match_name'], 'Djokovic vs Nadal')
        self.assertEqual(bets[0]['selection'], 'Djokovic')
        self.assertEqual(bets[0]['odds'], 1.0)

    def test_ticket_status_serializer_exposes_mobile_contract(self):
        user = User.objects.create_user(username='ocruser', password='testpass123')
        ticket = Ticket.objects.create(
            user=user,
            image='tickets/test.jpg',
            ocr_raw_data={
                'bets': [{
                    'match_name': 'PSG vs OM',
                    'selection': 'PSG gagne',
                    'odds': 1.8,
                    'stake': 10,
                }]
            },
        )

        data = TicketStatusSerializer(ticket).data

        self.assertEqual(str(data['ticket_id']), str(ticket.id))
        self.assertEqual(data['ocr_data']['match'], 'PSG vs OM')
        self.assertEqual(data['ocr_data']['selection'], 'PSG gagne')
