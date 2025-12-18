"""Error taxonomy system with stable error codes and user-facing remediation.

This module provides a standardized error classification system that maps
all errors to stable taxonomy codes and provides user-facing remediation steps.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Stable error taxonomy codes.
    
    These codes are stable and should not change. New error types should
    be added as new enum values, not by modifying existing ones.
    """
    
    # Auth errors
    AUTH_MISSING = "AUTH_MISSING"
    AUTH_INVALID = "AUTH_INVALID"
    AUTH_EXPIRED = "AUTH_EXPIRED"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_INSUFFICIENT_PERMISSIONS"
    
    # API Contract errors
    CONTRACT_MISMATCH = "CONTRACT_MISMATCH"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_TYPE = "INVALID_FIELD_TYPE"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"
    
    # Dependency errors
    DEPENDENCY_MISSING = "DEPENDENCY_MISSING"
    ENGINE_OFFLINE = "ENGINE_OFFLINE"
    DB_UNAVAILABLE = "DB_UNAVAILABLE"
    REDIS_UNAVAILABLE = "REDIS_UNAVAILABLE"
    
    # Download errors
    DOWNLOAD_FAILED = "DOWNLOAD_FAILED"
    CHECKSUM_MISMATCH = "CHECKSUM_MISMATCH"
    DISK_FULL = "DISK_FULL"
    DOWNLOAD_TIMEOUT = "DOWNLOAD_TIMEOUT"
    DOWNLOAD_CANCELLED = "DOWNLOAD_CANCELLED"
    
    # File system errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INSUFFICIENT_DISK_SPACE = "INSUFFICIENT_DISK_SPACE"
    
    # Network errors
    CONNECTION_REFUSED = "CONNECTION_REFUSED"
    CONNECTION_TIMEOUT = "CONNECTION_TIMEOUT"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_PARAMETER = "MISSING_PARAMETER"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Model/Content errors
    LICENSE_UNKNOWN = "LICENSE_UNKNOWN"
    CHECKSUM_MISSING = "CHECKSUM_MISSING"
    
    # Workflow/Pipeline errors
    CONSENT_MISSING = "CONSENT_MISSING"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    ENGINE_TIMEOUT = "ENGINE_TIMEOUT"
    SAFETY_FILTER = "SAFETY_FILTER"
    
    # Unknown
    UNKNOWN_ERROR = "UNKNOWN_ERROR"


