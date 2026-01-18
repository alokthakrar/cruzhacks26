from typing import List, Optional
import io
import base64
import json
import os
import fitz  # PyMuPDF
from PIL import Image
from ..config import get_settings


EXTRACTION_PROMPT_TEMPLATE = """Analyze this math problem sheet image and identify all individual questions/problems.

IMPORTANT: The image dimensions are {width}x{height} pixels. Use these exact dimensions when calculating bounding boxes.

For each question found, provide:
1. The complete text content of the question
2. Any mathematical expressions in LaTeX format
3. The question type (integral, derivative, equation, word_problem, series, limit, other)
4. A difficulty estimate (easy, medium, hard)
5. The bounding box coordinates in pixels (x, y, width, height) that tightly encloses the question
   - x: pixels from LEFT edge of image (0 to {width})
   - y: pixels from TOP edge of image (0 to {height})
   - width: width of bounding box in pixels
   - height: height of bounding box in pixels

Return your response as JSON only, with no markdown formatting:
{{
    "questions": [
        {{
            "question_number": 1,
            "text_content": "Find the derivative of f(x) = x^3 + 2x",
            "latex_content": "f(x) = x^3 + 2x",
            "question_type": "derivative",
            "difficulty_estimate": "easy",
            "bounding_box": {{"x": 50, "y": 100, "width": 400, "height": 60}},
            "confidence": 0.95
        }}
    ],
    "total_questions": 1
}}

Be precise with bounding boxes - they should tightly enclose each question including any diagrams or figures.
Add 10-20 pixels of padding around the text for readability.
If no questions are found, return {{"questions": [], "total_questions": 0}}."""


