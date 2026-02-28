import logging
from django.db import transaction
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.functions import Greatest
from tickets.models import Ticket, BetSelection
from tickets.services import GeminiOCRService
from sports.models import Match
from decimal import Decimal
from datetime import datetime


logger = logging.getLogger(__name__)


def process_ticket_image(ticket_id):
    """
    Orchestrates the OCR process for a given ticket.
    
    Thread-safe implementation:
    - Receives only ticket_id (not object) to avoid shared memory
    - Uses its own database transactions
    - Comprehensive logging for background monitoring
    - Secure match linking with PostgreSQL Trigram fuzzy search
    """
    logger.info(f"[Thread] Starting OCR processing for ticket {ticket_id}")
    
    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        logger.error(f"[Thread] Ticket {ticket_id} not found in database")
        return

    # Update status to PROCESSING
    ticket.status = Ticket.Status.PROCESSING
    ticket.save()
    logger.info(f"[Thread] Ticket {ticket_id} status updated to PROCESSING")

    ocr_service = GeminiOCRService()
    
    try:
        # Assuming image is stored locally and path is accessible
        # In production with S3, we'd need to download it or pass a URL/bytes
        image_path = ticket.image.path
        
        logger.info(f"[Thread] Calling Gemini OCR for ticket {ticket_id}")
        data = ocr_service.extract_data(image_path)
        
        # Save raw data
        ticket.ocr_raw_data = data
        logger.info(f"[Thread] OCR data extracted for ticket {ticket_id}: {len(data.get('bets', []))} bets found")
        
        # Create BetSelections with secure match linking
        # We use a transaction to ensure atomicity
        with transaction.atomic():
            bets = data.get('bets', [])
            unmatched_bets = []  # Track bets that couldn't be matched
            
            for bet in bets:
                match_name = bet.get('match_name', '')
                selection = bet.get('selection', 'Unknown')
                odds = bet.get('odds', 1.0)
                
                # CRITICAL: Fuzzy match using PostgreSQL Trigram Similarity
                # Similarity threshold: 0.6 (60% confidence minimum - strong matches only)
                match = None
                similarity_threshold = 0.6
                
                if match_name:
                    # Calculate similarity on both home_team and away_team fields
                    # Use the greatest (best) similarity score between the two
                    matches = Match.objects.annotate(
                        similarity=Greatest(
                            TrigramSimilarity('home_team', match_name),
                            TrigramSimilarity('away_team', match_name)
                        )
                    ).filter(
                        similarity__gt=similarity_threshold
                    ).order_by('-similarity')
                    
                    if matches.exists():
                        match = matches.first()
                        # Successfully matched with similarity > threshold
                        BetSelection.objects.create(
                            ticket=ticket,
                            match=match,
                            selection=selection,
                            odds=Decimal(str(odds))
                        )
                        logger.debug(f"[Thread] Bet matched: '{match_name}' -> {match} (similarity > {similarity_threshold})")
                    else:
                        # FAIL-SAFE: No match found with sufficient similarity
                        # DO NOT create BetSelection with arbitrary match
                        unmatched_bets.append({
                            'match_name': match_name,
                            'selection': selection,
                            'odds': odds,
                            'reason': f'No match found with similarity > {similarity_threshold}'
                        })
                        logger.warning(f"[Thread] No match found for '{match_name}' (threshold: {similarity_threshold})")
                else:
                    # No match name provided by OCR
                    unmatched_bets.append({
                        'match_name': '<empty>',
                        'selection': selection,
                        'odds': odds,
                        'reason': 'Empty match name from OCR'
                    })
                    logger.warning(f"[Thread] Empty match name in OCR data")

            # If any bets couldn't be matched, mark ticket for manual review
            if unmatched_bets:
                ticket.status = Ticket.Status.REVIEW_NEEDED
                # Log detailed error information for manual review
                error_log = f"[{datetime.now().isoformat()}] Match linking failed:\n"
                for idx, unmatched in enumerate(unmatched_bets, 1):
                    error_log += f"  Bet #{idx}: '{unmatched['match_name']}' - {unmatched['reason']}\n"
                    error_log += f"    Selection: {unmatched['selection']}, Odds: {unmatched['odds']}\n"
                ticket.ocr_error_log = error_log
                ticket.save()
                logger.warning(
                    f"[Thread] Ticket {ticket.id} requires manual review - "
                    f"{len(unmatched_bets)} bet(s) could not be matched"
                )
            else:
                # All bets successfully matched
                ticket.status = Ticket.Status.VALIDATED
                ticket.save()
                logger.info(f"[Thread] Ticket {ticket.id} processed successfully - all bets matched")

    except Exception as e:
        logger.error(
            f"[Thread] Error processing ticket {ticket_id}: {str(e)}",
            exc_info=True
        )
        ticket.status = Ticket.Status.REJECTED
        ticket.ocr_error_log = f"[{datetime.now().isoformat()}] Processing error: {str(e)}"
        ticket.save()
    
    logger.info(f"[Thread] Completed OCR processing for ticket {ticket_id} - Final status: {ticket.status}")
