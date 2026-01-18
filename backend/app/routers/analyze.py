from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from typing import Optional

# from ..services.ocr import ocr_service  # Disabled for BKT testing - pyarrow issue


router = APIRouter(prefix="/analyze", tags=["analyze"])


class OCRAnalysisResponse(BaseModel):
    """Response model for OCR + AI analysis."""
    latex_string: str
    ocr_confidence: float
    ocr_error: Optional[str]
    is_correct: Optional[bool]
    feedback: str
    hints: list[str]
    error_types: list[str]
    analysis_error: Optional[str]


@router.post("/ocr_first", response_model=OCRAnalysisResponse)
async def analyze_handwriting_ocr_first(
    image: UploadFile = File(..., description="PNG image of handwritten math work")
):
    """
    OCR-first analysis pipeline:
    1. Extract LaTeX from handwritten image using Pix2Text
    2. Analyze the LaTeX using Gemini AI for correctness and hints
    
    This two-step approach allows users to verify what the AI "saw" before trusting its feedback.
    """
    
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    image_bytes = await image.read()
    
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty image file"
        )
    
    ocr_result = ocr_service.extract_latex(image_bytes)
    
    if ocr_result["error"]:
        return OCRAnalysisResponse(
            latex_string=ocr_result["latex"],
            ocr_confidence=ocr_result["confidence"],
            ocr_error=ocr_result["error"],
            is_correct=None,
            feedback="Cannot analyze - handwriting unclear",
            hints=[],
            error_types=[],
            analysis_error=ocr_result["error"]
        )
    
    latex_string = ocr_result["latex"]
    
    if not latex_string:
        return OCRAnalysisResponse(
            latex_string="",
            ocr_confidence=0.0,
            ocr_error="No text detected in image",
            is_correct=None,
            feedback="No mathematical expression detected. Please write more clearly or check the image.",
            hints=["Ensure your handwriting is clear and dark", "Make sure the entire expression is visible"],
            error_types=[],
            analysis_error="No text detected"
        )
    
    ai_result = ocr_service.analyze_with_gemini(latex_string)
    
    return OCRAnalysisResponse(
        latex_string=latex_string,
        ocr_confidence=ocr_result["confidence"],
        ocr_error=None,
        is_correct=ai_result["is_correct"],
        feedback=ai_result["feedback"],
        hints=ai_result["hints"],
        error_types=ai_result.get("error_types", []),
        analysis_error=ai_result["error"]
    )
