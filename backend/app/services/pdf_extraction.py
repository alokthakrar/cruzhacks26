import io
import base64
import json
from typing import List, Dict
from PIL import Image
import google.generativeai as genai
from pdf2image import convert_from_bytes
from ..config import get_settings


class PDFExtractionService:
    """Service for extracting math questions from PDFs using Gemini Flash."""
    
    def __init__(self):
        self.gemini_model = None
        
    def load_model(self):
        """Configure Gemini Flash AI model."""
        settings = get_settings()
        if settings.gemini_api_key:
            print("🔄 Configuring Gemini Flash for PDF extraction...")
            genai.configure(api_key=settings.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("✅ Gemini Flash configured successfully")
        else:
            raise ValueError("GEMINI_API_KEY not set - PDF extraction requires Gemini API")
    
    async def extract_questions_from_pdf(self, pdf_bytes: bytes) -> List[Dict]:
        """
        Extract math questions from a PDF using Gemini Flash.
        
        Args:
            pdf_bytes: PDF file as bytes
            
        Returns:
            List of question dicts
        """
        if not self.gemini_model:
            self.load_model()
        
        # Convert PDF to images
        print("🔄 Converting PDF to images...")
        images = convert_from_bytes(pdf_bytes, dpi=150)
        print(f"✅ Converted {len(images)} pages")
        
        all_questions = []
        global_question_number = 1
        
        for page_num, image in enumerate(images, start=1):
            print(f"🔄 Processing page {page_num}/{len(images)}...")
            
            # Convert to base64
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            # Extract questions
            page_questions = await self._extract_questions_from_page(image, page_num, global_question_number)
            
            for q in page_questions:
                q['cropped_image'] = img_base64
                q['bounding_box'] = {"x": 0, "y": 0, "width": image.width, "height": image.height}
            
            all_questions.extend(page_questions)
            global_question_number += len(page_questions)
        
        print(f"✅ Extracted {len(all_questions)} questions")
        return all_questions
    
    async def _extract_questions_from_page(self, image: Image.Image, page_number: int, start_question_num: int) -> List[Dict]:
        """Extract questions from a page using Gemini Vision."""
        try:
            prompt = f"""Analyze this math problem set page and extract ALL questions.

Return JSON format:
{{
    "questions": [
        {{
            "question_number": {start_question_num},
            "text_content": "complete question text",
            "question_type": "derivative|integral|limit|equation|word_problem|algebra|other",
            "difficulty_estimate": "easy|medium|hard",
            "extraction_confidence": 0.95
        }}
    ]
}}

Rules:
- Extract COMPLETE question text
- Number from {start_question_num}
- If no questions, return empty array
- Return ONLY JSON, no other text"""

            response = self.gemini_model.generate_content([prompt, image])
            response_text = response.text.strip()
            
            # Clean JSON
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            result = json.loads(response_text)
            questions = result.get('questions', [])
            
            for q in questions:
                q['page_number'] = page_number
            
            print(f"  ✅ Found {len(questions)} questions")
            return questions
            
        except Exception as e:
            print(f"  ⚠️  Error on page {page_number}: {e}")
            return []


# Global instance
pdf_extraction_service = PDFExtractionService()
