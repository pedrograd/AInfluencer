"""
Performance Optimizer
Handles parallel processing, caching, and resource management
"""
import logging
from typing import Dict, Optional, Any, List, Callable
from functools import lru_cache, partial
from multiprocessing import Pool, cpu_count
import time
import threading

logger = logging.getLogger(__name__)

class ResourceManager:
    """Manages system resources"""
    
    def __init__(self, max_gpu_memory: float = 0.8):
        self.max_gpu_memory = max_gpu_memory
        self.lock = threading.Lock()
    
    def check_resources(self) -> bool:
        """Check if resources are available"""
        try:
            # TODO: Implement actual GPU memory checking
            # For now, return True
            return True
        except Exception as e:
            logger.warning(f"Error checking resources: {e}")
            return True
    
    def wait_for_resources(self, timeout: int = 300):
        """Wait for resources to become available"""
        start_time = time.time()
        while not self.check_resources():
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout waiting for resources")
            time.sleep(10)

class PerformanceOptimizer:
    """Service for performance optimization"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or min(cpu_count(), 4)
        self.resource_manager = ResourceManager()
    
    def parallel_generate(
        self,
        prompts: List[str],
        generator_func: Callable,
        **kwargs
    ) -> List[Any]:
        """
        Generate content in parallel
        
        Args:
            prompts: List of prompts
            generator_func: Function to generate content
            **kwargs: Additional parameters
        
        Returns:
            List of generated content
        """
        if len(prompts) == 1:
            # Single item, no need for parallel processing
            return [generator_func(prompts[0], **kwargs)]
        
        # Wait for resources
        self.resource_manager.wait_for_resources()
        
        # Process in parallel
        with Pool(processes=self.max_workers) as pool:
            worker = partial(generator_func, **kwargs)
            results = pool.map(worker, prompts)
        
        return results
    
    def batch_process(
        self,
        items: List[Any],
        processor_func: Callable,
        batch_size: int = 4,
        **kwargs
    ) -> List[Any]:
        """
        Process items in batches
        
        Args:
            items: List of items to process
            processor_func: Function to process items
            batch_size: Number of items per batch
            **kwargs: Additional parameters
        
        Returns:
            List of processed items
        """
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Wait for resources before each batch
            self.resource_manager.wait_for_resources()
            
            # Process batch
            batch_results = [
                processor_func(item, **kwargs)
                for item in batch
            ]
            
            results.extend(batch_results)
        
        return results

# Caching utilities
@lru_cache(maxsize=100)
def cached_generation(prompt_hash: str) -> Any:
    """Cache expensive generation operations"""
    # This would be used with a hash of the prompt
    # For now, it's a placeholder
    return None

def get_prompt_hash(prompt: str, settings: Dict[str, Any]) -> str:
    """Generate hash for prompt caching"""
    import hashlib
    import json
    
    combined = f"{prompt}_{json.dumps(settings, sort_keys=True)}"
    return hashlib.md5(combined.encode()).hexdigest()
