"""
Comprehensive Troubleshooting Service
Implements all troubleshooting capabilities from docs/30-TROUBLESHOOTING-COMPLETE.md
"""
import logging
import subprocess
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime
import json
import sys

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Error codes from troubleshooting guide"""
    # CUDA Errors
    CUDA_OUT_OF_MEMORY = "CUDA_OUT_OF_MEMORY"
    CUDA_DRIVER_INSUFFICIENT = "CUDA_DRIVER_INSUFFICIENT"
    CUDA_DEVICE_NOT_FOUND = "CUDA_DEVICE_NOT_FOUND"
    
    # Model Errors
    MODEL_FILE_NOT_FOUND = "MODEL_FILE_NOT_FOUND"
    MODEL_VERSION_MISMATCH = "MODEL_VERSION_MISMATCH"
    MODEL_LOADING_FAILED = "MODEL_LOADING_FAILED"
    
    # API Errors
    API_UNAUTHORIZED = "API_UNAUTHORIZED"
    API_RATE_LIMITED = "API_RATE_LIMITED"
    API_INTERNAL_ERROR = "API_INTERNAL_ERROR"
    
    # Generation Errors
    GENERATION_FAILED = "GENERATION_FAILED"
    GENERATION_TIMEOUT = "GENERATION_TIMEOUT"
    GENERATION_QUALITY_LOW = "GENERATION_QUALITY_LOW"
    
    # Face Consistency Errors
    FACE_CONSISTENCY_FAILED = "FACE_CONSISTENCY_FAILED"
    FACE_REFERENCE_INVALID = "FACE_REFERENCE_INVALID"
    FACE_DETECTION_FAILED = "FACE_DETECTION_FAILED"
    
    # System Errors
    COMFYUI_NOT_RUNNING = "COMFYUI_NOT_RUNNING"
    DISK_SPACE_INSUFFICIENT = "DISK_SPACE_INSUFFICIENT"
    MEMORY_INSUFFICIENT = "MEMORY_INSUFFICIENT"
    PYTHON_VERSION_INCOMPATIBLE = "PYTHON_VERSION_INCOMPATIBLE"
    
    # Integration Errors
    PLATFORM_AUTH_FAILED = "PLATFORM_AUTH_FAILED"
    PLATFORM_RATE_LIMITED = "PLATFORM_RATE_LIMITED"
    BROWSER_AUTOMATION_FAILED = "BROWSER_AUTOMATION_FAILED"


class TroubleshootingService:
    """Comprehensive troubleshooting service"""
    
    def __init__(self, comfyui_path: Optional[Path] = None):
        self.comfyui_path = comfyui_path or (Path(__file__).parent.parent.parent / "ComfyUI")
        self.system = platform.system()
        self.error_resolutions = self._load_error_resolutions()
    
    def _load_error_resolutions(self) -> Dict[str, Dict[str, Any]]:
        """Load error code to resolution mapping"""
        return {
            ErrorCode.CUDA_OUT_OF_MEMORY.value: {
                "title": "GPU Out of Memory",
                "description": "GPU memory is full. Reduce batch size, lower resolution, or clear cache.",
                "solutions": [
                    "Reduce batch size to 1",
                    "Generate at lower resolution (512x512) and upscale later",
                    "Clear GPU cache: `torch.cuda.empty_cache()`",
                    "Enable CPU offloading if available",
                    "Close other GPU-intensive applications"
                ],
                "diagnostic_commands": [
                    "nvidia-smi",
                    "Check GPU memory usage"
                ],
                "severity": "high"
            },
            ErrorCode.CUDA_DRIVER_INSUFFICIENT.value: {
                "title": "CUDA Driver Version Insufficient",
                "description": "CUDA driver version is too old for the installed CUDA toolkit.",
                "solutions": [
                    "Update NVIDIA drivers: `sudo ubuntu-drivers autoinstall` (Linux) or download from NVIDIA website (Windows)",
                    "Reboot system after driver update",
                    "Verify driver version: `nvidia-smi`",
                    "Check CUDA compatibility: `nvcc --version`"
                ],
                "diagnostic_commands": [
                    "nvidia-smi",
                    "nvcc --version"
                ],
                "severity": "critical"
            },
            ErrorCode.CUDA_DEVICE_NOT_FOUND.value: {
                "title": "GPU Not Detected",
                "description": "CUDA device not found. GPU may not be installed or drivers not loaded.",
                "solutions": [
                    "Check GPU installation: `nvidia-smi`",
                    "Install NVIDIA drivers if missing",
                    "Verify PyTorch CUDA support: `python -c 'import torch; print(torch.cuda.is_available())'`",
                    "Reinstall PyTorch with CUDA support if needed"
                ],
                "diagnostic_commands": [
                    "nvidia-smi",
                    "python -c 'import torch; print(torch.cuda.is_available())'"
                ],
                "severity": "critical"
            },
            ErrorCode.MODEL_FILE_NOT_FOUND.value: {
                "title": "Model File Not Found",
                "description": "Required model file is missing or not accessible.",
                "solutions": [
                    "Check model file exists: `ls -lh models/model.safetensors`",
                    "Re-download model from source",
                    "Verify model path in configuration",
                    "Check file permissions"
                ],
                "diagnostic_commands": [
                    "ls -lh models/",
                    "Check model directory structure"
                ],
                "severity": "high"
            },
            ErrorCode.MODEL_VERSION_MISMATCH.value: {
                "title": "Model Version Mismatch",
                "description": "Model version is incompatible with current system.",
                "solutions": [
                    "Check model version and compatibility",
                    "Update dependencies to match model requirements",
                    "Use compatible model version",
                    "Check model documentation for version requirements"
                ],
                "diagnostic_commands": [
                    "Check model metadata",
                    "Verify dependency versions"
                ],
                "severity": "medium"
            },
            ErrorCode.MODEL_LOADING_FAILED.value: {
                "title": "Model Loading Failed",
                "description": "Model file is corrupted or cannot be loaded.",
                "solutions": [
                    "Re-download model file",
                    "Verify file integrity (checksum if available)",
                    "Check file format compatibility",
                    "Try loading with safetensors library to verify"
                ],
                "diagnostic_commands": [
                    "python -c 'import safetensors; safetensors.torch.load_file(\"model.safetensors\")'"
                ],
                "severity": "high"
            },
            ErrorCode.GENERATION_FAILED.value: {
                "title": "Content Generation Failed",
                "description": "Generation process failed or returned errors.",
                "solutions": [
                    "Check GPU availability: `nvidia-smi`",
                    "Verify model files exist",
                    "Check disk space: `df -h`",
                    "Review error logs",
                    "Restart services"
                ],
                "diagnostic_commands": [
                    "nvidia-smi",
                    "df -h",
                    "tail -f logs/app.log"
                ],
                "severity": "high"
            },
            ErrorCode.GENERATION_QUALITY_LOW.value: {
                "title": "Low Quality Output",
                "description": "Generated content has blur, artifacts, or unrealistic appearance.",
                "solutions": [
                    "Increase resolution",
                    "Use more inference steps (30-50)",
                    "Use better quality models",
                    "Improve prompts with quality modifiers",
                    "Apply post-processing",
                    "Check face consistency settings"
                ],
                "diagnostic_commands": [
                    "Check generation settings",
                    "Review prompt quality"
                ],
                "severity": "medium"
            },
            ErrorCode.FACE_CONSISTENCY_FAILED.value: {
                "title": "Face Consistency Failed",
                "description": "Face consistency is not working or producing inconsistent results.",
                "solutions": [
                    "Check reference image quality (high resolution, clear face)",
                    "Increase face consistency strength",
                    "Verify face consistency method is applied",
                    "Use better face consistency method (IP-Adapter, InstantID)",
                    "Check face detection is working",
                    "Ensure reference image has detectable face"
                ],
                "diagnostic_commands": [
                    "Validate face reference image",
                    "Check face detection"
                ],
                "severity": "medium"
            },
            ErrorCode.COMFYUI_NOT_RUNNING.value: {
                "title": "ComfyUI Not Running",
                "description": "ComfyUI server is not accessible or not running.",
                "solutions": [
                    "Start ComfyUI: `cd ComfyUI && python main.py`",
                    "Verify it's running: `http://127.0.0.1:8188/system_stats`",
                    "Check firewall settings",
                    "Verify port 8188 is not in use",
                    "Check ComfyUI logs for errors"
                ],
                "diagnostic_commands": [
                    "curl http://127.0.0.1:8188/system_stats",
                    "Check ComfyUI process"
                ],
                "severity": "critical"
            },
            ErrorCode.DISK_SPACE_INSUFFICIENT.value: {
                "title": "Insufficient Disk Space",
                "description": "Not enough disk space for generation or model storage.",
                "solutions": [
                    "Free up disk space",
                    "Delete unused models or media",
                    "Move models to external storage",
                    "Check disk usage: `df -h`"
                ],
                "diagnostic_commands": [
                    "df -h",
                    "du -sh models/"
                ],
                "severity": "high"
            },
            ErrorCode.PYTHON_VERSION_INCOMPATIBLE.value: {
                "title": "Python Version Incompatible",
                "description": "Python version is incompatible with required packages.",
                "solutions": [
                    "Use Python 3.11 or 3.12 (recommended)",
                    "Create virtual environment with correct Python version",
                    "Check package compatibility",
                    "Update packages if possible"
                ],
                "diagnostic_commands": [
                    "python --version",
                    "pip list"
                ],
                "severity": "high"
            },
            ErrorCode.API_RATE_LIMITED.value: {
                "title": "API Rate Limited",
                "description": "Too many requests to API. Rate limit exceeded.",
                "solutions": [
                    "Implement rate limiting with delays",
                    "Use exponential backoff",
                    "Reduce request frequency",
                    "Check API rate limit documentation"
                ],
                "diagnostic_commands": [
                    "Check API response headers",
                    "Review request frequency"
                ],
                "severity": "medium"
            },
            ErrorCode.API_UNAUTHORIZED.value: {
                "title": "API Authentication Failed",
                "description": "API authentication credentials are invalid or expired.",
                "solutions": [
                    "Check credentials are correct",
                    "Verify token expiration",
                    "Refresh authentication token",
                    "Re-authenticate if needed"
                ],
                "diagnostic_commands": [
                    "Check credential configuration",
                    "Verify token validity"
                ],
                "severity": "high"
            }
        }
    
    def diagnose_error(self, error_code: str, error_message: str = "", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Diagnose an error and provide resolution"""
        context = context or {}
        
        # Get error resolution
        resolution = self.error_resolutions.get(error_code, {
            "title": "Unknown Error",
            "description": "Error code not recognized",
            "solutions": ["Check logs for more information"],
            "diagnostic_commands": [],
            "severity": "unknown"
        })
        
        # Run diagnostics based on error code
        diagnostics = self._run_diagnostics(error_code, context)
        
        return {
            "error_code": error_code,
            "error_message": error_message,
            "resolution": resolution,
            "diagnostics": diagnostics,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _run_diagnostics(self, error_code: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run diagnostic checks based on error code"""
        diagnostics = {}
        
        if error_code in [ErrorCode.CUDA_OUT_OF_MEMORY.value, ErrorCode.CUDA_DEVICE_NOT_FOUND.value, ErrorCode.CUDA_DRIVER_INSUFFICIENT.value]:
            diagnostics["gpu"] = self._diagnose_gpu()
        
        if error_code in [ErrorCode.MODEL_FILE_NOT_FOUND.value, ErrorCode.MODEL_LOADING_FAILED.value]:
            model_path = context.get("model_path")
            if model_path:
                diagnostics["model"] = self._diagnose_model(model_path)
        
        if error_code == ErrorCode.COMFYUI_NOT_RUNNING.value:
            diagnostics["comfyui"] = self._diagnose_comfyui()
        
        if error_code == ErrorCode.DISK_SPACE_INSUFFICIENT.value:
            diagnostics["disk"] = self._diagnose_disk_space()
        
        if error_code == ErrorCode.PYTHON_VERSION_INCOMPATIBLE.value:
            diagnostics["python"] = self._diagnose_python()
        
        if error_code == ErrorCode.GENERATION_FAILED.value:
            diagnostics["system"] = self._diagnose_system()
        
        return diagnostics
    
    def _diagnose_gpu(self) -> Dict[str, Any]:
        """Diagnose GPU status"""
        result = {
            "available": False,
            "name": None,
            "memory_total": None,
            "memory_used": None,
            "memory_free": None,
            "driver_version": None,
            "cuda_available": False
        }
        
        # Check via nvidia-smi
        try:
            if self.system == "Windows":
                output = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            else:
                output = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version", "--format=csv,noheader"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            
            if output.returncode == 0 and output.stdout:
                lines = output.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split(',')
                    if len(parts) >= 4:
                        result["available"] = True
                        result["name"] = parts[0].strip()
                        result["memory_total"] = parts[1].strip()
                        result["memory_used"] = parts[2].strip()
                        result["driver_version"] = parts[3].strip()
                        result["memory_free"] = "N/A"  # Calculate if needed
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError) as e:
            logger.warning(f"nvidia-smi check failed: {e}")
        
        # Check PyTorch CUDA
        try:
            import torch
            result["cuda_available"] = torch.cuda.is_available()
            if result["cuda_available"]:
                result["available"] = True
                if not result["name"]:
                    result["name"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        except ImportError:
            pass
        
        return result
    
    def _diagnose_model(self, model_path: str) -> Dict[str, Any]:
        """Diagnose model file"""
        result = {
            "exists": False,
            "size": None,
            "readable": False,
            "format_valid": False
        }
        
        path = Path(model_path)
        result["exists"] = path.exists()
        
        if result["exists"]:
            result["size"] = path.stat().st_size
            result["readable"] = path.is_file() and path.stat().st_size > 0
            
            # Try to validate format
            try:
                if path.suffix in [".safetensors", ".ckpt", ".pt", ".pth"]:
                    result["format_valid"] = True  # Assume valid if extension matches
            except Exception:
                pass
        
        return result
    
    def _diagnose_comfyui(self) -> Dict[str, Any]:
        """Diagnose ComfyUI status"""
        result = {
            "running": False,
            "accessible": False,
            "port": 8188,
            "path_exists": False
        }
        
        result["path_exists"] = self.comfyui_path.exists()
        
        # Check if accessible
        try:
            import requests
            response = requests.get(
                f"http://127.0.0.1:8188/system_stats",
                timeout=2
            )
            result["accessible"] = response.status_code == 200
            result["running"] = result["accessible"]
        except Exception:
            pass
        
        return result
    
    def _diagnose_disk_space(self) -> Dict[str, Any]:
        """Diagnose disk space"""
        result = {
            "total": None,
            "used": None,
            "free": None,
            "percent_used": None
        }
        
        try:
            import shutil
            stat = shutil.disk_usage(self.comfyui_path if self.comfyui_path.exists() else Path.cwd())
            result["total"] = stat.total / (1024**3)  # GB
            result["used"] = stat.used / (1024**3)
            result["free"] = stat.free / (1024**3)
            result["percent_used"] = (stat.used / stat.total) * 100
        except Exception as e:
            logger.warning(f"Disk space check failed: {e}")
        
        return result
    
    def _diagnose_python(self) -> Dict[str, Any]:
        """Diagnose Python version"""
        result = {
            "version": sys.version,
            "version_info": {
                "major": sys.version_info.major,
                "minor": sys.version_info.minor,
                "micro": sys.version_info.micro
            },
            "compatible": False,
            "recommended": "3.11 or 3.12"
        }
        
        # Check compatibility
        major, minor = sys.version_info.major, sys.version_info.minor
        result["compatible"] = (major == 3 and minor in [11, 12]) or (major == 3 and minor >= 10)
        
        return result
    
    def _diagnose_system(self) -> Dict[str, Any]:
        """Diagnose general system status"""
        result = {
            "gpu": self._diagnose_gpu(),
            "disk": self._diagnose_disk_space(),
            "python": self._diagnose_python(),
            "comfyui": self._diagnose_comfyui()
        }
        
        return result
    
    def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive system diagnostics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.machine()
            },
            "gpu": self._diagnose_gpu(),
            "python": self._diagnose_python(),
            "disk": self._diagnose_disk_space(),
            "comfyui": self._diagnose_comfyui(),
            "memory": self._diagnose_memory()
        }
    
    def _diagnose_memory(self) -> Dict[str, Any]:
        """Diagnose system memory"""
        result = {
            "total": None,
            "available": None,
            "used": None,
            "percent": None
        }
        
        try:
            import psutil
            mem = psutil.virtual_memory()
            result["total"] = mem.total / (1024**3)  # GB
            result["available"] = mem.available / (1024**3)
            result["used"] = mem.used / (1024**3)
            result["percent"] = mem.percent
        except ImportError:
            pass
        
        return result
    
    def get_error_resolution(self, error_code: str) -> Optional[Dict[str, Any]]:
        """Get resolution for a specific error code"""
        return self.error_resolutions.get(error_code)
    
    def list_all_error_codes(self) -> List[Dict[str, Any]]:
        """List all available error codes with their information"""
        return [
            {
                "code": code,
                **info
            }
            for code, info in self.error_resolutions.items()
        ]
    
    def check_generation_quality_issues(self, image_path: Optional[Path] = None, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check for common generation quality issues"""
        issues = []
        recommendations = []
        
        settings = settings or {}
        
        # Check resolution
        resolution = settings.get("resolution", 512)
        if resolution < 512:
            issues.append("Low resolution may cause blurry images")
            recommendations.append("Increase resolution to at least 512x512, preferably 1024x1024")
        
        # Check inference steps
        steps = settings.get("steps", 20)
        if steps < 25:
            issues.append("Low inference steps may reduce quality")
            recommendations.append("Use at least 25-30 inference steps for better quality")
        
        # Check CFG scale
        cfg = settings.get("cfg_scale", 7.0)
        if cfg < 5.0 or cfg > 15.0:
            issues.append("CFG scale outside recommended range")
            recommendations.append("Use CFG scale between 7-12 for best results")
        
        return {
            "issues": issues,
            "recommendations": recommendations,
            "settings_checked": {
                "resolution": resolution,
                "steps": steps,
                "cfg_scale": cfg
            }
        }
    
    def check_face_consistency_issues(self, reference_path: Optional[Path] = None, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Check for face consistency issues"""
        issues = []
        recommendations = []
        
        config = config or {}
        
        # Check if enabled
        if not config.get("enabled"):
            return {
                "issues": [],
                "recommendations": [],
                "enabled": False
            }
        
        # Check reference image
        if reference_path:
            if not reference_path.exists():
                issues.append("Face reference image not found")
                recommendations.append("Upload a valid face reference image")
            else:
                # Check file size (should be reasonable)
                size_mb = reference_path.stat().st_size / (1024**2)
                if size_mb > 10:
                    issues.append("Face reference image is very large")
                    recommendations.append("Use a smaller reference image (< 5MB recommended)")
        
        # Check strength
        strength = config.get("strength", 1.0)
        if strength < 0.5:
            issues.append("Face consistency strength is low")
            recommendations.append("Increase strength to 0.7-1.0 for better consistency")
        
        return {
            "issues": issues,
            "recommendations": recommendations,
            "config_checked": config
        }
    
    def check_performance_issues(self) -> Dict[str, Any]:
        """Check for performance issues"""
        issues = []
        recommendations = []
        
        # Check GPU
        gpu_info = self._diagnose_gpu()
        if not gpu_info["available"]:
            issues.append("GPU not available - generation will be very slow")
            recommendations.append("Ensure GPU is available and drivers are installed")
        else:
            # Check GPU memory
            if gpu_info.get("memory_used"):
                # Parse memory info if available
                pass
        
        # Check disk space
        disk_info = self._diagnose_disk_space()
        if disk_info.get("free"):
            free_gb = disk_info["free"]
            if free_gb < 10:
                issues.append("Low disk space may cause issues")
                recommendations.append("Free up at least 10GB of disk space")
        
        return {
            "issues": issues,
            "recommendations": recommendations,
            "gpu": gpu_info,
            "disk": disk_info
        }
