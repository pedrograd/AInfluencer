#!/usr/bin/env python3
"""
Batch Quality Testing Script
Tests quality for multiple content files as per docs/28-QUALITY-ASSURANCE-SYSTEM.md
"""
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.quality_scorer_service import QualityScorer
from services.detection_tester_service import DetectionTester


def test_content_quality(content_path: Path) -> Dict[str, Any]:
    """Test content quality"""
    scorer = QualityScorer()
    detector = DetectionTester()
    
    # Load content
    content_type = "video" if content_path.suffix.lower() in [".mp4", ".avi", ".mov"] else "image"
    
    # Score quality
    quality_scores = scorer.score(content_path, content_type)
    
    # Test detection
    detection_results = detector.test(content_path)
    
    # Overall assessment
    passed = (
        quality_scores.get('overall', 0) >= 8.0 and
        detection_results.get('passed', False)
    )
    
    return {
        'file': str(content_path),
        'quality': quality_scores,
        'detection': detection_results,
        'passed': passed
    }


def batch_test_quality(content_folder: Path) -> Dict[str, Any]:
    """Batch test quality for all content in folder"""
    results = []
    
    # Find all image and video files
    image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    video_extensions = ['.mp4', '.avi', '.mov']
    
    content_files = []
    for ext in image_extensions + video_extensions:
        content_files.extend(content_folder.glob(f'*{ext}'))
        content_files.extend(content_folder.glob(f'**/*{ext}'))
    
    print(f"Found {len(content_files)} content files")
    
    for content_file in content_files:
        print(f"Testing: {content_file.name}")
        try:
            result = test_content_quality(content_file)
            results.append(result)
        except Exception as e:
            print(f"Error testing {content_file.name}: {e}")
            results.append({
                'file': str(content_file),
                'error': str(e),
                'passed': False
            })
    
    # Summary
    passed = sum(1 for r in results if r.get('passed', False))
    total = len(results)
    
    return {
        'results': results,
        'summary': {
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': (passed / total * 100) if total > 0 else 0
        }
    }


def main():
    parser = argparse.ArgumentParser(description='Batch quality testing')
    parser.add_argument('content_folder', type=Path, help='Folder containing content files')
    parser.add_argument('--output', type=Path, help='Output JSON file for results')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.content_folder.exists():
        print(f"Error: Content folder does not exist: {args.content_folder}")
        sys.exit(1)
    
    print(f"Testing quality for content in: {args.content_folder}")
    print("=" * 60)
    
    # Run batch test
    results = batch_test_quality(args.content_folder)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total files tested: {results['summary']['total']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Pass rate: {results['summary']['pass_rate']:.1f}%")
    
    # Print failed files
    failed = [r for r in results['results'] if not r.get('passed', False)]
    if failed:
        print("\nFailed files:")
        for r in failed:
            print(f"  - {Path(r['file']).name}")
            if 'quality' in r:
                print(f"    Quality: {r['quality'].get('overall', 0):.1f}/10")
            if 'detection' in r:
                print(f"    Detection: {r['detection'].get('average', 0):.2f}")
    
    # Save results if output specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")
    
    # Exit with error code if any failed
    if results['summary']['failed'] > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
