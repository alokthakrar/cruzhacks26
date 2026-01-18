from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List, Dict
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..services.ocr import ocr_service


router = APIRouter(prefix="/analyze", tags=["analyze"])


class PipelineResult(BaseModel):
    """Result from a single pipeline approach."""
    latex_string: str
    is_correct: Optional[bool]
    feedback: str
    hints: list[str]
    error_types: list[str]
    error: Optional[str]
    timing: Dict[str, float]


class OCRAnalysisResponse(BaseModel):
    """Response model for OCR + AI analysis with parallel pipelines."""
    # Primary result (Pix2Text pipeline)
    latex_string: str
    ocr_confidence: float
    ocr_error: Optional[str]
    is_correct: Optional[bool]
    feedback: str
    hints: list[str]
    error_types: list[str]
    analysis_error: Optional[str]
    timing: Dict[str, float]
    # Gemini Vision pipeline result
    gemini_vision_result: Optional[PipelineResult]


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
    
    # Run both pipelines in parallel using ThreadPoolExecutor
    executor = ThreadPoolExecutor(max_workers=2)
    loop = asyncio.get_event_loop()
    
    # Pipeline 1: Traditional Pix2Text OCR + Gemini analysis (sequential)
    async def run_traditional_pipeline():
        traditional_timing = {}
        start_trad = time.time()
        
        # OCR Extraction
        start = time.time()
        ocr_result = await loop.run_in_executor(executor, ocr_service.extract_latex, image_bytes)
        traditional_timing["ocr_total_ms"] = round((time.time() - start) * 1000, 2)
        if "timing" in ocr_result:
            for key, value in ocr_result["timing"].items():
                traditional_timing[f"ocr_{key}"] = value
        
        if ocr_result["error"] or not ocr_result["latex"]:
            traditional_timing["total_ms"] = round((time.time() - start_trad) * 1000, 2)
            return ocr_result, None, traditional_timing
        
        # AI Analysis
        start = time.time()
        ai_result = await loop.run_in_executor(executor, ocr_service.analyze_with_gemini, ocr_result["latex"])
        traditional_timing["ai_total_ms"] = round((time.time() - start) * 1000, 2)
        if "timing" in ai_result:
            for key, value in ai_result["timing"].items():
                traditional_timing[f"ai_{key}"] = value
        
        traditional_timing["total_ms"] = round((time.time() - start_trad) * 1000, 2)
        return ocr_result, ai_result, traditional_timing
    
    # Pipeline 2: Gemini Vision (single call)
    async def run_gemini_vision_pipeline():
        return await loop.run_in_executor(executor, ocr_service.analyze_with_gemini_vision, image_bytes)
    
    # Run both pipelines in parallel
    start_parallel = time.time()
    (ocr_result, ai_result, traditional_timing), gemini_vision_result = await asyncio.gather(
        run_traditional_pipeline(),
        run_gemini_vision_pipeline()
    )
    timing["parallel_execution_ms"] = round((time.time() - start_parallel) * 1000, 2)
    
    # Merge traditional pipeline timing
    timing.update(traditional_timing)
    
    # Handle errors in traditional pipeline
    if ocr_result["error"]:
        timing["total_pipeline_ms"] = round((time.time() - start_total) * 1000, 2)
        return OCRAnalysisResponse(
            latex_string=ocr_result["latex"],
            ocr_confidence=ocr_result["confidence"],
            ocr_error=ocr_result["error"],
            is_correct=None,
            feedback="Cannot analyze - handwriting unclear",
            hints=[],
            error_types=[],
            analysis_error=ocr_result["error"],
            timing=timing,
            gemini_vision_result=PipelineResult(
                latex_string=gemini_vision_result["latex"],
                is_correct=gemini_vision_result["is_correct"],
                feedback=gemini_vision_result["feedback"],
                hints=gemini_vision_result["hints"],
                error_types=gemini_vision_result["error_types"],
                error=gemini_vision_result["error"],
                timing=gemini_vision_result["timing"]
            ) if not gemini_vision_result.get("error") else None
        )
    
    latex_string = ocr_result["latex"]
    
    if not latex_string:
        timing["total_pipeline_ms"] = round((time.time() - start_total) * 1000, 2)
        return OCRAnalysisResponse(
            latex_string="",
            ocr_confidence=0.0,
            ocr_error="No text detected in image",
            is_correct=None,
            feedback="No mathematical expression detected. Please write more clearly or check the image.",
            hints=["Ensure your handwriting is clear and dark", "Make sure the entire expression is visible"],
            error_types=[],
            analysis_error="No text detected",
            timing=timing,
            gemini_vision_result=PipelineResult(
                latex_string=gemini_vision_result["latex"],
                is_correct=gemini_vision_result["is_correct"],
                feedback=gemini_vision_result["feedback"],
                hints=gemini_vision_result["hints"],
                error_types=gemini_vision_result["error_types"],
                error=gemini_vision_result["error"],
                timing=gemini_vision_result["timing"]
            ) if not gemini_vision_result.get("error") else None
        )
    
    timing["total_pipeline_ms"] = round((time.time() - start_total) * 1000, 2)
    
    # Log timing breakdown to terminal with BOTH pipelines
    print("\n" + "="*80)
    print("📊 PARALLEL OCR PIPELINE COMPARISON")
    print("="*80)
    print("\n🔵 Traditional Pipeline (Pix2Text → Gemini)")
    print("-"*80)
    print(f"  Validation:           {timing.get('validation_ms', 0):>8.2f} ms")
    print(f"  OCR Total:            {timing.get('ocr_total_ms', 0):>8.2f} ms")
    print(f"    ├─ Image Load:      {timing.get('ocr_image_load_ms', 0):>8.2f} ms")
    print(f"    ├─ Recognition:     {timing.get('ocr_ocr_recognition_ms', 0):>8.2f} ms  ⚡")
    print(f"    ├─ Parse Result:    {timing.get('ocr_parse_result_ms', 0):>8.2f} ms")
    print(f"    └─ LaTeX Conv:      {timing.get('ocr_latex_conversion_ms', 0):>8.2f} ms")
    print(f"  AI Analysis:          {timing.get('ai_total_ms', 0):>8.2f} ms")
    print(f"    ├─ Prompt Build:    {timing.get('ai_prompt_build_ms', 0):>8.2f} ms")
    print(f"    ├─ Gemini API:      {timing.get('ai_gemini_api_call_ms', 0):>8.2f} ms  🌐")
    print(f"    └─ Parse Response:  {timing.get('ai_parse_response_ms', 0):>8.2f} ms")
    print(f"  Sequential Total:     {timing.get('total_ms', 0):>8.2f} ms")
    print(f"  Extracted: {latex_string[:50]}{'...' if len(latex_string) > 50 else ''}")
    print(f"  Result: {'✓ Correct' if ai_result['is_correct'] else '✗ Incorrect' if ai_result['is_correct'] is False else '? Unknown'}")
    
    print("\n🟢 Gemini Vision Pipeline (Single Call)")
    print("-"*80)
    if gemini_vision_result and not gemini_vision_result.get("error"):
        gv_timing = gemini_vision_result["timing"]
        print(f"  Image Prep:           {gv_timing.get('image_prep_ms', 0):>8.2f} ms")
        print(f"  Prompt Build:         {gv_timing.get('prompt_build_ms', 0):>8.2f} ms")
        print(f"  Gemini Vision API:    {gv_timing.get('gemini_vision_api_call_ms', 0):>8.2f} ms  👁️")
        print(f"  Parse Response:       {gv_timing.get('parse_response_ms', 0):>8.2f} ms")
        print(f"  Single Call Total:    {gv_timing.get('total_ms', 0):>8.2f} ms")
        print(f"  Extracted: {gemini_vision_result['latex'][:50]}{'...' if len(gemini_vision_result['latex']) > 50 else ''}")
        print(f"  Result: {'✓ Correct' if gemini_vision_result['is_correct'] else '✗ Incorrect' if gemini_vision_result['is_correct'] is False else '? Unknown'}")
        
        # Calculate speedup
        speedup = (timing.get('total_ms', 0) / gv_timing.get('total_ms', 1)) if gv_timing.get('total_ms', 0) > 0 else 0
        faster_pipeline = "Gemini Vision" if speedup > 1 else "Traditional"
        speedup_pct = abs(speedup - 1) * 100
        print(f"\n  ⚡ {faster_pipeline} is {speedup_pct:.1f}% {'faster' if speedup > 1 else 'slower'}")
    else:
        print(f"  ❌ Failed: {gemini_vision_result.get('error', 'Unknown error')}")
    
    print("\n⏱️  Parallel Execution")
    print("-"*80)
    print(f"  Wall Clock Time:      {timing.get('parallel_execution_ms', 0):>8.2f} ms")
    print(f"  Total Pipeline:       {timing.get('total_pipeline_ms', 0):>8.2f} ms")
    print("="*80 + "\n")
    
    return OCRAnalysisResponse(
        latex_string=latex_string,
        ocr_confidence=ocr_result["confidence"],
        ocr_error=None,
        is_correct=ai_result["is_correct"],
        feedback=ai_result["feedback"],
        hints=ai_result["hints"],
        error_types=ai_result.get("error_types", []),
        analysis_error=ai_result["error"],
        timing=timing,
        gemini_vision_result=PipelineResult(
            latex_string=gemini_vision_result["latex"],
            is_correct=gemini_vision_result["is_correct"],
            feedback=gemini_vision_result["feedback"],
            hints=gemini_vision_result["hints"],
            error_types=gemini_vision_result["error_types"],
            error=gemini_vision_result["error"],
            timing=gemini_vision_result["timing"]
        ) if gemini_vision_result and not gemini_vision_result.get("error") else None
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
