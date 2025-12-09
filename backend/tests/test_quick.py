"""
Quick endpoint test script
Run this to quickly test if all endpoints are accessible
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(method, path, data=None, description=""):
    """Test a single endpoint"""
    try:
        url = f"{BASE_URL}{path}"
        print(f"\n🧪 Testing: {description or path}")
        
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            print(f"  ❌ Unknown method: {method}")
            return False
        
        if response.status_code in [200, 201]:
            print(f"  ✅ {method} {path} - OK ({response.status_code})")
            if response.headers.get('content-type', '').startswith('application/json'):
                result = response.json()
                if result.get('success'):
                    print(f"     Response: success=True")
                else:
                    print(f"     Response: {result.get('error', 'Unknown error')}")
            return True
        else:
            print(f"  ⚠️  {method} {path} - Status {response.status_code}")
            try:
                error = response.json()
                print(f"     Error: {error.get('error', {}).get('message', 'Unknown')}")
            except:
                print(f"     Error: {response.text[:100]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Connection failed - Is server running at {BASE_URL}?")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Quick Endpoint Test Suite")
    print("=" * 60)
    
    # Test server connection
    print("\n📡 Testing server connection...")
    if not test_endpoint("GET", "/api/health", description="Health Check"):
        print("\n❌ Server is not running or not accessible!")
        print("   Please start the backend server:")
        print("   cd backend && python -m uvicorn main:app --reload")
        sys.exit(1)
    
    print("\n✅ Server is running!")
    
    # Test endpoints
    tests = [
        # Prompt Engineering
        ("POST", "/api/prompts/build", {
            "character_description": "A 25-year-old woman",
            "platform": "instagram"
        }, "Build Prompt"),
        
        ("POST", "/api/prompts/optimize", {
            "prompt": "A woman, nice photo",
            "target_quality": "high"
        }, "Optimize Prompt"),
        
        ("POST", "/api/prompts/variations", {
            "base_prompt": "A 25-year-old woman, professional photography",
            "count": 3
        }, "Prompt Variations"),
        
        # Quality Assurance
        ("POST", "/api/quality/score", {
            "content_path": "/test/path/image.jpg",
            "content_type": "image"
        }, "Quality Score"),
        
        ("POST", "/api/quality/validate", {
            "content_path": "/test/path/image.jpg",
            "content_type": "image",
            "min_score": 8.0
        }, "Quality Validate"),
        
        # Anti-Detection
        ("POST", "/api/anti-detection/process", {
            "image_path": "/test/path/image.jpg",
            "config": {"remove_metadata": True}
        }, "Anti-Detection Process"),
        
        ("POST", "/api/anti-detection/test", {
            "image_path": "/test/path/image.jpg"
        }, "Anti-Detection Test"),
        
        # Generation
        ("POST", "/api/generate/image", {
            "prompt": "A 25-year-old woman, professional photography",
            "negative_prompt": "low quality, blurry"
        }, "Generate Image"),
        
        ("POST", "/api/generate/video", {
            "prompt": "A 25-year-old woman walking",
            "negative_prompt": "low quality"
        }, "Generate Video"),
        
        # Media
        ("GET", "/api/media?page=1&limit=10", None, "List Media"),
        
        # Characters
        ("GET", "/api/characters?page=1&limit=10", None, "List Characters"),
    ]
    
    print("\n" + "=" * 60)
    print("Testing All Endpoints")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for method, path, data, description in tests:
        if test_endpoint(method, path, data, description):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ All endpoint structures are correct!")
        return 0
    else:
        print(f"\n⚠️  {failed} endpoint(s) need attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())
