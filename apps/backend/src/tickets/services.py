import os
import json
import google.generativeai as genai
from django.conf import settings

class GeminiOCRService:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def extract_data(self, image_path):
        """
        Sends image to Gemini Flash and extracts structured predictions as JSON.
        Focused on prediction verification, NOT gambling data (odds/stake/payout).
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        import PIL.Image
        img = PIL.Image.open(image_path)

        prompt = """
        Extract sports predictions from this betting ticket image as JSON.
        Return ONLY valid JSON. Do not use markdown formatting.
        
        Focus on PREDICTIONS, not betting amounts.
        
        Required Keys:
        - predictions (list of objects):
            - match_name (string, e.g. "PSG vs Real Madrid", "Djokovic vs Nadal")
            - sport (string, one of: FOOTBALL, TENNIS, BASKETBALL, RUGBY, VOLLEYBALL, HANDBALL, HOCKEY, BASEBALL, FORMULA1, MMA)
            - prediction_type (string, one of: MATCH_RESULT, OVER_UNDER, BTTS, GOALSCORER, DOUBLE_CHANCE, CORRECT_SCORE, WINNER, SET_SCORE, TOTAL_POINTS, HANDICAP, OTHER)
            - prediction_value (string, e.g. "Home Win", "Over 2.5", "BTTS Yes", "Mbappé", "1X", "2-1", "Djokovic")
            - match_date (string, date if visible on ticket, format YYYY-MM-DD, or null)
        
        Guidelines for prediction_type:
        - MATCH_RESULT: 1, N, 2, Home Win, Draw, Away Win
        - OVER_UNDER: Over 2.5, Under 3.5, etc.
        - BTTS: Both Teams To Score Yes/No
        - GOALSCORER: A specific player to score
        - DOUBLE_CHANCE: 1X, X2, 12
        - CORRECT_SCORE: Exact score like 2-1
        - WINNER: Winner of a match (tennis, MMA, etc.)
        - SET_SCORE: Score in sets (tennis)
        - TOTAL_POINTS: Total points over/under (basketball)
        - HANDICAP: Handicap betting
        - OTHER: Anything else
        """

        try:
            response = self.model.generate_content([prompt, img])
            response_text = response.text
            
            # Clean up markdown if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            return json.loads(cleaned_text.strip())
            
        except Exception as e:
            print(f"Gemini OCR Error: {e}")
            raise e

