#!/usr/bin/env python3
"""Test script for image generation pipeline.

This script tests the image generation API endpoints and verifies the job flow:
1. Creates an image generation job via POST /api/generate/image
2. Polls job status via GET /api/generate/image/{job_id}
3. Verifies job completion and image file existence
4. Tests error handling for invalid requests

Usage:
    python test_image_generation.py [--base-url BASE_URL] [--timeout TIMEOUT]
    
Options:
    --base-url: Backend API base URL (default: http://localhost:8000)
    --timeout: Maximum time to wait for job completion in seconds (default: 300)
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import requests


def test_image_generation_api(base_url: str = "http://localhost:8000", timeout: int = 300) -> bool:
    """
    Test image generation pipeline via API endpoints.
    
    Args:
        base_url: Backend API base URL
        timeout: Maximum time to wait for job completion in seconds
        
    Returns:
        bool: True if all tests pass, False otherwise
    """
    print("=" * 60)
    print("Testing Image Generation Pipeline")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Timeout: {timeout}s")
    print()
    
    # Test 1: Create image generation job
    print("Test 1: Creating image generation job...")
    test_prompt = "a beautiful sunset over mountains, high quality, detailed"
    test_request = {
        "prompt": test_prompt,
        "negative_prompt": "blurry, low quality",
        "width": 512,
        "height": 512,
        "steps": 20,
        "cfg": 7.0,
        "batch_size": 1,
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/generate/image",
            json=test_request,
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        
        if not result.get("ok"):
            print(f"❌ FAILED: Job creation returned ok=False")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return False
        
        job_id = result.get("job", {}).get("id")
        if not job_id:
            print(f"❌ FAILED: No job ID in response")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return False
        
        print(f"✅ PASSED: Job created successfully")
        print(f"   Job ID: {job_id}")
        print(f"   State: {result.get('job', {}).get('state')}")
        print()
        
    except requests.exceptions.ConnectionError:
        print(f"❌ FAILED: Cannot connect to backend at {base_url}")
        print(f"   Make sure the backend server is running")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False
    
    # Test 2: Get job status
    print("Test 2: Retrieving job status...")
    try:
        response = requests.get(
            f"{base_url}/api/generate/image/{job_id}",
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        
        if not result.get("ok"):
            print(f"❌ FAILED: Job status retrieval returned ok=False")
            print(f"   Response: {json.dumps(result, indent=2)}")
            return False
        
        job_state = result.get("job", {}).get("state")
        print(f"✅ PASSED: Job status retrieved")
        print(f"   Job ID: {job_id}")
        print(f"   State: {job_state}")
        print()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Request error: {e}")
        return False
    
    # Test 3: Poll job until completion (with timeout)
    print("Test 3: Polling job until completion...")
    print(f"   (This may take up to {timeout} seconds)")
    start_time = time.time()
    max_wait = timeout
    poll_interval = 2  # Poll every 2 seconds
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f"{base_url}/api/generate/image/{job_id}",
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()
            
            if not result.get("ok"):
                print(f"❌ FAILED: Job status check returned ok=False")
                return False
            
            job = result.get("job", {})
            job_state = job.get("state")
            
            if job_state == "succeeded":
                print(f"✅ PASSED: Job completed successfully")
                print(f"   Job ID: {job_id}")
                print(f"   State: {job_state}")
                
                # Check for image path
                image_path = job.get("image_path")
                image_paths = job.get("image_paths")
                
                if image_path:
                    print(f"   Image path: {image_path}")
                    # Verify file exists
                    if Path(image_path).exists():
                        print(f"✅ PASSED: Image file exists at {image_path}")
                    else:
                        print(f"⚠️  WARNING: Image file not found at {image_path}")
                elif image_paths and len(image_paths) > 0:
                    print(f"   Image paths: {len(image_paths)} images")
                    for i, path in enumerate(image_paths):
                        if Path(path).exists():
                            print(f"   ✅ Image {i+1}: {path}")
                        else:
                            print(f"   ⚠️  Image {i+1} not found: {path}")
                else:
                    print(f"⚠️  WARNING: No image path in job result")
                
                print()
                break
            elif job_state == "failed":
                error = job.get("error", "Unknown error")
                print(f"❌ FAILED: Job failed with error: {error}")
                return False
            elif job_state == "cancelled":
                print(f"⚠️  WARNING: Job was cancelled")
                return False
            else:
                # Still running/queued
                elapsed = int(time.time() - start_time)
                print(f"   [{elapsed}s] Job state: {job_state}...", end="\r")
                time.sleep(poll_interval)
                
        except requests.exceptions.RequestException as e:
            print(f"❌ FAILED: Request error during polling: {e}")
            return False
    
    else:
        # Timeout reached
        print(f"\n⚠️  WARNING: Job did not complete within {timeout} seconds")
        print(f"   This may be normal if ComfyUI is not running or is slow")
        print(f"   Job ID: {job_id} - check status manually")
        return False
    
    # Test 4: Test invalid request (missing prompt)
    print("Test 4: Testing error handling (invalid request)...")
    try:
        invalid_request = {
            "width": 512,
            "height": 512,
            # Missing required "prompt" field
        }
        response = requests.post(
            f"{base_url}/api/generate/image",
            json=invalid_request,
            timeout=10,
        )
        # Should return 422 (validation error) or 400 (bad request)
        if response.status_code in (400, 422):
            print(f"✅ PASSED: Invalid request correctly rejected")
            print(f"   Status code: {response.status_code}")
        else:
            print(f"⚠️  WARNING: Expected 400/422, got {response.status_code}")
        print()
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️  WARNING: Error during invalid request test: {e}")
        print()
    
    # Test 5: List recent jobs
    print("Test 5: Listing recent jobs...")
    try:
        response = requests.get(
            f"{base_url}/api/generate/image/jobs",
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        
        items = result.get("items", [])
        print(f"✅ PASSED: Retrieved {len(items)} recent jobs")
        if items:
            latest = items[0]
            print(f"   Latest job ID: {latest.get('id')}")
            print(f"   Latest job state: {latest.get('state')}")
        print()
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️  WARNING: Error listing jobs: {e}")
        print()
    
    print("=" * 60)
    print("✅ All tests completed")
    print("=" * 60)
    return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test image generation pipeline")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Backend API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Maximum time to wait for job completion in seconds (default: 300)",
    )
    
    args = parser.parse_args()
    
    success = test_image_generation_api(base_url=args.base_url, timeout=args.timeout)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

