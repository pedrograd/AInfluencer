"""
Detection Tester Service
AI detection testing as per docs/28-QUALITY-ASSURANCE-SYSTEM.md
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from services.anti_detection_service import HiveModeration, SensityAI, AIOrNot

logger = logging.getLogger(__name__)


class DetectionTester:
    """AI detection testing service"""
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.tools = [
            HiveModeration(db_session=db_session),
            SensityAI(db_session=db_session),
            AIOrNot(db_session=db_session)
        ]
    
    def test(self, content_path: Path) -> Dict[str, Any]:
        """Test content against AI detection tools
        
        Returns:
            {
                'scores': Dict[str, float],  # Tool name -> score
                'average': float,
                'passed': bool
            }
        """
        results = {}
        
        for tool in self.tools:
            try:
                result = tool.detect(content_path)
                score = tool.get_score(result)
                results[tool.name] = score
            except Exception as e:
                logger.error(f"Error testing with {tool.name}: {e}")
                results[tool.name] = 0.5  # Default neutral score
        
        # Calculate average
        scores = list(results.values())
        avg_score = sum(scores) / len(scores) if scores else 0.5
        
        # Pass criteria:
        # - Average detection score: < 0.3 (30%)
        # - Individual tool scores: < 0.4 (40%)
        # - No tool score: > 0.5 (50%)
        passed = (
            avg_score < 0.3 and
            all(score < 0.4 for score in scores) and
            all(score < 0.5 for score in scores)
        )
        
        return {
            'scores': results,
            'average': avg_score,
            'passed': passed,
            'threshold': 0.3
        }
