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
    
    def analyze_with_gemini_vision(self, image_bytes: bytes, problem_context: str = None, previous_step: str = None) -> dict:
        """
        Alternative pipeline: Use Gemini vision to extract LaTeX and analyze in ONE call.
        Bypasses Pix2Text entirely - Gemini does both OCR and analysis.
        
        Args:
            image_bytes: PNG image of handwritten math
            problem_context: Optional original problem statement for consistency checking
        
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
            # Build prompt with optional problem context and previous step
            context_section = ""
            if problem_context:
                context_section = f"\n\nORIGINAL PROBLEM: {problem_context}\n\nIMPORTANT: Check that the student's work is consistent with the original problem. Flag if they're simplifying in a way that doesn't match the problem's form or if they're solving for the wrong variable."
            
            step_validation = ""
            if previous_step:
                step_validation = f"\n\nPREVIOUS STEP: {previous_step}\n\n⚠️ CRITICAL VALIDATION REQUIRED ⚠️\nThis current step MUST be a mathematically valid transformation from '{previous_step}'.\n\nYOU MUST CHECK:\n1. ARITHMETIC: Verify all numbers are calculated correctly (e.g., 13-5 MUST equal 8, NOT 9 or any other number)\n2. OPERATIONS: Same operation must be applied to BOTH sides of equation\n3. ALGEBRA: Simplification must follow proper algebraic rules\n4. PROGRESSION: This must logically follow from the previous step\n\n❌ IF ANY ARITHMETIC IS WRONG, YOU MUST SET is_correct=false AND provide bounding_box!\n❌ Example: If previous is '2x+5=13' and student wrote '2x=9', this is INCORRECT because 13-5=8, not 9!\n\nDo NOT mark as correct unless the transformation is 100% mathematically valid."
            
            # Log what context Gemini is receiving
            print(f"\n🔍 Gemini Context Debug:")
            print(f"  Problem Context: {problem_context}")
            print(f"  Previous Step: {previous_step}")
            
            prompt = f"""You are a math tutor reviewing a student's handwritten work.{context_section}{step_validation}

Analyze the image and provide:
1. Extract the mathematical expression (convert to plain text, not LaTeX)
2. Determine if the work is correct AND consistent with the original problem AND a valid transformation from the previous step
3. Provide educational feedback
4. If there's an error OR inconsistency OR invalid transformation, identify the EXACT location with a bounding box and provide the correct answer

IMPORTANT FOR EXTRACTED TEXT:
- Use ONLY standard ASCII characters for math: + - * / = ( ) digits and letters
- Use regular hyphen (-) for minus/subtraction, NOT Unicode minus (−), NOT en-dash (–), NOT em-dash (—)
- Use standard parentheses ( ), NOT Unicode variants
- Do NOT use special Unicode symbols, dashes, or other formatting characters
- Example CORRECT: "m^2-5m-14=0" or "x=-10+3"
- Example WRONG: "m²–5m–14=0" or "x=−10+3"

Return JSON format:
{{
    "extracted_text": "the mathematical expression in plain text using ONLY ASCII characters (e.g., x^2+5x+6, -10n+24=-6n+24)",
    "is_correct": true/false/null (null if you cannot determine),
    "feedback": "A brief assessment of the work",
    "hints": ["hint1", "hint2", ...] (helpful suggestions if there are errors),
    "error_types": ["error_type1", ...] (categories like "algebraic_manipulation", "sign_error", "inconsistent_form", etc.),
    "bounding_box": [ymin, xmin, ymax, xmax] (0-1000 scale) OR null if correct/no error to highlight,
    "visual_feedback": "Short, educational HINT about the error (NOT the solution)" OR null if no error,
    "correct_answer": null (we don't provide solutions, only hints)
}}

For bounding_box: Use 0-1000 normalized coordinates to mark the SPECIFIC incorrect part (e.g., wrong number, sign error, inconsistent simplification).

For visual_feedback: Provide EDUCATIONAL HINTS, NOT SOLUTIONS:
- ❌ DON'T say: "Should be: 8"
- ✅ DO say: "Check your arithmetic!" or "Double-check this subtraction" or "Recount carefully"
- ❌ DON'T say: "The answer is x=4"  
- ✅ DO say: "Try dividing both sides" or "One more step to isolate the variable"
- ❌ DON'T say: "This should be negative"
- ✅ DO say: "Watch your signs!" or "Check the sign of this term"

Be constructive, encouraging, and guide the student WITHOUT giving away the answer.
For consistency: If solving "2x + 5 = 13" but student simplifies to "y = 4", flag the inconsistency.
If the expression is incomplete or just shows setup, indicate that in your feedback."""
            
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
                "bounding_box": result.get("bounding_box"),
                "visual_feedback": result.get("visual_feedback"),
                "correct_answer": result.get("correct_answer"),
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
    
    def validate_step_with_llm(self, prev_expr: str, curr_expr: str) -> dict:
        """
        Use LLM to validate a math step and provide feedback.
        Called as fallback when symbolic validation fails.
        
        Args:
            prev_expr: Previous step expression
            curr_expr: Current step expression
            
        Returns:
            dict with 'is_valid' (bool), 'error' (str), 'explanation' (str)
        """
        if not self.gemini_model:
            return {
                "is_valid": False,
                "error": "Complete this step to continue",
                "explanation": "Check your work"
            }
        
        try:
            prompt = f"""You are a strict math tutor validating algebra work step-by-step.

Previous step: {prev_expr}
Current step: {curr_expr}

The current step might be garbled by OCR or incomplete. Your job:

1. If the current step is just arrows/symbols/incomplete (like "→", "—", or gibberish):
   - Mark is_valid = false
   - In "error": Suggest what the ACTUAL next algebraic step should be from the previous step
   
2. If you can infer a real math expression was attempted:
   - Check if that transformation is mathematically correct
   - If wrong, explain the mistake and what they should do instead

Always be specific about the mathematics, not the formatting.

Respond with JSON:
{{
    "is_valid": false (almost always false for incomplete/wrong steps),
    "error": "What they should do mathematically (e.g., 'Distribute -12 across (x-12) to get -12x + 144' or 'This step is incorrect because...')",
    "explanation": "Brief hint about the algebraic operation needed"
}}"""
            
            response = self.gemini_model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean JSON markers
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
                "is_valid": result.get("is_valid", False),
                "error": result.get("error", "Check your work"),
                "explanation": result.get("explanation", "")
            }
            
        except Exception as e:
            print(f"LLM validation error: {e}")
            return {
                "is_valid": False,
                "error": "Complete this step to continue",
                "explanation": "Check your work"
            }


ocr_service = OCRService()
