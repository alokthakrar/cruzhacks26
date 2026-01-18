import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from io import BytesIO
import sys

# Mock heavy dependencies before importing app
sys.modules['pix2text'] = Mock()
sys.modules['google.generativeai'] = Mock()
sys.modules['fitz'] = Mock()

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for upload testing."""
    # Minimal valid PDF bytes
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    return ("test.pdf", BytesIO(pdf_bytes), "application/pdf")


@pytest.fixture
def mock_extraction_result():
    """Sample extraction result from pdf_extractor_service."""
    return {
        "total_pages": 2,
        "questions": [
            {
                "page_number": 1,
                "question_number": 1,
                "text_content": "Find the derivative of f(x) = x^2",
                "latex_content": r"f(x) = x^2",
                "question_type": "derivative",
                "difficulty_estimate": "easy",
                "bounding_box": {"x": 50, "y": 100, "width": 400, "height": 60},
                "cropped_image": "data:image/png;base64,iVBORw0KGgo=",
                "confidence": 0.95,
            },
            {
                "page_number": 1,
                "question_number": 2,
                "text_content": "Evaluate the integral",
                "latex_content": r"\int_0^1 x^2 dx",
                "question_type": "integral",
                "difficulty_estimate": "medium",
                "bounding_box": {"x": 50, "y": 200, "width": 400, "height": 80},
                "cropped_image": "data:image/png;base64,iVBORw0KGgo=",
                "confidence": 0.92,
            },
        ],
        "page_images": [
            "data:image/png;base64,page1base64",
            "data:image/png;base64,page2base64",
        ],
        "error": None,
    }


class TestPDFUploadAPI:
    """Test suite for /api/pdf endpoints."""

    @patch('app.routers.pdf.get_pdfs_collection')
    @patch('app.routers.pdf.get_questions_collection')
    @patch('app.routers.pdf.pdf_extractor_service')
    def test_upload_pdf_success(
        self,
        mock_service,
        mock_questions_coll,
        mock_pdfs_coll,
        client,
        sample_pdf_file,
        mock_extraction_result,
    ):
        """Test successful PDF upload and extraction."""
        # Setup mocks
        mock_pdfs_collection = Mock()
        mock_pdfs_collection.insert_one = AsyncMock()
        mock_pdfs_collection.update_one = AsyncMock()
        mock_pdfs_coll.return_value = mock_pdfs_collection

        mock_questions_collection = Mock()
        mock_questions_collection.insert_one = AsyncMock()
        mock_questions_coll.return_value = mock_questions_collection

        mock_service.process_pdf.return_value = mock_extraction_result

        response = client.post(
            "/api/pdf/upload",
            files={"pdf": sample_pdf_file},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total_pages"] == 2
        assert data["question_count"] == 2
        assert "Successfully extracted" in data["message"]

    @patch('app.routers.pdf.get_pdfs_collection')
    @patch('app.routers.pdf.pdf_extractor_service')
    def test_upload_pdf_extraction_error(
        self,
        mock_service,
        mock_pdfs_coll,
        client,
        sample_pdf_file,
    ):
        """Test PDF upload with extraction error."""
        mock_pdfs_collection = Mock()
        mock_pdfs_collection.insert_one = AsyncMock()
        mock_pdfs_collection.update_one = AsyncMock()
        mock_pdfs_coll.return_value = mock_pdfs_collection

        mock_service.process_pdf.return_value = {
            "total_pages": 0,
            "questions": [],
            "page_images": [],
            "error": "Failed to convert PDF to images",
        }

        response = client.post(
            "/api/pdf/upload",
            files={"pdf": sample_pdf_file},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert "Failed to convert" in data["message"]

    def test_upload_invalid_file_type(self, client):
        """Test PDF upload with non-PDF file."""
        text_file = ("test.txt", BytesIO(b"not a pdf"), "text/plain")

        response = client.post(
            "/api/pdf/upload",
            files={"pdf": text_file},
        )

        assert response.status_code == 400
        assert "must be a PDF" in response.json()["detail"]

    def test_upload_empty_file(self, client):
        """Test PDF upload with empty file."""
        empty_file = ("empty.pdf", BytesIO(b""), "application/pdf")

        response = client.post(
            "/api/pdf/upload",
            files={"pdf": empty_file},
        )

        assert response.status_code == 400
        assert "Empty PDF file" in response.json()["detail"]

    def test_upload_missing_file(self, client):
        """Test PDF upload without file."""
        response = client.post("/api/pdf/upload")

        assert response.status_code == 422


class TestPDFListAPI:
    """Test suite for listing PDFs."""

    @patch('app.routers.pdf.get_pdfs_collection')
    @patch('app.routers.pdf.get_questions_collection')
    def test_list_pdfs_success(
        self, mock_questions_coll, mock_pdfs_coll, client
    ):
        """Test listing user's PDFs."""
        mock_pdfs_collection = Mock()
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[
            {
                "_id": "pdf_123",
                "user_id": "dev_user_123",
                "original_filename": "test.pdf",
                "upload_timestamp": "2026-01-17T10:00:00",
                "total_pages": 2,
                "processing_status": "completed",
                "processing_error": None,
            }
        ])
        mock_pdfs_collection.find.return_value = mock_cursor
        mock_pdfs_coll.return_value = mock_pdfs_collection

        mock_questions_collection = Mock()
        mock_questions_collection.count_documents = AsyncMock(return_value=5)
        mock_questions_coll.return_value = mock_questions_collection

        response = client.get("/api/pdf")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["original_filename"] == "test.pdf"
        assert data[0]["question_count"] == 5


