"""Resource management service for tracking and managing system resources.

This service provides:
- Real-time resource usage tracking (CPU, memory, disk, GPU)
- Configurable resource limits and thresholds
- Automatic cleanup of temporary files and old data
- Resource usage alerts and warnings
"""

from __future__ import annotations

import os
import platform
import psutil
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.paths import repo_root
from app.services.unified_logging import get_unified_logger


@dataclass
class ResourceUsage:
    """Current resource usage metrics."""
    timestamp: float
    cpu_percent: float
    memory_used_gb: float
    memory_total_gb: float
    memory_percent: float
    disk_used_gb: float
    disk_total_gb: float
    disk_percent: float
    gpu_available: bool
    gpu_memory_used_gb: float | None
    gpu_memory_total_gb: float | None
    gpu_utilization_percent: float | None


@dataclass
class ResourceLimits:
    """Resource limits and thresholds for alerts."""
    cpu_warning_percent: float = 80.0
    cpu_critical_percent: float = 95.0
    memory_warning_percent: float = 80.0
    memory_critical_percent: float = 95.0
    disk_warning_percent: float = 80.0
    disk_critical_percent: float = 90.0
    gpu_memory_warning_percent: float = 80.0
    gpu_memory_critical_percent: float = 95.0
    gpu_utilization_warning_percent: float = 90.0
    gpu_utilization_critical_percent: float = 98.0


@dataclass
class ResourceAlert:
    """Resource alert information."""
    resource_type: str  # "cpu", "memory", "disk", "gpu_memory", "gpu_utilization"
    severity: str  # "warning" or "critical"
    current_value: float
    threshold: float
    message: str
    timestamp: float


