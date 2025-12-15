#!/usr/bin/env python3
"""Test script for face consistency service.

This script tests the face consistency service API endpoints and functionality.
It can be run manually to verify the face consistency service is working correctly.

Usage:
    python3 test_face_consistency.py [--base-url BASE_URL]
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)


def test_health_check(base_url: str) -> bool:
    """Test the health check endpoint."""
    print("\n[1] Testing health check endpoint...")
    try:
        response = requests.get(f"{base_url}/api/generate/face-embedding/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
            print(f"   Service: {data.get('service')}")
            print(f"   Embeddings directory: {data.get('embeddings_dir')}")
            print(f"   Embeddings count: {data.get('embeddings_count')}")
            print(f"   Supported methods: {', '.join(data.get('supported_methods', []))}")
            print(f"   PIL available: {data.get('pil_available')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_list_embeddings(base_url: str) -> bool:
    """Test the list embeddings endpoint."""
    print("\n[2] Testing list embeddings endpoint...")
    try:
        response = requests.get(f"{base_url}/api/generate/face-embedding/list", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ List embeddings passed")
            print(f"   Total embeddings: {data.get('count', 0)}")
            if data.get('embeddings'):
                print(f"   Sample embedding: {data['embeddings'][0].get('embedding_id', 'N/A')}")
            return True
        else:
            print(f"❌ List embeddings failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ List embeddings error: {e}")
        return False


def test_extract_embedding(base_url: str, test_image_path: str | None = None) -> bool:
    """Test the extract embedding endpoint."""
    print("\n[3] Testing extract embedding endpoint...")
    
    if not test_image_path:
        print("⚠️  Skipping extract test (no test image provided)")
        print("   To test extraction, provide a valid image path with --test-image")
        return True
    
    test_path = Path(test_image_path)
    if not test_path.exists():
        print(f"⚠️  Test image not found: {test_image_path}")
        print("   Skipping extract test")
        return True
    
    try:
        payload = {
            "face_image_path": str(test_path),
            "method": "ip_adapter"
        }
        response = requests.post(
            f"{base_url}/api/generate/face-embedding/extract",
            json=payload,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Extract embedding passed")
            print(f"   Embedding ID: {data.get('embedding_id')}")
            print(f"   Method: {data.get('method')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Metadata saved: {data.get('metadata_saved', False)}")
            return True
        else:
            print(f"❌ Extract embedding failed: {response.status_code}")
            error_data = response.json()
            print(f"   Error: {error_data.get('error')}")
            print(f"   Message: {error_data.get('message')}")
            return False
    except Exception as e:
        print(f"❌ Extract embedding error: {e}")
        return False


def main():
    """Run face consistency service tests."""
    parser = argparse.ArgumentParser(description="Test face consistency service")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the API server (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--test-image",
        help="Path to test image for extraction test (optional)"
    )
    args = parser.parse_args()
    
    print("=" * 60)
    print("Face Consistency Service Test")
    print("=" * 60)
    print(f"Base URL: {args.base_url}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check(args.base_url)))
    results.append(("List Embeddings", test_list_embeddings(args.base_url)))
    results.append(("Extract Embedding", test_extract_embedding(args.base_url, args.test_image)))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

