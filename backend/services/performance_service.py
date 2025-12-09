"""
Performance Service
Handles performance optimization, memory management, queue optimization
"""

import logging
import psutil
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import gc

logger = logging.getLogger(__name__)

class PerformanceService:
    """Service for performance monitoring and optimization"""
    
    def __init__(self):
        """Initialize performance service"""
        self.metrics_history = []
        self.max_history = 100
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024 ** 3)
            
            # GPU metrics (if available)
            gpu_info = self._get_gpu_info()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count
                },
                "memory": {
                    "percent": memory_percent,
                    "available_gb": round(memory_available_gb, 2),
                    "total_gb": round(memory_total_gb, 2),
                    "used_gb": round((memory_total_gb - memory_available_gb), 2)
                },
                "disk": {
                    "percent": disk_percent,
                    "free_gb": round(disk_free_gb, 2)
                },
                "gpu": gpu_info,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Get performance metrics error: {e}")
            return {"error": str(e)}
    
    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information if available"""
        try:
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines:
                    values = lines[0].split(', ')
                    return {
                        "available": True,
                        "memory_used_mb": int(values[0]) if len(values) > 0 else 0,
                        "memory_total_mb": int(values[1]) if len(values) > 1 else 0,
                        "utilization_percent": int(values[2]) if len(values) > 2 else 0
                    }
        except Exception:
            pass
        
        return {"available": False}
    
    def detect_bottlenecks(self) -> Dict[str, Any]:
        """Detect performance bottlenecks"""
        try:
            metrics = self.get_performance_metrics()
            bottlenecks = []
            
            # Check CPU
            if metrics.get("cpu", {}).get("percent", 0) > 90:
                bottlenecks.append({
                    "type": "cpu",
                    "severity": "high",
                    "message": "CPU usage is very high (>90%)",
                    "recommendation": "Reduce parallel generation jobs or upgrade CPU"
                })
            
            # Check memory
            if metrics.get("memory", {}).get("percent", 0) > 90:
                bottlenecks.append({
                    "type": "memory",
                    "severity": "high",
                    "message": "Memory usage is very high (>90%)",
                    "recommendation": "Clear cache, reduce batch size, or add more RAM"
                })
            
            # Check disk
            if metrics.get("disk", {}).get("percent", 0) > 90:
                bottlenecks.append({
                    "type": "disk",
                    "severity": "high",
                    "message": "Disk space is running low (>90% used)",
                    "recommendation": "Free up disk space or add more storage"
                })
            
            # Check GPU
            gpu = metrics.get("gpu", {})
            if gpu.get("available") and gpu.get("utilization_percent", 0) > 95:
                bottlenecks.append({
                    "type": "gpu",
                    "severity": "high",
                    "message": "GPU utilization is very high (>95%)",
                    "recommendation": "Reduce concurrent GPU operations"
                })
            
            return {
                "bottlenecks": bottlenecks,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Detect bottlenecks error: {e}")
            return {"error": str(e), "bottlenecks": []}
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get detailed memory usage"""
        try:
            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "system": {
                    "total_gb": round(memory.total / (1024 ** 3), 2),
                    "available_gb": round(memory.available / (1024 ** 3), 2),
                    "used_gb": round(memory.used / (1024 ** 3), 2),
                    "percent": memory.percent
                },
                "process": {
                    "rss_mb": round(process_memory.rss / (1024 ** 2), 2),
                    "vms_mb": round(process_memory.vms / (1024 ** 2), 2)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Get memory usage error: {e}")
            return {"error": str(e)}
    
    def optimize_batch_generation(self, batch_size: int, parallel_count: int) -> Dict[str, Any]:
        """Optimize batch generation parameters based on system resources"""
        try:
            metrics = self.get_performance_metrics()
            memory_gb = metrics.get("memory", {}).get("available_gb", 0)
            cpu_count = metrics.get("cpu", {}).get("count", 1)
            
            # Calculate optimal parameters
            optimal_batch_size = min(batch_size, max(1, int(memory_gb / 2)))  # 2GB per batch item
            optimal_parallel = min(parallel_count, max(1, cpu_count - 1))  # Leave 1 core free
            
            return {
                "original": {
                    "batch_size": batch_size,
                    "parallel_count": parallel_count
                },
                "optimized": {
                    "batch_size": optimal_batch_size,
                    "parallel_count": optimal_parallel
                },
                "reasoning": {
                    "memory_constraint": f"Available memory: {memory_gb}GB",
                    "cpu_constraint": f"CPU cores: {cpu_count}"
                }
            }
        except Exception as e:
            logger.error(f"Optimize batch generation error: {e}")
            return {"error": str(e)}
    
    def clear_cache(self, cache_type: Optional[str] = None) -> Dict[str, Any]:
        """Clear cache to free memory"""
        try:
            freed_mb = 0
            
            if cache_type is None or cache_type == "python":
                # Force Python garbage collection
                before = psutil.Process().memory_info().rss / (1024 ** 2)
                gc.collect()
                after = psutil.Process().memory_info().rss / (1024 ** 2)
                freed_mb = before - after
            
            return {
                "cache_type": cache_type or "all",
                "freed_mb": round(freed_mb, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Clear cache error: {e}")
            return {"error": str(e)}
    
    def optimize_queue(self, queue_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Optimize generation queue order for better performance"""
        try:
            # Sort by priority and estimated time
            def get_priority_score(item: Dict[str, Any]) -> float:
                priority_map = {"urgent": 4, "high": 3, "normal": 2, "low": 1}
                priority = item.get("priority", "normal")
                estimated_time = item.get("estimated_time", 60)
                
                # Higher priority = higher score, lower time = higher score
                return priority_map.get(priority, 2) * 1000 - estimated_time
            
            optimized = sorted(queue_items, key=get_priority_score, reverse=True)
            
            return {
                "original_count": len(queue_items),
                "optimized_order": optimized,
                "estimated_time_saved": "Calculated based on priority ordering"
            }
        except Exception as e:
            logger.error(f"Optimize queue error: {e}")
            return {"error": str(e)}