# User-facing remediation steps for each error code
REMEDIATION_STEPS: dict[ErrorCode, list[str]] = {
    ErrorCode.AUTH_MISSING: [
        "On localhost: Auth is automatically bypassed in dev mode",
        "In production: Include 'Authorization: Bearer <token>' header in your request",
        "Get a token by logging in via /api/auth/login",
    ],
    ErrorCode.AUTH_INVALID: [
        "Your authentication token is invalid or malformed",
        "Try logging in again to get a new token",
        "Check that the token is in the format: 'Bearer <token>'",
    ],
    ErrorCode.AUTH_EXPIRED: [
        "Your authentication token has expired",
        "Refresh your token using /api/auth/refresh",
        "Or log in again to get a new token",
    ],
    ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: [
        "You don't have permission to perform this action",
        "Contact your administrator to request access",
        "Check that you're using the correct account",
    ],
    ErrorCode.CONTRACT_MISMATCH: [
        "The request format doesn't match the API contract",
        "Ensure you're sending a JSON body with Content-Type: application/json",
        "Check the API documentation for the correct request format",
    ],
    ErrorCode.MISSING_REQUIRED_FIELD: [
        "A required field is missing from your request",
        "Check the API documentation for required fields",
        "Review the error detail to see which field is missing",
    ],
    ErrorCode.INVALID_FIELD_TYPE: [
        "A field has the wrong data type",
        "Check the API documentation for the correct field types",
        "Ensure numbers are sent as numbers, not strings",
    ],
    ErrorCode.INVALID_FIELD_VALUE: [
        "A field has an invalid value",
        "Check the API documentation for valid value ranges",
        "Review the error detail for specific constraints",
    ],
    ErrorCode.DEPENDENCY_MISSING: [
        "A required dependency is not installed or configured",
        "Check the installation guide for required dependencies",
        "Run the installer/setup to install missing components",
    ],
    ErrorCode.ENGINE_OFFLINE: [
        "The generation engine (ComfyUI) is not running",
        "Install ComfyUI if not installed: Use the 'Install ComfyUI' button",
        "Start ComfyUI if installed: Use the 'Start ComfyUI' button",
        "Check that ComfyUI is accessible at the configured URL",
    ],
    ErrorCode.DB_UNAVAILABLE: [
        "The database is not available or not configured",
        "For MVP: SQLite database is created automatically on first use",
        "For production: Ensure PostgreSQL is running and configured",
        "Check database connection settings in .env file",
    ],
    ErrorCode.REDIS_UNAVAILABLE: [
        "Redis is not available (optional for MVP)",
        "Redis is optional for MVP - some features may be limited",
        "For production: Install and start Redis server",
        "Check Redis connection settings in .env file",
    ],
    ErrorCode.DOWNLOAD_FAILED: [
        "Model download failed",
        "Check your internet connection",
        "Try downloading again - downloads can be resumed",
        "Check available disk space",
    ],
    ErrorCode.CHECKSUM_MISMATCH: [
        "Downloaded file checksum doesn't match expected value",
        "The file may be corrupted - try downloading again",
        "Check your internet connection for stability",
    ],
    ErrorCode.DISK_FULL: [
        "Insufficient disk space",
        "Free up disk space and try again",
        "Check available space: The error message shows required space",
    ],
    ErrorCode.DOWNLOAD_TIMEOUT: [
        "Download timed out",
        "Try downloading again - downloads can be resumed",
        "Check your internet connection speed",
        "Large models may take a long time to download",
    ],
    ErrorCode.DOWNLOAD_CANCELLED: [
        "Download was cancelled",
        "You can restart the download - it will resume from where it stopped",
    ],
    ErrorCode.FILE_NOT_FOUND: [
        "The requested file or resource was not found",
        "Check that the file path is correct",
        "The file may have been deleted or moved",
    ],
    ErrorCode.PERMISSION_DENIED: [
        "You don't have permission to access this resource",
        "Check file permissions if accessing local files",
        "Ensure you're authenticated if accessing protected resources",
    ],
    ErrorCode.INSUFFICIENT_DISK_SPACE: [
        "Not enough disk space for this operation",
        "Free up disk space and try again",
        "Check available space in the error message",
    ],
    ErrorCode.CONNECTION_REFUSED: [
        "Connection to service was refused",
        "Check that the service is running",
        "Verify the service URL/port is correct",
        "Check firewall settings",
    ],
    ErrorCode.CONNECTION_TIMEOUT: [
        "Connection to service timed out",
        "Check that the service is running and accessible",
        "Verify network connectivity",
        "The service may be overloaded - try again later",
    ],
    ErrorCode.SERVICE_UNAVAILABLE: [
        "The requested service is currently unavailable",
        "Check service status in the dashboard",
        "Try again in a few moments",
        "Check service logs for more details",
    ],
    ErrorCode.VALIDATION_ERROR: [
        "Request validation failed",
        "Check that all required fields are provided",
        "Verify field types and values match the API contract",
        "Review the error detail for specific issues",
    ],
    ErrorCode.MISSING_PARAMETER: [
        "A required parameter is missing",
        "Check the API documentation for required parameters",
        "Review the error detail to see which parameter is missing",
    ],
    ErrorCode.RATE_LIMIT_EXCEEDED: [
        "Too many requests - rate limit exceeded",
        "Wait a moment before trying again",
        "Check the rate limit headers in the response",
        "Reduce the frequency of your requests",
    ],
    ErrorCode.LICENSE_UNKNOWN: [
        "Model has unknown license. Verify license before using.",
        "If unsure, contact model creator or use a different model.",
        "Check the model source for license information.",
    ],
    ErrorCode.CHECKSUM_MISSING: [
        "Model download URL does not include a checksum for verification.",
        "Download at your own risk - file integrity cannot be verified.",
        "Consider using a model with a verified checksum for safety.",
    ],
    ErrorCode.CONSENT_MISSING: [
        "Identity-based workflows require consent.",
        "Check the 'I have permission to use this face' checkbox.",
        "You must acknowledge that you have permission to use the identity reference.",
    ],
    ErrorCode.INSUFFICIENT_FUNDS: [
        "Not enough credits for this operation.",
        "Upgrade your plan or use a local engine (free).",
        "Check your credit balance in Settings.",
    ],
    ErrorCode.ENGINE_TIMEOUT: [
        "The generation engine did not respond in time.",
        "The engine may be overloaded - try again later.",
        "Check engine status in Setup Hub.",
        "Consider using a different engine or reducing quality settings.",
    ],
    ErrorCode.SAFETY_FILTER: [
        "Content was blocked by safety filter (NSFW/violence detection).",
        "Modify your prompt to avoid prohibited content.",
        "Check platform content policies for allowed content types.",
    ],
    ErrorCode.UNKNOWN_ERROR: [
        "An unexpected error occurred",
        "Check the error logs for more details",
        "Try the operation again",
        "If the problem persists, check the logs in runs/launcher/<timestamp>/",
    ],
}


