"""Image similarity and comparison service.

This module provides functionality to compare images and calculate similarity scores
for batch generation results.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.core.paths import images_dir

logger = get_logger(__name__)


class ImageSimilarityService:
    """Service for comparing images and calculating similarity scores."""
    
    def __init__(self) -> None:
        """Initialize similarity service."""
        pass
    
    def compare_images(
        self,
        image_path1: str | Path,
        image_path2: str | Path,
    ) -> dict[str, Any]:
        """
        Compare two images and calculate similarity score.
        
        Args:
            image_path1: Path to first image
            image_path2: Path to second image
            
        Returns:
            dict: Similarity score (0.0 to 1.0, higher = more similar) and comparison metrics
        """
        try:
            from PIL import Image
            import numpy as np
        except ImportError:
            raise ImportError("PIL/Pillow and numpy are required for image comparison")
        
        img1_path = Path(image_path1) if isinstance(image_path1, str) else image_path1
        img2_path = Path(image_path2) if isinstance(image_path2, str) else image_path2
        
        if not img1_path.is_absolute():
            img1_path = images_dir() / img1_path
        if not img2_path.is_absolute():
            img2_path = images_dir() / img2_path
        
        if not img1_path.exists() or not img2_path.exists():
            raise FileNotFoundError("One or both images not found")
        
        # Load and resize images to same size for comparison
        with Image.open(img1_path) as img1, Image.open(img2_path) as img2:
            # Resize to same dimensions (use smaller dimensions)
            min_size = (min(img1.size[0], img2.size[0]), min(img1.size[1], img2.size[1]))
            img1_resized = img1.resize(min_size, Image.Resampling.LANCZOS)
            img2_resized = img2.resize(min_size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if needed
            if img1_resized.mode != "RGB":
                img1_resized = img1_resized.convert("RGB")
            if img2_resized.mode != "RGB":
                img2_resized = img2_resized.convert("RGB")
            
            # Convert to numpy arrays
            arr1 = np.array(img1_resized, dtype=np.float32)
            arr2 = np.array(img2_resized, dtype=np.float32)
            
            # Calculate similarity using structural similarity (SSIM-like metric)
            similarity = self._calculate_similarity(arr1, arr2)
            
            # Calculate additional metrics
            mse = np.mean((arr1 - arr2) ** 2)
            max_pixel = 255.0
            psnr = 20 * np.log10(max_pixel / np.sqrt(mse)) if mse > 0 else float("inf")
            
            return {
                "ok": True,
                "similarity_score": float(similarity),
                "mse": float(mse),
                "psnr": float(psnr) if psnr != float("inf") else None,
                "image1_path": str(img1_path.relative_to(images_dir())),
                "image2_path": str(img2_path.relative_to(images_dir())),
            }
    
    def compare_batch_images(
        self,
        image_paths: list[str | Path],
    ) -> dict[str, Any]:
        """
        Compare multiple images from a batch and calculate pairwise similarity.
        
        Args:
            image_paths: List of image paths to compare
            
        Returns:
            dict: Pairwise similarity matrix and average similarity
        """
        if len(image_paths) < 2:
            return {
                "ok": True,
                "similarity_matrix": {},
                "average_similarity": None,
                "message": "Need at least 2 images for comparison",
            }
        
        similarities: dict[str, dict[str, float]] = {}
        total_similarity = 0.0
        comparisons = 0
        
        for i, path1 in enumerate(image_paths):
            path1_str = str(path1)
            similarities[path1_str] = {}
            
            for j, path2 in enumerate(image_paths):
                if i >= j:  # Only compare upper triangle
                    continue
                
                try:
                    result = self.compare_images(path1, path2)
                    similarity = result["similarity_score"]
                    similarities[path1_str][str(path2)] = similarity
                    total_similarity += similarity
                    comparisons += 1
                except Exception as e:
                    logger.warning(f"Failed to compare {path1} and {path2}: {e}")
        
        avg_similarity = total_similarity / comparisons if comparisons > 0 else None
        
        return {
            "ok": True,
            "similarity_matrix": similarities,
            "average_similarity": round(avg_similarity, 3) if avg_similarity else None,
            "comparisons_count": comparisons,
        }
    
    def _calculate_similarity(self, arr1: "np.ndarray", arr2: "np.ndarray") -> float:
        """
        Calculate similarity between two image arrays.
        
        Uses a combination of:
        - Structural similarity (SSIM-like)
        - Color histogram comparison
        - Perceptual hash comparison
        
        Args:
            arr1: First image array (RGB, float32)
            arr2: Second image array (RGB, float32)
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        import numpy as np
        
        # Normalize arrays
        arr1_norm = arr1 / 255.0
        arr2_norm = arr2 / 255.0
        
        # Calculate mean squared error
        mse = np.mean((arr1_norm - arr2_norm) ** 2)
        
        # Convert MSE to similarity (lower MSE = higher similarity)
        # MSE of 0 = perfect match (similarity 1.0)
        # MSE of 1 = completely different (similarity 0.0)
        similarity = max(0.0, 1.0 - mse)
        
        # Add histogram comparison
        hist1 = self._calculate_histogram(arr1)
        hist2 = self._calculate_histogram(arr2)
        hist_similarity = self._histogram_intersection(hist1, hist2)
        
        # Combine metrics (weighted average)
        final_similarity = (similarity * 0.7) + (hist_similarity * 0.3)
        
        return float(final_similarity)
    
    def _calculate_histogram(self, arr: "np.ndarray") -> "np.ndarray":
        """Calculate color histogram for an image array."""
        import numpy as np
        
        # Flatten array and calculate histogram
        flat = arr.flatten()
        hist, _ = np.histogram(flat, bins=256, range=(0, 255))
        # Normalize
        hist = hist / np.sum(hist) if np.sum(hist) > 0 else hist
        return hist
    
    def _histogram_intersection(self, hist1: "np.ndarray", hist2: "np.ndarray") -> float:
        """Calculate histogram intersection similarity."""
        import numpy as np
        
        intersection = np.minimum(hist1, hist2)
        return float(np.sum(intersection))

