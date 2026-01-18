#!/usr/bin/env python3
"""
Verification script to test OCR-first analysis setup.
Run this after starting the backend server to verify everything works.
"""

import sys
import httpx
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


def create_test_image(text: str) -> bytes:
    """Create a simple test image with text."""
    img = Image.new('RGB', (500, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 50)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 70), text, fill='black', font=font)
    
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    return img_bytes.getvalue()


def verify_health():
    """Verify the API is running."""
    print("🔍 Checking API health...")
    try:
        response = httpx.get("http://localhost:8000/health", timeout=5.0)
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except httpx.ConnectError:
        print("❌ Cannot connect to API. Is the server running on port 8000?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def verify_ocr_endpoint():
    """Verify the OCR analysis endpoint works."""
    print("\n🔍 Testing OCR analysis endpoint...")
    
    test_cases = [
        ("x^2 + 5", "Simple equation"),
        ("∫ x dx", "Integration"),
        ("2x = 10", "Linear equation"),
    ]
    
    for text, description in test_cases:
        print(f"\n  Testing: {description} ({text})")
        image_bytes = create_test_image(text)
        
        try:
            with httpx.Client(timeout=60.0) as client:
                files = {"image": ("test.png", image_bytes, "image/png")}
                response = client.post(
                    "http://localhost:8000/api/analyze/ocr_first",
                    files=files
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"    ✅ OCR Success")
                    print(f"       LaTeX detected: {data['latex_string'][:50]}...")
                    print(f"       Confidence: {data['ocr_confidence']*100:.1f}%")
                    print(f"       Feedback: {data['feedback'][:80]}...")
                    if data['hints']:
                        print(f"       Hints: {len(data['hints'])} provided")
                else:
                    print(f"    ❌ Failed with status {response.status_code}")
                    print(f"       {response.text}")
                    return False
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return False
    
    return True


def verify_models_loaded():
    """Check if models are properly loaded."""
    print("\n🔍 Verifying model initialization...")
    
    blank_img = Image.new('RGB', (100, 100), color='white')
    img_bytes = BytesIO()
    blank_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    try:
        with httpx.Client(timeout=30.0) as client:
            files = {"image": ("blank.png", img_bytes.getvalue(), "image/png")}
            response = client.post(
                "http://localhost:8000/api/analyze/ocr_first",
                files=files
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('ocr_error') and 'not loaded' in data['ocr_error']:
                    print("❌ Pix2Text model not loaded")
                    return False
                
                if data.get('analysis_error') and 'not configured' in data['analysis_error']:
                    print("⚠️  Gemini API not configured (optional)")
                    print("   Set GEMINI_API_KEY in .env to enable AI feedback")
                else:
                    print("✅ Models loaded successfully")
                
                return True
            else:
                print(f"❌ Unexpected status: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all verification checks."""
    print("=" * 60)
    print("OCR-First Analysis Setup Verification")
    print("=" * 60)
    
    checks = [
        ("API Health", verify_health),
        ("Model Loading", verify_models_loaded),
        ("OCR Endpoint", verify_ocr_endpoint),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} check failed with exception: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:.<40} {status}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✅ All checks passed! System is ready to use.")
        print("\nNext steps:")
        print("  1. Navigate to http://localhost:3000/canvas")
        print("  2. Draw a math expression")
        print("  3. Click 'Check My Work'")
        print("  4. Verify the OCR detection and AI feedback\n")
        return 0
    else:
        print("\n❌ Some checks failed. Please review the errors above.")
        print("\nTroubleshooting:")
        print("  - Ensure backend server is running: uvicorn app.main:app --reload --port 8000")
        print("  - Check that all dependencies are installed: pip install -r requirements.txt")
        print("  - Verify .env file has GEMINI_API_KEY set (optional but recommended)\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
