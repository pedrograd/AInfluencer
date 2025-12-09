"""
GPU Optimization Service
Manages GPU memory and performance optimization
"""
import logging
import os
from typing import Dict, Any, Optional
import torch

logger = logging.getLogger(__name__)

class GPUOptimizationService:
    """Service for GPU optimization and memory management"""
    
    def __init__(self):
        self.gpu_available = torch.cuda.is_available()
        self.gpu_count = torch.cuda.device_count() if self.gpu_available else 0
        self.memory_fraction = float(os.getenv("GPU_MEMORY_FRACTION", "0.9"))
        
        if self.gpu_available:
            self._configure_gpu()
    
    def _configure_gpu(self):
        """Configure GPU settings"""
        try:
            # Set memory fraction
            torch.cuda.set_per_process_memory_fraction(self.memory_fraction)
            logger.info(f"GPU memory fraction set to {self.memory_fraction}")
        except Exception as e:
            logger.warning(f"Failed to set GPU memory fraction: {e}")
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        if not self.gpu_available:
            return {
                "available": False,
                "count": 0
            }
        
        info = {
            "available": True,
            "count": self.gpu_count,
            "devices": []
        }
        
        for i in range(self.gpu_count):
            device_info = {
                "index": i,
                "name": torch.cuda.get_device_name(i),
                "memory_total": torch.cuda.get_device_properties(i).total_memory,
                "memory_allocated": torch.cuda.memory_allocated(i),
                "memory_reserved": torch.cuda.memory_reserved(i),
                "memory_free": torch.cuda.get_device_properties(i).total_memory - torch.cuda.memory_reserved(i)
            }
            info["devices"].append(device_info)
        
        return info
    
    def clear_cache(self, device: Optional[int] = None):
        """Clear GPU cache"""
        if not self.gpu_available:
            return
        
        try:
            if device is not None:
                with torch.cuda.device(device):
                    torch.cuda.empty_cache()
            else:
                torch.cuda.empty_cache()
            logger.debug("GPU cache cleared")
        except Exception as e:
            logger.error(f"Failed to clear GPU cache: {e}")
    
    def optimize_for_batch(self, batch_size: int) -> Dict[str, Any]:
        """Optimize GPU settings for batch processing"""
        if not self.gpu_available:
            return {"optimized": False, "reason": "GPU not available"}
        
        recommendations = {
            "optimized": True,
            "batch_size": batch_size,
            "recommendations": []
        }
        
        # Get GPU memory info
        gpu_info = self.get_gpu_info()
        if gpu_info["devices"]:
            device = gpu_info["devices"][0]
            free_memory = device["memory_free"]
            
            # Estimate memory per item (rough estimate)
            estimated_memory_per_item = 500 * 1024 * 1024  # 500MB per item
            
            max_batch = int(free_memory / estimated_memory_per_item)
            
            if batch_size > max_batch:
                recommendations["recommendations"].append(
                    f"Reduce batch size from {batch_size} to {max_batch} for available memory"
                )
                recommendations["optimal_batch_size"] = max_batch
            else:
                recommendations["optimal_batch_size"] = batch_size
        
        return recommendations
    
    def use_mixed_precision(self) -> bool:
        """Check if mixed precision should be used"""
        return os.getenv("USE_MIXED_PRECISION", "true").lower() == "true"
    
    def get_autocast_context(self):
        """Get autocast context for mixed precision"""
        if not self.gpu_available:
            return None
        
        if self.use_mixed_precision():
            return torch.cuda.amp.autocast()
        return None

# Global instance
gpu_optimization_service = GPUOptimizationService()
