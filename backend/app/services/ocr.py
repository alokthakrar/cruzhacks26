from typing import Optional
import io
from PIL import Image
from pix2text import Pix2Text
import google.generativeai as genai
from ..config import get_settings


class OCRService:
    """Service for OCR and AI analysis using Pix2Text and Gemini."""
    
    def __init__(self):
        self.p2t_model: Optional[Pix2Text] = None
        self.gemini_model = None
        
    def load_models(self):
        """Load Pix2Text and configure Gemini. Called during app startup."""
        print("🔄 Loading Pix2Text model...")
        self.p2t_model = Pix2Text.from_config()
        print("✅ Pix2Text model loaded successfully")
        
        settings = get_settings()
        if settings.gemini_api_key:
            print("🔄 Configuring Gemini AI...")
            genai.configure(api_key=settings.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("✅ Gemini AI configured successfully")
        else:
            print("⚠️  Warning: GEMINI_API_KEY not set. AI analysis will be disabled.")
    
    def extract_latex(self, image_bytes: bytes) -> dict:
        """
        Extract LaTeX from an image using Pix2Text.
        
        Returns:
            dict with 'latex' (str), 'confidence' (float), and 'error' (str or None)
        """
        if not self.p2t_model:
            return {
                "latex": "",
                "confidence": 0.0,
                "error": "OCR model not loaded"
            }
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            result = self.p2t_model.recognize(image, resized_shape=608)
            
            if isinstance(result, str):
                latex_string = result.strip()
            elif isinstance(result, dict):
                latex_string = result.get('text', '').strip()
            else:
                latex_string = str(result).strip()
            
            if not latex_string:
                return {
                    "latex": "",
                    "confidence": 0.0,
                    "error": "Handwriting unclear - no text detected"
                }
            
            return {
                "latex": latex_string,
                "confidence": 1.0,
                "error": None
            }
            
        except Exception as e:
            return {
                "latex": "",
                "confidence": 0.0,
                "error": f"OCR failed: {str(e)}"
            }
    
    def analyze_with_gemini(self, latex_string: str) -> dict:
        """
        Analyze the LaTeX expression using Gemini to provide feedback.
        
        Returns:
            dict with 'is_correct' (bool), 'feedback' (str), 'hints' (list), 'error' (str or None)
        """
        if not self.gemini_model:
            return {
                "is_correct": None,
                "feedback": "AI analysis unavailable - Gemini not configured",
                "hints": [],
                "error": "Gemini API key not set"
            }
        
        try:
            prompt = f"""You are a math tutor reviewing a student's work. The student has written the following mathematical expression in LaTeX:

{latex_string}

Analyze this expression and provide feedback in the following JSON format:
{{
    "is_correct": true/false/null (null if you cannot determine),
    "feedback": "A brief assessment of the work",
    "hints": ["hint1", "hint2", ...] (helpful suggestions if there are errors),
    "error_types": ["error_type1", ...] (categories like "algebraic_manipulation", "sign_error", "integration_error", etc.)
}}

Be constructive and educational. If the expression is incomplete or just shows setup, indicate that in your feedback."""

            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()
            
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            import json
            result = json.loads(response_text)
            
            return {
                "is_correct": result.get("is_correct"),
                "feedback": result.get("feedback", ""),
                "hints": result.get("hints", []),
                "error_types": result.get("error_types", []),
                "error": None
            }
            
        except Exception as e:
            return {
                "is_correct": None,
                "feedback": f"Analysis failed: {str(e)}",
                "hints": [],
                "error_types": [],
                "error": str(e)
            }


ocr_service = OCRService()
