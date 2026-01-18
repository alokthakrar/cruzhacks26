"""
Test script to debug Gemini/Vertex AI API issues.

Run from backend directory:
    python -m scripts.test_gemini
"""

import os
import sys
from pathlib import Path

# Add parent directory to path and change to backend dir for .env
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))
os.chdir(backend_dir)

from app.config import get_settings


def test_gemini():
    """Test various Gemini models and configurations."""

    print("=" * 60)
    print("GEMINI API DEBUG TEST")
    print("=" * 60)

    # Load settings
    settings = get_settings()
    print(f"\n1. CONFIGURATION:")
    print(f"   GCP Project ID: {settings.gcp_project_id or 'NOT SET'}")
    print(f"   GCP Location: {settings.gcp_location}")
    print(f"   Auth file exists: {os.path.exists('auth.json')}")

    if not settings.gcp_project_id:
        print("\n❌ ERROR: GCP_PROJECT_ID not set in .env")
        return

    if not os.path.exists("auth.json"):
        print("\n❌ ERROR: auth.json not found in backend directory")
        return

    # Set credentials
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "auth.json"
    print(f"   GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")

    # Initialize Vertex AI
    print(f"\n2. INITIALIZING VERTEX AI...")
    try:
        import vertexai
        vertexai.init(project=settings.gcp_project_id, location=settings.gcp_location)
        print(f"   ✅ Vertex AI initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize Vertex AI: {e}")
        return

    # Test different models
    from vertexai.generative_models import GenerativeModel

    models_to_test = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-2.0-flash-001",
        "gemini-2.5-flash",
    ]

    test_prompt = "What is 2 + 2? Reply with just the number."

    print(f"\n3. TESTING MODELS:")
    print(f"   Test prompt: '{test_prompt}'")
    print("-" * 60)

    for model_name in models_to_test:
        print(f"\n   Testing: {model_name}")
        try:
            model = GenerativeModel(model_name)
            response = model.generate_content(test_prompt)
            print(f"   ✅ SUCCESS: Response = '{response.text.strip()}'")
        except Exception as e:
            error_str = str(e)
            print(f"   ❌ FAILED: {error_str[:100]}...")

            # Parse common errors
            if "404" in error_str:
                print(f"      → Model not found/available in your project")
            elif "403" in error_str:
                print(f"      → Permission denied - check IAM roles")
            elif "400" in error_str:
                print(f"      → Bad request - model may not be enabled")
                if "Precondition" in error_str:
                    print(f"      → Precondition failed - API may need to be enabled")
            elif "429" in error_str:
                print(f"      → Rate limited - too many requests")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    print("\nNEXT STEPS:")
    print("- If gemini-1.5-flash works but gemini-2.5-flash doesn't:")
    print("  → gemini-2.5-flash may not be available in your region yet")
    print("  → Try enabling it in GCP Console → Vertex AI → Model Garden")
    print("- If all models fail with 'Precondition':")
    print("  → Enable 'Vertex AI API' in GCP Console")
    print("  → Check your service account has 'Vertex AI User' role")


if __name__ == "__main__":
    test_gemini()
