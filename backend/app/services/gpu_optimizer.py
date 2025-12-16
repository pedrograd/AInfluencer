"""GPU utilization optimization service.

This service provides:
- GPU-aware batch size recommendations based on actual GPU memory availability
- Dynamic batch size optimization for better GPU utilization
- GPU memory management and cleanup suggestions
- Queue management optimization based on GPU utilization
"""

from __future__ import annotations

from app.services.resource_manager import ResourceManager, ResourceUsage


class GPUOptimizer:
    """Service for optimizing GPU utilization in image generation tasks."""

    def __init__(self, resource_manager: ResourceManager | None = None) -> None:
        """
        Initialize GPU optimizer.

        Args:
            resource_manager: Optional ResourceManager instance. Creates new one if not provided.
        """
        self.resource_manager = resource_manager or ResourceManager()

    def recommend_batch_size(
        self,
        width: int,
        height: int,
        batch_size: int | None = None,
        conservative: bool = True,
    ) -> dict[str, int | float | bool | str]:
        """
        Recommend optimal batch size based on actual GPU memory availability.

        Args:
            width: Image width in pixels
            height: Image height in pixels
            batch_size: Requested batch size (used as upper bound if provided)
            conservative: If True, uses conservative memory estimates. If False, uses aggressive estimates.

        Returns:
            Dictionary with:
                - recommended_batch_size: Recommended batch size (1-8)
                - can_use_requested: Whether requested batch_size can be used safely
                - gpu_memory_available_gb: Available GPU memory in GB
                - gpu_memory_total_gb: Total GPU memory in GB
                - estimated_memory_per_image_gb: Estimated memory per image in GB
                - reason: Explanation for the recommendation
        """
        usage = self.resource_manager.get_current_usage()

        # If GPU not available, use conservative defaults
        if not usage.gpu_available or usage.gpu_memory_total_gb is None:
            safe_size = min(batch_size or 1, 1)
            return {
                "recommended_batch_size": safe_size,
                "can_use_requested": batch_size is None or batch_size <= 1,
                "gpu_memory_available_gb": None,
                "gpu_memory_total_gb": None,
                "estimated_memory_per_image_gb": None,
                "reason": "GPU not available - using conservative batch size of 1",
            }

        total_memory_gb = usage.gpu_memory_total_gb
        used_memory_gb = usage.gpu_memory_used_gb or 0.0
        available_memory_gb = max(0.0, total_memory_gb - used_memory_gb)

        # Estimate memory per image (conservative: 4 bytes per pixel, plus overhead)
        # Conservative: ~4-6GB overhead for model weights, activations, etc.
        # Aggressive: ~2-3GB overhead
        base_overhead_gb = 5.0 if conservative else 3.0
        memory_per_pixel_gb = 4.0 / (1024**3)  # 4 bytes per pixel in GB
        pixel_count = width * height
        estimated_per_image_gb = (pixel_count * memory_per_pixel_gb) + (
            base_overhead_gb / 8
        )  # Divide overhead across images in batch

        # Reserve 15% of total memory for system/OS/other processes
        reserved_memory_gb = total_memory_gb * 0.15
        usable_memory_gb = available_memory_gb - reserved_memory_gb

        # Calculate max safe batch size
        if estimated_per_image_gb <= 0:
            max_safe_batch = 1
        else:
            max_safe_batch = int(usable_memory_gb / estimated_per_image_gb)
            max_safe_batch = max(1, min(max_safe_batch, 8))  # Clamp to 1-8

        # If batch_size is provided, check if it's safe
        requested = batch_size or 1
        can_use_requested = requested <= max_safe_batch

        # Recommend optimal batch size (prefer requested if safe, otherwise max safe)
        recommended = min(requested, max_safe_batch) if requested > 0 else max_safe_batch

        # Generate reason
        if not can_use_requested:
            reason = (
                f"Requested batch_size={requested} exceeds safe limit. "
                f"Available GPU memory: {available_memory_gb:.1f}GB (reserved: {reserved_memory_gb:.1f}GB). "
                f"Estimated memory per image: {estimated_per_image_gb:.2f}GB. "
                f"Recommended: {recommended}"
            )
        elif recommended == requested:
            reason = (
                f"Requested batch_size={requested} is safe. "
                f"Available GPU memory: {available_memory_gb:.1f}GB. "
                f"Estimated memory per image: {estimated_per_image_gb:.2f}GB"
            )
        else:
            reason = (
                f"Optimized batch_size to {recommended} for better GPU utilization. "
                f"Available GPU memory: {available_memory_gb:.1f}GB. "
                f"Estimated memory per image: {estimated_per_image_gb:.2f}GB"
            )

        return {
            "recommended_batch_size": recommended,
            "can_use_requested": can_use_requested,
            "gpu_memory_available_gb": round(available_memory_gb, 2),
            "gpu_memory_total_gb": round(total_memory_gb, 2),
            "estimated_memory_per_image_gb": round(estimated_per_image_gb, 2),
            "reason": reason,
        }

    def should_wait_for_gpu(self, min_memory_gb: float = 2.0) -> dict[str, bool | float | str]:
        """
        Check if we should wait for GPU memory to free up before starting new generation.

        Args:
            min_memory_gb: Minimum required GPU memory in GB to proceed.

        Returns:
            Dictionary with:
                - should_wait: Whether to wait for GPU memory
                - current_available_gb: Currently available GPU memory in GB
                - min_required_gb: Minimum required GPU memory in GB
                - reason: Explanation
        """
        usage = self.resource_manager.get_current_usage()

        if not usage.gpu_available or usage.gpu_memory_total_gb is None:
            return {
                "should_wait": False,
                "current_available_gb": None,
                "min_required_gb": min_memory_gb,
                "reason": "GPU not available - cannot determine wait status",
            }

        total_memory_gb = usage.gpu_memory_total_gb
        used_memory_gb = usage.gpu_memory_used_gb or 0.0
        available_memory_gb = max(0.0, total_memory_gb - used_memory_gb)

        should_wait = available_memory_gb < min_memory_gb

        if should_wait:
            reason = (
                f"Insufficient GPU memory. Available: {available_memory_gb:.1f}GB, "
                f"Required: {min_memory_gb:.1f}GB. Consider waiting or reducing batch size."
            )
        else:
            reason = (
                f"Sufficient GPU memory available: {available_memory_gb:.1f}GB "
                f"(required: {min_memory_gb:.1f}GB)"
            )

        return {
            "should_wait": should_wait,
            "current_available_gb": round(available_memory_gb, 2),
            "min_required_gb": min_memory_gb,
            "reason": reason,
        }

    def get_utilization_status(self) -> dict[str, float | bool | str]:
        """
        Get current GPU utilization status for optimization decisions.

        Returns:
            Dictionary with GPU utilization metrics and recommendations.
        """
        usage = self.resource_manager.get_current_usage()

        if not usage.gpu_available:
            return {
                "gpu_available": False,
                "utilization_percent": None,
                "memory_used_percent": None,
                "status": "unavailable",
                "recommendation": "GPU not available",
            }

        utilization = usage.gpu_utilization_percent or 0.0

        memory_percent = None
        if usage.gpu_memory_used_gb is not None and usage.gpu_memory_total_gb is not None:
            if usage.gpu_memory_total_gb > 0:
                memory_percent = (usage.gpu_memory_used_gb / usage.gpu_memory_total_gb) * 100

        # Determine status and recommendation
        if utilization < 50 and (memory_percent is None or memory_percent < 50):
            status = "underutilized"
            recommendation = "GPU is underutilized - can handle larger batches or more concurrent jobs"
        elif utilization > 90 or (memory_percent is not None and memory_percent > 90):
            status = "overutilized"
            recommendation = (
                "GPU is highly utilized - consider smaller batches or waiting for current jobs to complete"
            )
        else:
            status = "optimal"
            recommendation = "GPU utilization is in optimal range"

        return {
            "gpu_available": True,
            "utilization_percent": round(utilization, 1),
            "memory_used_percent": round(memory_percent, 1) if memory_percent is not None else None,
            "status": status,
            "recommendation": recommendation,
        }


# Global instance for easy import
_gpu_optimizer: GPUOptimizer | None = None


def get_gpu_optimizer() -> GPUOptimizer:
    """Get or create global GPU optimizer instance."""
    global _gpu_optimizer
    if _gpu_optimizer is None:
        _gpu_optimizer = GPUOptimizer()
    return _gpu_optimizer

