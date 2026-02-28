import os
import json
import google.generativeai as genai
from django.conf import settings

class GeminiOCRService:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            # Fallback to settings if not in env directly (though settings usually read env)
            api_key = getattr(settings, 'GEMINI_API_KEY', None)
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
            
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def extract_data(self, image_path):
        """
        Sends image to Gemini Flash and extracts bet details as JSON.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at {image_path}")

        # Upload the file to Gemini
        # Note: For efficiency in production, we might send bytes directly if supported,
        # but the library often handles paths or PIL images.
        # Using PIL image is safer for local/server processing.
        import PIL.Image
        img = PIL.Image.open(image_path)

        prompt = """
        Extract bet details from this betting ticket image as JSON.
        Return ONLY valid JSON. Do not use markdown formatting.
        
        Required Keys:
        - bookmaker (string)
        - total_stake (number)
        - potential_payout (number)
        - bets (list of objects)
            - match_name (string, e.g. "Team A vs Team B")
            - selection (string, e.g. "Home Win", "Over 2.5")
            - odds (number)
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
