"""
System Setup Verification Service
Verifies NVIDIA GPU, CUDA, cuDNN, models, and tools as per docs/18-AI-TOOLS-NVIDIA-SETUP.md
"""
import logging
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import sys

logger = logging.getLogger(__name__)

class SystemSetupService:
    """Service for verifying and checking system setup"""
    
    def __init__(self, comfyui_path: Optional[Path] = None):
        self.comfyui_path = comfyui_path or (Path(__file__).parent.parent.parent / "ComfyUI")
        self.system = platform.system()
        
    def verify_complete_setup(self) -> Dict[str, Any]:
        """Verify complete system setup according to the NVIDIA setup guide"""
        results = {
            "hardware": self.verify_hardware(),
            "nvidia_driver": self.verify_nvidia_driver(),
            "cuda": self.verify_cuda(),
            "cudnn": self.verify_cudnn(),
            "python": self.verify_python(),
            "comfyui": self.verify_comfyui_installation(),
            "models": self.verify_models(),
            "face_consistency": self.verify_face_consistency_setup(),
            "video_generation": self.verify_video_generation_setup(),
            "post_processing": self.verify_post_processing_setup(),
            "overall_status": "unknown"
        }
        
        # Determine overall status
        critical_checks = [
            results["hardware"]["gpu_available"],
            results["nvidia_driver"]["installed"],
            results["cuda"]["installed"],
            results["comfyui"]["installed"]
        ]
        
        if all(critical_checks):
            results["overall_status"] = "ready"
        elif any(critical_checks[:3]):  # GPU, driver, CUDA
            results["overall_status"] = "partial"
        else:
            results["overall_status"] = "not_ready"
        
        return results
    
    def verify_hardware(self) -> Dict[str, Any]:
        """Verify hardware requirements"""
        result = {
            "gpu_available": False,
            "gpu_name": None,
            "gpu_memory_total": None,
            "gpu_memory_free": None,
            "gpu_memory_used": None,
            "system_ram": None,
            "cpu_cores": None,
            "storage_free": None,
            "meets_minimum": False,
            "meets_recommended": False
        }
        
        try:
            # Check GPU via PyTorch if available
            try:
                import torch
                if torch.cuda.is_available():
                    result["gpu_available"] = True
                    result["gpu_name"] = torch.cuda.get_device_name(0)
                    result["gpu_memory_total"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
                    result["gpu_memory_free"] = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / (1024**3)
                    result["gpu_memory_used"] = torch.cuda.memory_allocated(0) / (1024**3)
            except ImportError:
                logger.warning("PyTorch not available, checking via nvidia-smi")
                result["gpu_available"] = False
            
            # Fallback to nvidia-smi
            if not result["gpu_available"]:
                nvidia_info = self._get_nvidia_smi_info()
                if nvidia_info:
                    result["gpu_available"] = True
                    result["gpu_name"] = nvidia_info.get("name", "NVIDIA GPU")
                    result["gpu_memory_total"] = nvidia_info.get("memory_total")
                    result["gpu_memory_used"] = nvidia_info.get("memory_used")
                    result["gpu_memory_free"] = nvidia_info.get("memory_free")
            
            # Check system RAM
            try:
                import psutil
                result["system_ram"] = psutil.virtual_memory().total / (1024**3)  # GB
            except ImportError:
                pass
            
            # Check CPU cores
            result["cpu_cores"] = platform.processor() or "Unknown"
            
            # Check storage
            try:
                import shutil
                result["storage_free"] = shutil.disk_usage(self.comfyui_path).free / (1024**3)  # GB
            except Exception:
                pass
            
            # Check if meets requirements
            # Minimum: RTX 3060 (12GB), 16GB RAM, 500GB storage
            # Recommended: RTX 4090 (24GB), 32GB RAM, 2TB storage
            gpu_memory = result["gpu_memory_total"] or 0
            ram = result["system_ram"] or 0
            storage = result["storage_free"] or 0
            
            result["meets_minimum"] = (
                gpu_memory >= 12 and
                ram >= 16 and
                storage >= 500
            )
            
            result["meets_recommended"] = (
                gpu_memory >= 24 and
                ram >= 32 and
                storage >= 2000
            )
            
        except Exception as e:
            logger.error(f"Hardware verification error: {e}")
        
        return result
    
    def verify_nvidia_driver(self) -> Dict[str, Any]:
        """Verify NVIDIA driver installation"""
        result = {
            "installed": False,
            "version": None,
            "check_method": None,
            "error": None
        }
        
        try:
            # Try nvidia-smi first
            if self.system == "Windows":
                try:
                    output = subprocess.check_output(
                        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                        stderr=subprocess.DEVNULL,
                        timeout=5
                    )
                    result["installed"] = True
                    result["version"] = output.decode().strip()
                    result["check_method"] = "nvidia-smi"
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    pass
            else:
                try:
                    output = subprocess.check_output(
                        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                        stderr=subprocess.DEVNULL,
                        timeout=5
                    )
                    result["installed"] = True
                    result["version"] = output.decode().strip()
                    result["check_method"] = "nvidia-smi"
                except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                    pass
            
            # Try PyTorch as fallback
            if not result["installed"]:
                try:
                    import torch
                    if torch.cuda.is_available():
                        result["installed"] = True
                        result["version"] = f"CUDA {torch.version.cuda}"
                        result["check_method"] = "pytorch"
                except ImportError:
                    pass
            
        except Exception as e:
            logger.error(f"NVIDIA driver verification error: {e}")
            result["error"] = str(e)
        
        return result
    
    def verify_cuda(self) -> Dict[str, Any]:
        """Verify CUDA toolkit installation"""
        result = {
            "installed": False,
            "version": None,
            "check_method": None,
            "error": None
        }
        
        try:
            # Try nvcc (CUDA compiler)
            try:
                output = subprocess.check_output(
                    ["nvcc", "--version"],
                    stderr=subprocess.DEVNULL,
                    timeout=5
                )
                # Parse version from output
                output_str = output.decode()
                if "release" in output_str.lower():
                    for line in output_str.split("\n"):
                        if "release" in line.lower():
                            # Extract version (e.g., "11.8" or "12.1")
                            parts = line.split("release")[-1].strip().split(",")[0]
                            result["version"] = parts.strip()
                            break
                result["installed"] = True
                result["check_method"] = "nvcc"
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            # Try PyTorch as fallback
            if not result["installed"]:
                try:
                    import torch
                    if torch.version.cuda:
                        result["installed"] = True
                        result["version"] = torch.version.cuda
                        result["check_method"] = "pytorch"
                except ImportError:
                    pass
            
        except Exception as e:
            logger.error(f"CUDA verification error: {e}")
            result["error"] = str(e)
        
        return result
    
    def verify_cudnn(self) -> Dict[str, Any]:
        """Verify cuDNN installation (optional but recommended)"""
        result = {
            "installed": False,
            "version": None,
            "check_method": None,
            "note": "Optional but recommended for 20-30% performance improvement"
        }
        
        try:
            # Try PyTorch
            try:
                import torch
                if hasattr(torch.backends, 'cudnn') and torch.backends.cudnn.is_available():
                    result["installed"] = True
                    result["version"] = "Available (version via PyTorch)"
                    result["check_method"] = "pytorch"
            except ImportError:
                pass
            
        except Exception as e:
            logger.error(f"cuDNN verification error: {e}")
        
        return result
    
    def verify_python(self) -> Dict[str, Any]:
        """Verify Python version"""
        result = {
            "version": sys.version.split()[0],
            "version_info": {
                "major": sys.version_info.major,
                "minor": sys.version_info.minor,
                "micro": sys.version_info.micro
            },
            "meets_requirements": False
        }
        
        # Require Python 3.10 or 3.11
        result["meets_requirements"] = (
            result["version_info"]["major"] == 3 and
            result["version_info"]["minor"] in [10, 11]
        )
        
        return result
    
    def verify_comfyui_installation(self) -> Dict[str, Any]:
        """Verify ComfyUI installation"""
        result = {
            "installed": False,
            "path": str(self.comfyui_path),
            "main_py_exists": False,
            "models_dir_exists": False,
            "requirements_installed": False
        }
        
        try:
            # Check if ComfyUI directory exists
            if self.comfyui_path.exists():
                result["installed"] = True
                
                # Check main.py
                main_py = self.comfyui_path / "main.py"
                result["main_py_exists"] = main_py.exists()
                
                # Check models directory
                models_dir = self.comfyui_path / "models"
                result["models_dir_exists"] = models_dir.exists()
                
        except Exception as e:
            logger.error(f"ComfyUI verification error: {e}")
        
        return result
    
    def verify_models(self) -> Dict[str, Any]:
        """Verify installed AI models"""
        result = {
            "checkpoints": [],
            "sdxl_models": [],
            "recommended_models": {
                "realistic_vision_v6": False,
                "juggernaut_xl_v9": False,
                "dreamshaper_xl": False,
                "realvisxl_v4": False,
                "sdxl_base_1_0": False
            },
            "total_size_gb": 0.0
        }
        
        try:
            models_dir = self.comfyui_path / "models" / "checkpoints"
            if models_dir.exists():
                # List all checkpoint files
                checkpoints = list(models_dir.glob("*.safetensors")) + list(models_dir.glob("*.ckpt"))
                
                for checkpoint in checkpoints:
                    size_gb = checkpoint.stat().st_size / (1024**3)
                    result["checkpoints"].append({
                        "name": checkpoint.name,
                        "size_gb": round(size_gb, 2),
                        "path": str(checkpoint)
                    })
                    result["total_size_gb"] += size_gb
                    
                    # Check for recommended models
                    name_lower = checkpoint.name.lower()
                    if "realistic" in name_lower and "vision" in name_lower and "v6" in name_lower:
                        result["recommended_models"]["realistic_vision_v6"] = True
                    elif "juggernaut" in name_lower and "xl" in name_lower:
                        result["recommended_models"]["juggernaut_xl_v9"] = True
                    elif "dreamshaper" in name_lower and "xl" in name_lower:
                        result["recommended_models"]["dreamshaper_xl"] = True
                    elif "realvis" in name_lower and "xl" in name_lower:
                        result["recommended_models"]["realvisxl_v4"] = True
                    elif "sdxl" in name_lower and "base" in name_lower:
                        result["recommended_models"]["sdxl_base_1_0"] = True
                    
                    # Check if SDXL model
                    if "xl" in name_lower or checkpoint.stat().st_size > 6 * (1024**3):  # > 6GB likely SDXL
                        result["sdxl_models"].append(checkpoint.name)
                
                result["total_size_gb"] = round(result["total_size_gb"], 2)
        
        except Exception as e:
            logger.error(f"Model verification error: {e}")
        
        return result
    
    def verify_face_consistency_setup(self) -> Dict[str, Any]:
        """Verify face consistency tools (IP-Adapter, InstantID)"""
        result = {
            "ip_adapter": {
                "installed": False,
                "models": [],
                "path": None
            },
            "instantid": {
                "installed": False,
                "models": [],
                "path": None
            },
            "faceid": {
                "installed": False,
                "models": [],
                "path": None
            }
        }
        
        try:
            # Check IP-Adapter
            ip_adapter_path = self.comfyui_path / "models" / "ip-adapter"
            if ip_adapter_path.exists():
                result["ip_adapter"]["installed"] = True
                result["ip_adapter"]["path"] = str(ip_adapter_path)
                models = list(ip_adapter_path.glob("*.safetensors")) + list(ip_adapter_path.glob("*.bin"))
                result["ip_adapter"]["models"] = [m.name for m in models]
            
            # Check custom nodes for IP-Adapter
            custom_nodes_path = self.comfyui_path / "custom_nodes"
            if custom_nodes_path.exists():
                ip_adapter_node = custom_nodes_path / "ComfyUI_IPAdapter_plus"
                if ip_adapter_node.exists():
                    result["ip_adapter"]["installed"] = True
            
            # Check InstantID
            instantid_path = self.comfyui_path / "models" / "instantid"
            if instantid_path.exists():
                result["instantid"]["installed"] = True
                result["instantid"]["path"] = str(instantid_path)
                models = list(instantid_path.glob("*.bin")) + list(instantid_path.glob("*.safetensors"))
                result["instantid"]["models"] = [m.name for m in models]
            
            instantid_node = custom_nodes_path / "ComfyUI_InstantID" if custom_nodes_path.exists() else None
            if instantid_node and instantid_node.exists():
                result["instantid"]["installed"] = True
            
            # Check FaceID
            faceid_node = custom_nodes_path / "ComfyUI_FaceID" if custom_nodes_path.exists() else None
            if faceid_node and faceid_node.exists():
                result["faceid"]["installed"] = True
        
        except Exception as e:
            logger.error(f"Face consistency verification error: {e}")
        
        return result
    
    def verify_video_generation_setup(self) -> Dict[str, Any]:
        """Verify video generation tools (AnimateDiff, SVD)"""
        result = {
            "animatediff": {
                "installed": False,
                "models": [],
                "path": None
            },
            "stable_video_diffusion": {
                "installed": False,
                "models": [],
                "path": None
            }
        }
        
        try:
            # Check AnimateDiff
            animatediff_path = self.comfyui_path / "models" / "animatediff"
            if animatediff_path.exists():
                result["animatediff"]["installed"] = True
                result["animatediff"]["path"] = str(animatediff_path)
                models = list(animatediff_path.glob("*.ckpt"))
                result["animatediff"]["models"] = [m.name for m in models]
            
            custom_nodes_path = self.comfyui_path / "custom_nodes"
            animatediff_node = custom_nodes_path / "ComfyUI-AnimateDiff-Evolved" if custom_nodes_path.exists() else None
            if animatediff_node and animatediff_node.exists():
                result["animatediff"]["installed"] = True
            
            # Check Stable Video Diffusion
            svd_path = self.comfyui_path / "models" / "svd"
            if svd_path.exists():
                result["stable_video_diffusion"]["installed"] = True
                result["stable_video_diffusion"]["path"] = str(svd_path)
                models = list(svd_path.glob("*.safetensors")) + list(svd_path.glob("*.ckpt"))
                result["stable_video_diffusion"]["models"] = [m.name for m in models]
            
            svd_node = custom_nodes_path / "ComfyUI_Stable_Video_Diffusion" if custom_nodes_path.exists() else None
            if svd_node and svd_node.exists():
                result["stable_video_diffusion"]["installed"] = True
        
        except Exception as e:
            logger.error(f"Video generation verification error: {e}")
        
        return result
    
    def verify_post_processing_setup(self) -> Dict[str, Any]:
        """Verify post-processing tools (upscaling, face restoration)"""
        result = {
            "upscaling": {
                "realesrgan_installed": False,
                "models": [],
                "python_package": False
            },
            "face_restoration": {
                "gfpgan_installed": False,
                "codeformer_installed": False,
                "models": [],
                "python_package": False
            },
            "metadata_tools": {
                "exiftool_available": False
            }
        }
        
        try:
            # Check Real-ESRGAN
            upscale_path = self.comfyui_path / "models" / "upscale_models"
            if upscale_path.exists():
                models = list(upscale_path.glob("*.pth"))
                if models:
                    result["upscaling"]["realesrgan_installed"] = True
                    result["upscaling"]["models"] = [m.name for m in models]
            
            # Check Python packages
            try:
                import realesrgan
                result["upscaling"]["python_package"] = True
            except ImportError:
                pass
            
            # Check GFPGAN
            face_restore_path = self.comfyui_path / "models" / "face_restore"
            if face_restore_path.exists():
                gfpgan_models = list(face_restore_path.glob("*GFPGAN*.pth"))
                if gfpgan_models:
                    result["face_restoration"]["gfpgan_installed"] = True
                    result["face_restoration"]["models"] = [m.name for m in gfpgan_models]
            
            try:
                import gfpgan
                result["face_restoration"]["python_package"] = True
            except ImportError:
                pass
            
            # Check CodeFormer
            codeformer_models = list(face_restore_path.glob("*CodeFormer*.pth")) if face_restore_path.exists() else []
            if codeformer_models:
                result["face_restoration"]["codeformer_installed"] = True
            
            # Check exiftool
            try:
                subprocess.run(
                    ["exiftool", "-ver"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=2
                )
                result["metadata_tools"]["exiftool_available"] = True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                pass
        
        except Exception as e:
            logger.error(f"Post-processing verification error: {e}")
        
        return result
    
    def _get_nvidia_smi_info(self) -> Optional[Dict[str, Any]]:
        """Get GPU info from nvidia-smi"""
        try:
            # Get GPU name
            name_output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            name = name_output.decode().strip()
            
            # Get memory info
            mem_output = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=memory.total,memory.used,memory.free", "--format=csv,noheader,nounits"],
                stderr=subprocess.DEVNULL,
                timeout=5
            )
            mem_values = mem_output.decode().strip().split(",")
            
            return {
                "name": name,
                "memory_total": float(mem_values[0].strip()) / 1024,  # Convert MB to GB
                "memory_used": float(mem_values[1].strip()) / 1024,
                "memory_free": float(mem_values[2].strip()) / 1024
            }
        except Exception:
            return None