def classify_error(error: Exception | str, context: dict[str, Any] | None = None) -> tuple[ErrorCode, list[str]]:
    """Classify an error and return taxonomy code with remediation steps.
    
    Args:
        error: Exception object or error message string
        context: Optional context dictionary with additional information
        
    Returns:
        Tuple of (ErrorCode, list of remediation steps)
    """
    context = context or {}
    error_str = str(error).lower()
    error_type = type(error).__name__ if isinstance(error, Exception) else None
    
    # Auth errors
    if "authorization" in error_str or "auth" in error_str or "token" in error_str:
        if "missing" in error_str:
            return ErrorCode.AUTH_MISSING, REMEDIATION_STEPS[ErrorCode.AUTH_MISSING]
        if "expired" in error_str or "expir" in error_str:
            return ErrorCode.AUTH_EXPIRED, REMEDIATION_STEPS[ErrorCode.AUTH_EXPIRED]
        if "invalid" in error_str or "malformed" in error_str:
            return ErrorCode.AUTH_INVALID, REMEDIATION_STEPS[ErrorCode.AUTH_INVALID]
        if "permission" in error_str or "forbidden" in error_str:
            return ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS, REMEDIATION_STEPS[ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS]
    
    # Database errors
    if "database" in error_str or "db" in error_str or "connection refused" in error_str:
        if "postgres" in error_str or "sqlite" in error_str:
            return ErrorCode.DB_UNAVAILABLE, REMEDIATION_STEPS[ErrorCode.DB_UNAVAILABLE]
    
    # Redis errors
    if "redis" in error_str:
        return ErrorCode.REDIS_UNAVAILABLE, REMEDIATION_STEPS[ErrorCode.REDIS_UNAVAILABLE]
    
    # Engine/ComfyUI errors
    if "comfyui" in error_str or "engine" in error_str or "offline" in error_str:
        return ErrorCode.ENGINE_OFFLINE, REMEDIATION_STEPS[ErrorCode.ENGINE_OFFLINE]
    
    # Download errors
    if "download" in error_str:
        if "timeout" in error_str:
            return ErrorCode.DOWNLOAD_TIMEOUT, REMEDIATION_STEPS[ErrorCode.DOWNLOAD_TIMEOUT]
        if "cancelled" in error_str or "cancel" in error_str:
            return ErrorCode.DOWNLOAD_CANCELLED, REMEDIATION_STEPS[ErrorCode.DOWNLOAD_CANCELLED]
        if "checksum" in error_str or "hash" in error_str:
            return ErrorCode.CHECKSUM_MISMATCH, REMEDIATION_STEPS[ErrorCode.CHECKSUM_MISMATCH]
        if "disk" in error_str or "space" in error_str:
            return ErrorCode.DISK_FULL, REMEDIATION_STEPS[ErrorCode.DISK_FULL]
        return ErrorCode.DOWNLOAD_FAILED, REMEDIATION_STEPS[ErrorCode.DOWNLOAD_FAILED]
    
    # File system errors
    if error_type == "FileNotFoundError" or "file not found" in error_str:
        return ErrorCode.FILE_NOT_FOUND, REMEDIATION_STEPS[ErrorCode.FILE_NOT_FOUND]
    if error_type == "PermissionError" or "permission denied" in error_str:
        return ErrorCode.PERMISSION_DENIED, REMEDIATION_STEPS[ErrorCode.PERMISSION_DENIED]
    
    # Network errors
    if error_type == "ConnectionError" or "connection" in error_str:
        if "refused" in error_str:
            return ErrorCode.CONNECTION_REFUSED, REMEDIATION_STEPS[ErrorCode.CONNECTION_REFUSED]
        if "timeout" in error_str:
            return ErrorCode.CONNECTION_TIMEOUT, REMEDIATION_STEPS[ErrorCode.CONNECTION_TIMEOUT]
        return ErrorCode.SERVICE_UNAVAILABLE, REMEDIATION_STEPS[ErrorCode.SERVICE_UNAVAILABLE]
    if error_type == "TimeoutError" or "timeout" in error_str:
        return ErrorCode.CONNECTION_TIMEOUT, REMEDIATION_STEPS[ErrorCode.CONNECTION_TIMEOUT]
    
    # Validation errors
    if error_type == "ValueError" or "validation" in error_str:
        if "missing" in error_str or "required" in error_str:
            return ErrorCode.MISSING_REQUIRED_FIELD, REMEDIATION_STEPS[ErrorCode.MISSING_REQUIRED_FIELD]
        return ErrorCode.VALIDATION_ERROR, REMEDIATION_STEPS[ErrorCode.VALIDATION_ERROR]
    if error_type == "KeyError" or "missing parameter" in error_str:
        return ErrorCode.MISSING_PARAMETER, REMEDIATION_STEPS[ErrorCode.MISSING_PARAMETER]
    
    # API contract errors
    if "contract" in error_str or "mismatch" in error_str or "422" in error_str:
        return ErrorCode.CONTRACT_MISMATCH, REMEDIATION_STEPS[ErrorCode.CONTRACT_MISMATCH]
    
    # Rate limiting
    if "rate limit" in error_str or "too many" in error_str:
        return ErrorCode.RATE_LIMIT_EXCEEDED, REMEDIATION_STEPS[ErrorCode.RATE_LIMIT_EXCEEDED]
    
    # License/checksum errors
    if "license" in error_str and "unknown" in error_str:
        return ErrorCode.LICENSE_UNKNOWN, REMEDIATION_STEPS[ErrorCode.LICENSE_UNKNOWN]
    if "checksum" in error_str and "missing" in error_str:
        return ErrorCode.CHECKSUM_MISSING, REMEDIATION_STEPS[ErrorCode.CHECKSUM_MISSING]
    
    # Workflow/pipeline errors
    if "consent" in error_str and "missing" in error_str:
        return ErrorCode.CONSENT_MISSING, REMEDIATION_STEPS[ErrorCode.CONSENT_MISSING]
    if "insufficient" in error_str and ("funds" in error_str or "credits" in error_str or "balance" in error_str):
        return ErrorCode.INSUFFICIENT_FUNDS, REMEDIATION_STEPS[ErrorCode.INSUFFICIENT_FUNDS]
    if "timeout" in error_str and ("engine" in error_str or "generation" in error_str):
        return ErrorCode.ENGINE_TIMEOUT, REMEDIATION_STEPS[ErrorCode.ENGINE_TIMEOUT]
    if "safety" in error_str or "nsfw" in error_str or "filter" in error_str:
        return ErrorCode.SAFETY_FILTER, REMEDIATION_STEPS[ErrorCode.SAFETY_FILTER]
    
    # Default to unknown
    return ErrorCode.UNKNOWN_ERROR, REMEDIATION_STEPS[ErrorCode.UNKNOWN_ERROR]


def create_error_response(
    error_code: ErrorCode,
    message: str,
    detail: str | None = None,
    remediation: list[str] | None = None,
) -> dict[str, Any]:
    """Create a standardized error response with taxonomy code and remediation.
    
    Args:
        error_code: Taxonomy error code
        message: Human-readable error message
        detail: Optional detailed error information (for dev mode, secrets redacted)
        remediation: Optional custom remediation steps (uses default if None)
        
    Returns:
        Dictionary with error response structure:
        {
            "ok": false,
            "error": error_code.value,  # Backward compatibility
            "error_code": error_code.value,
            "message": message,
            "remediation": [...],
            "detail": detail  # Optional, redacted in production
        }
    """
    return {
        "ok": False,
        "error": error_code.value,  # Backward compatibility
        "error_code": error_code.value,
        "message": message,
        "remediation": remediation or REMEDIATION_STEPS.get(error_code, []),
        "detail": detail,  # Only shown in dev mode, secrets should be redacted
    }
