"""Result synchronization service."""
import logging
from datetime import date
from sports.models import Match
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.functions import Greatest
from django.db import transaction

logger = logging.getLogger(__name__)


class ResultSyncService:
    """
    Service for synchronizing match results and updating match statuses.
    
    Uses a multi-strategy approach to match external data with database records:
    1. First, try to match by external_id (if available)
    2. Fallback to fuzzy matching using PostgreSQL Trigram Similarity
    """
    
    def __init__(self):
        self.similarity_threshold = 0.6  # 60% minimum confidence for fuzzy matching
    
    def sync_results_for_date(self, date_obj: date):
        """
        Main synchronization method for a given date.
        
        Args:
            date_obj: The date for which to sync results
            
        Returns:
            dict: Summary of sync operation with counts of updated/failed matches
        """
        logger.info("[ResultSync] Starting synchronization for date: %s", date_obj)
        
        # Fetch mock data (in production, this would call an external API)
        results = self._fetch_mock_data()
        
        stats = {
            'total': len(results),
            'updated': 0,
            'failed': 0,
            'errors': []
        }
        
        for result in results:
            try:
                match = self._find_match(result)
                
                if match:
                    self._update_match(match, result)
                    stats['updated'] += 1
                    logger.info("[ResultSync] Updated: %s vs %s", result['home_team'], result['away_team'])
                else:
                    stats['failed'] += 1
                    error_msg = f"No match found for: {result['home_team']} vs {result['away_team']}"
                    stats['errors'].append(error_msg)
                    logger.warning("[ResultSync] %s", error_msg)
                    
            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Error processing {result['home_team']} vs {result['away_team']}: {str(e)}"
                stats['errors'].append(error_msg)
                logger.exception("[ResultSync] %s", error_msg)
        
        logger.info(
            "[ResultSync] Sync completed: %s/%s updated, %s failed",
            stats['updated'],
            stats['total'],
            stats['failed'],
        )
        return stats
    
    def _fetch_mock_data(self):
        """
        Returns hardcoded test data for match results.
        
        In production, this would fetch data from an external API.
        
        Returns:
            list: List of dictionaries containing match result data
        """
        return [
            {
                'external_id': None,  # Mock matches don't have external IDs yet
                'home_team': 'Real Madrid',
                'away_team': 'Barcelona',
                'home_score': 3,
                'away_score': 1,
                'status': 'FINISHED'
            },
            {
                'external_id': None,
                'home_team': 'PSG',
                'away_team': 'OM',
                'home_score': 2,
                'away_score': 2,
                'status': 'FINISHED'
            }
        ]
    
    def _find_match(self, result_data):
        """
        Find a match in the database using multiple strategies.
        
        Strategy 1: Match by external_id (if available)
        Strategy 2: Fuzzy match using trigram similarity on team names
        
        Args:
            result_data: Dictionary containing match data from external source
            
        Returns:
            Match object if found, None otherwise
        """
        # Strategy 1: Try to find by external_id
        external_id = result_data.get('external_id')
        if external_id:
            try:
                match = Match.objects.get(external_id=external_id)
                logger.debug("[ResultSync] Matched by external_id: %s", external_id)
                return match
            except Match.DoesNotExist:
                logger.debug("[ResultSync] No match found by external_id: %s; trying fuzzy search", external_id)
        
        # Strategy 2: Fuzzy matching using trigram similarity
        home_team = result_data.get('home_team', '')
        away_team = result_data.get('away_team', '')
        
        if not home_team or not away_team:
            logger.warning("[ResultSync] Missing team names; cannot perform fuzzy search")
            return None
        
        # Search based on similarity to both team names
        # We want to find matches where the home_team OR away_team is similar
        matches = Match.objects.annotate(
            home_similarity=TrigramSimilarity('home_team', home_team),
            away_similarity=TrigramSimilarity('away_team', away_team),
            # Calculate the best overall similarity
            max_similarity=Greatest(
                TrigramSimilarity('home_team', home_team),
                TrigramSimilarity('away_team', away_team)
            )
        ).filter(
            max_similarity__gt=self.similarity_threshold
        ).order_by('-max_similarity')
        
        if matches.exists():
            best_match = matches.first()
            similarity_score = best_match.max_similarity
            logger.debug(
                "[ResultSync] Matched by fuzzy search: %s vs %s (similarity: %.2f)",
                best_match.home_team,
                best_match.away_team,
                similarity_score,
            )
            return best_match
        
        logger.debug("[ResultSync] No match found with similarity > %s", self.similarity_threshold)
        return None
    
    def _update_match(self, match, result_data):
        """
        Update a match with result data.
        
        Args:
            match: Match object to update
            result_data: Dictionary containing the new data
        """
        with transaction.atomic():
            # Update scores and status
            match.home_score = result_data['home_score']
            match.away_score = result_data['away_score']
            match.status = result_data['status']
            
            # If external_id is provided and match doesn't have one, save it
            if result_data.get('external_id') and not match.external_id:
                match.external_id = result_data['external_id']
            
            match.save()
            
            # Trigger settlement process (placeholder for now)
            self.trigger_settlement(match)
    
    def settle_bets_for_match(self, match):
        """
        Settlement logic for all bets linked to a finished match.
        
        Algorithm:
        1. Determine the actual match result (1N2):
           - Home Win: home_score > away_score
           - Away Win: away_score > home_score
           - Draw: home_score == away_score
        2. Retrieve all BetSelections linked to this match with PENDING status
        3. For each bet:
           - Normalize bet_selection.selection to lowercase
           - Compare with winning result
           - If match: set outcome to WON
           - If no match: set outcome to LOST
           - Save BetSelection
        4. Use transaction.atomic() to guarantee integrity
        
        Handles simple cases: "Home Win", "Away Win", "Draw", "1", "2", "X"
        
        Args:
            match: The match that has been updated with final scores
        """
        from tickets.models import BetSelection
        
        # Vérification: Le match doit avoir des scores finaux
        if match.home_score is None or match.away_score is None:
            logger.warning("[Settlement] Match %s n'a pas de scores finaux; règlement annulé", match.id)
            return
        
        # Étape 1: Déterminer le résultat réel du match (1N2)
        if match.home_score > match.away_score:
            winning_result = "home win"
            logger.info("[Settlement] Résultat: HOME WIN (%s-%s)", match.home_score, match.away_score)
        elif match.away_score > match.home_score:
            winning_result = "away win"
            logger.info("[Settlement] Résultat: AWAY WIN (%s-%s)", match.home_score, match.away_score)
        else:
            winning_result = "draw"
            logger.info("[Settlement] Résultat: DRAW (%s-%s)", match.home_score, match.away_score)
        
        # Mapping des variantes possibles pour normalisation
        # Permet de gérer "Home Win", "1", "home win", etc.
        result_mappings = {
            "home win": ["home win", "1", "home"],
            "away win": ["away win", "2", "away"],
            "draw": ["draw", "x", "nul"]
        }
        
        # Étape 2: Récupérer tous les BetSelections PENDING pour ce match
        pending_bets = BetSelection.objects.filter(
            match=match,
            outcome=BetSelection.Outcome.PENDING
        )
        
        total_bets = pending_bets.count()
        logger.info("[Settlement] %s paris à traiter pour ce match", total_bets)
        
        if total_bets == 0:
            logger.info("[Settlement] Aucun pari en attente, règlement terminé")
            return
        
        # Compteurs pour statistiques
        won_count = 0
        lost_count = 0
        updated_bets = []
        
        # Étape 3: Traiter chaque pari avec transaction atomique
        with transaction.atomic():
            for bet in pending_bets:
                # Normaliser la sélection du pari en minuscules
                normalized_selection = bet.selection.lower().strip()
                
                # Vérifier si la sélection correspond au résultat gagnant
                is_winner = normalized_selection in result_mappings.get(winning_result, [])
                
                if is_winner:
                    bet.outcome = BetSelection.Outcome.WON
                    won_count += 1
                    logger.debug(
                        "[Settlement] Pari gagnant: selection=%s match=%s vs %s odds=%s",
                        bet.selection,
                        match.home_team,
                        match.away_team,
                        bet.odds,
                    )
                else:
                    bet.outcome = BetSelection.Outcome.LOST
                    lost_count += 1
                    logger.debug("[Settlement] Pari perdant: %s (résultat: %s)", bet.selection, winning_result)
                
                updated_bets.append(bet)
            
            # Sauvegarder tous les BetSelections en une seule requête
            if updated_bets:
                BetSelection.objects.bulk_update(updated_bets, ['outcome'])
        
        # Résumé final
        logger.info(
            "[Settlement] Règlement terminé: %s gagnants, %s perdants sur %s paris",
            won_count,
            lost_count,
            total_bets,
        )
    
    def trigger_settlement(self, match):
        """
        Wrapper method that calls the settlement logic.
        
        Args:
            match: The match that has been updated with final scores
        """
        self.settle_bets_for_match(match)