class PDFExtractorService:
    """Service for extracting math questions from PDF documents using Gemini 2.5 Flash."""

    def __init__(self):
        self.gemini_model = None
        self.dpi = 200  # Resolution for PDF-to-image conversion

    def load_model(self):
        """Configure Vertex AI Gemini. Called during app startup."""
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        settings = get_settings()
        if settings.gcp_project_id:
            print("🔄 Configuring Vertex AI for PDF extraction...")
            # Set auth.json path
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "auth.json"
            
            # Initialize Vertex AI
            vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
            
            # Use gemini-2.5-flash for $300 credits
            self.gemini_model = GenerativeModel("gemini-2.5-flash")
            print("✅ Vertex AI configured for PDF extraction with gemini-2.5-flash")
        else:
            print("⚠️  Warning: GCP_PROJECT_ID not set. PDF extraction will be disabled.")

    def pdf_to_images(self, pdf_bytes: bytes) -> List[bytes]:
        """
        Convert PDF pages to PNG images.

        Args:
            pdf_bytes: Raw PDF file bytes

        Returns:
            List of PNG image bytes, one per page
        """
        images = []
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Render at specified DPI
                mat = fitz.Matrix(self.dpi / 72, self.dpi / 72)
                pix = page.get_pixmap(matrix=mat)
                img_bytes = pix.tobytes("png")
                images.append(img_bytes)
            doc.close()
        except Exception as e:
            raise PDFConversionError(f"Failed to convert PDF to images: {str(e)}")
        return images

    def extract_page_elements(self, pdf_bytes: bytes, page_number: int) -> dict:
        """
        Extract images and text blocks with precise bounding boxes using PyMuPDF.

        Args:
            pdf_bytes: Raw PDF file bytes
            page_number: 0-indexed page number

        Returns:
            Dict with:
                - images: List of dicts with {bbox, image_bytes, xref}
                - text_blocks: List of dicts with {bbox, text, block_type}
                - page_rect: Dict with page dimensions {width, height}
        """
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page = doc[page_number]

            # Get page dimensions (in points, 72 DPI)
            page_rect = page.rect
            scale = self.dpi / 72  # Scale factor for our target DPI

            # Extract embedded images with bounding boxes
            images = []
            image_list = page.get_images(full=True)
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                # Get image bounding box (where it's placed on the page)
                img_rects = page.get_image_rects(xref)
                for rect in img_rects:
                    # Scale bounding box to match rendered image DPI
                    bbox = {
                        "x": int(rect.x0 * scale),
                        "y": int(rect.y0 * scale),
                        "width": int((rect.x1 - rect.x0) * scale),
                        "height": int((rect.y1 - rect.y0) * scale),
                    }
                    # Extract the actual image
                    try:
                        base_image = doc.extract_image(xref)
                        img_bytes = base_image["image"]
                        images.append({
                            "bbox": bbox,
                            "image_bytes": img_bytes,
                            "xref": xref,
                            "image_index": img_index,
                        })
                    except:
                        # Skip images that can't be extracted
                        pass

            # Extract text blocks with bounding boxes
            text_blocks = []
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block["type"] == 0:  # Text block
                    rect = block["bbox"]
                    bbox = {
                        "x": int(rect[0] * scale),
                        "y": int(rect[1] * scale),
                        "width": int((rect[2] - rect[0]) * scale),
                        "height": int((rect[3] - rect[1]) * scale),
                    }
                    # Extract text content
                    text_content = ""
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text_content += span.get("text", "")
                        text_content += "\n"
                    text_blocks.append({
                        "bbox": bbox,
                        "text": text_content.strip(),
                        "block_type": "text",
                    })

            doc.close()

            return {
                "images": images,
                "text_blocks": text_blocks,
                "page_rect": {
                    "width": int(page_rect.width * scale),
                    "height": int(page_rect.height * scale),
                },
            }

        except Exception as e:
            raise PDFConversionError(f"Failed to extract page elements: {str(e)}")

    def extract_questions_from_page(
        self,
        page_image_bytes: bytes,
        page_number: int
    ) -> tuple[List[dict], dict]:
        """
        Use Gemini to identify and extract questions from a single page image.

        Args:
            page_image_bytes: PNG image bytes of the page
            page_number: 1-indexed page number

        Returns:
            Tuple of (list of question dicts, debug info dict)
        """
        if not self.gemini_model:
            raise GeminiExtractionError("Gemini model not configured")

        try:
            # Create PIL image for Gemini
            image = Image.open(io.BytesIO(page_image_bytes))
            img_width, img_height = image.size

            # Format prompt with actual image dimensions
            prompt = EXTRACTION_PROMPT_TEMPLATE.format(width=img_width, height=img_height)

            print(f"📄 Page {page_number}: Image size {img_width}x{img_height}px")

            # Send to Gemini with extraction prompt
            response = self.gemini_model.generate_content([prompt, image])
            response_text = response.text.strip()

            # Strip markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            # Parse JSON response
            result = json.loads(response_text)
            questions = result.get("questions", [])

            # Add page number and debug info to each question
            debug_info = {"image_width": img_width, "image_height": img_height}
            for q in questions:
                q["page_number"] = page_number
                bbox = q.get("bounding_box", {})
                print(f"   Q{q.get('question_number', '?')}: bbox x={bbox.get('x')}, y={bbox.get('y')}, "
                      f"w={bbox.get('width')}, h={bbox.get('height')}")

            return questions, debug_info

        except json.JSONDecodeError as e:
            raise GeminiExtractionError(f"Failed to parse Gemini response as JSON: {str(e)}")
        except Exception as e:
            raise GeminiExtractionError(f"Gemini extraction failed: {str(e)}")

    def extract_questions_with_grounding(
        self,
        page_image_bytes: bytes,
        page_number: int
    ) -> tuple[List[dict], dict]:
        """
        Use Gemini's object localization (grounding) to detect questions with bounding boxes.

        This method uses Gemini's spatial prompting to get normalized [0-1000] bounding boxes
        in [ymin, xmin, ymax, xmax] format, then converts them to pixel coordinates.

        Args:
            page_image_bytes: PNG image bytes of the page
            page_number: 1-indexed page number

        Returns:
            Tuple of (list of question dicts, debug info dict)
        """
        if not self.gemini_model:
            raise GeminiExtractionError("Gemini model not configured")

        try:
            from vertexai.generative_models import Part
            
            # Open image to get dimensions
            image = Image.open(io.BytesIO(page_image_bytes))
            img_width, img_height = image.size

            print(f"📄 Page {page_number}: Image size {img_width}x{img_height}px")

            # Grounding prompt - uses Gemini's object localization mode
            # CRITICAL: Must use exact [ymin, xmin, ymax, xmax] format with 0-1000 scale
            prompt = """TASK: Detect bounding boxes for COMPLETE question regions on this exam page.

IMPORTANT: Each bounding box must capture the ENTIRE question area including:
- Question number and prompt text
- ALL work space / answer area below the question
- Any diagrams, graphs, or figures
- The FULL rectangular region allocated to that question on the page

DO NOT just box the question text - box the WHOLE question area from top to bottom!

Return ONLY valid JSON:
{
  "questions": [
    {
      "question_number": 1,
      "text_preview": "Find the derivative...",
      "latex_content": "f(x) = x^3",
      "question_type": "derivative",
      "difficulty_estimate": "easy",
      "box_2d": [ymin, xmin, ymax, xmax],
      "confidence": 0.95
    }
  ]
}

BOUNDING BOX RULES (box_2d):
1. Format: [ymin, xmin, ymax, xmax] with integers 0-1000
2. Coordinates:
   - ymin = TOP of question region (0 = top of page, 1000 = bottom)
   - xmin = LEFT edge (0 = left of page, 1000 = right)
   - ymax = BOTTOM of question region (include ALL work space)
   - xmax = RIGHT edge
3. Size: Each question should typically span 10-20% of page height (100-200 units)
4. Must satisfy: ymax > ymin and xmax > xmin

EXAMPLE for a typical exam question with work space:
box_2d: [50, 80, 220, 450]  (17% of page height - captures question + work area)

NOT just: [50, 80, 80, 450]  (3% of page - only question text, WRONG!)

If no questions found: {"questions": []}"""

            # Vertex AI requires Part objects for images, not PIL Images
            image_part = Part.from_data(data=page_image_bytes, mime_type="image/png")
            
            response = self.gemini_model.generate_content([prompt, image_part])
            response_text = response.text.strip()

            # Strip markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            result = json.loads(response_text)
            questions = result.get("questions", [])

            # Convert normalized 0-1000 coordinates to pixel coordinates
            for q in questions:
                q["page_number"] = page_number
                box_2d = q.get("box_2d", [])
                
                if len(box_2d) == 4:
                    ymin, xmin, ymax, xmax = box_2d
                    
                    # Debug: Check if box_2d values are reasonable
                    if not (0 <= ymin <= 1000 and 0 <= xmin <= 1000 and 
                            0 <= ymax <= 1000 and 0 <= xmax <= 1000):
                        print(f"   ⚠️  Q{q.get('question_number', '?')}: box_2d out of range! {box_2d}")
                    
                    if ymax <= ymin or xmax <= xmin:
                        print(f"   ⚠️  Q{q.get('question_number', '?')}: invalid box (ymax<=ymin or xmax<=xmin)! {box_2d}")
                    
                    # TRY WITHOUT Y-FLIP FIRST
                    # Gemini prompt says: ymin=0 is TOP, ymax=1000 is BOTTOM (standard image coords)
                    # So we should NOT flip
                    bbox = {
                        "x": int((xmin / 1000.0) * img_width),
                        "y": int((ymin / 1000.0) * img_height),  # Direct conversion - no flip
                        "width": int(((xmax - xmin) / 1000.0) * img_width),
                        "height": int(((ymax - ymin) / 1000.0) * img_height),
                    }
                    
                    # Add padding to prevent overcropping (especially at top)
                    padding_top = 15  # Extra padding at top to prevent overcropping
                    padding_sides = 10  # Padding for left/right
                    padding_bottom = 10  # Padding at bottom
                    
                    bbox["x"] -= padding_sides
                    bbox["y"] -= padding_top
                    bbox["width"] += padding_sides * 2
                    bbox["height"] += padding_top + padding_bottom
                    
                    # Ensure bounds are within image
                    bbox["x"] = max(0, bbox["x"])
                    bbox["y"] = max(0, bbox["y"])
                    bbox["width"] = min(bbox["width"], img_width - bbox["x"])
                    bbox["height"] = min(bbox["height"], img_height - bbox["y"])
                    
                    q["bounding_box"] = bbox
                    
                    # Calculate percentage position for debugging
                    y_percent = int((ymin / 10))  # 0-100%
                    x_percent = int((xmin / 10))
                    
                    print(f"   Q{q.get('question_number', '?')}: "
                          f"box_2d={box_2d} (~{y_percent}% down, {x_percent}% across) → "
                          f"bbox=(x={bbox['x']}, y={bbox['y']}, w={bbox['width']}, h={bbox['height']}) [NO FLIP]")
                else:
                    # Fallback if box_2d is missing or malformed
                    print(f"   Q{q.get('question_number', '?')}: Warning - invalid box_2d: {box_2d}")
                    q["bounding_box"] = {
                        "x": 0,
                        "y": 0,
                        "width": img_width,
                        "height": img_height // len(questions) if questions else img_height
                    }
                
                # Store text_content from text_preview if not already set
                if "text_content" not in q and "text_preview" in q:
                    q["text_content"] = q["text_preview"]

            debug_info = {
                "image_width": img_width,
                "image_height": img_height,
                "grounding_method": "gemini_2d_spatial",
                "questions_detected": len(questions),
            }

            return questions, debug_info

        except json.JSONDecodeError as e:
            raise GeminiExtractionError(f"Failed to parse Gemini response as JSON: {str(e)}")
        except Exception as e:
            raise GeminiExtractionError(f"Grounding extraction failed: {str(e)}")

    def extract_questions_hybrid(
        self,
        pdf_bytes: bytes,
        page_image_bytes: bytes,
        page_number: int
    ) -> tuple[List[dict], dict]:
        """
        Hybrid extraction: Use PyMuPDF for precise bounding boxes + Gemini for content analysis.
        
        NOTE: This method is now deprecated in favor of extract_questions_with_grounding().
        Kept for backward compatibility.

        This method:
        1. Uses PyMuPDF to extract text blocks and images with accurate bounding boxes
        2. Uses Gemini to analyze the page and identify which blocks are questions
        3. Combines both for accurate question extraction with proper image cropping

        Args:
            pdf_bytes: Raw PDF file bytes
            page_image_bytes: PNG image bytes of the page
            page_number: 1-indexed page number

        Returns:
            Tuple of (list of question dicts, debug info dict)
        """
        if not self.gemini_model:
            raise GeminiExtractionError("Gemini model not configured")

        try:
            # Step 1: Extract precise bounding boxes from PDF using PyMuPDF
            elements = self.extract_page_elements(pdf_bytes, page_number - 1)  # 0-indexed
            print(f"📄 Page {page_number}: Found {len(elements['images'])} images, {len(elements['text_blocks'])} text blocks")

            # Step 2: Use Gemini to analyze content and identify questions
            image = Image.open(io.BytesIO(page_image_bytes))
            img_width, img_height = image.size

            # Updated prompt that asks Gemini to identify regions, not provide bounding boxes
            prompt = f"""Analyze this math problem sheet and identify all questions.

For each question found, provide:
1. Question number (sequential)
2. The complete text content
3. Any mathematical expressions in LaTeX
4. Question type (integral, derivative, equation, word_problem, series, limit, other)
5. Difficulty estimate (easy, medium, hard)
6. A brief description of WHERE the question is located (e.g., "top left", "middle of page", "bottom right after problem 3")

Return as JSON:
{{
    "questions": [
        {{
            "question_number": 1,
            "text_content": "Find the derivative...",
            "latex_content": "f(x) = x^3",
            "question_type": "derivative",
            "difficulty_estimate": "easy",
            "location_description": "top left of page",
            "confidence": 0.95
        }}
    ]
}}

If no questions found, return {{"questions": []}}."""

            response = self.gemini_model.generate_content([prompt, image])
            response_text = response.text.strip()

            # Strip markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            result = json.loads(response_text)
            questions = result.get("questions", [])

            # Step 3: Match questions with PyMuPDF text blocks based on content
            for q in questions:
                q["page_number"] = page_number
                q_text = q.get("text_content", "")

                # Try to find matching text block
                best_match = None
                best_score = 0
                for block in elements["text_blocks"]:
                    # Simple matching: check if question text is in block
                    block_text = block["text"]
                    if q_text and block_text:
                        # Calculate overlap score
                        q_words = set(q_text.lower().split())
                        b_words = set(block_text.lower().split())
                        if q_words and b_words:
                            overlap = len(q_words & b_words) / len(q_words)
                            if overlap > best_score:
                                best_score = overlap
                                best_match = block

                # Use matched block's bounding box if found, otherwise create a default
                if best_match and best_score > 0.3:  # 30% word overlap threshold
                    q["bounding_box"] = best_match["bbox"]
                    print(f"   Q{q.get('question_number', '?')}: Matched with text block "
                          f"(score={best_score:.2f}) bbox={best_match['bbox']}")
                else:
                    # No good match - use a region based on question position
                    q["bounding_box"] = self._estimate_bbox_from_position(
                        q.get("location_description", ""),
                        img_width,
                        img_height
                    )
                    print(f"   Q{q.get('question_number', '?')}: Using estimated bbox based on location")

            # Step 4: Extract any embedded images (diagrams, figures) that might be questions
            for img_data in elements["images"]:
                # Create a "question" entry for standalone images
                # These might be diagrams or graphical problems
                questions.append({
                    "question_number": len(questions) + 1,
                    "text_content": "[Image/Diagram]",
                    "latex_content": None,
                    "question_type": "other",
                    "difficulty_estimate": "unknown",
                    "bounding_box": img_data["bbox"],
                    "page_number": page_number,
                    "confidence": 0.8,
                    "is_embedded_image": True,
                })
                print(f"   Added embedded image: bbox={img_data['bbox']}")

            debug_info = {
                "image_width": img_width,
                "image_height": img_height,
                "pymupdf_images_found": len(elements["images"]),
                "pymupdf_text_blocks_found": len(elements["text_blocks"]),
            }

            return questions, debug_info

        except json.JSONDecodeError as e:
            raise GeminiExtractionError(f"Failed to parse Gemini response as JSON: {str(e)}")
        except Exception as e:
            raise GeminiExtractionError(f"Hybrid extraction failed: {str(e)}")

    def _estimate_bbox_from_position(self, location_desc: str, width: int, height: int) -> dict:
        """
        Estimate a bounding box based on location description.
        Fallback when text matching fails.
        """
        location_desc = location_desc.lower()
        
        # Default to full page
        bbox = {"x": 0, "y": 0, "width": width, "height": height}
        
        # Rough position estimation
        if "top" in location_desc:
            bbox["y"] = 0
            bbox["height"] = height // 3
        elif "bottom" in location_desc:
            bbox["y"] = 2 * height // 3
            bbox["height"] = height // 3
        else:
            bbox["y"] = height // 3
            bbox["height"] = height // 3
        
        if "left" in location_desc:
            bbox["x"] = 0
            bbox["width"] = width // 2
        elif "right" in location_desc:
            bbox["x"] = width // 2
            bbox["width"] = width // 2
        
        return bbox

    def crop_question_image(
        self,
        page_image_bytes: bytes,
        bounding_box: dict
    ) -> str:
        """
        Crop a question region from the page image.

        Args:
            page_image_bytes: PNG image bytes of the full page
            bounding_box: Dict with x, y, width, height

        Returns:
            Base64-encoded PNG string of the cropped region
        """
        try:
            image = Image.open(io.BytesIO(page_image_bytes))

            x = bounding_box.get("x", 0)
            y = bounding_box.get("y", 0)
            width = bounding_box.get("width", 100)
            height = bounding_box.get("height", 50)

            # Ensure bounds are within image
            img_width, img_height = image.size
            x = max(0, min(x, img_width - 1))
            y = max(0, min(y, img_height - 1))
            right = min(x + width, img_width)
            bottom = min(y + height, img_height)

            # Crop the region
            cropped = image.crop((x, y, right, bottom))

            # Convert to base64
            buffer = io.BytesIO()
            cropped.save(buffer, format="PNG")
            buffer.seek(0)
            base64_str = base64.b64encode(buffer.read()).decode("utf-8")

            return f"data:image/png;base64,{base64_str}"

        except Exception as e:
            raise ImageCropError(f"Failed to crop question image: {str(e)}")

    def process_pdf(
        self,
        pdf_bytes: bytes,
        user_id: str,
        filename: str
    ) -> dict:
        """
        Full PDF processing pipeline.

        Args:
            pdf_bytes: Raw PDF file bytes
            user_id: ID of the user uploading the PDF
            filename: Original filename

        Returns:
            Dict with:
                - total_pages: int
                - questions: List of question dicts ready for database storage
                - page_images: List of base64 page images
                - error: Optional error message
        """
        result = {
            "total_pages": 0,
            "questions": [],
            "page_images": [],
            "error": None
        }

        try:
            # Step 1: Convert PDF to images
            page_images_bytes = self.pdf_to_images(pdf_bytes)
            result["total_pages"] = len(page_images_bytes)

            # Convert page images to base64 for storage
            for img_bytes in page_images_bytes:
                base64_str = base64.b64encode(img_bytes).decode("utf-8")
                result["page_images"].append(f"data:image/png;base64,{base64_str}")

            # Step 2: Extract questions from each page using Gemini grounding
            all_questions = []
            for page_num, page_img_bytes in enumerate(page_images_bytes, start=1):
                try:
                    # Use Gemini grounding: object localization with 0-1000 normalized boxes
                    questions, debug_info = self.extract_questions_with_grounding(
                        page_img_bytes, page_num
                    )

                    # Step 3: Crop each question image using Gemini's grounded bounding boxes
                    for q in questions:
                        bbox = q.get("bounding_box", {})
                        cropped_image = self.crop_question_image(page_img_bytes, bbox)
                        q["cropped_image"] = cropped_image
                        # Store debug info for troubleshooting
                        q["_debug"] = debug_info

                    all_questions.extend(questions)

                except GeminiExtractionError as e:
                    # Log but continue with other pages
                    print(f"Warning: Failed to extract from page {page_num}: {str(e)}")
                    continue

            result["questions"] = all_questions

        except PDFConversionError as e:
            result["error"] = str(e)
        except Exception as e:
            result["error"] = f"PDF processing failed: {str(e)}"

        return result


class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""
    pass


class PDFConversionError(PDFProcessingError):
    """Failed to convert PDF to images."""
    pass


class GeminiExtractionError(PDFProcessingError):
    """Gemini API call failed."""
    pass


class ImageCropError(PDFProcessingError):
    """Failed to crop question image."""
    pass


# Singleton instance
pdf_extractor_service = PDFExtractorService()
