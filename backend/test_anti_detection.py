"""
Automated Anti-Detection Testing Script
Tests all anti-detection features automatically
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try loading from parent directory
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from services.anti_detection_service import (
    AntiDetectionService,
    MetadataCleaner,
    ContentHumanizer
)
from PIL import Image
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AntiDetectionTester:
    """Automated tester for anti-detection features"""
    
    def __init__(self):
        self.anti_detection = AntiDetectionService()
        self.metadata_cleaner = MetadataCleaner()
        self.content_humanizer = ContentHumanizer()
        self.test_results = []
        self.test_dir = Path(__file__).parent / "test_output"
        self.test_dir.mkdir(exist_ok=True)
    
    def create_test_image(self, output_path: Path, size: tuple = (1024, 1024)) -> Path:
        """Create a test image for testing"""
        logger.info(f"Creating test image: {output_path}")
        
        # Create a simple test image
        img = Image.new("RGB", size, color=(128, 128, 128))
        
        # Add some content
        pixels = np.array(img)
        # Add gradient
        for y in range(size[1]):
            for x in range(size[0]):
                pixels[y, x] = [
                    int(255 * x / size[0]),
                    int(255 * y / size[1]),
                    128
                ]
        
        img = Image.fromarray(pixels.astype(np.uint8))
        img.save(output_path, "PNG")
        
        logger.info(f"Test image created: {output_path}")
        return output_path
    
    def test_metadata_removal(self, image_path: Path) -> Dict[str, Any]:
        """Test metadata removal"""
        logger.info("Testing metadata removal...")
        
        # Create test image with metadata
        test_image = self.test_dir / "test_with_metadata.png"
        self.create_test_image(test_image)
        
        # Add some metadata (simulated)
        cleaned_image = self.test_dir / "test_cleaned.png"
        
        # Test metadata cleaning
        success = self.metadata_cleaner.clean_all_metadata(test_image, cleaned_image)
        
        # Verify removal
        from services.anti_detection_service import AntiDetectionService
        check = AntiDetectionService()
        metadata_check = check.check_metadata(cleaned_image)
        
        result = {
            "test": "metadata_removal",
            "success": success,
            "metadata_clean": metadata_check.get("clean", False),
            "has_exif": metadata_check.get("has_exif", False),
            "has_piexif": metadata_check.get("has_piexif", False),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Metadata removal test: {result}")
        return result
    
    def test_detection_tools(self, image_path: Path) -> Dict[str, Any]:
        """Test detection tools"""
        logger.info("Testing detection tools...")
        
        results = self.anti_detection.test_detection(
            image_path,
            tools=None,  # Test all tools
            threshold=0.3
        )
        
        result = {
            "test": "detection_tools",
            "average_score": results["average_score"],
            "threshold": results["threshold"],
            "passed": results["passed"],
            "tool_results": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Extract individual tool results
        for tool_name, tool_result in results["results"].items():
            result["tool_results"][tool_name] = {
                "score": tool_result.get("score", 0.5),
                "detected": tool_result.get("detected", False),
                "error": tool_result.get("error")
            }
        
        logger.info(f"Detection tools test: Average score = {results['average_score']:.2%}, Passed = {results['passed']}")
        return result
    
    def test_pre_publication_check(self, image_path: Path) -> Dict[str, Any]:
        """Test pre-publication check"""
        logger.info("Testing pre-publication check...")
        
        check_results = self.anti_detection.pre_publication_test(
            image_path,
            threshold=0.3
        )
        
        result = {
            "test": "pre_publication_check",
            "passed": check_results["passed"],
            "ready_for_publication": check_results["ready_for_publication"],
            "detection": {
                "average_score": check_results["detection"]["average_score"],
                "passed": check_results["detection"]["passed"]
            },
            "metadata": check_results["metadata"],
            "quality": check_results["quality"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Pre-publication check: Ready = {check_results['ready_for_publication']}")
        return result
    
    def test_content_humanization(self, image_path: Path) -> Dict[str, Any]:
        """Test content humanization"""
        logger.info("Testing content humanization...")
        
        # Load image
        img = Image.open(image_path)
        
        # Apply humanization
        humanized = self.content_humanizer.add_natural_imperfections(img, intensity=0.1)
        
        # Save humanized version
        humanized_path = self.test_dir / "test_humanized.png"
        humanized.save(humanized_path, "PNG")
        
        # Test detection on humanized version
        detection_results = self.anti_detection.test_detection(humanized_path, threshold=0.3)
        
        result = {
            "test": "content_humanization",
            "original_score": 0.5,  # Placeholder
            "humanized_score": detection_results["average_score"],
            "improvement": detection_results["average_score"] < 0.5,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Content humanization test: Score = {detection_results['average_score']:.2%}")
        return result
    
    def test_metadata_check(self, image_path: Path) -> Dict[str, Any]:
        """Test metadata checking"""
        logger.info("Testing metadata check...")
        
        metadata_check = self.anti_detection.check_metadata(image_path)
        quality_check = self.anti_detection.check_image_quality(image_path)
        
        result = {
            "test": "metadata_check",
            "metadata": metadata_check,
            "quality": quality_check,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Metadata check: Clean = {metadata_check.get('clean', False)}")
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all anti-detection tests"""
        logger.info("=" * 60)
        logger.info("Starting Anti-Detection Test Suite")
        logger.info("=" * 60)
        
        # Create test image
        test_image = self.test_dir / "test_image.png"
        self.create_test_image(test_image, size=(1024, 1024))
        
        all_results = {
            "test_suite": "anti_detection",
            "started_at": datetime.utcnow().isoformat(),
            "tests": []
        }
        
        # Run all tests
        try:
            # Test 1: Metadata removal
            result = self.test_metadata_removal(test_image)
            all_results["tests"].append(result)
            self.test_results.append(result)
            
            # Test 2: Detection tools
            result = self.test_detection_tools(test_image)
            all_results["tests"].append(result)
            self.test_results.append(result)
            
            # Test 3: Pre-publication check
            result = self.test_pre_publication_check(test_image)
            all_results["tests"].append(result)
            self.test_results.append(result)
            
            # Test 4: Content humanization
            result = self.test_content_humanization(test_image)
            all_results["tests"].append(result)
            self.test_results.append(result)
            
            # Test 5: Metadata check
            result = self.test_metadata_check(test_image)
            all_results["tests"].append(result)
            self.test_results.append(result)
            
        except Exception as e:
            logger.error(f"Test error: {e}", exc_info=True)
            all_results["error"] = str(e)
        
        all_results["completed_at"] = datetime.utcnow().isoformat()
        
        # Calculate summary
        passed_tests = sum(1 for t in all_results["tests"] if t.get("passed", False) or t.get("success", False))
        total_tests = len(all_results["tests"])
        
        all_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "pass_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
        }
        
        # Save results
        results_file = self.test_dir / f"test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(all_results, f, indent=2)
        
        logger.info("=" * 60)
        logger.info("Test Suite Complete")
        logger.info(f"Results saved to: {results_file}")
        logger.info(f"Summary: {passed_tests}/{total_tests} tests passed ({all_results['summary']['pass_rate']:.1f}%)")
        logger.info("=" * 60)
        
        return all_results
    
    def print_summary(self):
        """Print test summary"""
        if not self.test_results:
            logger.warning("No test results to display")
            return
        
        print("\n" + "=" * 60)
        print("ANTI-DETECTION TEST SUMMARY")
        print("=" * 60)
        
        for result in self.test_results:
            test_name = result.get("test", "unknown")
            status = "✓ PASS" if result.get("passed", result.get("success", False)) else "✗ FAIL"
            print(f"\n{test_name}: {status}")
            
            if "average_score" in result:
                print(f"  Average Score: {result['average_score']:.2%}")
            if "metadata_clean" in result:
                print(f"  Metadata Clean: {result['metadata_clean']}")
            if "ready_for_publication" in result:
                print(f"  Ready for Publication: {result['ready_for_publication']}")
        
        print("\n" + "=" * 60)


def main():
    """Main test runner"""
    print("Anti-Detection Automated Test Suite")
    print("=" * 60)
    
    # Check API keys
    print("\nChecking API keys...")
    api_keys = {
        "HIVE_API_KEY": os.getenv("HIVE_API_KEY"),
        "SENSITY_API_KEY": os.getenv("SENSITY_API_KEY"),
        "AI_OR_NOT_API_KEY": os.getenv("AI_OR_NOT_API_KEY")
    }
    
    missing_keys = [key for key, value in api_keys.items() if not value]
    if missing_keys:
        print(f"\n⚠️  Warning: Missing API keys: {', '.join(missing_keys)}")
        print("Some detection tools may not work without API keys.")
        print("Set them in .env file or environment variables.\n")
    else:
        print("✓ All API keys configured\n")
    
    # Run tests
    tester = AntiDetectionTester()
    results = tester.run_all_tests()
    
    # Print summary
    tester.print_summary()
    
    # Return exit code
    if results.get("summary", {}).get("pass_rate", 0) >= 80:
        print("\n✓ Test suite passed!")
        return 0
    else:
        print("\n✗ Some tests failed. Review results above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
