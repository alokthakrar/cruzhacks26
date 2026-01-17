import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from PIL import Image
import sys

# Mock pix2text and dependencies before importing OCRService
sys.modules['pix2text'] = Mock()
sys.modules['google.generativeai'] = Mock()

from app.services.ocr import OCRService


@pytest.fixture
def ocr_service():
    """Create an OCR service instance for testing."""
    service = OCRService()
    return service


@pytest.fixture
def sample_image_bytes():
    """Create a sample PNG image as bytes."""
    img = Image.new('RGB', (100, 100), color='white')
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.read()


class TestOCRService:
    """Test suite for OCR service."""
    
    def test_service_initialization(self, ocr_service):
        """Test that OCR service initializes correctly."""
        assert ocr_service.p2t_model is None
        assert ocr_service.gemini_model is None
    
    @patch('app.services.ocr.Pix2Text')
    @patch('app.services.ocr.genai')
    @patch('app.services.ocr.get_settings')
    def test_load_models_success(self, mock_settings, mock_genai, mock_pix2text, ocr_service):
        """Test successful model loading."""
        mock_settings.return_value.gemini_api_key = "test_api_key"
        mock_p2t_instance = Mock()
        mock_pix2text.from_config.return_value = mock_p2t_instance
        mock_gemini_model = Mock()
        mock_genai.GenerativeModel.return_value = mock_gemini_model
        
        ocr_service.load_models()
        
        assert ocr_service.p2t_model == mock_p2t_instance
        assert ocr_service.gemini_model == mock_gemini_model
        mock_pix2text.from_config.assert_called_once()
        mock_genai.configure.assert_called_once_with(api_key="test_api_key")
    
    @patch('app.services.ocr.Pix2Text')
    @patch('app.services.ocr.get_settings')
    def test_load_models_no_gemini_key(self, mock_settings, mock_pix2text, ocr_service):
        """Test model loading without Gemini API key."""
        mock_settings.return_value.gemini_api_key = ""
        mock_p2t_instance = Mock()
        mock_pix2text.from_config.return_value = mock_p2t_instance
        
        ocr_service.load_models()
        
        assert ocr_service.p2t_model == mock_p2t_instance
        assert ocr_service.gemini_model is None
    
    def test_extract_latex_no_model_loaded(self, ocr_service, sample_image_bytes):
        """Test LaTeX extraction when model is not loaded."""
        result = ocr_service.extract_latex(sample_image_bytes)
        
        assert result["latex"] == ""
        assert result["confidence"] == 0.0
        assert result["error"] == "OCR model not loaded"
    
    @patch('app.services.ocr.Image.open')
    def test_extract_latex_success(self, mock_image_open, ocr_service, sample_image_bytes):
        """Test successful LaTeX extraction."""
        mock_p2t = Mock()
        mock_p2t.recognize.return_value = r"\int x^2 dx"
        ocr_service.p2t_model = mock_p2t
        
        mock_image = Mock()
        mock_image_open.return_value = mock_image
        
        result = ocr_service.extract_latex(sample_image_bytes)
        
        assert result["latex"] == r"\int x^2 dx"
        assert result["confidence"] == 1.0
        assert result["error"] is None
        mock_p2t.recognize.assert_called_once_with(mock_image, resized_shape=608)
    
    @patch('app.services.ocr.Image.open')
    def test_extract_latex_dict_result(self, mock_image_open, ocr_service, sample_image_bytes):
        """Test LaTeX extraction when Pix2Text returns a dict."""
        mock_p2t = Mock()
        mock_p2t.recognize.return_value = {"text": r"x^2 + 5"}
        ocr_service.p2t_model = mock_p2t
        
        mock_image = Mock()
        mock_image_open.return_value = mock_image
        
        result = ocr_service.extract_latex(sample_image_bytes)
        
        assert result["latex"] == r"x^2 + 5"
        assert result["confidence"] == 1.0
        assert result["error"] is None
    
    @patch('app.services.ocr.Image.open')
    def test_extract_latex_empty_result(self, mock_image_open, ocr_service, sample_image_bytes):
        """Test LaTeX extraction when no text is detected."""
        mock_p2t = Mock()
        mock_p2t.recognize.return_value = ""
        ocr_service.p2t_model = mock_p2t
        
        mock_image = Mock()
        mock_image_open.return_value = mock_image
        
        result = ocr_service.extract_latex(sample_image_bytes)
        
        assert result["latex"] == ""
        assert result["confidence"] == 0.0
        assert result["error"] == "Handwriting unclear - no text detected"
    
    @patch('app.services.ocr.Image.open')
    def test_extract_latex_exception(self, mock_image_open, ocr_service, sample_image_bytes):
        """Test LaTeX extraction when an exception occurs."""
        mock_p2t = Mock()
        mock_p2t.recognize.side_effect = Exception("OCR failed")
        ocr_service.p2t_model = mock_p2t
        
        mock_image_open.side_effect = Exception("Image processing error")
        
        result = ocr_service.extract_latex(sample_image_bytes)
        
        assert result["latex"] == ""
        assert result["confidence"] == 0.0
        assert "OCR failed" in result["error"]
    
    def test_analyze_with_gemini_no_model(self, ocr_service):
        """Test Gemini analysis when model is not loaded."""
        result = ocr_service.analyze_with_gemini(r"\int x^2 dx")
        
        assert result["is_correct"] is None
        assert "unavailable" in result["feedback"]
        assert result["hints"] == []
        assert result["error"] == "Gemini API key not set"
    
    def test_analyze_with_gemini_success(self, ocr_service):
        """Test successful Gemini analysis."""
        mock_gemini = Mock()
        mock_response = Mock()
        mock_response.text = '''```json
{
    "is_correct": false,
    "feedback": "Missing constant of integration",
    "hints": ["Remember to add + C"],
    "error_types": ["integration_error"]
}```'''
        mock_gemini.generate_content.return_value = mock_response
        ocr_service.gemini_model = mock_gemini
        
        result = ocr_service.analyze_with_gemini(r"\int x^2 dx = \frac{x^3}{3}")
        
        assert result["is_correct"] is False
        assert "constant" in result["feedback"]
        assert len(result["hints"]) == 1
        assert result["error_types"] == ["integration_error"]
        assert result["error"] is None
    
    def test_analyze_with_gemini_exception(self, ocr_service):
        """Test Gemini analysis when an exception occurs."""
        mock_gemini = Mock()
        mock_gemini.generate_content.side_effect = Exception("API error")
        ocr_service.gemini_model = mock_gemini
        
        result = ocr_service.analyze_with_gemini(r"\int x^2 dx")
        
        assert result["is_correct"] is None
        assert "failed" in result["feedback"]
        assert result["hints"] == []
        assert "API error" in result["error"]
