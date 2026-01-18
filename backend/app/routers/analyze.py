from fastapi import APIRouter, UploadFile, File, HTTPException, status, Form
from pydantic import BaseModel
from typing import Optional, List, Dict
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..services.ocr import ocr_service
from ..services.symbolic_validator import get_validator


router = APIRouter(prefix="/analyze", tags=["analyze"])


class PipelineResult(BaseModel):
    """Result from a single pipeline approach."""
    latex_string: str
    is_correct: Optional[bool]
    feedback: str
    hints: list[str]
    error_types: list[str]
    bounding_box: Optional[list[int]] = None
    visual_feedback: Optional[str] = None
    correct_answer: Optional[str] = None
    error: Optional[str]
    timing: Dict[str, float]


class OCRAnalysisResponse(BaseModel):
    """Response model for OCR + AI analysis with Gemini Vision as primary."""
    # Primary result (Gemini Vision)
    latex_string: str
    is_correct: Optional[bool]
    feedback: str
    hints: list[str]
    error_types: list[str]
    bounding_box: Optional[list[int]] = None
    visual_feedback: Optional[str] = None
    correct_answer: Optional[str] = None
    analysis_error: Optional[str]
    timing: Dict[str, float]
    # Legacy Pix2Text pipeline result (optional, for comparison)
    pix2text_result: Optional[PipelineResult] = None


@router.post("/ocr_first", response_model=OCRAnalysisResponse)
async def analyze_handwriting_ocr_first(
    image: UploadFile = File(..., description="PNG image of handwritten math work"),
    problem_context: Optional[str] = Form(None),
    previous_step: Optional[str] = Form(None)
):
    """
    Gemini Vision pipeline: Extract math, analyze correctness, and detect visual errors in ONE call.
    Fast and includes bounding box highlighting for errors.
    Optionally accepts problem_context to check consistency with original problem.
    Optionally accepts previous_step to validate step-by-step transformations.
    """
    timing = {}
    start_total = time.time()
    
    # Stage 1: Validation
    start = time.time()
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
    timing["validation_ms"] = round((time.time() - start) * 1000, 2)
    
    # Use Gemini Vision for everything (OCR + analysis + bounding box)
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, ocr_service.analyze_with_gemini_vision, image_bytes, problem_context, previous_step)
    
    # Merge timing
    if "timing" in result:
        timing.update(result["timing"])
    
    timing["total_pipeline_ms"] = round((time.time() - start_total) * 1000, 2)
    
    # Handle errors
    if result.get("error"):
        return OCRAnalysisResponse(
            latex_string="",
            is_correct=None,
            feedback=result.get("feedback", "Analysis failed"),
            hints=[],
            error_types=[],
            bounding_box=None,
            visual_feedback=None,
            analysis_error=result["error"],
            timing=timing
        )
    
    # Log results
    print("\n" + "="*80)
    print("🟢 GEMINI VISION PIPELINE (Single Call)")
    print("="*80)
    print(f"  Validation:           {timing.get('validation_ms', 0):>8.2f} ms")
    print(f"  Image Prep:           {timing.get('image_prep_ms', 0):>8.2f} ms")
    print(f"  Gemini Vision API:    {timing.get('gemini_vision_api_call_ms', 0):>8.2f} ms  👁️")
    print(f"  Parse Response:       {timing.get('parse_response_ms', 0):>8.2f} ms")
    print(f"  Total:                {timing.get('total_pipeline_ms', 0):>8.2f} ms")
    print(f"  Extracted: {result['latex'][:50]}{'...' if len(result['latex']) > 50 else ''}")
    print(f"  Result: {'✓ Correct' if result['is_correct'] else '✗ Incorrect' if result['is_correct'] is False else '? Unknown'}")
    if result.get('bounding_box'):
        print(f"  Visual Error: {result.get('visual_feedback', 'N/A')}")
    print("="*80 + "\n")
    
    return OCRAnalysisResponse(
        latex_string=result["latex"],
        is_correct=result["is_correct"],
        feedback=result["feedback"],
        hints=result["hints"],
        error_types=result["error_types"],
        bounding_box=result.get("bounding_box"),
        visual_feedback=result.get("visual_feedback"),
        correct_answer=result.get("correct_answer"),
        analysis_error=None,
        timing=timing
    )


class ValidateSequenceRequest(BaseModel):
    """Request to validate a sequence of math steps."""
    expressions: List[str]


class StepValidationResult(BaseModel):
    """Result for a single step validation."""
    step_number: int
    from_expr: str
    to_expr: str
    is_valid: bool
    error: Optional[str]
    explanation: str
    warning: Optional[str] = None


class ValidateSequenceResponse(BaseModel):
    """Response with validation results for all steps."""
    results: List[StepValidationResult]
    all_valid: bool


@router.post("/validate_sequence", response_model=ValidateSequenceResponse)
async def validate_sequence(request: ValidateSequenceRequest):
    """
    Validate a sequence of algebraic steps using SymPy (no AI).
    Checks if each step N+1 follows algebraically from step N.
    """
    if len(request.expressions) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Need at least 2 expressions to validate steps"
        )
    
    validator = get_validator()
    results = validator.validate_sequence(request.expressions)
    
    all_valid = all(r["is_valid"] for r in results)
    
    return ValidateSequenceResponse(
        results=[StepValidationResult(**r) for r in results],
        all_valid=all_valid
    )


class VisualFeedbackResponse(BaseModel):
    error_detected: bool
    bounding_box: Optional[List[int]] = None  # [ymin, xmin, ymax, xmax] 0-1000
    feedback: Optional[str] = None
    error: Optional[str] = None


@router.post("/visual_feedback", response_model=VisualFeedbackResponse)
async def get_visual_feedback(
    image: UploadFile = File(..., description="PNG image of handwritten math work")
):
    """
    Get targeted visual feedback for a handwritten math step.
    Returns a bounding box around the error if found.
    """
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    image_bytes = await image.read()
    
    result = await asyncio.get_event_loop().run_in_executor(
        None, 
        ocr_service.detect_visual_errors, 
        image_bytes
    )
    
    return VisualFeedbackResponse(
        error_detected=result.get("error_detected", False),
        bounding_box=result.get("bounding_box"),
        feedback=result.get("feedback"),
        error=result.get("error")
    )
