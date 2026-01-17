# Testing Guide

This guide covers how to test the OCR-first analysis backend.

## Setup

Install test dependencies:
```bash
pip install -r requirements.txt
```

## Running Tests

### Unit Tests

Run all unit tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_ocr_service.py -v
pytest tests/test_analyze_api.py -v
```

### Test Coverage

Run tests with coverage report:
```bash
pytest --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html
```

## Verification Script

The `verify_setup.py` script tests the complete system end-to-end.

**Prerequisites:**
1. Backend server must be running:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

2. (Optional) Set GEMINI_API_KEY in `.env` for full functionality

**Run verification:**
```bash
python verify_setup.py
```

**Expected output:**
```
============================================================
OCR-First Analysis Setup Verification
============================================================
🔍 Checking API health...
✅ API is healthy

🔍 Verifying model initialization...
✅ Models loaded successfully

🔍 Testing OCR analysis endpoint...
  Testing: Simple equation (x^2 + 5)
    ✅ OCR Success
       LaTeX detected: x^2 + 5...
       Confidence: 95.0%
       Feedback: This is a quadratic equation...

============================================================
Verification Summary
============================================================
API Health.................................... ✅ PASSED
Model Loading................................. ✅ PASSED
OCR Endpoint.................................. ✅ PASSED
============================================================

✅ All checks passed! System is ready to use.
```

## Test Structure

```
tests/
├── __init__.py
├── test_ocr_service.py      # Unit tests for OCR service
├── test_analyze_api.py      # API endpoint tests
└── test_integration.py      # Integration tests
```

## Test Categories

### 1. OCR Service Tests (`test_ocr_service.py`)
- Model initialization
- LaTeX extraction (success, empty, errors)
- Gemini AI analysis (success, errors, missing API key)

### 2. API Endpoint Tests (`test_analyze_api.py`)
- Valid image upload and analysis
- Invalid file types
- Empty files
- Error handling
- Response format validation

### 3. Integration Tests (`test_integration.py`)
- Full OCR → AI pipeline
- Blank image handling
- Invalid requests

## Manual Testing

### Test the API Directly

Using curl:
```bash
# Create a test image (requires ImageMagick)
convert -size 400x200 xc:white -pointsize 40 -draw "text 100,100 'x^2 + 5'" test.png

# Test the endpoint
curl -X POST http://localhost:8000/api/analyze/ocr_first \
  -F "image=@test.png" | jq
```

Using httpx (Python):
```python
import httpx
from pathlib import Path

with open("test.png", "rb") as f:
    files = {"image": ("test.png", f, "image/png")}
    response = httpx.post("http://localhost:8000/api/analyze/ocr_first", files=files)
    print(response.json())
```

## Troubleshooting Tests

### Pix2Text model not loading
- Check that `pix2text>=1.0.0` is installed
- Model downloads on first load (may take time)
- Check disk space for model files

### Gemini API errors
- Verify `GEMINI_API_KEY` is set in `.env`
- Check API key is valid at https://makersuite.google.com/
- Tests will skip Gemini if key not set (graceful degradation)

### Integration test failures
- Ensure backend server is running on port 8000
- Check MongoDB is running if database tests are included
- Verify no port conflicts

## CI/CD Integration

Add to your CI pipeline:
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml
```

## Frontend Verification

See `/Users/alokthakrar/Projects/cruzhacks26/frontend/TESTING.md` for frontend testing guide.