class ResourceManager:
    """Manages system resources including tracking, limits, and cleanup."""
    
    def __init__(self, limits: ResourceLimits | None = None) -> None:
        """
        Initialize resource manager.
        
        Args:
            limits: Optional resource limits configuration. Uses defaults if not provided.
        """
        self.limits = limits or ResourceLimits()
        self.logger = get_unified_logger()
        self._project_root = repo_root()
        self._gpu_available = self._check_gpu_available()
    
    def _check_gpu_available(self) -> bool:
        """Check if GPU is available via nvidia-smi."""
        try:
            result = subprocess.run(
                ["nvidia-smi", "-L"],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _get_gpu_memory(self) -> tuple[float | None, float | None]:
        """Get GPU memory usage (used, total) in GB.
        
        Returns:
            Tuple of (used_gb, total_gb) or (None, None) if unavailable.
        """
        if not self._gpu_available:
            return None, None
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
            if result.returncode != 0:
                return None, None
            
            lines = result.stdout.strip().split("\n")
            if not lines:
                return None, None
            
            # Get first GPU
            parts = lines[0].strip().split(",")
            if len(parts) != 2:
                return None, None
            
            used_mb = float(parts[0].strip())
            total_mb = float(parts[1].strip())
            return round(used_mb / 1024, 2), round(total_mb / 1024, 2)
        except Exception:  # noqa: BLE001
            return None, None
    
    def _get_gpu_utilization(self) -> float | None:
        """Get GPU utilization percentage.
        
        Returns:
            GPU utilization percentage (0-100) or None if unavailable.
        """
        if not self._gpu_available:
            return None
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=2.0,
                check=False,
            )
            if result.returncode != 0:
                return None
            
            lines = result.stdout.strip().split("\n")
            if not lines:
                return None
            
            # Get first GPU
            util = float(lines[0].strip())
            return round(util, 1)
        except Exception:  # noqa: BLE001
            return None
    
    def get_current_usage(self) -> ResourceUsage:
        """Get current system resource usage.
        
        Returns:
            ResourceUsage object with current metrics.
        """
        now = time.time()
        
        # CPU usage (average over 1 second)
        cpu_percent = psutil.cpu_percent(interval=1.0)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_used_gb = round(memory.used / (1024**3), 2)
        memory_total_gb = round(memory.total / (1024**3), 2)
        memory_percent = memory.percent
        
        # Disk usage
        disk = shutil.disk_usage(self._project_root)
        disk_used_gb = round(disk.used / (1024**3), 2)
        disk_total_gb = round(disk.total / (1024**3), 2)
        disk_percent = round((disk.used / disk.total) * 100, 1)
        
        # GPU usage
        gpu_memory_used, gpu_memory_total = self._get_gpu_memory()
        gpu_utilization = self._get_gpu_utilization()
        
        return ResourceUsage(
            timestamp=now,
            cpu_percent=round(cpu_percent, 1),
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            memory_percent=round(memory_percent, 1),
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            disk_percent=disk_percent,
            gpu_available=self._gpu_available,
            gpu_memory_used_gb=gpu_memory_used,
            gpu_memory_total_gb=gpu_memory_total,
            gpu_utilization_percent=gpu_utilization,
        )
    
    def check_alerts(self, usage: ResourceUsage | None = None) -> list[ResourceAlert]:
        """Check resource usage against limits and return alerts.
        
        Args:
            usage: Optional ResourceUsage object. If not provided, fetches current usage.
        
        Returns:
            List of ResourceAlert objects for any exceeded thresholds.
        """
        if usage is None:
            usage = self.get_current_usage()
        
        alerts: list[ResourceAlert] = []
        
        # CPU alerts
        if usage.cpu_percent >= self.limits.cpu_critical_percent:
            alerts.append(ResourceAlert(
                resource_type="cpu",
                severity="critical",
                current_value=usage.cpu_percent,
                threshold=self.limits.cpu_critical_percent,
                message=f"CPU usage is critical: {usage.cpu_percent}% (threshold: {self.limits.cpu_critical_percent}%)",
                timestamp=usage.timestamp,
            ))
        elif usage.cpu_percent >= self.limits.cpu_warning_percent:
            alerts.append(ResourceAlert(
                resource_type="cpu",
                severity="warning",
                current_value=usage.cpu_percent,
                threshold=self.limits.cpu_warning_percent,
                message=f"CPU usage is high: {usage.cpu_percent}% (threshold: {self.limits.cpu_warning_percent}%)",
                timestamp=usage.timestamp,
            ))
        
        # Memory alerts
        if usage.memory_percent >= self.limits.memory_critical_percent:
            alerts.append(ResourceAlert(
                resource_type="memory",
                severity="critical",
                current_value=usage.memory_percent,
                threshold=self.limits.memory_critical_percent,
                message=f"Memory usage is critical: {usage.memory_percent}% ({usage.memory_used_gb}GB / {usage.memory_total_gb}GB)",
                timestamp=usage.timestamp,
            ))
        elif usage.memory_percent >= self.limits.memory_warning_percent:
            alerts.append(ResourceAlert(
                resource_type="memory",
                severity="warning",
                current_value=usage.memory_percent,
                threshold=self.limits.memory_warning_percent,
                message=f"Memory usage is high: {usage.memory_percent}% ({usage.memory_used_gb}GB / {usage.memory_total_gb}GB)",
                timestamp=usage.timestamp,
            ))
        
        # Disk alerts
        if usage.disk_percent >= self.limits.disk_critical_percent:
            alerts.append(ResourceAlert(
                resource_type="disk",
                severity="critical",
                current_value=usage.disk_percent,
                threshold=self.limits.disk_critical_percent,
                message=f"Disk usage is critical: {usage.disk_percent}% ({usage.disk_used_gb}GB / {usage.disk_total_gb}GB)",
                timestamp=usage.timestamp,
            ))
        elif usage.disk_percent >= self.limits.disk_warning_percent:
            alerts.append(ResourceAlert(
                resource_type="disk",
                severity="warning",
                current_value=usage.disk_percent,
                threshold=self.limits.disk_warning_percent,
                message=f"Disk usage is high: {usage.disk_percent}% ({usage.disk_used_gb}GB / {usage.disk_total_gb}GB)",
                timestamp=usage.timestamp,
            ))
        
        # GPU memory alerts
        if usage.gpu_available and usage.gpu_memory_used_gb is not None and usage.gpu_memory_total_gb is not None:
            gpu_memory_percent = (usage.gpu_memory_used_gb / usage.gpu_memory_total_gb) * 100
            if gpu_memory_percent >= self.limits.gpu_memory_critical_percent:
                alerts.append(ResourceAlert(
                    resource_type="gpu_memory",
                    severity="critical",
                    current_value=gpu_memory_percent,
                    threshold=self.limits.gpu_memory_critical_percent,
                    message=f"GPU memory usage is critical: {gpu_memory_percent:.1f}% ({usage.gpu_memory_used_gb}GB / {usage.gpu_memory_total_gb}GB)",
                    timestamp=usage.timestamp,
                ))
            elif gpu_memory_percent >= self.limits.gpu_memory_warning_percent:
                alerts.append(ResourceAlert(
                    resource_type="gpu_memory",
                    severity="warning",
                    current_value=gpu_memory_percent,
                    threshold=self.limits.gpu_memory_warning_percent,
                    message=f"GPU memory usage is high: {gpu_memory_percent:.1f}% ({usage.gpu_memory_used_gb}GB / {usage.gpu_memory_total_gb}GB)",
                    timestamp=usage.timestamp,
                ))
        
        # GPU utilization alerts
        if usage.gpu_available and usage.gpu_utilization_percent is not None:
            if usage.gpu_utilization_percent >= self.limits.gpu_utilization_critical_percent:
                alerts.append(ResourceAlert(
                    resource_type="gpu_utilization",
                    severity="critical",
                    current_value=usage.gpu_utilization_percent,
                    threshold=self.limits.gpu_utilization_critical_percent,
                    message=f"GPU utilization is critical: {usage.gpu_utilization_percent}%",
                    timestamp=usage.timestamp,
                ))
            elif usage.gpu_utilization_percent >= self.limits.gpu_utilization_warning_percent:
                alerts.append(ResourceAlert(
                    resource_type="gpu_utilization",
                    severity="warning",
                    current_value=usage.gpu_utilization_percent,
                    threshold=self.limits.gpu_utilization_warning_percent,
                    message=f"GPU utilization is high: {usage.gpu_utilization_percent}%",
                    timestamp=usage.timestamp,
                ))
        
        return alerts
    
    def cleanup_temp_files(self, max_age_days: int = 7, dry_run: bool = False) -> dict[str, Any]:
        """Clean up temporary files older than specified age.
        
        Args:
            max_age_days: Maximum age in days for temporary files (default: 7).
            dry_run: If True, only report what would be deleted without actually deleting.
        
        Returns:
            Dictionary with cleanup statistics.
        """
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        temp_dirs = [
            self._project_root / "tmp",
            self._project_root / "temp",
            self._project_root / ".cache",
        ]
        
        deleted_count = 0
        deleted_size_bytes = 0
        errors: list[str] = []
        
        for temp_dir in temp_dirs:
            if not temp_dir.exists():
                continue
            
            try:
                for item in temp_dir.rglob("*"):
                    if not item.is_file():
                        continue
                    
                    try:
                        age = now - item.stat().st_mtime
                        if age > max_age_seconds:
                            size = item.stat().st_size
                            if not dry_run:
                                item.unlink()
                            deleted_count += 1
                            deleted_size_bytes += size
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"Error processing {item}: {exc}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Error scanning {temp_dir}: {exc}")
        
        deleted_size_gb = round(deleted_size_bytes / (1024**3), 2)
        
        result = {
            "deleted_count": deleted_count,
            "deleted_size_gb": deleted_size_gb,
            "dry_run": dry_run,
            "errors": errors,
        }
        
        if not dry_run and deleted_count > 0:
            self.logger.info(
                "resource_manager",
                f"Cleaned up {deleted_count} temporary files ({deleted_size_gb}GB)"
            )
        
        return result
    
    def cleanup_old_logs(self, max_age_days: int = 30, dry_run: bool = False) -> dict[str, Any]:
        """Clean up old log files.
        
        Args:
            max_age_days: Maximum age in days for log files (default: 30).
            dry_run: If True, only report what would be deleted without actually deleting.
        
        Returns:
            Dictionary with cleanup statistics.
        """
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        log_dirs = [
            self._project_root / "runs",
        ]
        
        deleted_count = 0
        deleted_size_bytes = 0
        errors: list[str] = []
        
        for log_dir in log_dirs:
            if not log_dir.exists():
                continue
            
            try:
                for log_file in log_dir.rglob("*.log"):
                    try:
                        age = now - log_file.stat().st_mtime
                        if age > max_age_seconds:
                            size = log_file.stat().st_size
                            if not dry_run:
                                log_file.unlink()
                            deleted_count += 1
                            deleted_size_bytes += size
                    except Exception as exc:  # noqa: BLE001
                        errors.append(f"Error processing {log_file}: {exc}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Error scanning {log_dir}: {exc}")
        
        deleted_size_gb = round(deleted_size_bytes / (1024**3), 2)
        
        result = {
            "deleted_count": deleted_count,
            "deleted_size_gb": deleted_size_gb,
            "dry_run": dry_run,
            "errors": errors,
        }
        
        if not dry_run and deleted_count > 0:
            self.logger.info(
                "resource_manager",
                f"Cleaned up {deleted_count} old log files ({deleted_size_gb}GB)"
            )
        
        return result
    
    def get_usage_summary(self) -> dict[str, Any]:
        """Get comprehensive resource usage summary with alerts.
        
        Returns:
            Dictionary containing usage metrics, alerts, and recommendations.
        """
        usage = self.get_current_usage()
        alerts = self.check_alerts(usage)
        
        # Convert to dictionaries for JSON serialization
        usage_dict = {
            "timestamp": usage.timestamp,
            "cpu": {
                "percent": usage.cpu_percent,
            },
            "memory": {
                "used_gb": usage.memory_used_gb,
                "total_gb": usage.memory_total_gb,
                "percent": usage.memory_percent,
            },
            "disk": {
                "used_gb": usage.disk_used_gb,
                "total_gb": usage.disk_total_gb,
                "percent": usage.disk_percent,
            },
            "gpu": {
                "available": usage.gpu_available,
                "memory_used_gb": usage.gpu_memory_used_gb,
                "memory_total_gb": usage.gpu_memory_total_gb,
                "utilization_percent": usage.gpu_utilization_percent,
            },
        }
        
        alerts_dict = [
            {
                "resource_type": alert.resource_type,
                "severity": alert.severity,
                "current_value": alert.current_value,
                "threshold": alert.threshold,
                "message": alert.message,
                "timestamp": alert.timestamp,
            }
            for alert in alerts
        ]
        
        return {
            "usage": usage_dict,
            "alerts": alerts_dict,
            "limits": {
                "cpu_warning_percent": self.limits.cpu_warning_percent,
                "cpu_critical_percent": self.limits.cpu_critical_percent,
                "memory_warning_percent": self.limits.memory_warning_percent,
                "memory_critical_percent": self.limits.memory_critical_percent,
                "disk_warning_percent": self.limits.disk_warning_percent,
                "disk_critical_percent": self.limits.disk_critical_percent,
                "gpu_memory_warning_percent": self.limits.gpu_memory_warning_percent,
                "gpu_memory_critical_percent": self.limits.gpu_memory_critical_percent,
                "gpu_utilization_warning_percent": self.limits.gpu_utilization_warning_percent,
                "gpu_utilization_critical_percent": self.limits.gpu_utilization_critical_percent,
            },
        }


# Global instance
_resource_manager: ResourceManager | None = None


def get_resource_manager() -> ResourceManager:
    """Get or create global resource manager instance."""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager

