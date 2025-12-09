"""
Performance Monitor Service
Implements performance best practices monitoring and optimization
"""
import logging
import time
import psutil
import GPUtil
from typing import Dict, Any, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor system performance and enforce best practices"""
    
    def __init__(self):
        self.metrics_history: deque = deque(maxlen=1000)
        self.gpu_available = False
        
        # Try to detect GPU
        try:
            gpus = GPUtil.getGPUs()
            self.gpu_available = len(gpus) > 0
            if self.gpu_available:
                self.gpu = gpus[0]
                logger.info(f"GPU detected: {self.gpu.name}")
        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")
            self.gpu_available = False
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": psutil.cpu_percent(interval=0.1),
                "count": psutil.cpu_count(),
                "frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
                "used": psutil.virtual_memory().used
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            }
        }
        
        # GPU metrics if available
        if self.gpu_available:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    metrics["gpu"] = {
                        "name": gpu.name,
                        "memory_total": gpu.memoryTotal,
                        "memory_used": gpu.memoryUsed,
                        "memory_free": gpu.memoryFree,
                        "memory_percent": (gpu.memoryUsed / gpu.memoryTotal) * 100,
                        "temperature": gpu.temperature,
                        "load": gpu.load * 100
                    }
            except Exception as e:
                logger.warning(f"Failed to get GPU metrics: {e}")
        
        # Store in history
        self.metrics_history.append(metrics)
        
        return metrics
    
    def check_performance_issues(self) -> Dict[str, Any]:
        """Check for performance issues based on best practices"""
        metrics = self.get_system_metrics()
        issues = []
        recommendations = []
        
        # CPU check
        if metrics["cpu"]["percent"] > 90:
            issues.append({
                "type": "high_cpu",
                "severity": "high",
                "message": f"CPU usage is {metrics['cpu']['percent']:.1f}%",
                "recommendation": "Reduce concurrent operations or optimize code"
            })
        
        # Memory check
        if metrics["memory"]["percent"] > 90:
            issues.append({
                "type": "high_memory",
                "severity": "critical",
                "message": f"Memory usage is {metrics['memory']['percent']:.1f}%",
                "recommendation": "Clear cache or reduce batch sizes"
            })
        
        # GPU check
        if "gpu" in metrics:
            gpu_mem_percent = metrics["gpu"]["memory_percent"]
            if gpu_mem_percent > 90:
                issues.append({
                    "type": "high_gpu_memory",
                    "severity": "critical",
                    "message": f"GPU memory usage is {gpu_mem_percent:.1f}%",
                    "recommendation": "Clear GPU cache, reduce batch size, or optimize memory usage"
                })
            
            if metrics["gpu"]["temperature"] > 85:
                issues.append({
                    "type": "high_gpu_temperature",
                    "severity": "high",
                    "message": f"GPU temperature is {metrics['gpu']['temperature']}°C",
                    "recommendation": "Check cooling, reduce load, or pause intensive operations"
                })
        
        # Disk check
        if metrics["disk"]["percent"] > 90:
            issues.append({
                "type": "low_disk_space",
                "severity": "high",
                "message": f"Disk usage is {metrics['disk']['percent']:.1f}%",
                "recommendation": "Free up disk space or expand storage"
            })
        
        return {
            "metrics": metrics,
            "issues": issues,
            "healthy": len(issues) == 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def optimize_gpu_memory(self) -> bool:
        """Attempt to optimize GPU memory usage"""
        if not self.gpu_available:
            return False
        
        try:
            # This would typically clear CUDA cache
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("GPU cache cleared")
                return True
        except ImportError:
            logger.warning("PyTorch not available for GPU optimization")
        except Exception as e:
            logger.error(f"Failed to optimize GPU memory: {e}")
        
        return False
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        check = self.check_performance_issues()
        
        # Calculate averages from history
        if len(self.metrics_history) > 0:
            recent_metrics = list(self.metrics_history)[-100:]  # Last 100 samples
            
            avg_cpu = sum(m["cpu"]["percent"] for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m["memory"]["percent"] for m in recent_metrics) / len(recent_metrics)
            
            report = {
                **check,
                "averages": {
                    "cpu_percent": avg_cpu,
                    "memory_percent": avg_memory
                },
                "sample_count": len(recent_metrics)
            }
        else:
            report = check
        
        return report
