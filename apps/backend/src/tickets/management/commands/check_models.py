import os
import google.generativeai as genai
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'List available Gemini models to debug 404 errors'

    def handle(self, *args, **options):
        # 1. Configure API
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.stdout.write(self.style.ERROR("GEMINI_API_KEY not found in environment variables."))
            return

        genai.configure(api_key=api_key)

        # 2. List and filter models
        self.stdout.write("Listing available models supporting 'generateContent':")
        try:
            found_any = False
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    self.stdout.write(self.style.SUCCESS(f"- {m.name}"))
                    found_any = True
            
            if not found_any:
                self.stdout.write(self.style.WARNING("No models found with 'generateContent' capability."))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error contacting Google AI API: {e}"))
