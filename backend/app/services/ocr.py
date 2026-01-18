from typing import Optional, TYPE_CHECKING
import io
import os
import time
from PIL import Image
from ..config import get_settings

# Lazy imports to avoid startup errors - imported inside load_models()
if TYPE_CHECKING:
    from pix2text import Pix2Text
    from vertexai.generative_models import GenerativeModel


class OCRService:
    """Service for OCR and AI analysis using Pix2Text and Gemini."""
    
    def __init__(self):
        self.p2t_model: Optional[Pix2Text] = None
        self.gemini_model = None
        self.use_google_ai = False
        
    def load_models(self):
        """Load Pix2Text and Gemini models on startup."""
        # Import here to avoid startup errors from pix2text dependencies
        from pix2text import Pix2Text
        
        print("Loading Pix2Text model...")
        # Configure fast image processor for better performance
        self.p2t_model = Pix2Text.from_config(
            total_configs={
                'text_formula': {
                    'formula_config': {
                        'more_processor_configs': {'use_fast': True}
                    }
                }
            }
        )
        print("✅ Pix2Text model loaded")

        settings = get_settings()
        
        # Try Google AI Studio first (simpler API key auth)
        if settings.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.google_api_key)
                self.gemini_model = genai.GenerativeModel("gemini-2.0-flash-exp")
                self.use_google_ai = True
                print("✅ OCR Service: Using Google AI Studio (gemini-2.0-flash-exp)")
                return
            except Exception as e:
                print(f"⚠️  OCR Service: Failed to init Google AI Studio: {e}")
        
        # Fall back to Vertex AI (service account auth)
        if settings.gcp_project_id:
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel
                print("Configuring Vertex AI...")
                # Set auth.json path
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "auth.json"
                
                # Initialize Vertex AI
                vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
                
                # Use gemini-2.5-flash for $300 credits
                self.gemini_model = GenerativeModel("gemini-2.5-flash")
                self.use_google_ai = False
                print("✅ OCR Service: Using Vertex AI (gemini-2.5-flash)")
                return
            except Exception as e:
                print(f"⚠️  OCR Service: Failed to init Vertex AI: {e}")
        
        print("⚠️  Warning: No API configured. AI analysis will be disabled.")
    
    def extract_latex(self, image_bytes: bytes) -> dict:
        """
        Extract text from handwriting using Pix2Text and convert to plain text.
        
        Returns:
            dict with 'latex' (str), 'confidence' (float), 'error' (str or None),
            'timing' (dict with stage timings in milliseconds)
        """
        timing = {}
        start_total = time.time()
        
        if not self.p2t_model:
            return {
                "latex": "",
                "confidence": 0.0,
                "error": "OCR model not loaded",
                "timing": {}
            }
        
        try:
            # Stage 1: Image loading
            start = time.time()
            image = Image.open(io.BytesIO(image_bytes))
            timing["image_load_ms"] = round((time.time() - start) * 1000, 2)
            
            # Stage 2: OCR recognition (Pix2Text)
            start = time.time()
            result = self.p2t_model.recognize(image, resized_shape=608)
            timing["ocr_recognition_ms"] = round((time.time() - start) * 1000, 2)
            
            # Stage 3: Parse OCR result
            start = time.time()
            if isinstance(result, str):
                latex_string = result.strip()
            elif isinstance(result, dict):
                latex_string = result.get('text', '').strip()
            else:
                latex_string = str(result).strip()
            timing["parse_result_ms"] = round((time.time() - start) * 1000, 2)
            
            if not latex_string:
                timing["total_ms"] = round((time.time() - start_total) * 1000, 2)
                return {
                    "latex": "",
                    "confidence": 0.0,
                    "error": "Handwriting unclear - no text detected",
                    "timing": timing
                }
            
            # Stage 4: Convert LaTeX to plain text
            start = time.time()
            plain_text = self._latex_to_plain_text(latex_string)
            timing["latex_conversion_ms"] = round((time.time() - start) * 1000, 2)
            
            timing["total_ms"] = round((time.time() - start_total) * 1000, 2)
            return {
                "latex": plain_text,
                "confidence": 1.0,
                "error": None,
                "timing": timing
            }
            
        except Exception as e:
            timing["total_ms"] = round((time.time() - start_total) * 1000, 2)
            return {
                "latex": "",
                "confidence": 0.0,
                "error": f"OCR failed: {str(e)}",
                "timing": timing
            }
    
    def _latex_to_plain_text(self, latex: str) -> str:
        """Convert LaTeX to readable plain text."""
        text = latex
        
        # Remove $$ and $ delimiters
        text = text.replace('$$', '').replace('$', '').strip()
        
        # Convert fractions: \frac{a}{b} → a/b
        import re
        text = re.sub(r'\\frac\s*\{([^}]+)\}\s*\{([^}]+)\}', r'(\1)/(\2)', text)
        
        # Convert superscripts
        text = re.sub(r'\^\{([^}]+)\}', r'^(\1)', text)
        text = re.sub(r'\^(\w)', r'^\1', text)
        
        # Convert subscripts
        text = re.sub(r'_\{([^}]+)\}', r'_(\1)', text)
        text = re.sub(r'_(\w)', r'_\1', text)
        
        # Convert sqrt
        text = re.sub(r'\\sqrt\s*\{([^}]+)\}', r'√(\1)', text)
        
        # Convert operators
        text = text.replace('\\times', '×')
        text = text.replace('\\cdot', '·')
        text = text.replace('\\div', '÷')
        text = text.replace('\\pm', '±')
        text = text.replace('\\pi', 'π')
        
        # Remove all spaces
        text = re.sub(r'\s+', '', text)
        
        # Clean up simple fractions
        text = re.sub(r'\((\d+)\)/\((\d+)\)', r'\1/\2', text)
        text = re.sub(r'\(([a-z])\)/\((\d+)\)', r'\1/\2', text)
        
        return text
    
    def analyze_with_gemini_vision(self, image_bytes: bytes) -> dict:
        """
        Alternative pipeline: Use Gemini vision to extract LaTeX and analyze in ONE call.
        Bypasses Pix2Text entirely - Gemini does both OCR and analysis.
        
        Returns:
            dict with 'latex' (str), 'is_correct' (bool), 'feedback' (str), 'hints' (list),
            'error' (str or None), 'timing' (dict)
        """
        timing = {}
        start_total = time.time()
        
        if not self.gemini_model:
            return {
                "latex": "",
                "is_correct": None,
                "feedback": "AI analysis unavailable - Gemini not configured",
                "hints": [],
                "error_types": [],
                "error": "Gemini API key not set",
                "timing": {}
            }
        
        try:
            # Stage 1: Prepare image for Gemini
            start = time.time()
            prompt = """You are a math tutor reviewing a student's handwritten work. 

Analyze the image and provide:
1. Extract the mathematical expression (convert to plain text, not LaTeX)
2. Determine if the work is correct
3. Provide educational feedback

Return JSON format:
{
    "extracted_text": "the mathematical expression in plain text (e.g., x^2+5x+6, not LaTeX)",
    "is_correct": true/false/null (null if you cannot determine),
    "feedback": "A brief assessment of the work",
    "hints": ["hint1", "hint2", ...] (helpful suggestions if there are errors),
    "error_types": ["error_type1", ...] (categories like "algebraic_manipulation", "sign_error", etc.)
}

Be constructive and educational. If the expression is incomplete or just shows setup, indicate that in your feedback."""
            
            if self.use_google_ai:
                image = Image.open(io.BytesIO(image_bytes))
                timing["image_prep_ms"] = round((time.time() - start) * 1000, 2)
            else:
                from vertexai.generative_models import Part
                image = Part.from_data(image_bytes, mime_type="image/png")
                timing["image_prep_ms"] = round((time.time() - start) * 1000, 2)
            
            # Stage 2: Call Gemini Vision API
            start = time.time()
            response = self.gemini_model.generate_content([prompt, image])
            timing["gemini_vision_api_call_ms"] = round((time.time() - start) * 1000, 2)
            
            # Stage 4: Parse response
            start = time.time()
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
            timing["parse_response_ms"] = round((time.time() - start) * 1000, 2)
            
            timing["total_ms"] = round((time.time() - start_total) * 1000, 2)
            return {
                "latex": result.get("extracted_text", ""),
                "is_correct": result.get("is_correct"),
                "feedback": result.get("feedback", ""),
                "hints": result.get("hints", []),
                "error_types": result.get("error_types", []),
                "error": None,
                "timing": timing
            }
            
        except Exception as e:
            timing["total_ms"] = round((time.time() - start_total) * 1000, 2)
            return {
                "latex": "",
                "is_correct": None,
                "feedback": f"Gemini vision analysis failed: {str(e)}",
                "hints": [],
                "error_types": [],
                "error": str(e),
                "timing": timing
            }
    
    def detect_visual_errors(self, image_bytes: bytes) -> dict:
        """
        Analyze the handwritten image to locate the specific error visually.
        Returns bounding boxes for the erroneous parts.
        """
        if not self.gemini_model:
            return {"error": "Gemini model not loaded"}

        try:
            prompt = """
            Analyze this handwritten math work. Identify the FIRST mathematical error in the steps.
            
            Return a JSON object with:
            1. "error_detected": boolean
            2. "bounding_box": [ymin, xmin, ymax, xmax] coordinates (0-1000 scale) of the SPECIFIC part of the equation that is incorrect. If no error, use null.
            3. "feedback": Short, targeted feedback explaining exactly what is wrong in that highlighted box.
            
            Focus on the exact algebraic mistake (e.g., sign error, arithmetic error).
            """
            
            if self.use_google_ai:
                image = Image.open(io.BytesIO(image_bytes))
            else:
                from vertexai.generative_models import Part
                image = Part.from_data(image_bytes, mime_type="image/png")
            
            response = self.gemini_model.generate_content([prompt, image])
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            import json
            return json.loads(response_text.strip())
            
        except Exception as e:
            print(f"Visual error detection failed: {e}")
            return {"error": str(e), "error_detected": False}

    def analyze_with_gemini(self, latex_string: str) -> dict:
        """
        Analyze the LaTeX expression using Gemini to provide feedback.
        
        Returns:
            dict with 'is_correct' (bool), 'feedback' (str), 'hints' (list), 'error' (str or None),
            'timing' (dict with stage timings in milliseconds)
        """
        timing = {}
        start_total = time.time()
        
        if not self.gemini_model:
            return {
                "is_correct": None,
                "feedback": "AI analysis unavailable - Gemini not configured",
                "hints": [],
                "error": "Gemini API key not set",
                "timing": {}
            }
        
        try:
            # Stage 1: Build prompt
            start = time.time()
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
            timing["prompt_build_ms"] = round((time.time() - start) * 1000, 2)

            # Stage 2: Call Gemini API
            start = time.time()
            response = self.gemini_model.generate_content(prompt)
            timing["gemini_api_call_ms"] = round((time.time() - start) * 1000, 2)
            
            # Stage 3: Parse response
            start = time.time()
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
            timing["parse_response_ms"] = round((time.time() - start) * 1000, 2)
            
            timing["total_ms"] = round((time.time() - start_total) * 1000, 2)
            return {
                "is_correct": result.get("is_correct"),
                "feedback": result.get("feedback", ""),
                "hints": result.get("hints", []),
                "error_types": result.get("error_types", []),
                "error": None,
                "timing": timing
            }
            
        except Exception as e:
            timing["total_ms"] = round((time.time() - start_total) * 1000, 2)
            return {
                "is_correct": None,
                "feedback": f"Analysis failed: {str(e)}",
                "hints": [],
                "error_types": [],
                "error": str(e),
                "timing": timing
            }


ocr_service = OCRService()
