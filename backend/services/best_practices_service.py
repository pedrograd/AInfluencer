"""
Best Practices Service
Implements comprehensive best practices validation, monitoring, and enforcement
Based on docs/31-BEST-PRACTICES-COMPLETE.md
"""
import logging
import inspect
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import ast
import re

logger = logging.getLogger(__name__)


class PracticeCategory(Enum):
    """Best practice categories"""
    CONTENT = "content"
    TECHNICAL = "technical"
    WORKFLOW = "workflow"
    QUALITY = "quality"
    SECURITY = "security"
    PERFORMANCE = "performance"
    LEGAL = "legal"
    ETHICAL = "ethical"
    COMMUNITY = "community"


class PracticeSeverity(Enum):
    """Practice violation severity"""
    CRITICAL = "critical"  # Must fix immediately
    HIGH = "high"  # Should fix soon
    MEDIUM = "medium"  # Should fix
    LOW = "low"  # Nice to have
    INFO = "info"  # Informational


@dataclass
class PracticeViolation:
    """Represents a best practice violation"""
    category: PracticeCategory
    severity: PracticeSeverity
    practice: str
    description: str
    location: str
    suggestion: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PracticeCheck:
    """Represents a best practice check result"""
    practice: str
    passed: bool
    score: float  # 0.0 to 1.0
    violations: List[PracticeViolation] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PracticeReport:
    """Comprehensive best practices report"""
    timestamp: datetime
    overall_score: float  # 0.0 to 1.0
    category_scores: Dict[PracticeCategory, float]
    checks: List[PracticeCheck]
    violations: List[PracticeViolation]
    recommendations: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class BestPracticesService:
    """Service for validating and enforcing best practices"""
    
    # Quality thresholds
    MIN_QUALITY_SCORE = 8.0
    MIN_FACE_CONSISTENCY = 0.85
    
    # Security requirements
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_2FA = True
    
    # Performance thresholds
    MAX_RESPONSE_TIME_MS = 2000
    MAX_GPU_MEMORY_PERCENT = 90
    
    def __init__(self):
        self.violations: List[PracticeViolation] = []
        self.checks: List[PracticeCheck] = []
    
    # ============================================================================
    # Content Creation Best Practices
    # ============================================================================
    
    def validate_prompt_quality(self, prompt: str, negative_prompt: Optional[str] = None) -> PracticeCheck:
        """Validate prompt follows best practices"""
        violations = []
        score = 1.0
        
        # Check prompt is detailed and specific
        if len(prompt.split()) < 10:
            violations.append(PracticeViolation(
                category=PracticeCategory.CONTENT,
                severity=PracticeSeverity.HIGH,
                practice="Use detailed, specific prompts",
                description="Prompt is too short/vague",
                location="prompt",
                suggestion="Add more descriptive details about subject, appearance, pose, setting, style"
            ))
            score -= 0.3
        
        # Check for quality modifiers
        quality_keywords = ["high quality", "ultra realistic", "photorealistic", "masterpiece", "8k", "4k"]
        has_quality = any(keyword in prompt.lower() for keyword in quality_keywords)
        if not has_quality:
            violations.append(PracticeViolation(
                category=PracticeCategory.CONTENT,
                severity=PracticeSeverity.MEDIUM,
                practice="Include quality modifiers",
                description="Prompt lacks quality modifiers",
                location="prompt",
                suggestion="Add quality modifiers like 'high quality', 'ultra realistic', 'photorealistic'"
            ))
            score -= 0.2
        
        # Check for negative prompt
        if not negative_prompt or len(negative_prompt.strip()) < 5:
            violations.append(PracticeViolation(
                category=PracticeCategory.CONTENT,
                severity=PracticeSeverity.MEDIUM,
                practice="Use negative prompts",
                description="Negative prompt is missing or too short",
                location="negative_prompt",
                suggestion="Add comprehensive negative prompt to avoid unwanted artifacts"
            ))
            score -= 0.15
        
        # Check for conflicting styles
        conflicting_pairs = [
            ("realistic", "cartoon"),
            ("photography", "illustration"),
            ("natural", "artificial")
        ]
        for pair in conflicting_pairs:
            if pair[0] in prompt.lower() and pair[1] in prompt.lower():
                violations.append(PracticeViolation(
                    category=PracticeCategory.CONTENT,
                    severity=PracticeSeverity.MEDIUM,
                    practice="Avoid conflicting styles",
                    description=f"Conflicting styles detected: {pair[0]} and {pair[1]}",
                    location="prompt",
                    suggestion=f"Choose one style: either {pair[0]} or {pair[1]}"
                ))
                score -= 0.1
        
        score = max(0.0, score)
        
        return PracticeCheck(
            practice="Prompt Quality",
            passed=score >= 0.7,
            score=score,
            violations=violations,
            details={"prompt_length": len(prompt), "has_quality_modifiers": has_quality}
        )
    
    def validate_face_consistency(self, consistency_score: float, method: str) -> PracticeCheck:
        """Validate face consistency meets standards"""
        violations = []
        score = 1.0
        
        if consistency_score < self.MIN_FACE_CONSISTENCY:
            violations.append(PracticeViolation(
                category=PracticeCategory.CONTENT,
                severity=PracticeSeverity.HIGH,
                practice="Maintain consistent face across content",
                description=f"Face consistency score {consistency_score:.2f} below threshold {self.MIN_FACE_CONSISTENCY}",
                location="face_consistency",
                suggestion=f"Improve face consistency using {method}. Use high-quality reference images."
            ))
            score = consistency_score / self.MIN_FACE_CONSISTENCY
        
        if method not in ["instantid", "lora", "ip-adapter"]:
            violations.append(PracticeViolation(
                category=PracticeCategory.CONTENT,
                severity=PracticeSeverity.MEDIUM,
                practice="Use appropriate face consistency methods",
                description=f"Unknown or inappropriate method: {method}",
                location="face_consistency.method",
                suggestion="Use InstantID, LoRA, or IP-Adapter for face consistency"
            ))
            score -= 0.2
        
        score = max(0.0, score)
        
        return PracticeCheck(
            practice="Face Consistency",
            passed=score >= 0.85,
            score=score,
            violations=violations,
            details={"consistency_score": consistency_score, "method": method}
        )
    
    def validate_post_processing(self, config: Dict[str, Any], metadata_removed: bool) -> PracticeCheck:
        """Validate post-processing follows best practices"""
        violations = []
        score = 1.0
        
        # Check metadata removal
        if not metadata_removed:
            violations.append(PracticeViolation(
                category=PracticeCategory.CONTENT,
                severity=PracticeSeverity.CRITICAL,
                practice="Remove all metadata",
                description="Metadata not removed from file",
                location="post_processing",
                suggestion="Always remove metadata before publishing"
            ))
            score -= 0.5
        
        # Check post-processing is enabled
        if not config.get("enabled", False):
            violations.append(PracticeViolation(
                category=PracticeCategory.CONTENT,
                severity=PracticeSeverity.HIGH,
                practice="Always post-process content",
                description="Post-processing is disabled",
                location="post_processing.enabled",
                suggestion="Enable post-processing to enhance quality and remove artifacts"
            ))
            score -= 0.3
        
        score = max(0.0, score)
        
        return PracticeCheck(
            practice="Post-Processing",
            passed=score >= 0.7,
            score=score,
            violations=violations,
            details={"config": config, "metadata_removed": metadata_removed}
        )
    
    # ============================================================================
    # Technical Best Practices
    # ============================================================================
    
    def validate_code_quality(self, file_path: Path) -> PracticeCheck:
        """Validate code quality in a Python file"""
        violations = []
        score = 1.0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            # Check for type hints
            functions_without_hints = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    has_return_type = node.returns is not None
                    has_param_types = any(arg.annotation is None for arg in node.args.args if arg.arg != 'self')
                    if not has_return_type or has_param_types:
                        functions_without_hints.append(node.name)
            
            if functions_without_hints:
                violations.append(PracticeViolation(
                    category=PracticeCategory.TECHNICAL,
                    severity=PracticeSeverity.MEDIUM,
                    practice="Use type hints",
                    description=f"Functions without type hints: {', '.join(functions_without_hints[:5])}",
                    location=str(file_path),
                    suggestion="Add type hints to all function parameters and return types"
                ))
                score -= 0.2 * min(len(functions_without_hints) / 10, 1.0)
            
            # Check for error handling
            has_try_except = "try:" in content or "except" in content
            if not has_try_except and "def " in content:
                violations.append(PracticeViolation(
                    category=PracticeCategory.TECHNICAL,
                    severity=PracticeSeverity.HIGH,
                    practice="Handle all errors",
                    description="No error handling found",
                    location=str(file_path),
                    suggestion="Add try/except blocks for error handling"
                ))
                score -= 0.3
            
            # Check for logging
            has_logging = "logger" in content or "logging" in content
            if not has_logging and "def " in content:
                violations.append(PracticeViolation(
                    category=PracticeCategory.TECHNICAL,
                    severity=PracticeSeverity.MEDIUM,
                    practice="Log errors properly",
                    description="No logging found",
                    location=str(file_path),
                    suggestion="Add logging for errors and important events"
                ))
                score -= 0.15
            
            # Check for bare except
            if "except:" in content or "except Exception:" in content:
                violations.append(PracticeViolation(
                    category=PracticeCategory.TECHNICAL,
                    severity=PracticeSeverity.MEDIUM,
                    practice="Use specific exception types",
                    description="Bare except or generic Exception catch found",
                    location=str(file_path),
                    suggestion="Use specific exception types instead of bare except"
                ))
                score -= 0.1
            
        except Exception as e:
            logger.error(f"Error validating code quality for {file_path}: {e}")
            violations.append(PracticeViolation(
                category=PracticeCategory.TECHNICAL,
                severity=PracticeSeverity.LOW,
                practice="Code validation",
                description=f"Could not parse file: {e}",
                location=str(file_path),
                suggestion="Check file syntax"
            ))
            score -= 0.1
        
        score = max(0.0, score)
        
        return PracticeCheck(
            practice="Code Quality",
            passed=score >= 0.7,
            score=score,
            violations=violations,
            details={"file_path": str(file_path)}
        )
    
    def validate_error_handling(self, func: Callable) -> PracticeCheck:
        """Validate function has proper error handling"""
        violations = []
        score = 1.0
        
        source = inspect.getsource(func)
        
        # Check for try/except
        if "try:" not in source and "except" not in source:
            violations.append(PracticeViolation(
                category=PracticeCategory.TECHNICAL,
                severity=PracticeSeverity.HIGH,
                practice="Handle all errors",
                description=f"Function {func.__name__} lacks error handling",
                location=f"{func.__module__}.{func.__name__}",
                suggestion="Add try/except blocks for error handling"
            ))
            score -= 0.5
        
        # Check for bare except
        if "except:" in source:
            violations.append(PracticeViolation(
                category=PracticeCategory.TECHNICAL,
                severity=PracticeSeverity.MEDIUM,
                practice="Use specific exception types",
                description=f"Function {func.__name__} uses bare except",
                location=f"{func.__module__}.{func.__name__}",
                suggestion="Use specific exception types instead of bare except"
            ))
            score -= 0.3
        
        score = max(0.0, score)
        
        return PracticeCheck(
            practice="Error Handling",
            passed=score >= 0.7,
            score=score,
            violations=violations,
            details={"function": func.__name__}
        )
    
    # ============================================================================
    # Quality Standards
    # ============================================================================
    
    def validate_quality_score(self, quality_score: float, min_score: Optional[float] = None) -> PracticeCheck:
        """Validate quality score meets standards"""
        violations = []
        min_threshold = min_score or self.MIN_QUALITY_SCORE
        
        if quality_score < min_threshold:
            violations.append(PracticeViolation(
                category=PracticeCategory.QUALITY,
                severity=PracticeSeverity.HIGH,
                practice="Set quality thresholds (8.0+)",
                description=f"Quality score {quality_score:.2f} below threshold {min_threshold}",
                location="quality_score",
                suggestion=f"Improve quality to meet minimum threshold of {min_threshold}"
            ))
        
        score = min(1.0, quality_score / min_threshold) if min_threshold > 0 else 0.0
        
        return PracticeCheck(
            practice="Quality Score",
            passed=quality_score >= min_threshold,
            score=score,
            violations=violations,
            details={"quality_score": quality_score, "min_threshold": min_threshold}
        )
    
    def validate_qa_process(self, qa_checks: Dict[str, bool]) -> PracticeCheck:
        """Validate QA process is comprehensive"""
        violations = []
        score = 1.0
        
        required_checks = ["quality", "detection", "metadata", "consistency"]
        missing_checks = [check for check in required_checks if not qa_checks.get(check, False)]
        
        if missing_checks:
            violations.append(PracticeViolation(
                category=PracticeCategory.QUALITY,
                severity=PracticeSeverity.HIGH,
                practice="Implement comprehensive QA",
                description=f"Missing QA checks: {', '.join(missing_checks)}",
                location="qa_process",
                suggestion="Run all required QA checks before publishing"
            ))
            score -= 0.25 * len(missing_checks)
        
        score = max(0.0, score)
        
        return PracticeCheck(
            practice="QA Process",
            passed=score >= 0.75,
            score=score,
            violations=violations,
            details={"qa_checks": qa_checks}
        )
    
    # ============================================================================
    # Security Best Practices
    # ============================================================================
    
    def validate_security(self, config: Dict[str, Any]) -> PracticeCheck:
        """Validate security best practices"""
        violations = []
        score = 1.0
        
        # Check for hardcoded credentials
        if config.get("has_hardcoded_credentials", False):
            violations.append(PracticeViolation(
                category=PracticeCategory.SECURITY,
                severity=PracticeSeverity.CRITICAL,
                practice="Use environment variables",
                description="Hardcoded credentials detected",
                location="config",
                suggestion="Move credentials to environment variables"
            ))
            score -= 0.5
        
        # Check for HTTPS
        if not config.get("uses_https", True):
            violations.append(PracticeViolation(
                category=PracticeCategory.SECURITY,
                severity=PracticeSeverity.CRITICAL,
                practice="Use HTTPS",
                description="HTTP instead of HTTPS detected",
                location="config",
                suggestion="Always use HTTPS in production"
            ))
            score -= 0.5
        
        # Check for rate limiting
        if not config.get("has_rate_limiting", False):
            violations.append(PracticeViolation(
                category=PracticeCategory.SECURITY,
                severity=PracticeSeverity.HIGH,
                practice="Implement rate limiting",
                description="Rate limiting not configured",
                location="config",
                suggestion="Implement rate limiting to prevent abuse"
            ))
            score -= 0.3
        
        score = max(0.0, score)
        
        return PracticeCheck(
            practice="Security",
            passed=score >= 0.7,
            score=score,
            violations=violations,
            details=config
        )
    
    def validate_metadata_removal(self, has_metadata: bool) -> PracticeCheck:
        """Validate metadata is removed"""
        violations = []
        
        if has_metadata:
            violations.append(PracticeViolation(
                category=PracticeCategory.SECURITY,
                severity=PracticeSeverity.CRITICAL,
                practice="Remove metadata",
                description="Metadata still present in file",
                location="file",
                suggestion="Remove all metadata before publishing"
            ))
        
        return PracticeCheck(
            practice="Metadata Removal",
            passed=not has_metadata,
            score=0.0 if has_metadata else 1.0,
            violations=violations,
            details={"has_metadata": has_metadata}
        )
    
    # ============================================================================
    # Performance Best Practices
    # ============================================================================
    
    def validate_performance(self, metrics: Dict[str, Any]) -> PracticeCheck:
        """Validate performance metrics"""
        violations = []
        score = 1.0
        
        # Check response time
        response_time = metrics.get("response_time_ms", 0)
        if response_time > self.MAX_RESPONSE_TIME_MS:
            violations.append(PracticeViolation(
                category=PracticeCategory.PERFORMANCE,
                severity=PracticeSeverity.MEDIUM,
                practice="Optimize bottlenecks",
                description=f"Response time {response_time}ms exceeds threshold {self.MAX_RESPONSE_TIME_MS}ms",
                location="performance",
                suggestion="Profile code and optimize slow operations"
            ))
            score -= 0.3
        
        # Check GPU memory usage
        gpu_memory_percent = metrics.get("gpu_memory_percent", 0)
        if gpu_memory_percent > self.MAX_GPU_MEMORY_PERCENT:
            violations.append(PracticeViolation(
                category=PracticeCategory.PERFORMANCE,
                severity=PracticeSeverity.HIGH,
                practice="Optimize memory",
                description=f"GPU memory usage {gpu_memory_percent}% exceeds threshold {self.MAX_GPU_MEMORY_PERCENT}%",
                location="gpu_memory",
                suggestion="Clear cache, reduce batch size, or optimize memory usage"
            ))
            score -= 0.4
        
        # Check for caching
        if not metrics.get("uses_caching", False):
            violations.append(PracticeViolation(
                category=PracticeCategory.PERFORMANCE,
                severity=PracticeSeverity.MEDIUM,
                practice="Use caching",
                description="Caching not implemented",
                location="performance",
                suggestion="Implement caching for frequently accessed data"
            ))
            score -= 0.2
        
        score = max(0.0, score)
        
        return PracticeCheck(
            practice="Performance",
            passed=score >= 0.7,
            score=score,
            violations=violations,
            details=metrics
        )
    
    # ============================================================================
    # Workflow Optimization
    # ============================================================================
    
    def validate_automation(self, automation_config: Dict[str, Any]) -> PracticeCheck:
        """Validate automation best practices"""
        violations = []
        score = 1.0
        
        # Check for batch processing
        if not automation_config.get("uses_batch_processing", False):
            violations.append(PracticeViolation(
                category=PracticeCategory.WORKFLOW,
                severity=PracticeSeverity.MEDIUM,
                practice="Use batch processing",
                description="Batch processing not enabled",
                location="automation",
                suggestion="Enable batch processing for efficiency"
            ))
            score -= 0.2
        
        # Check for scheduling
        if not automation_config.get("has_scheduling", False):
            violations.append(PracticeViolation(
                category=PracticeCategory.WORKFLOW,
                severity=PracticeSeverity.LOW,
                practice="Implement scheduling",
                description="Scheduling not configured",
                location="automation",
                suggestion="Implement scheduling for automated tasks"
            ))
            score -= 0.15
        
        # Check for monitoring
        if not automation_config.get("has_monitoring", False):
            violations.append(PracticeViolation(
                category=PracticeCategory.WORKFLOW,
                severity=PracticeSeverity.MEDIUM,
                practice="Monitor automation",
                description="Automation monitoring not configured",
                location="automation",
                suggestion="Add monitoring for automation workflows"
            ))
            score -= 0.2
        
        score = max(0.0, score)
        
        return PracticeCheck(
            practice="Automation",
            passed=score >= 0.7,
            score=score,
            violations=violations,
            details=automation_config
        )
    
    # ============================================================================
    # Comprehensive Reporting
    # ============================================================================
    
    def generate_report(self, checks: List[PracticeCheck]) -> PracticeReport:
        """Generate comprehensive best practices report"""
        all_violations = []
        category_scores: Dict[PracticeCategory, List[float]] = {}
        
        for check in checks:
            all_violations.extend(check.violations)
            
            for violation in check.violations:
                if violation.category not in category_scores:
                    category_scores[violation.category] = []
                # Lower score for violations
                category_scores[violation.category].append(1.0 - check.score)
        
        # Calculate category scores
        category_averages: Dict[PracticeCategory, float] = {}
        for category in PracticeCategory:
            if category in category_scores:
                avg = sum(category_scores[category]) / len(category_scores[category])
                category_averages[category] = max(0.0, 1.0 - avg)
            else:
                category_averages[category] = 1.0
        
        # Calculate overall score
        if checks:
            overall_score = sum(check.score for check in checks) / len(checks)
        else:
            overall_score = 1.0
        
        # Generate recommendations
        recommendations = []
        critical_violations = [v for v in all_violations if v.severity == PracticeSeverity.CRITICAL]
        high_violations = [v for v in all_violations if v.severity == PracticeSeverity.HIGH]
        
        if critical_violations:
            recommendations.append(f"Fix {len(critical_violations)} critical violations immediately")
        
        if high_violations:
            recommendations.append(f"Address {len(high_violations)} high-priority violations")
        
        # Category-specific recommendations
        for category, score in category_averages.items():
            if score < 0.7:
                recommendations.append(f"Improve {category.value} practices (current score: {score:.2f})")
        
        return PracticeReport(
            timestamp=datetime.utcnow(),
            overall_score=overall_score,
            category_scores=category_averages,
            checks=checks,
            violations=all_violations,
            recommendations=recommendations,
            metadata={
                "total_checks": len(checks),
                "total_violations": len(all_violations),
                "critical_count": len(critical_violations),
                "high_count": len(high_violations)
            }
        )
    
    def validate_generation_request(self, request: Dict[str, Any]) -> PracticeReport:
        """Validate a generation request against all best practices"""
        checks = []
        
        # Content creation checks
        prompt = request.get("prompt", "")
        negative_prompt = request.get("negative_prompt")
        checks.append(self.validate_prompt_quality(prompt, negative_prompt))
        
        # Face consistency check
        face_consistency = request.get("face_consistency", {})
        if face_consistency.get("enabled"):
            consistency_score = face_consistency.get("similarity_score", 0.0)
            method = face_consistency.get("method", "unknown")
            checks.append(self.validate_face_consistency(consistency_score, method))
        
        # Post-processing check
        post_processing = request.get("post_processing", {})
        metadata_removed = post_processing.get("remove_metadata", False)
        checks.append(self.validate_post_processing(post_processing, metadata_removed))
        
        # Quality check
        quality_check = request.get("quality_check", {})
        if quality_check.get("enabled"):
            quality_score = quality_check.get("score", 0.0)
            min_score = quality_check.get("min_score", self.MIN_QUALITY_SCORE)
            checks.append(self.validate_quality_score(quality_score, min_score))
        
        # Security check
        security_config = {
            "has_hardcoded_credentials": False,  # Would check actual config
            "uses_https": True,  # Would check actual config
            "has_rate_limiting": True  # Would check actual config
        }
        checks.append(self.validate_security(security_config))
        
        # Performance check
        performance_metrics = {
            "response_time_ms": request.get("response_time_ms", 0),
            "gpu_memory_percent": request.get("gpu_memory_percent", 0),
            "uses_caching": request.get("uses_caching", False)
        }
        checks.append(self.validate_performance(performance_metrics))
        
        return self.generate_report(checks)
