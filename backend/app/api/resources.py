"""Resource management API endpoints.

This module provides REST API endpoints for:
- Getting current resource usage (CPU, memory, disk, GPU)
- Getting resource limits and thresholds
- Triggering resource cleanup operations
- Getting resource usage summary with alerts
"""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.resource_manager import get_resource_manager, ResourceLimits


router = APIRouter()


class ResourceLimitsUpdate(BaseModel):
    """Request model for updating resource limits."""
    cpu_warning_percent: float | None = None
    cpu_critical_percent: float | None = None
    memory_warning_percent: float | None = None
    memory_critical_percent: float | None = None
    disk_warning_percent: float | None = None
    disk_critical_percent: float | None = None
    gpu_memory_warning_percent: float | None = None
    gpu_memory_critical_percent: float | None = None
    gpu_utilization_warning_percent: float | None = None
    gpu_utilization_critical_percent: float | None = None


@router.get("/usage")
def get_resource_usage() -> dict:
    """Get current system resource usage.
    
    Returns:
        Dictionary containing current CPU, memory, disk, and GPU usage metrics.
    """
    manager = get_resource_manager()
    usage = manager.get_current_usage()
    
    return {
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


@router.get("/summary")
def get_resource_summary() -> dict:
    """Get comprehensive resource usage summary with alerts.
    
    Returns:
        Dictionary containing usage metrics, alerts, and limits.
    """
    manager = get_resource_manager()
    return manager.get_usage_summary()


@router.get("/limits")
def get_resource_limits() -> dict:
    """Get current resource limits and thresholds.
    
    Returns:
        Dictionary containing all resource limit thresholds.
    """
    manager = get_resource_manager()
    limits = manager.limits
    
    return {
        "cpu_warning_percent": limits.cpu_warning_percent,
        "cpu_critical_percent": limits.cpu_critical_percent,
        "memory_warning_percent": limits.memory_warning_percent,
        "memory_critical_percent": limits.memory_critical_percent,
        "disk_warning_percent": limits.disk_warning_percent,
        "disk_critical_percent": limits.disk_critical_percent,
        "gpu_memory_warning_percent": limits.gpu_memory_warning_percent,
        "gpu_memory_critical_percent": limits.gpu_memory_critical_percent,
        "gpu_utilization_warning_percent": limits.gpu_utilization_warning_percent,
        "gpu_utilization_critical_percent": limits.gpu_utilization_critical_percent,
    }


@router.put("/limits")
def update_resource_limits(limits_update: ResourceLimitsUpdate) -> dict:
    """Update resource limits and thresholds.
    
    Args:
        limits_update: Resource limits update request.
    
    Returns:
        Dictionary containing updated resource limits.
    """
    manager = get_resource_manager()
    limits = manager.limits
    
    # Update only provided fields
    if limits_update.cpu_warning_percent is not None:
        limits.cpu_warning_percent = limits_update.cpu_warning_percent
    if limits_update.cpu_critical_percent is not None:
        limits.cpu_critical_percent = limits_update.cpu_critical_percent
    if limits_update.memory_warning_percent is not None:
        limits.memory_warning_percent = limits_update.memory_warning_percent
    if limits_update.memory_critical_percent is not None:
        limits.memory_critical_percent = limits_update.memory_critical_percent
    if limits_update.disk_warning_percent is not None:
        limits.disk_warning_percent = limits_update.disk_warning_percent
    if limits_update.disk_critical_percent is not None:
        limits.disk_critical_percent = limits_update.disk_critical_percent
    if limits_update.gpu_memory_warning_percent is not None:
        limits.gpu_memory_warning_percent = limits_update.gpu_memory_warning_percent
    if limits_update.gpu_memory_critical_percent is not None:
        limits.gpu_memory_critical_percent = limits_update.gpu_memory_critical_percent
    if limits_update.gpu_utilization_warning_percent is not None:
        limits.gpu_utilization_warning_percent = limits_update.gpu_utilization_warning_percent
    if limits_update.gpu_utilization_critical_percent is not None:
        limits.gpu_utilization_critical_percent = limits_update.gpu_utilization_critical_percent
    
    return {
        "cpu_warning_percent": limits.cpu_warning_percent,
        "cpu_critical_percent": limits.cpu_critical_percent,
        "memory_warning_percent": limits.memory_warning_percent,
        "memory_critical_percent": limits.memory_critical_percent,
        "disk_warning_percent": limits.disk_warning_percent,
        "disk_critical_percent": limits.disk_critical_percent,
        "gpu_memory_warning_percent": limits.gpu_memory_warning_percent,
        "gpu_memory_critical_percent": limits.gpu_memory_critical_percent,
        "gpu_utilization_warning_percent": limits.gpu_utilization_warning_percent,
        "gpu_utilization_critical_percent": limits.gpu_utilization_critical_percent,
    }


@router.get("/alerts")
def get_resource_alerts() -> dict:
    """Get current resource alerts (warnings and critical issues).
    
    Returns:
        Dictionary containing list of active resource alerts.
    """
    manager = get_resource_manager()
    alerts = manager.check_alerts()
    
    return {
        "alerts": [
            {
                "resource_type": alert.resource_type,
                "severity": alert.severity,
                "current_value": alert.current_value,
                "threshold": alert.threshold,
                "message": alert.message,
                "timestamp": alert.timestamp,
            }
            for alert in alerts
        ],
    }


@router.post("/cleanup/temp")
def cleanup_temp_files(
    max_age_days: int = Query(7, ge=1, le=365, description="Maximum age in days for temporary files"),
    dry_run: bool = Query(False, description="If true, only report what would be deleted"),
) -> dict:
    """Clean up temporary files older than specified age.
    
    Args:
        max_age_days: Maximum age in days for temporary files (default: 7).
        dry_run: If true, only report what would be deleted without actually deleting.
    
    Returns:
        Dictionary containing cleanup statistics.
    """
    manager = get_resource_manager()
    return manager.cleanup_temp_files(max_age_days=max_age_days, dry_run=dry_run)


@router.post("/cleanup/logs")
def cleanup_old_logs(
    max_age_days: int = Query(30, ge=1, le=365, description="Maximum age in days for log files"),
    dry_run: bool = Query(False, description="If true, only report what would be deleted"),
) -> dict:
    """Clean up old log files.
    
    Args:
        max_age_days: Maximum age in days for log files (default: 30).
        dry_run: If true, only report what would be deleted without actually deleting.
    
    Returns:
        Dictionary containing cleanup statistics.
    """
    manager = get_resource_manager()
    return manager.cleanup_old_logs(max_age_days=max_age_days, dry_run=dry_run)

