"""
Robust Generator
Generation with retry logic and error handling
"""
import logging
from typing import Dict, Optional, Any, Callable
from functools import wraps
import time

try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False
    logger = logging.getLogger(__name__)
    logger.warning("tenacity not installed, using basic retry logic")

logger = logging.getLogger(__name__)

class RobustGenerator:
    """Generator with retry logic and error handling"""
    
    def __init__(
        self,
        generator: Any,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0
    ):
        self.generator = generator
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def generate_with_retry(
        self,
        prompt: str,
        **kwargs
    ) -> Any:
        """
        Generate with automatic retry on failure
        
        Args:
            prompt: Generation prompt
            **kwargs: Additional generation parameters
        
        Returns:
            Generated content
        """
        if HAS_TENACITY:
            return self._generate_with_tenacity(prompt, **kwargs)
        else:
            return self._generate_with_basic_retry(prompt, **kwargs)
    
    def _generate_with_tenacity(self, prompt: str, **kwargs) -> Any:
        """Generate with tenacity retry decorator"""
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=self.base_delay, min=self.base_delay, max=self.max_delay),
            reraise=True
        )
        def _generate():
            try:
                return self.generator.generate(prompt, **kwargs)
            except Exception as e:
                logger.warning(f"Generation failed: {e}, retrying...")
                raise
        
        return _generate()
    
    def _generate_with_basic_retry(self, prompt: str, **kwargs) -> Any:
        """Generate with basic retry logic"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return self.generator.generate(prompt, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = min(
                        self.base_delay * (2 ** attempt),
                        self.max_delay
                    )
                    logger.warning(
                        f"Generation failed (attempt {attempt + 1}/{self.max_retries}): {e}, "
                        f"retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Generation failed after {self.max_retries} attempts: {e}")
        
        raise last_error
    
    def generate_safe(
        self,
        prompt: str,
        fallback_handler: Optional[Callable] = None,
        **kwargs
    ) -> Optional[Any]:
        """
        Generate with safe error handling and fallback
        
        Args:
            prompt: Generation prompt
            fallback_handler: Function to call on failure
            **kwargs: Additional generation parameters
        
        Returns:
            Generated content or None if failed
        """
        try:
            return self.generate_with_retry(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Generation failed after retries: {e}")
            if fallback_handler:
                return fallback_handler(prompt, e, **kwargs)
            return None

def handle_errors(content: Any, error: Exception) -> Optional[Any]:
    """Handle different types of errors"""
    error_type = type(error).__name__
    
    error_handlers = {
        'TimeoutError': lambda c, e: retry_generation(c, e),
        'ConnectionError': lambda c, e: wait_and_retry(c, e),
        'ValueError': lambda c, e: reprocess_content(c, e),
        'QualityError': lambda c, e: reprocess_content(c, e),
    }
    
    handler = error_handlers.get(error_type)
    if handler:
        return handler(content, error)
    else:
        logger.error(f"Unknown error type: {error_type}")
        return None

def retry_generation(content: Any, error: Exception) -> Optional[Any]:
    """Retry generation"""
    logger.info("Retrying generation...")
    # Would retry the generation
    return None

def wait_and_retry(content: Any, error: Exception) -> Optional[Any]:
    """Wait and retry"""
    logger.info("Waiting and retrying...")
    time.sleep(5)
    # Would retry
    return None

def reprocess_content(content: Any, error: Exception) -> Optional[Any]:
    """Reprocess content"""
    logger.info("Reprocessing content...")
    # Would reprocess
    return None
