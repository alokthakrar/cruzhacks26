import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from io import BytesIO
from PIL import Image
import sys

# Mock heavy dependencies before importing app
sys.modules['pix2text'] = Mock()
sys.modules['google.generativeai'] = Mock()

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_image_file():
    """Create a sample image file for upload testing."""
    img = Image.new('RGB', (200, 100), color='white')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return ("test_canvas.png", img_byte_arr, "image/png")


class TestAnalyzeAPI:
    """Test suite for /api/analyze endpoints."""
    
    @patch('app.routers.analyze.ocr_service')
    def test_ocr_first_success(self, mock_service, client, sample_image_file):
        """Test successful OCR analysis request."""
        mock_service.extract_latex.return_value = {
            "latex": r"\int x^2 dx",
            "confidence": 0.95,
            "error": None
        }
        mock_service.analyze_with_gemini.return_value = {
            "is_correct": False,
            "feedback": "Missing constant of integration",
            "hints": ["Add + C to your answer"],
            "error_types": ["integration_error"],
            "error": None
        }
        
        response = client.post(
            "/api/analyze/ocr_first",
            files={"image": sample_image_file}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["latex_string"] == r"\int x^2 dx"
        assert data["ocr_confidence"] == 0.95
        assert data["ocr_error"] is None
        assert data["is_correct"] is False
        assert "constant" in data["feedback"]
        assert len(data["hints"]) == 1
        assert data["error_types"] == ["integration_error"]
    
    @patch('app.routers.analyze.ocr_service')
    def test_ocr_first_ocr_error(self, mock_service, client, sample_image_file):
        """Test OCR analysis with OCR extraction error."""
        mock_service.extract_latex.return_value = {
            "latex": "",
            "confidence": 0.0,
            "error": "Handwriting unclear - no text detected"
        }
        
        response = client.post(
            "/api/analyze/ocr_first",
            files={"image": sample_image_file}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["latex_string"] == ""
        assert data["ocr_confidence"] == 0.0
        assert data["ocr_error"] == "Handwriting unclear - no text detected"
        assert data["is_correct"] is None
        assert "unclear" in data["feedback"]
    
    @patch('app.routers.analyze.ocr_service')
    def test_ocr_first_empty_text(self, mock_service, client, sample_image_file):
        """Test OCR analysis when no text is detected."""
        mock_service.extract_latex.return_value = {
            "latex": "",
            "confidence": 0.0,
            "error": None
        }
        
        response = client.post(
            "/api/analyze/ocr_first",
            files={"image": sample_image_file}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["latex_string"] == ""
        assert "No mathematical expression detected" in data["feedback"]
        assert len(data["hints"]) > 0
        assert data["analysis_error"] == "No text detected"
    
    def test_ocr_first_invalid_file_type(self, client):
        """Test OCR analysis with non-image file."""
        text_file = ("test.txt", BytesIO(b"not an image"), "text/plain")
        
        response = client.post(
            "/api/analyze/ocr_first",
            files={"image": text_file}
        )
        
        assert response.status_code == 400
        assert "must be an image" in response.json()["detail"]
    
    def test_ocr_first_empty_file(self, client):
        """Test OCR analysis with empty file."""
        empty_file = ("empty.png", BytesIO(b""), "image/png")
        
        response = client.post(
            "/api/analyze/ocr_first",
            files={"image": empty_file}
        )
        
        assert response.status_code == 400
        assert "Empty image file" in response.json()["detail"]
    
    def test_ocr_first_missing_file(self, client):
        """Test OCR analysis without uploading a file."""
        response = client.post("/api/analyze/ocr_first")
        
        assert response.status_code == 422
    
    @patch('app.routers.analyze.ocr_service')
    def test_ocr_first_correct_solution(self, mock_service, client, sample_image_file):
        """Test OCR analysis with correct mathematical solution."""
        mock_service.extract_latex.return_value = {
            "latex": r"\int x^2 dx = \frac{x^3}{3} + C",
            "confidence": 0.98,
            "error": None
        }
        mock_service.analyze_with_gemini.return_value = {
            "is_correct": True,
            "feedback": "Great work! Your integration is correct.",
            "hints": [],
            "error_types": [],
            "error": None
        }
        
        response = client.post(
            "/api/analyze/ocr_first",
            files={"image": sample_image_file}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert "correct" in data["feedback"].lower()
        assert len(data["hints"]) == 0
    
    @patch('app.routers.analyze.ocr_service')
    def test_ocr_first_gemini_error(self, mock_service, client, sample_image_file):
        """Test OCR analysis when Gemini analysis fails."""
        mock_service.extract_latex.return_value = {
            "latex": r"\int x^2 dx",
            "confidence": 0.90,
            "error": None
        }
        mock_service.analyze_with_gemini.return_value = {
            "is_correct": None,
            "feedback": "Analysis failed: API error",
            "hints": [],
            "error_types": [],
            "error": "API error"
        }
        
        response = client.post(
            "/api/analyze/ocr_first",
            files={"image": sample_image_file}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["latex_string"] == r"\int x^2 dx"
        assert data["analysis_error"] == "API error"
