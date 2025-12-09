#!/usr/bin/env python3
"""
Monitor QA Metrics
Continuously monitors QA metrics and alerts on issues
"""
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db, init_db
from services.quality_dashboard_service import QualityDashboard
from services.quality_metrics_service import QualityMetrics


def format_metric(name: str, value: Any, target: Any = None, unit: str = "") -> str:
    """Format a metric for display"""
    if isinstance(value, float):
        value_str = f"{value:.2f}"
    else:
        value_str = str(value)
    
    status = ""
    if target is not None:
        if isinstance(value, (int, float)) and isinstance(target, (int, float)):
            if value >= target:
                status = "✅"
            else:
                status = "❌"
    
    return f"  {name}: {value_str}{unit} {status}"


def monitor_once(days: int = 7, verbose: bool = False) -> Dict[str, Any]:
    """Monitor metrics once"""
    init_db()
    db = next(get_db())
    
    dashboard = QualityDashboard(db)
    metrics = QualityMetrics(db)
    
    summary = dashboard.get_summary()
    all_metrics = metrics.get_all_metrics(days=days)
    alerts = dashboard.get_alerts()
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"QA Metrics Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        print(f"\n📊 Summary Metrics:")
        print(format_metric("Quality Average", summary.get('quality_avg', 0), 8.5, "/10"))
        print(format_metric("Approval Rate", summary.get('approval_rate', 0), 80, "%"))
        print(format_metric("Detection Pass Rate", summary.get('pass_rate', 0), 95, "%"))
        print(format_metric("Automation Rate", summary.get('automation_rate', 0), 90, "%"))
        print(format_metric("Generation Count", summary.get('generation_count', 0)))
        
        gen_metrics = all_metrics.get('generation', {})
        qual_metrics = all_metrics.get('quality', {})
        det_metrics = all_metrics.get('detection', {})
        
        print(f"\n📈 Detailed Metrics:")
        print(f"  Content per day: {gen_metrics.get('content_generated_per_day', 0):.1f}")
        print(f"  Quality avg: {qual_metrics.get('average_quality_score', 0):.1f}/10")
        print(f"  Face quality: {qual_metrics.get('face_quality_average', 0):.1f}/10")
        print(f"  Detection avg: {det_metrics.get('average_detection_score', 0):.2f}")
        print(f"  Detection pass rate: {det_metrics.get('detection_pass_rate', 0):.1f}%")
        
        if alerts:
            print(f"\n⚠️  Alerts ({len(alerts)}):")
            for alert in alerts:
                severity = alert.get('severity', 'medium')
                icon = "🔴" if severity == 'high' else "🟡"
                print(f"  {icon} {alert.get('category')}: {alert.get('message')}")
        else:
            print(f"\n✅ No alerts")
    else:
        # Compact format
        status = "✅" if not alerts else f"⚠️ {len(alerts)}"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"Quality: {summary.get('quality_avg', 0):.1f}/10 | "
              f"Approval: {summary.get('approval_rate', 0):.1f}% | "
              f"Detection: {summary.get('pass_rate', 0):.1f}% | "
              f"Status: {status}")
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": summary,
        "metrics": all_metrics,
        "alerts": alerts
    }


def monitor_continuous(interval: int = 60, days: int = 7, verbose: bool = False):
    """Monitor metrics continuously"""
    print(f"Starting continuous monitoring (interval: {interval}s)")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            monitor_once(days=days, verbose=verbose)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")


def main():
    parser = argparse.ArgumentParser(description='Monitor QA Metrics')
    parser.add_argument('--interval', type=int, default=60, help='Monitoring interval in seconds (default: 60)')
    parser.add_argument('--days', type=int, default=7, help='Metrics period in days (default: 7)')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        if args.once:
            monitor_once(days=args.days, verbose=args.verbose)
        else:
            monitor_continuous(interval=args.interval, days=args.days, verbose=args.verbose)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
