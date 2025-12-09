#!/usr/bin/env python3
"""
Test QA System
Tests the complete QA system with sample content
"""
import sys
import argparse
from pathlib import Path
from typing import Dict, Any
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.quality_scorer_service import QualityScorer
from services.detection_tester_service import DetectionTester
from services.quality_metrics_service import QualityMetrics
from services.quality_dashboard_service import QualityDashboard
from services.quality_improver_service import QualityImprover
from database import get_db, init_db


def test_quality_scoring(image_path: Path) -> Dict[str, Any]:
    """Test quality scoring"""
    print(f"\n{'='*60}")
    print("Testing Quality Scoring")
    print(f"{'='*60}")
    
    scorer = QualityScorer()
    scores = scorer.score(image_path, "image")
    
    print(f"\nQuality Scores:")
    print(f"  Overall: {scores.get('overall', 0):.1f}/10")
    print(f"  Face: {scores.get('face', 0):.1f}/10")
    print(f"  Technical: {scores.get('technical', 0):.1f}/10")
    print(f"  Realism: {scores.get('realism', 0):.1f}/10")
    print(f"  Passed: {'✅' if scores.get('passed') else '❌'}")
    print(f"  Auto-approved: {'✅' if scores.get('auto_approved') else '❌'}")
    
    return scores


def test_detection(image_path: Path) -> Dict[str, Any]:
    """Test AI detection"""
    print(f"\n{'='*60}")
    print("Testing AI Detection")
    print(f"{'='*60}")
    
    tester = DetectionTester()
    results = tester.test(image_path)
    
    print(f"\nDetection Results:")
    print(f"  Average Score: {results.get('average', 0):.2f}")
    print(f"  Threshold: {results.get('threshold', 0.3)}")
    print(f"  Passed: {'✅' if results.get('passed') else '❌'}")
    
    print(f"\nTool Scores:")
    for tool_name, score in results.get('scores', {}).items():
        status = "✅" if score < 0.3 else "⚠️" if score < 0.4 else "❌"
        print(f"  {tool_name}: {score:.2f} {status}")
    
    return results


def test_metrics():
    """Test quality metrics"""
    print(f"\n{'='*60}")
    print("Testing Quality Metrics")
    print(f"{'='*60}")
    
    init_db()
    db = next(get_db())
    metrics = QualityMetrics(db)
    
    all_metrics = metrics.get_all_metrics(days=7)
    
    print(f"\nGeneration Metrics:")
    gen = all_metrics.get('generation', {})
    print(f"  Content per day: {gen.get('content_generated_per_day', 0):.1f}")
    print(f"  Quality average: {gen.get('quality_score_average', 0):.1f}/10")
    print(f"  Approval rate: {gen.get('approval_rate', 0):.1f}%")
    print(f"  Rejection rate: {gen.get('rejection_rate', 0):.1f}%")
    
    print(f"\nQuality Metrics:")
    qual = all_metrics.get('quality', {})
    print(f"  Average quality: {qual.get('average_quality_score', 0):.1f}/10")
    print(f"  Face quality: {qual.get('face_quality_average', 0):.1f}/10")
    print(f"  Technical quality: {qual.get('technical_quality_average', 0):.1f}/10")
    print(f"  Realism: {qual.get('realism_score_average', 0):.1f}/10")
    
    print(f"\nDetection Metrics:")
    det = all_metrics.get('detection', {})
    print(f"  Average detection: {det.get('average_detection_score', 0):.2f}")
    print(f"  Pass rate: {det.get('detection_pass_rate', 0):.1f}%")
    
    return all_metrics


