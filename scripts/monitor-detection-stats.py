"""
Detection Statistics Monitor
Continuously monitors and displays detection statistics
"""
import os
import sys
import time
import requests
from datetime import datetime
from typing import Dict, Any

API_BASE = os.getenv("API_URL", "http://localhost:8000")


def get_detection_stats() -> Dict[str, Any]:
    """Get detection statistics from API"""
    try:
        response = requests.get(f"{API_BASE}/api/anti-detection/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("data", {})
    except Exception as e:
        print(f"Error fetching stats: {e}")
    return {}


def print_stats(stats: Dict[str, Any]):
    """Print formatted statistics"""
    print("\n" + "=" * 60)
    print(f"Detection Statistics - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if not stats:
        print("No statistics available")
        return
    
    print(f"\nTotal Tests: {stats.get('total_tests', 0)}")
    print(f"Passed Tests: {stats.get('passed_tests', 0)}")
    print(f"Failed Tests: {stats.get('failed_tests', 0)}")
    print(f"Pass Rate: {stats.get('pass_rate', 0):.1f}%")
    print(f"Average Score: {stats.get('average_score', 0):.2%}")
    print(f"Recent Tests (24h): {stats.get('recent_tests_24h', 0)}")
    
    # Calculate trend
    if stats.get('total_tests', 0) > 0:
        pass_rate = stats.get('pass_rate', 0)
        if pass_rate >= 80:
            status = "✓ EXCELLENT"
        elif pass_rate >= 60:
            status = "⚠ GOOD"
        elif pass_rate >= 40:
            status = "⚠ NEEDS IMPROVEMENT"
        else:
            status = "✗ POOR"
        
        print(f"\nOverall Status: {status}")
    
    print("=" * 60)


def monitor_loop(interval: int = 60):
    """Monitor loop"""
    print("Starting Detection Statistics Monitor")
    print(f"Monitoring every {interval} seconds")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            stats = get_detection_stats()
            print_stats(stats)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor detection statistics")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Update interval in seconds (default: 60)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Print stats once and exit"
    )
    
    args = parser.parse_args()
    
    if args.once:
        stats = get_detection_stats()
        print_stats(stats)
    else:
        monitor_loop(args.interval)


if __name__ == "__main__":
    main()
