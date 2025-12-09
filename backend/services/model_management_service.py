"""
Model Management Service
Comprehensive model management based on docs/33-MODELS-AND-CHECKPOINTS-COMPLETE-GUIDE.md
Supports all model types: Image, Video, Face Consistency, Post-Processing, ControlNet
"""
import logging
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import requests
from urllib.parse import urlparse
import shutil

logger = logging.getLogger(__name__)

class ModelManagementService:
    """Comprehensive service for managing all AI models"""
    
    def __init__(self, comfyui_path: Optional[Path] = None, root_path: Optional[Path] = None):
        self.root_path = root_path or (Path(__file__).parent.parent.parent)
        self.comfyui_path = comfyui_path or (self.root_path / "ComfyUI")
        self.models_dir = self.comfyui_path / "models"
        
        # Model directories
        self.model_dirs = {
            "checkpoints": self.models_dir / "checkpoints",
            "controlnet": self.models_dir / "controlnet",
            "upscale_models": self.models_dir / "upscale_models",
            "face_restore": self.models_dir / "face_restore",
            "ipadapter": self.models_dir / "ipadapter",
            "instantid": self.models_dir / "instantid",
            "insightface": self.models_dir / "insightface",
            "animatediff": self.models_dir / "animatediff",
            "vae": self.models_dir / "vae"
        }
        
        # Create directories
        for dir_path in self.model_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Load model sources from JSON
        self.model_sources = self._load_model_sources()
        
        # Recommended model setups
        self.recommended_setups = {
            "best_quality": {
                "name": "Best Quality Setup",
                "description": "Maximum quality for production content",
                "primary_model": "Flux_Dev",
                "face_consistency": "InstantID",
                "upscaling": "4x_UltraSharp",
                "face_restoration": "CodeFormer",
                "control": "ControlNet_OpenPose"
            },
            "best_speed": {
                "name": "Best Speed Setup",
                "description": "Fastest generation for batch processing",
                "primary_model": "Flux_Schnell",
                "face_consistency": "IP_Adapter_Plus",
                "upscaling": "RealESRGAN",
                "face_restoration": "GFPGAN",
                "control": "ControlNet_OpenPose"
            },
            "balanced": {
                "name": "Balanced Setup",
                "description": "Best quality/speed balance",
                "primary_model": "Realistic_Vision_V6",
                "face_consistency": "IP_Adapter_Plus",
                "upscaling": "RealESRGAN",
                "face_restoration": "GFPGAN",
                "control": "ControlNet_OpenPose"
            },
            "instagram": {
                "name": "Instagram Content",
                "description": "Optimized for Instagram posts",
                "primary_model": "Realistic_Vision_V6",
                "face_consistency": "InstantID",
                "upscaling": "RealESRGAN",
                "aspect_ratio": "1:1 or 4:5"
            },
            "onlyfans": {
                "name": "OnlyFans Content",
                "description": "Premium quality for OnlyFans",
                "primary_model": "Flux_Dev",
                "face_consistency": "InstantID",
                "upscaling": "4x_UltraSharp",
                "face_restoration": "CodeFormer",
                "aspect_ratio": "9:16 or 16:9"
            },
            "video": {
                "name": "Video Generation",
                "description": "High-quality video content",
                "video_model": "Stable_Video_Diffusion",
                "face_consistency": "IP_Adapter_Plus",
                "upscaling": "RealESRGAN",
                "resolution": "1080p minimum"
            }
        }
    
    def _load_model_sources(self) -> Dict[str, Any]:
        """Load model sources from MODEL_SOURCES.json"""
        try:
            sources_file = self.root_path / "MODEL_SOURCES.json"
            if sources_file.exists():
                with open(sources_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading MODEL_SOURCES.json: {e}")
        
        return {}
    
    def list_all_models(self, category: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List all models organized by category"""
        result = {
            "image_models": [],
            "video_models": [],
            "face_consistency": [],
            "post_processing": [],
            "controlnet": []
        }
        
        # Image models (checkpoints)
        if not category or category == "image":
            result["image_models"] = self._list_models_in_category("Image_Models", "checkpoints")
        
        # Video models
        if not category or category == "video":
            result["video_models"] = self._list_models_in_category("Video_Models", "checkpoints", ["animatediff"])
        
        # Face consistency
        if not category or category == "face":
            result["face_consistency"] = self._list_models_in_category("Face_Consistency", ["instantid", "ipadapter", "insightface"])
        
        # Post-processing
        if not category or category == "post_processing":
            result["post_processing"] = self._list_models_in_category("Post_Processing", ["upscale_models", "face_restore"])
        
        # ControlNet
        if not category or category == "controlnet":
            result["controlnet"] = self._list_models_in_category("ControlNet", "controlnet")
        
        return result
    
    def _list_models_in_category(self, category_key: str, dir_keys: Any, additional_dirs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """List models in a specific category"""
        models = []
        
        if category_key not in self.model_sources:
            return models
        
        category_data = self.model_sources[category_key]
        
        # Determine directories to search
        if isinstance(dir_keys, str):
            dirs_to_search = [self.model_dirs.get(dir_keys, self.models_dir / dir_keys)]
        else:
            dirs_to_search = [self.model_dirs.get(d, self.models_dir / d) for d in dir_keys]
        
        if additional_dirs:
            dirs_to_search.extend([self.model_dirs.get(d, self.models_dir / d) for d in additional_dirs])
        
        # Iterate through model definitions
        for model_key, model_info in category_data.items():
            if model_key.startswith("_"):
                continue
            
            # Find model file
            target_path = self.root_path / model_info.get("target", "")
            installed = target_path.exists() if target_path else False
            
            # Get file size if installed
            size_gb = 0.0
            if installed and target_path.exists():
                try:
                    size_gb = target_path.stat().st_size / (1024**3)
                except:
                    pass
            
            model_data = {
                "key": model_key,
                "name": model_info.get("description", model_key),
                "description": model_info.get("description", ""),
                "source": model_info.get("source", ""),
                "url": model_info.get("url", ""),
                "target": model_info.get("target", ""),
                "installed": installed,
                "installed_path": str(target_path) if installed else None,
                "size_gb": round(size_gb, 2) if installed else model_info.get("size_gb", 0),
                "quality": model_info.get("quality", 0),
                "speed": model_info.get("speed", ""),
                "vram_min": model_info.get("vram_min", 0),
                "priority": model_info.get("priority", "low"),
                "required": model_info.get("required", False),
                "tier": model_info.get("tier", 0),
                "category": category_key
            }
            
            models.append(model_data)
        
        return models
    
    def get_model_info(self, model_key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model"""
        # Search all categories
        for category_key in ["Image_Models", "Video_Models", "Face_Consistency", "Post_Processing", "ControlNet"]:
            if category_key in self.model_sources:
                if model_key in self.model_sources[category_key]:
                    model_info = self.model_sources[category_key][model_key]
                    target_path = self.root_path / model_info.get("target", "")
                    installed = target_path.exists() if target_path else False
                    
                    size_gb = 0.0
                    if installed and target_path.exists():
                        try:
                            size_gb = target_path.stat().st_size / (1024**3)
                        except:
                            pass
                    
                    return {
                        "key": model_key,
                        "name": model_info.get("description", model_key),
                        "description": model_info.get("description", ""),
                        "source": model_info.get("source", ""),
                        "url": model_info.get("url", ""),
                        "target": model_info.get("target", ""),
                        "installed": installed,
                        "installed_path": str(target_path) if installed else None,
                        "size_gb": round(size_gb, 2) if installed else model_info.get("size_gb", 0),
                        "quality": model_info.get("quality", 0),
                        "speed": model_info.get("speed", ""),
                        "vram_min": model_info.get("vram_min", 0),
                        "priority": model_info.get("priority", "low"),
                        "required": model_info.get("required", False),
                        "tier": model_info.get("tier", 0),
                        "category": category_key,
                        "dependency": model_info.get("dependency"),
                        "auto_download": model_info.get("auto_download", False)
                    }
        
        return None
    
    def get_recommended_setups(self) -> Dict[str, Dict[str, Any]]:
        """Get recommended model setups"""
        return self.recommended_setups
    
    def get_setup_recommendation(self, use_case: str) -> Optional[Dict[str, Any]]:
        """Get model setup recommendation for a specific use case"""
        use_case_lower = use_case.lower()
        
        # Map use cases to setups
        use_case_map = {
            "instagram": "instagram",
            "onlyfans": "onlyfans",
            "video": "video",
            "quality": "best_quality",
            "speed": "best_speed",
            "balanced": "balanced",
            "fast": "best_speed",
            "best": "best_quality"
        }
        
        setup_key = use_case_map.get(use_case_lower, "balanced")
        return self.recommended_setups.get(setup_key)
    
    def verify_model(self, model_key: str) -> Dict[str, Any]:
        """Verify model installation and integrity"""
        result = {
            "valid": False,
            "exists": False,
            "size_matches": False,
            "error": None,
            "model_key": model_key
        }
        
        model_info = self.get_model_info(model_key)
        if not model_info:
            result["error"] = f"Model not found: {model_key}"
            return result
        
        target_path = Path(model_info["target"]) if model_info.get("target") else None
        if not target_path:
            result["error"] = "No target path specified"
            return result
        
        full_path = self.root_path / target_path
        result["exists"] = full_path.exists()
        
        if not result["exists"]:
            result["error"] = "Model file not found"
            return result
        
        # Check file size
        try:
            actual_size = full_path.stat().st_size / (1024**3)
            expected_size = model_info.get("size_gb", 0)
            
            if expected_size > 0:
                # Allow 10% variance
                if abs(actual_size - expected_size) / expected_size < 0.1:
                    result["size_matches"] = True
                else:
                    result["error"] = f"Size mismatch: expected {expected_size}GB, got {actual_size:.2f}GB"
            else:
                result["size_matches"] = True
            
            # Check file extension
            if full_path.suffix in [".safetensors", ".ckpt", ".pth", ".bin", ".onnx"]:
                result["valid"] = True
            else:
                result["error"] = f"Invalid file extension: {full_path.suffix}"
        
        except Exception as e:
            logger.error(f"Model verification error: {e}")
            result["error"] = str(e)
        
        return result
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get comprehensive storage information"""
        result = {
            "models_dir": str(self.models_dir),
            "directories": {},
            "total_size_gb": 0.0,
            "total_models": 0,
            "available_space_gb": 0.0,
            "by_category": {}
        }
        
        try:
            # Get disk usage
            stat = shutil.disk_usage(self.models_dir)
            result["available_space_gb"] = round(stat.free / (1024**3), 2)
            
            # Calculate sizes by directory
            for dir_name, dir_path in self.model_dirs.items():
                if dir_path.exists():
                    total_size = 0
                    file_count = 0
                    
                    for file in dir_path.rglob("*"):
                        if file.is_file():
                            try:
                                total_size += file.stat().st_size
                                file_count += 1
                            except:
                                pass
                    
                    size_gb = total_size / (1024**3)
                    result["directories"][dir_name] = {
                        "path": str(dir_path),
                        "size_gb": round(size_gb, 2),
                        "file_count": file_count
                    }
                    result["total_size_gb"] += size_gb
                    result["total_models"] += file_count
            
            # Calculate by category
            all_models = self.list_all_models()
            for category, models in all_models.items():
                category_size = sum(m.get("size_gb", 0) for m in models if m.get("installed"))
                result["by_category"][category] = {
                    "count": len([m for m in models if m.get("installed")]),
                    "total_size_gb": round(category_size, 2)
                }
            
            result["total_size_gb"] = round(result["total_size_gb"], 2)
        
        except Exception as e:
            logger.error(f"Storage info error: {e}")
            result["error"] = str(e)
        
        return result
    
    def get_download_status(self) -> Dict[str, Any]:
        """Get download status for all models"""
        result = {
            "total": 0,
            "installed": 0,
            "missing": 0,
            "required_installed": 0,
            "required_missing": 0,
            "by_category": {},
            "missing_required": []
        }
        
        all_models = self.list_all_models()
        
        for category, models in all_models.items():
            category_stats = {
                "total": len(models),
                "installed": 0,
                "missing": 0,
                "required_installed": 0,
                "required_missing": 0
            }
            
            for model in models:
                result["total"] += 1
                if model.get("installed"):
                    result["installed"] += 1
                    category_stats["installed"] += 1
                    if model.get("required"):
                        result["required_installed"] += 1
                        category_stats["required_installed"] += 1
                else:
                    result["missing"] += 1
                    category_stats["missing"] += 1
                    if model.get("required"):
                        result["required_missing"] += 1
                        category_stats["required_missing"] += 1
                        result["missing_required"].append({
                            "key": model.get("key"),
                            "name": model.get("name"),
                            "category": category
                        })
            
            result["by_category"][category] = category_stats
        
        return result
    
    def list_installed_models(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List only installed models"""
        all_models = self.list_all_models(category)
        installed = []
        
        for category_models in all_models.values():
            installed.extend([m for m in category_models if m.get("installed")])
        
        return installed
    
    def delete_model(self, model_key: str) -> Dict[str, Any]:
        """Delete a model file"""
        result = {
            "success": False,
            "model_key": model_key,
            "error": None
        }
        
        model_info = self.get_model_info(model_key)
        if not model_info:
            result["error"] = f"Model not found: {model_key}"
            return result
        
        if not model_info.get("installed"):
            result["error"] = "Model not installed"
            return result
        
        target_path = Path(model_info["installed_path"])
        if not target_path.exists():
            result["error"] = "Model file not found"
            return result
        
        try:
            target_path.unlink()
            result["success"] = True
        except Exception as e:
            logger.error(f"Model deletion error: {e}")
            result["error"] = str(e)
        
        return result
