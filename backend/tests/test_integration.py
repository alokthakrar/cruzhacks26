import pytest
import httpx
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import sys
from unittest.mock import Mock

# Mock heavy dependencies
sys.modules['pix2text'] = Mock()
sys.modules['google.generativeai'] = Mock()


@pytest.fixture
def api_base_url():
    """Base URL for the API."""
    return "http://localhost:8000/api"


@pytest.fixture
def create_test_image():
    """Factory to create test images with mathematical expressions."""
    def _create_image(text: str, size=(400, 200)):
        img = Image.new('RGB', size, color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes.getvalue()
    
    return _create_image


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for the OCR-first analysis pipeline."""
    
    async def test_health_check(self, api_base_url):
        """Test that the API is running."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base_url.replace('/api', '')}/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    
    async def test_full_ocr_pipeline(self, api_base_url, create_test_image):
        """Test the complete OCR -> AI analysis pipeline."""
        image_bytes = create_test_image("x^2 + 5 = 10")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"image": ("test.png", image_bytes, "image/png")}
            response = await client.post(
                f"{api_base_url}/analyze/ocr_first",
                files=files
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "latex_string" in data
            assert "ocr_confidence" in data
            assert "feedback" in data
            assert "hints" in data
            assert isinstance(data["hints"], list)
            assert "error_types" in data
            assert isinstance(data["error_types"], list)
    
    async def test_blank_image(self, api_base_url):
        """Test OCR with a blank white image."""
        img = Image.new('RGB', (400, 200), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"image": ("blank.png", img_bytes.getvalue(), "image/png")}
            response = await client.post(
                f"{api_base_url}/analyze/ocr_first",
                files=files
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["ocr_confidence"] == 0.0 or data["latex_string"] == ""
    
    async def test_invalid_request(self, api_base_url):
        """Test API error handling with invalid input."""
        async with httpx.AsyncClient() as client:
            files = {"image": ("test.txt", b"not an image", "text/plain")}
            response = await client.post(
                f"{api_base_url}/analyze/ocr_first",
                files=files
            )
            
            assert response.status_code == 400
            assert "must be an image" in response.json()["detail"]


@pytest.mark.skipif(
    True,  # Change to False when you want to run live API tests
    reason="Live API tests require running backend server"
)
class TestLiveAPI:
    """Live API tests that require the server to be running."""
    
    @pytest.mark.asyncio
    async def test_live_ocr_endpoint(self, create_test_image):
        """Test OCR endpoint with live backend (requires running server)."""
        image_bytes = create_test_image("2x + 3 = 7")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {"image": ("test.png", image_bytes, "image/png")}
            response = await client.post(
                "http://localhost:8000/api/analyze/ocr_first",
                files=files
            )
            
            print(f"\n--- Live API Test Result ---")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"LaTeX: {data['latex_string']}")
                print(f"Confidence: {data['ocr_confidence']}")
                print(f"Feedback: {data['feedback']}")
                print(f"Hints: {data['hints']}")
            else:
                print(f"Error: {response.text}")
            
            assert response.status_code == 200