def test_dashboard():
    """Test dashboard"""
    print(f"\n{'='*60}")
    print("Testing Dashboard")
    print(f"{'='*60}")
    
    init_db()
    db = next(get_db())
    dashboard = QualityDashboard(db)
    
    summary = dashboard.get_summary()
    trends = dashboard.get_trends(days=7)
    alerts = dashboard.get_alerts()
    
    print(f"\nDashboard Summary:")
    print(f"  Quality avg: {summary.get('quality_avg', 0):.1f}/10")
    print(f"  Approval rate: {summary.get('approval_rate', 0):.1f}%")
    print(f"  Detection avg: {summary.get('detection_avg', 0):.2f}")
    print(f"  Pass rate: {summary.get('pass_rate', 0):.1f}%")
    print(f"  Automation rate: {summary.get('automation_rate', 0):.1f}%")
    
    print(f"\nTrends:")
    trend = trends.get('trend', {})
    print(f"  Quality: {trend.get('quality', 'stable')}")
    print(f"  Approval: {trend.get('approval', 'stable')}")
    print(f"  Detection: {trend.get('detection', 'stable')}")
    
    if alerts:
        print(f"\nAlerts ({len(alerts)}):")
        for alert in alerts:
            print(f"  ⚠️  {alert.get('category')}: {alert.get('message')}")
    else:
        print(f"\n✅ No alerts")
    
    return {
        "summary": summary,
        "trends": trends,
        "alerts": alerts
    }


def test_improvements():
    """Test improvement analysis"""
    print(f"\n{'='*60}")
    print("Testing Improvement Analysis")
    print(f"{'='*60}")
    
    init_db()
    db = next(get_db())
    improver = QualityImprover(db)
    
    analysis = improver.analyze_rejections(period_days=7)
    
    patterns = analysis.get('patterns', {})
    print(f"\nRejection Patterns:")
    print(f"  Quality issues: {patterns.get('quality_issues', 0)}")
    print(f"  Detection issues: {patterns.get('detection_issues', 0)}")
    print(f"  Technical issues: {patterns.get('technical_issues', 0)}")
    print(f"  Total rejections: {patterns.get('total_rejections', 0)}")
    
    recommendations = analysis.get('recommendations', [])
    if recommendations:
        print(f"\nRecommendations:")
        for rec in recommendations:
            print(f"  • {rec}")
    else:
        print(f"\n✅ No recommendations")
    
    return analysis


def main():
    parser = argparse.ArgumentParser(description='Test QA System')
    parser.add_argument('image_path', type=Path, nargs='?', help='Path to test image')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--scoring', action='store_true', help='Test quality scoring')
    parser.add_argument('--detection', action='store_true', help='Test detection')
    parser.add_argument('--metrics', action='store_true', help='Test metrics')
    parser.add_argument('--dashboard', action='store_true', help='Test dashboard')
    parser.add_argument('--improvements', action='store_true', help='Test improvements')
    parser.add_argument('--output', type=Path, help='Output JSON file')
    
    args = parser.parse_args()
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "tests": {}
    }
    
    # If --all or no specific test, run all
    run_all = args.all or not any([
        args.scoring, args.detection, args.metrics,
        args.dashboard, args.improvements
    ])
    
    try:
        # Test quality scoring
        if run_all or args.scoring:
            if args.image_path and args.image_path.exists():
                results["tests"]["quality_scoring"] = test_quality_scoring(args.image_path)
            else:
                print("⚠️  Skipping quality scoring (no image provided)")
        
        # Test detection
        if run_all or args.detection:
            if args.image_path and args.image_path.exists():
                results["tests"]["detection"] = test_detection(args.image_path)
            else:
                print("⚠️  Skipping detection (no image provided)")
        
        # Test metrics
        if run_all or args.metrics:
            results["tests"]["metrics"] = test_metrics()
        
        # Test dashboard
        if run_all or args.dashboard:
            results["tests"]["dashboard"] = test_dashboard()
        
        # Test improvements
        if run_all or args.improvements:
            results["tests"]["improvements"] = test_improvements()
        
        # Save results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n✅ Results saved to: {args.output}")
        
        print(f"\n{'='*60}")
        print("✅ All tests completed!")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
