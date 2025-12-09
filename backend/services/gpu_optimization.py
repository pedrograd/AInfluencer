"""
GPU Optimization Service
Manages GPU memory and performance optimization
"""
import logging
import os
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GPUOptimizationService:
    """Service for GPU optimization and monitoring"""
    
    def __init__(self):
        self.gpu_available = self._check_gpu_available()
        self.memory_fraction = float(os.getenv("GPU_MEMORY_FRACTION", "0.9"))
    
    def _check_gpu_available(self) -> bool:
        """Check if GPU is available"""
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        if not self.gpu_available:
            return {
                "available": False,
                "error": "GPU not available"
            }
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu,utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {"available": True, "error": "Failed to query GPU"}
            
            # Parse output
            lines = result.stdout.strip().split('\n')
            gpus = []
            for line in lines:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 6:
                    gpus.append({
                        "name": parts[0],
                        "memory_total_mb": int(parts[1]),
                        "memory_used_mb": int(parts[2]),
                        "memory_free_mb": int(parts[3]),
                        "temperature_c": int(parts[4]),
                        "utilization_percent": int(parts[5])
                    })
            
            return {
                "available": True,
                "gpus": gpus,
                "count": len(gpus)
            }
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
            return {"available": True, "error": str(e)}
    
    def optimize_memory(self):
        """Optimize GPU memory usage"""
        if not self.gpu_available:
            return False
        
        try:
            import torch
            if torch.cuda.is_available():
                # Set memory fraction
                torch.cuda.set_per_process_memory_fraction(self.memory_fraction)
                
                # Clear cache
                torch.cuda.empty_cache()
                
                logger.info(f"GPU memory optimized: fraction={self.memory_fraction}")
                return True
        except ImportError:
            logger.warning("PyTorch not available for GPU optimization")
        except Exception as e:
            logger.error(f"Error optimizing GPU memory: {e}")
        
        return False
    
    def clear_cache(self):
        """Clear GPU cache"""
        if not self.gpu_available:
            return False
        
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                return True
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Error clearing GPU cache: {e}")
        
        return False
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get GPU memory statistics"""
        info = self.get_gpu_info()
        if not info.get("available") or "gpus" not in info:
            return {"error": "GPU not available"}
        
        total_memory = sum(gpu["memory_total_mb"] for gpu in info["gpus"])
        used_memory = sum(gpu["memory_used_mb"] for gpu in info["gpus"])
        free_memory = sum(gpu["memory_free_mb"] for gpu in info["gpus"])
        
        return {
            "total_mb": total_memory,
            "used_mb": used_memory,
            "free_mb": free_memory,
            "usage_percent": (used_memory / total_memory * 100) if total_memory > 0 else 0,
            "gpu_count": len(info["gpus"])
        }

# Global instance
gpu_optimization = GPUOptimizationService()