class TestPDFQuestionsAPI:
    """Test suite for getting PDF questions."""

    @patch('app.routers.pdf.get_pdfs_collection')
    @patch('app.routers.pdf.get_questions_collection')
    def test_get_questions_success(
        self, mock_questions_coll, mock_pdfs_coll, client
    ):
        """Test getting questions for a PDF."""
        mock_pdfs_collection = Mock()
        mock_pdfs_collection.find_one = AsyncMock(return_value={
            "_id": "pdf_123",
            "user_id": "dev_user_123",
        })
        mock_pdfs_coll.return_value = mock_pdfs_collection

        mock_questions_collection = Mock()
        mock_questions_collection.count_documents = AsyncMock(return_value=1)
        mock_cursor = Mock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[
            {
                "_id": "q_1",
                "pdf_id": "pdf_123",
                "user_id": "dev_user_123",
                "page_number": 1,
                "question_number": 1,
                "text_content": "Test question",
                "latex_content": "x^2",
                "question_type": "equation",
                "difficulty_estimate": "easy",
                "bounding_box": {"x": 0, "y": 0, "width": 100, "height": 50},
                "cropped_image": "data:image/png;base64,test",
                "extraction_confidence": 0.9,
                "created_at": "2026-01-17T10:00:00",
            }
        ])
        mock_questions_collection.find.return_value = mock_cursor
        mock_questions_coll.return_value = mock_questions_collection

        response = client.get("/api/pdf/pdf_123/questions")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["questions"]) == 1
        assert data["questions"][0]["text_content"] == "Test question"

    @patch('app.routers.pdf.get_pdfs_collection')
    def test_get_questions_pdf_not_found(self, mock_pdfs_coll, client):
        """Test getting questions for non-existent PDF."""
        mock_pdfs_collection = Mock()
        mock_pdfs_collection.find_one = AsyncMock(return_value=None)
        mock_pdfs_coll.return_value = mock_pdfs_collection

        response = client.get("/api/pdf/nonexistent/questions")

        assert response.status_code == 404
        assert "PDF not found" in response.json()["detail"]


class TestPDFDeleteAPI:
    """Test suite for deleting PDFs."""

    @patch('app.routers.pdf.get_pdfs_collection')
    @patch('app.routers.pdf.get_questions_collection')
    def test_delete_pdf_success(
        self, mock_questions_coll, mock_pdfs_coll, client
    ):
        """Test deleting a PDF and its questions."""
        mock_pdfs_collection = Mock()
        mock_pdfs_collection.find_one = AsyncMock(return_value={
            "_id": "pdf_123",
            "user_id": "dev_user_123",
        })
        mock_pdfs_collection.delete_one = AsyncMock()
        mock_pdfs_coll.return_value = mock_pdfs_collection

        mock_questions_collection = Mock()
        mock_questions_collection.delete_many = AsyncMock()
        mock_questions_coll.return_value = mock_questions_collection

        response = client.delete("/api/pdf/pdf_123")

        assert response.status_code == 204
        mock_questions_collection.delete_many.assert_called_once()
        mock_pdfs_collection.delete_one.assert_called_once()

    @patch('app.routers.pdf.get_pdfs_collection')
    def test_delete_pdf_not_found(self, mock_pdfs_coll, client):
        """Test deleting non-existent PDF."""
        mock_pdfs_collection = Mock()
        mock_pdfs_collection.find_one = AsyncMock(return_value=None)
        mock_pdfs_coll.return_value = mock_pdfs_collection

        response = client.delete("/api/pdf/nonexistent")

        assert response.status_code == 404
