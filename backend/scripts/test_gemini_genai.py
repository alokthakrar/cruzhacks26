"""
Test script to try Google Generative AI SDK (google-genai) instead of Vertex AI.
This uses API key authentication instead of service account.

Run from backend directory:
    python -m scripts.test_gemini_genai
"""

import os
import sys
from pathlib import Path

# Add parent directory to path and change to backend dir for .env
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))
os.chdir(backend_dir)

from dotenv import load_dotenv
load_dotenv()


def test_genai():
    """Test Google Generative AI SDK."""

    print("=" * 60)
    print("GOOGLE GENERATIVE AI SDK TEST")
    print("=" * 60)

    # Check for API key
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    print(f"\n1. CONFIGURATION:")
    print(f"   GOOGLE_API_KEY set: {bool(os.environ.get('GOOGLE_API_KEY'))}")
    print(f"   GEMINI_API_KEY set: {bool(os.environ.get('GEMINI_API_KEY'))}")

    if not api_key:
        print("\n❌ No API key found!")
        print("\nTo use Google Generative AI SDK:")
        print("1. Go to https://aistudio.google.com/app/apikey")
        print("2. Create an API key")
        print("3. Add to .env: GOOGLE_API_KEY=your_key_here")
        return

    print(f"\n2. INITIALIZING GOOGLE GENAI...")
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        print(f"   ✅ Google GenAI configured successfully")
    except ImportError:
        print("   ❌ google-generativeai not installed")
        print("   Run: pip install google-generativeai")
        return
    except Exception as e:
        print(f"   ❌ Failed to configure: {e}")
        return

    # Test models
    models_to_test = [
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-flash-preview-05-20",
    ]

    test_prompt = "What is 2 + 2? Reply with just the number."

    print(f"\n3. TESTING MODELS:")
    print(f"   Test prompt: '{test_prompt}'")
    print("-" * 60)

    for model_name in models_to_test:
        print(f"\n   Testing: {model_name}")
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(test_prompt)
            print(f"   ✅ SUCCESS: Response = '{response.text.strip()}'")
        except Exception as e:
            error_str = str(e)
            print(f"   ❌ FAILED: {error_str[:100]}...")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_genai()
