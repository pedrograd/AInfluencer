#!/usr/bin/env python3
"""
Adjust QA Thresholds
Analyzes current metrics and suggests/adjusts QA thresholds
"""
import sys
import argparse
from pathlib import Path
from typing import Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db, init_db
from models import Setting
from services.quality_metrics_service import QualityMetrics
from services.quality_dashboard_service import QualityDashboard


def get_current_thresholds(db) -> Dict[str, Any]:
    """Get current QA thresholds from database"""
    thresholds = {}
    
    # Try to get from settings
    settings = db.query(Setting).filter(
        Setting.category == "qa_thresholds"
    ).all()
    
    for setting in settings:
        thresholds[setting.key] = setting.value
    
    # Defaults if not set
    defaults = {
        "min_overall_score": 8.0,
        "min_face_score": 8.0,
        "min_technical_score": 7.5,
        "min_realism_score": 8.0,
        "auto_approval_overall": 9.0,
        "auto_approval_all": 8.5,
        "detection_threshold": 0.3,
        "detection_max_individual": 0.4,
        "detection_max_any": 0.5
    }
    
    for key, default in defaults.items():
        if key not in thresholds:
            thresholds[key] = default
    
    return thresholds


def analyze_metrics(db, days: int = 30) -> Dict[str, Any]:
    """Analyze current metrics to suggest threshold adjustments"""
    metrics = QualityMetrics(db)
    dashboard = QualityDashboard(db)
    
    all_metrics = metrics.get_all_metrics(days=days)
    summary = dashboard.get_summary()
    
    analysis = {
        "current_metrics": {
            "quality_avg": summary.get('quality_avg', 0),
            "approval_rate": summary.get('approval_rate', 0),
            "pass_rate": summary.get('pass_rate', 0),
            "automation_rate": summary.get('automation_rate', 0)
        },
        "targets": {
            "quality_avg": 8.5,
            "approval_rate": 80,
            "pass_rate": 95,
            "automation_rate": 90
        },
        "suggestions": []
    }
    
    # Analyze and suggest adjustments
    quality_avg = summary.get('quality_avg', 0)
    approval_rate = summary.get('approval_rate', 0)
    pass_rate = summary.get('pass_rate', 0)
    
    # If quality average is high but approval rate is low, thresholds might be too strict
    if quality_avg >= 8.5 and approval_rate < 70:
        analysis["suggestions"].append({
            "type": "lower_thresholds",
            "reason": "High quality average but low approval rate suggests thresholds are too strict",
            "recommendations": {
                "min_overall_score": 7.5,
                "min_face_score": 7.5,
                "min_technical_score": 7.0
            }
        })
    
    # If quality average is low, thresholds might be too lenient
    if quality_avg < 8.0:
        analysis["suggestions"].append({
            "type": "raise_thresholds",
            "reason": "Low quality average suggests thresholds should be raised",
            "recommendations": {
                "min_overall_score": 8.5,
                "min_face_score": 8.5,
                "min_technical_score": 8.0
            }
        })
    
    # If detection pass rate is low, detection threshold might be too strict
    if pass_rate < 90:
        analysis["suggestions"].append({
            "type": "adjust_detection",
            "reason": "Low detection pass rate suggests threshold might be too strict",
            "recommendations": {
                "detection_threshold": 0.35,
                "detection_max_individual": 0.45
            }
        })
    
    # If detection pass rate is very high (>98%), might be too lenient
    if pass_rate > 98:
        analysis["suggestions"].append({
            "type": "tighten_detection",
            "reason": "Very high pass rate suggests detection threshold might be too lenient",
            "recommendations": {
                "detection_threshold": 0.25,
                "detection_max_individual": 0.35
            }
        })
    
    return analysis


def save_thresholds(db, thresholds: Dict[str, Any]):
    """Save thresholds to database"""
    for key, value in thresholds.items():
        setting = db.query(Setting).filter(
            Setting.category == "qa_thresholds",
            Setting.key == key
        ).first()
        
        if setting:
            setting.value = value
        else:
            setting = Setting(
                category="qa_thresholds",
                key=key,
                value=value,
                description=f"QA threshold: {key}"
            )
            db.add(setting)
    
    db.commit()
    print("✅ Thresholds saved to database")


def main():
    parser = argparse.ArgumentParser(description='Adjust QA Thresholds')
    parser.add_argument('--analyze', action='store_true', help='Analyze and suggest adjustments')
    parser.add_argument('--days', type=int, default=30, help='Analysis period in days (default: 30)')
    parser.add_argument('--apply', action='store_true', help='Apply suggested adjustments')
    parser.add_argument('--set', type=str, help='Set specific threshold (format: key=value)')
    parser.add_argument('--list', action='store_true', help='List current thresholds')
    parser.add_argument('--output', type=Path, help='Output analysis to JSON file')
    
    args = parser.parse_args()
    
    init_db()
    db = next(get_db())
    
    try:
        if args.list:
            thresholds = get_current_thresholds(db)
            print("\nCurrent QA Thresholds:")
            print("=" * 60)
            for key, value in sorted(thresholds.items()):
                print(f"  {key}: {value}")
            return
        
        if args.set:
            key, value = args.set.split('=', 1)
            try:
                value = float(value) if '.' in value else int(value)
            except ValueError:
                print(f"❌ Invalid value: {value}")
                sys.exit(1)
            
            thresholds = get_current_thresholds(db)
            thresholds[key] = value
            save_thresholds(db, thresholds)
            print(f"✅ Set {key} = {value}")
            return
        
        if args.analyze:
            print("Analyzing metrics and suggesting threshold adjustments...")
            print("=" * 60)
            
            analysis = analyze_metrics(db, days=args.days)
            
            print(f"\nCurrent Metrics (last {args.days} days):")
            current = analysis["current_metrics"]
            targets = analysis["targets"]
            for key in current:
                current_val = current[key]
                target_val = targets.get(key, 0)
                status = "✅" if current_val >= target_val else "❌"
                print(f"  {key}: {current_val:.2f} (target: {target_val}) {status}")
            
            if analysis["suggestions"]:
                print(f"\n💡 Suggestions ({len(analysis['suggestions'])}):")
                for i, suggestion in enumerate(analysis["suggestions"], 1):
                    print(f"\n  {i}. {suggestion['type']}")
                    print(f"     Reason: {suggestion['reason']}")
                    print(f"     Recommendations:")
                    for rec_key, rec_value in suggestion['recommendations'].items():
                        print(f"       {rec_key}: {rec_value}")
                
                if args.apply:
                    print("\n" + "=" * 60)
                    confirm = input("Apply these adjustments? (y/N): ").strip().lower()
                    if confirm == 'y':
                        thresholds = get_current_thresholds(db)
                        for suggestion in analysis["suggestions"]:
                            thresholds.update(suggestion["recommendations"])
                        save_thresholds(db, thresholds)
                        print("✅ Thresholds updated")
                    else:
                        print("Cancelled")
            else:
                print("\n✅ No adjustments needed - metrics are within targets")
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(analysis, f, indent=2)
                print(f"\n✅ Analysis saved to: {args.output}")
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
