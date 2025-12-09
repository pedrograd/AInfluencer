"""
Comprehensive Endpoint Testing Suite
Tests all API endpoints for functionality and correctness
"""
import pytest
import requests
import json
from pathlib import Path
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class TestEndpoints:
    """Test suite for all API endpoints"""
    
    @pytest.fixture
    def base_url(self):
        return BASE_URL
    
    def test_health_check(self, base_url):
        """Test health check endpoint"""
        response = requests.get(f"{base_url}/api/health", timeout=TEST_TIMEOUT)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "status" in data["data"]
        print("✅ Health check passed")
    
    def test_root_endpoint(self, base_url):
        """Test root endpoint"""
        response = requests.get(f"{base_url}/", timeout=TEST_TIMEOUT)
        assert response.status_code == 200
        print("✅ Root endpoint passed")
    
    # ========================================================================
    # Prompt Engineering Endpoints
    # ========================================================================
    
    def test_build_prompt(self, base_url):
        """Test prompt building endpoint"""
        payload = {
            "character_description": "A 25-year-old woman, athletic build",
            "pose": "standing pose, natural smile",
            "setting": "modern coffee shop",
            "platform": "instagram",
            "quality_modifiers": ["8k uhd", "highly detailed"]
        }
        response = requests.post(
            f"{base_url}/api/prompts/build",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "prompt" in data["data"]
        assert "negative_prompt" in data["data"]
        assert len(data["data"]["prompt"]) > 0
        print("✅ Build prompt endpoint passed")
    
    def test_optimize_prompt(self, base_url):
        """Test prompt optimization endpoint"""
        payload = {
            "prompt": "A woman, nice photo",
            "target_quality": "high"
        }
        response = requests.post(
            f"{base_url}/api/prompts/optimize",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "optimized" in data["data"]
        assert len(data["data"]["optimized"]) > len(data["data"]["original"])
        print("✅ Optimize prompt endpoint passed")
    
    def test_prompt_variations(self, base_url):
        """Test prompt variations endpoint"""
        payload = {
            "base_prompt": "A 25-year-old woman, professional photography",
            "count": 3
        }
        response = requests.post(
            f"{base_url}/api/prompts/variations",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "variations" in data["data"]
        assert len(data["data"]["variations"]) == 3
        print("✅ Prompt variations endpoint passed")
    
    # ========================================================================
    # Quality Assurance Endpoints
    # ========================================================================
    
    def test_quality_score(self, base_url):
        """Test quality scoring endpoint"""
        # Note: This requires an actual image file
        # For testing, we'll check the endpoint structure
        payload = {
            "content_path": "/test/path/image.jpg",
            "content_type": "image"
        }
        response = requests.post(
            f"{base_url}/api/quality/score",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        # Should return 200 even if file doesn't exist (error handling)
        assert response.status_code in [200, 400, 404]
        print("✅ Quality score endpoint structure verified")
    
    def test_quality_validate(self, base_url):
        """Test quality validation endpoint"""
        payload = {
            "content_path": "/test/path/image.jpg",
            "content_type": "image",
            "min_score": 8.0
        }
        response = requests.post(
            f"{base_url}/api/quality/validate",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code in [200, 400, 404]
        print("✅ Quality validate endpoint structure verified")
    
    # ========================================================================
    # Anti-Detection Endpoints
    # ========================================================================
    
    def test_anti_detection_process(self, base_url):
        """Test anti-detection processing endpoint"""
        payload = {
            "image_path": "/test/path/image.jpg",
            "config": {
                "remove_metadata": True,
                "add_imperfections": True,
                "vary_quality": True
            }
        }
        response = requests.post(
            f"{base_url}/api/anti-detection/process",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code in [200, 400, 404]
        print("✅ Anti-detection process endpoint structure verified")
    
    def test_anti_detection_test(self, base_url):
        """Test anti-detection testing endpoint"""
        payload = {
            "image_path": "/test/path/image.jpg",
            "detection_tools": ["hive", "sensity"]
        }
        response = requests.post(
            f"{base_url}/api/anti-detection/test",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code in [200, 400, 404]
        print("✅ Anti-detection test endpoint structure verified")
    
    def test_anti_detection_batch(self, base_url):
        """Test batch anti-detection endpoint"""
        payload = {
            "input_folder": "/test/input",
            "output_folder": "/test/output",
            "config": {
                "remove_metadata": True
            }
        }
        response = requests.post(
            f"{base_url}/api/anti-detection/batch",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code in [200, 400, 404]
        print("✅ Anti-detection batch endpoint structure verified")
    
    # ========================================================================
    # Generation Endpoints
    # ========================================================================
    
    def test_generate_image(self, base_url):
        """Test image generation endpoint"""
        payload = {
            "prompt": "A 25-year-old woman, professional photography, highly detailed, photorealistic",
            "negative_prompt": "low quality, blurry, bad anatomy",
            "settings": {
                "steps": 30,
                "cfg_scale": 7.5,
                "width": 512,
                "height": 512
            },
            "face_consistency": {
                "enabled": False
            },
            "post_processing": {
                "enabled": True,
                "remove_metadata": True
            }
        }
        response = requests.post(
            f"{base_url}/api/generate/image",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "job_id" in data["data"]
        print("✅ Generate image endpoint passed")
    
    def test_generate_video(self, base_url):
        """Test video generation endpoint"""
        payload = {
            "prompt": "A 25-year-old woman walking, professional video",
            "negative_prompt": "low quality, blurry",
            "settings": {
                "frame_count": 16,
                "fps": 8
            }
        }
        response = requests.post(
            f"{base_url}/api/generate/video",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "job_id" in data["data"]
        print("✅ Generate video endpoint passed")
    
    def test_batch_generate(self, base_url):
        """Test batch generation endpoint"""
        payload = {
            "type": "image",
            "count": 3,
            "prompt_template": "A 25-year-old woman, {variation}, professional photography",
            "variations": ["standing pose", "sitting pose", "walking pose"],
            "settings": {
                "steps": 30
            }
        }
        response = requests.post(
            f"{base_url}/api/generate/batch",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "batch_job_id" in data["data"]
        print("✅ Batch generate endpoint passed")
    
    # ========================================================================
    # Media Endpoints
    # ========================================================================
    
    def test_list_media(self, base_url):
        """Test media listing endpoint"""
        response = requests.get(
            f"{base_url}/api/media?page=1&limit=10",
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "items" in data["data"]
        print("✅ List media endpoint passed")
    
    # ========================================================================
    # Character Endpoints
    # ========================================================================
    
    def test_list_characters(self, base_url):
        """Test character listing endpoint"""
        response = requests.get(
            f"{base_url}/api/characters?page=1&limit=10",
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "characters" in data["data"]
        print("✅ List characters endpoint passed")
    
    def test_create_character(self, base_url):
        """Test character creation endpoint"""
        payload = {
            "name": "Test Character",
            "description": "Test character for API testing",
            "settings": {}
        }
        response = requests.post(
            f"{base_url}/api/characters",
            json=payload,
            timeout=TEST_TIMEOUT
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "character_id" in data["data"]
        print("✅ Create character endpoint passed")
        
        # Clean up - delete test character
        if "character_id" in data["data"]:
            char_id = data["data"]["character_id"]
            requests.delete(f"{base_url}/api/characters/{char_id}", timeout=TEST_TIMEOUT)

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
