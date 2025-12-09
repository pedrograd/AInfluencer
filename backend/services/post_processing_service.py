"""
Post-Processing Service
Complete implementation based on Post-Processing Master Workflow document

Handles:
- Image Upscaling (Real-ESRGAN, 4x-UltraSharp, ESRGAN, Waifu2x)
- Face Restoration (GFPGAN, CodeFormer)
- Color Grading and Correction (with platform presets)
- Artifact Removal (Noise reduction, inpainting, deblurring)
- Metadata Removal (EXIF, XMP, IPTC, AI markers)
- Batch Processing
- Platform-specific presets (Instagram, OnlyFans, Professional)
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Any, Tuple, List
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

# Add parent directory to path to import post_process_pipeline
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
try:
    from post_process_pipeline import UltraRealisticPostProcessor
    USE_ENHANCED_PIPELINE = True
except ImportError:
    USE_ENHANCED_PIPELINE = False

# Import anti-detection services
try:
    from services.anti_detection_service import (
        MetadataCleaner,
        ContentHumanizer,
        AntiDetectionService
    )
    USE_ANTI_DETECTION = True
except ImportError:
    USE_ANTI_DETECTION = False

logger = logging.getLogger(__name__)

class PostProcessingService:
    """
    Service for post-processing generated content.
    Uses enhanced pipeline when available, falls back to basic implementation.
    """
    
    def __init__(self):
        self.comfyui_models_path = Path(__file__).parent.parent.parent / "ComfyUI" / "models"
        self.upscale_models_path = self.comfyui_models_path / "upscale_models"
        self.face_restore_path = self.comfyui_models_path / "face_restore"
        
        # Initialize enhanced processor if available
        if USE_ENHANCED_PIPELINE:
            try:
                self.processor = UltraRealisticPostProcessor()
                logger.info("Enhanced post-processing pipeline loaded")
            except Exception as e:
                logger.warning(f"Failed to load enhanced pipeline: {e}")
                self.processor = None
        else:
            self.processor = None
            logger.info("Using basic post-processing implementation")
        
        # Initialize processors (lazy loading for fallback)
        self.upscaler = None
        self.ultrasharp_upscaler = None
        self.face_enhancer = None
        self.codeformer = None
    
    def process_image(
        self,
        input_path: Path,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Process a single image with all enabled post-processing steps.
        
        Args:
            input_path: Path to input image
            output_path: Path to save processed image
            config: Processing configuration
        
        Returns:
            True if successful, False otherwise
        """
        config = config or {}
        
        # Use enhanced processor if available
        if self.processor:
            try:
                return self.processor.process_image(input_path, output_path, config)
            except Exception as e:
                logger.warning(f"Enhanced pipeline failed, using fallback: {e}")
        
        # Fallback to basic implementation
        return self._process_image_basic(input_path, output_path, config)
    
    def _process_image_basic(
        self,
        input_path: Path,
        output_path: Path,
        config: Dict[str, Any]
    ) -> bool:
        """Basic post-processing implementation (fallback)"""
        try:
            logger.info(f"Processing image: {input_path.name}")
            
            # Load image
            img = Image.open(input_path)
            original_size = img.size
            
            # 1. Upscaling (with multi-stage support)
            if config.get("upscale", False):
                upscale_factor = config.get("upscale_factor", 2)
                multi_stage = config.get("multi_stage_upscaling", True)  # Phase 1 enhancement
                img = self._upscale_image(img, upscale_factor, multi_stage=multi_stage)
                logger.info(f"Upscaled: {original_size} -> {img.size}")
            
            # 2. Face Restoration
            if config.get("face_restoration", False):
                face_weight = config.get("face_weight", 0.5)
                face_method = config.get("face_method", "gfpgan")
                img = self._restore_face(img, weight=face_weight, method=face_method)
                logger.info("Face restoration applied")
            
            # 3. Color Correction/Grading
            if config.get("color_grade", False) or config.get("color_correction", False):
                color_preset = config.get("color_preset", None)
                use_advanced = config.get("advanced_color_grade", False)
                color_look = config.get("color_look", "warm")
                
                if use_advanced:
                    img = self._advanced_color_grade(img, look=color_look)
                else:
                    img = self._color_grade(img, preset=color_preset, **config)
                logger.info("Color grading applied")
            
            # 4. Artifact Removal
            if config.get("remove_artifacts", False):
                img = self._remove_noise(img)
                logger.info("Artifacts removed")
            
            # 5. Content Humanization (for anti-detection)
            if config.get("humanize", False):
                humanize_intensity = config.get("humanize_intensity", 0.1)
                img = self.content_humanizer.add_natural_imperfections(img, humanize_intensity)
                logger.info("Content humanization applied")
            
            # 6. Metadata Removal (CRITICAL for anti-detection)
            if config.get("remove_metadata", True):  # Default to True
                # Use advanced metadata cleaner
                temp_path = output_path.parent / f"{output_path.stem}_temp{output_path.suffix}"
                img.save(temp_path)
                self.metadata_cleaner.clean_all_metadata(temp_path, output_path)
                img = Image.open(output_path)
                temp_path.unlink()  # Remove temp file
                logger.info("Metadata removed (advanced)")
            
            # 6. Quality Optimization
            if config.get("optimize_quality", True):
                img = self._optimize_quality(img)
                logger.info("Quality optimization applied")
            
            # 7. Resize if target size specified
            if config.get("target_size"):
                target_size = config["target_size"]
                if isinstance(target_size, (list, tuple)) and len(target_size) == 2:
                    img = img.resize(target_size, Image.Resampling.LANCZOS)
                    logger.info(f"Resized to {target_size}")
            
            # Save processed image
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine format
            output_format = config.get("output_format", "PNG")
            quality = config.get("quality", 95)
            
            if output_format.upper() == "PNG":
                img.save(output_path, "PNG", optimize=True)
            elif output_format.upper() in ["JPG", "JPEG"]:
                img = img.convert("RGB")  # Ensure RGB for JPEG
                img.save(output_path, "JPEG", quality=quality, optimize=True)
            elif output_format.upper() == "WEBP":
                img.save(output_path, "WEBP", quality=quality, method=6)
            else:
                img.save(output_path, output_format)
            
            logger.info(f"Processed image saved: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Post-processing error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def get_preset_config(self, preset: str) -> Dict[str, Any]:
        """
        Get configuration for platform-specific presets.
        
        Args:
            preset: Preset name ('instagram', 'onlyfans', 'professional')
        
        Returns:
            Configuration dictionary
        """
        presets = {
            'instagram': {
                "upscale": True,
                "upscale_factor": 4,
                "face_restoration": True,
                "face_weight": 0.5,
                "color_grade": True,
                "color_preset": "instagram",
                "remove_artifacts": True,
                "remove_metadata": True,
                "target_size": [1080, 1080],
                "output_format": "JPEG",
                "quality": 95
            },
            'onlyfans': {
                "upscale": True,
                "upscale_factor": 4,
                "face_restoration": True,
                "face_weight": 0.7,
                "color_grade": True,
                "color_preset": "onlyfans",
                "remove_artifacts": True,
                "remove_metadata": True,
                "output_format": "JPEG",
                "quality": 98
            },
            'professional': {
                "upscale": True,
                "upscale_factor": 4,
                "face_restoration": True,
                "face_weight": 0.5,
                "color_grade": True,
                "color_preset": "professional",
                "remove_artifacts": True,
                "remove_metadata": True,
                "output_format": "PNG",
                "quality": 100
            }
        }
        return presets.get(preset.lower(), presets['professional'])
    
    def _upscale_image(self, img: Image.Image, factor: int, multi_stage: bool = True) -> Image.Image:
        """
        Upscale image using available upscalers with optional multi-stage upscaling.
        
        Multi-stage upscaling: 2x → 4x → 8x for better quality (Phase 1 enhancement).
        """
        try:
            # Multi-stage upscaling for factors > 2
            if multi_stage and factor > 2:
                current_img = img
                remaining_factor = factor
                
                # Break down into stages: 2x, then 4x, then 8x
                stages = []
                current_scale = 1
                
                while remaining_factor >= 2 and current_scale < factor:
                    next_scale = min(2, remaining_factor)
                    stages.append(next_scale)
                    current_scale *= next_scale
                    remaining_factor = factor / current_scale
                
                # Apply stages sequentially
                logger.info(f"Multi-stage upscaling: {stages} (target: {factor}x)")
                for stage_factor in stages:
                    current_img = self._upscale_image_single_stage(current_img, stage_factor)
                    logger.info(f"  Stage complete: {current_img.size}")
                
                # Final resize if needed (rare)
                if current_scale < factor:
                    final_factor = factor / current_scale
                    new_size = (int(current_img.size[0] * final_factor), int(current_img.size[1] * final_factor))
                    current_img = current_img.resize(new_size, Image.Resampling.LANCZOS)
                
                return current_img
            else:
                # Single-stage upscaling
                return self._upscale_image_single_stage(img, factor)
            
        except Exception as e:
            logger.warning(f"Multi-stage upscaling failed, using fallback: {e}")
            new_size = (img.size[0] * factor, img.size[1] * factor)
            return img.resize(new_size, Image.Resampling.LANCZOS)
    
    def _upscale_image_single_stage(self, img: Image.Image, factor: int) -> Image.Image:
        """Upscale image by a single stage factor"""
        try:
            # Try Real-ESRGAN first
            if self._init_upscaler():
                import numpy as np
                img_array = np.array(img)
                output, _ = self.upscaler.enhance(img_array, outscale=factor)
                return Image.fromarray(output)
            
            # Try 4x-UltraSharp for high quality
            if factor >= 4:
                if self._init_ultrasharp_upscaler():
                    import numpy as np
                    img_array = np.array(img)
                    output, _ = self.ultrasharp_upscaler.enhance(img_array, outscale=4)
                    if factor == 4:
                        return Image.fromarray(output)
                    # If we need > 4x, upscale the result
                    if factor > 4:
                        remaining = factor / 4
                        upscaled = Image.fromarray(output)
                        new_size = (int(upscaled.size[0] * remaining), int(upscaled.size[1] * remaining))
                        return upscaled.resize(new_size, Image.Resampling.LANCZOS)
            
            # Fallback to PIL Lanczos upscaling
            new_size = (img.size[0] * factor, img.size[1] * factor)
            return img.resize(new_size, Image.Resampling.LANCZOS)
            
        except Exception as e:
            logger.warning(f"Single-stage upscaling failed, using fallback: {e}")
            new_size = (img.size[0] * factor, img.size[1] * factor)
            return img.resize(new_size, Image.Resampling.LANCZOS)
    
    def _restore_face(
        self, 
        img: Image.Image, 
        weight: float = 0.5,
        method: str = "gfpgan"
    ) -> Image.Image:
        """
        Restore face using GFPGAN or CodeFormer.
        
        Args:
            img: Input image
            weight: Restoration weight (0.0-1.0)
            method: Method ('gfpgan', 'codeformer')
        """
        try:
            # Try CodeFormer first if requested
            if method == "codeformer" and self._init_codeformer():
                try:
                    output = self.codeformer.restore(img, weight=weight)
                    return output
                except Exception as e:
                    logger.warning(f"CodeFormer failed: {e}, trying GFPGAN")
            
            # Use GFPGAN
            if self._init_face_enhancer():
                import numpy as np
                img_array = np.array(img)
                _, _, output = self.face_enhancer.enhance(
                    img_array,
                    has_aligned=False,
                    only_center_face=False,
                    paste_back=True,
                    weight=weight
                )
                return Image.fromarray(output)
            
            # No face enhancer available, return original
            return img
            
        except Exception as e:
            logger.warning(f"Face restoration failed: {e}")
            return img
    
    def _color_grade(
        self,
        img: Image.Image,
        preset: Optional[str] = None,
        brightness: float = 1.05,
        contrast: float = 1.1,
        saturation: float = 1.05,
        sharpness: float = 1.05,
        **kwargs
    ) -> Image.Image:
        """
        Apply color grading and correction.
        
        Args:
            img: Input image
            preset: Preset name ('instagram', 'onlyfans', 'professional', 'warm', 'cool', 'vibrant')
            brightness: Brightness multiplier
            contrast: Contrast multiplier
            saturation: Saturation multiplier
            sharpness: Sharpness multiplier
        """
        # Get preset values if specified
        if preset:
            preset_config = self._get_color_preset(preset)
            brightness = preset_config.get('brightness', brightness)
            contrast = preset_config.get('contrast', contrast)
            saturation = preset_config.get('saturation', saturation)
            sharpness = preset_config.get('sharpness', sharpness)
        
        # Override with config values if provided
        brightness = kwargs.get('brightness', brightness)
        contrast = kwargs.get('contrast', contrast)
        saturation = kwargs.get('saturation', saturation)
        sharpness = kwargs.get('sharpness', sharpness)
        
        # Brightness
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness)
        
        # Contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)
        
        # Color/Saturation
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(saturation)
        
        # Sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(sharpness)
        
        return img
    
    def _get_color_preset(self, preset: str) -> Dict[str, float]:
        """Get color grading preset configuration"""
        presets = {
            'instagram': {
                'brightness': 1.05,
                'contrast': 1.15,
                'saturation': 1.1,
                'sharpness': 1.05
            },
            'onlyfans': {
                'brightness': 1.05,
                'contrast': 1.1,
                'saturation': 1.05,
                'sharpness': 1.03
            },
            'professional': {
                'brightness': 1.0,
                'contrast': 1.05,
                'saturation': 1.0,
                'sharpness': 1.05
            },
            'warm': {
                'brightness': 1.05,
                'contrast': 1.1,
                'saturation': 1.08,
                'sharpness': 1.05
            },
            'cool': {
                'brightness': 1.03,
                'contrast': 1.1,
                'saturation': 1.05,
                'sharpness': 1.05
            },
            'vibrant': {
                'brightness': 1.05,
                'contrast': 1.15,
                'saturation': 1.15,
                'sharpness': 1.05
            }
        }
        return presets.get(preset.lower(), presets['professional'])
    
    def _advanced_color_grade(
        self, 
        img: Image.Image, 
        look: str = 'warm'
    ) -> Image.Image:
        """
        Advanced color grading using LAB color space.
        
        Args:
            img: Input image
            look: Color look ('warm', 'cool', 'vibrant')
        """
        try:
            import cv2
            
            # Convert PIL to OpenCV format
            img_array = np.array(img)
            if img.mode == 'RGBA':
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            elif img.mode != 'RGB':
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2RGB)
            
            # Convert to LAB color space
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply look
            if look == 'warm':
                # Increase warmth (yellow/orange)
                a = np.clip(a * 1.1, 0, 255).astype(np.uint8)
            elif look == 'cool':
                # Increase coolness (blue/cyan)
                b = np.clip(b * 0.9, 0, 255).astype(np.uint8)
            elif look == 'vibrant':
                # Increase saturation
                a = np.clip(a * 1.15, 0, 255).astype(np.uint8)
                b = np.clip(b * 1.15, 0, 255).astype(np.uint8)
            
            # Merge and convert back
            lab = cv2.merge([l, a, b])
            output = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
            # Convert back to PIL
            return Image.fromarray(output)
        except ImportError:
            logger.warning("OpenCV not available, using basic color grading")
            return self._color_grade(img)
        except Exception as e:
            logger.warning(f"Advanced color grading failed: {e}")
            return self._color_grade(img)
    
    def _remove_noise(self, img: Image.Image) -> Image.Image:
        """
        Remove noise from image using non-local means denoising.
        Falls back to median filter if OpenCV not available.
        """
        try:
            import cv2
            
            # Convert PIL to OpenCV
            img_array = np.array(img)
            if img.mode == 'RGBA':
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            
            # Apply non-local means denoising
            denoised = cv2.fastNlMeansDenoisingColored(img_array, None, 10, 10, 7, 21)
            
            # Convert back to PIL
            return Image.fromarray(denoised)
        except ImportError:
            logger.warning("OpenCV not available, using median filter")
            return img.filter(ImageFilter.MedianFilter(size=3))
        except Exception as e:
            logger.warning(f"Noise reduction failed: {e}")
            return img.filter(ImageFilter.MedianFilter(size=3))
    
    def _remove_metadata(self, img: Image.Image) -> Image.Image:
        """Remove all metadata from image (CRITICAL for anti-detection)"""
        try:
            # Create new image without metadata
            data = list(img.getdata())
            img_clean = Image.new(img.mode, img.size)
            img_clean.putdata(data)
            
            # Remove EXIF if present
            if hasattr(img_clean, '_getexif'):
                try:
                    img_clean._getexif = None
                except:
                    pass
            
            return img_clean
            
        except Exception as e:
            logger.warning(f"Metadata removal failed: {e}")
            return img
    
    def test_anti_detection(
        self,
        image_path: Path,
        tools: Optional[List[str]] = None,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Test image against detection tools"""
        return self.anti_detection.test_detection(image_path, tools, threshold)
    
    def pre_publication_check(
        self,
        image_path: Path,
        threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Comprehensive pre-publication anti-detection check"""
        return self.anti_detection.pre_publication_test(image_path, threshold)
    
    def _optimize_quality(self, img: Image.Image) -> Image.Image:
        """Optimize image quality"""
        # Additional quality optimizations can be added here
        # For now, just ensure proper mode
        if img.mode == "RGBA":
            # Convert RGBA to RGB for better compatibility
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            return background
        
        return img
    
    def _init_upscaler(self) -> bool:
        """Initialize Real-ESRGAN upscaler"""
        if self.upscaler is not None:
            return True
        
        try:
            from realesrgan import RealESRGANer
            
            model_path = self.upscale_models_path / "RealESRGAN_x4plus.pth"
            if not model_path.exists():
                # Try alternative paths
                models = list(self.upscale_models_path.glob("*.pth"))
                if not models:
                    logger.warning("No Real-ESRGAN model found")
                    return False
                model_path = models[0]
            
            self.upscaler = RealESRGANer(
                scale=4,
                model_path=str(model_path),
                model='RealESRGAN_x4plus'
            )
            logger.info("Real-ESRGAN upscaler initialized")
            return True
            
        except ImportError:
            logger.warning("realesrgan not installed, upscaling will use fallback")
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize upscaler: {e}")
            return False
    
    def _init_face_enhancer(self) -> bool:
        """Initialize GFPGAN face enhancer"""
        if self.face_enhancer is not None:
            return True
        
        try:
            from gfpgan import GFPGANer
            
            model_path = self.face_restore_path / "GFPGANv1.4.pth"
            if not model_path.exists():
                models = list(self.face_restore_path.glob("GFPGAN*.pth"))
                if not models:
                    logger.warning("No GFPGAN model found")
                    return False
                model_path = models[0]
            
            self.face_enhancer = GFPGANer(
                model_path=str(model_path),
                upscale=2,
                arch='clean',
                channel_multiplier=2,
                bg_upsampler=None
            )
            logger.info("GFPGAN face enhancer initialized")
            return True
            
        except ImportError:
            logger.warning("gfpgan not installed, face restoration disabled")
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize face enhancer: {e}")
            return False
    
    def _init_codeformer(self) -> bool:
        """Initialize CodeFormer face enhancer"""
        if self.codeformer is not None:
            return True
        
        try:
            from codeformer import CodeFormer
            
            codeformer_paths = [
                self.face_restore_path / "codeformer.pth",
                self.face_restore_path / "CodeFormer.pth"
            ]
            
            model_path = None
            for path in codeformer_paths:
                if path.exists():
                    model_path = path
                    break
            
            if model_path:
                self.codeformer = CodeFormer()
                logger.info("CodeFormer face enhancer initialized")
                return True
            else:
                logger.info("CodeFormer model not found (optional)")
                return False
                
        except ImportError:
            logger.info("CodeFormer not installed (optional)")
            return False
        except Exception as e:
            logger.info(f"CodeFormer not available: {e}")
            return False
    
    def _init_ultrasharp_upscaler(self) -> bool:
        """Initialize 4x-UltraSharp upscaler (Phase 1 enhancement)"""
        if self.ultrasharp_upscaler is not None:
            return True
        
        try:
            from realesrgan import RealESRGANer
            
            model_path = self.upscale_models_path / "4x-UltraSharp.pth"
            if not model_path.exists():
                # Try alternative paths
                models = list(self.upscale_models_path.glob("*UltraSharp*.pth"))
                if not models:
                    logger.debug("No 4x-UltraSharp model found")
                    return False
                model_path = models[0]
            
            self.ultrasharp_upscaler = RealESRGANer(
                scale=4,
                model_path=str(model_path),
                model='4x-UltraSharp'
            )
            logger.info("4x-UltraSharp upscaler initialized")
            return True
            
        except ImportError:
            logger.debug("realesrgan not installed for UltraSharp, using Real-ESRGAN")
            return False
        except Exception as e:
            logger.debug(f"Failed to initialize UltraSharp upscaler: {e}")
            return False
    
    def batch_process(
        self,
        input_folder: Path,
        output_folder: Path,
        config: Optional[Dict[str, Any]] = None,
        pipeline: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process all images in a folder.
        
        Args:
            input_folder: Input folder path
            output_folder: Output folder path
            config: Processing configuration
            pipeline: Pipeline preset ('instagram', 'onlyfans', 'professional')
        
        Returns:
            Dictionary with processing statistics
        """
        # Use enhanced processor if available
        if self.processor:
            try:
                return self.processor.batch_process(input_folder, output_folder, config, pipeline)
            except Exception as e:
                logger.warning(f"Enhanced batch processing failed, using fallback: {e}")
        
        # Fallback implementation
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        
        if not input_path.exists():
            return {"success": False, "error": "Input folder not found"}
        
        # Find image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG', '.WEBP']
        images = []
        for ext in image_extensions:
            images.extend(input_path.glob(f'*{ext}'))
        
        if not images:
            return {"success": False, "error": "No images found", "total": 0}
        
        # Use preset config if specified
        if pipeline:
            config = self.get_preset_config(pipeline)
        
        success_count = 0
        fail_count = 0
        results = []
        
        for img_path in images:
            output_file = output_path / img_path.name
            if self.process_image(img_path, output_file, config):
                success_count += 1
                results.append({"file": img_path.name, "status": "success"})
            else:
                fail_count += 1
                results.append({"file": img_path.name, "status": "failed"})
        
        return {
            "success": True,
            "total": len(images),
            "successful": success_count,
            "failed": fail_count,
            "results": results
        }
    
    def process_video(
        self,
        input_path: Path,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Process a video with post-processing.
        
        This involves:
        - Frame extraction
        - Frame-by-frame processing
        - Frame interpolation
        - Video encoding
        
        Args:
            input_path: Path to input video
            output_path: Path to save processed video
            config: Processing configuration
        
        Returns:
            True if successful, False otherwise
        """
        config = config or {}
        
        try:
            import cv2
            import tempfile
            
            logger.info(f"Processing video: {input_path.name}")
            
            # Create temporary directory for frames
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                frames_dir = tmp_path / "frames"
                processed_frames_dir = tmp_path / "processed_frames"
                frames_dir.mkdir()
                processed_frames_dir.mkdir()
                
                # Step 1: Extract frames
                logger.info("Extracting frames...")
                frames = self._extract_frames(input_path, frames_dir)
                if not frames:
                    logger.error("Failed to extract frames")
                    return False
                
                logger.info(f"Extracted {len(frames)} frames")
                
                # Step 2: Process each frame
                processed_frames = []
                for i, frame_path in enumerate(frames):
                    if i % 10 == 0:
                        logger.info(f"Processing frame {i+1}/{len(frames)}")
                    
                    processed_frame_path = processed_frames_dir / f"frame_{i:06d}.png"
                    
                    # Apply all enabled post-processing to frame
                    frame_config = config.copy()
                    frame_config["remove_metadata"] = False  # Remove metadata at end
                    
                    if self.process_image(frame_path, processed_frame_path, frame_config):
                        processed_frames.append(processed_frame_path)
                    else:
                        # If processing fails, use original frame
                        import shutil
                        shutil.copy2(frame_path, processed_frame_path)
                        processed_frames.append(processed_frame_path)
                
                # Step 3: Frame interpolation (if enabled)
                if config.get("frame_interpolation", False):
                    from services.frame_interpolation_service import FrameInterpolationService
                    interpolation_service = FrameInterpolationService()
                    
                    # Create temporary video from processed frames
                    temp_video = tmp_path / "temp_processed.mp4"
                    self._frames_to_video(processed_frames, temp_video, config.get("fps", 24))
                    
                    # Interpolate
                    interpolation_scale = config.get("interpolation_scale", 2)
                    interpolation_method = config.get("interpolation_method", "ffmpeg")
                    interpolated_video = tmp_path / "interpolated.mp4"
                    
                    if interpolation_service.interpolate_frames(
                        temp_video, interpolated_video,
                        method=interpolation_method,
                        scale=interpolation_scale
                    ):
                        # Extract interpolated frames
                        processed_frames_dir = tmp_path / "interpolated_frames"
                        processed_frames_dir.mkdir()
                        frames = self._extract_frames(interpolated_video, processed_frames_dir)
                        processed_frames = sorted(frames)
                
                # Step 4: Color grading (if enabled)
                if config.get("color_grading", False):
                    processed_frames = self._apply_color_grading(processed_frames, config)
                
                # Step 5: Stabilization (if enabled)
                if config.get("stabilization", False):
                    processed_frames = self._stabilize_video(processed_frames, config)
                
                # Step 6: Create final video
                output_fps = config.get("output_fps", 24)
                output_format = config.get("output_format", "mp4")
                
                logger.info(f"Creating final video: {output_fps}fps, format: {output_format}")
                success = self._frames_to_video(
                    processed_frames,
                    output_path,
                    output_fps,
                    codec=config.get("codec", "libx264"),
                    quality=config.get("quality", "high")
                )
                
                if success:
                    logger.info(f"Video processing complete: {output_path}")
                    return True
                else:
                    logger.error("Failed to create final video")
                    return False
                    
        except Exception as e:
            logger.error(f"Video processing error: {e}", exc_info=True)
            return False
    
    def _extract_frames(self, video_path: Path, output_dir: Path) -> List[Path]:
        """Extract frames from video"""
        try:
            import subprocess
            
            frame_pattern = str(output_dir / "frame_%06d.png")
            cmd = [
                "ffmpeg", "-i", str(video_path),
                "-vsync", "0",
                frame_pattern
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                frames = sorted(output_dir.glob("frame_*.png"))
                return frames
            else:
                logger.error(f"Frame extraction failed: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Frame extraction error: {e}")
            return []
    
    def _frames_to_video(
        self,
        frames: List[Path],
        output_path: Path,
        fps: int,
        codec: str = "libx264",
        quality: str = "high"
    ) -> bool:
        """Convert frames to video"""
        try:
            import subprocess
            
            if not frames:
                logger.error("No frames to process")
                return False
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine quality settings
            crf_map = {
                "low": "28",
                "medium": "23",
                "high": "18",
                "ultra": "15"
            }
            crf = crf_map.get(quality, "23")
            
            # Use first frame to get pattern
            frame_pattern = str(frames[0].parent / "frame_%06d.png")
            
            # Rename frames if needed to match pattern
            for i, frame in enumerate(frames):
                expected_name = frames[0].parent / f"frame_{i+1:06d}.png"
                if frame.name != expected_name.name:
                    import shutil
                    shutil.copy2(frame, expected_name)
            
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", frame_pattern,
                "-c:v", codec,
                "-preset", "medium",
                "-crf", crf,
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Video created: {output_path}")
                return True
            else:
                logger.error(f"Video creation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Frames to video error: {e}")
            return False
    
    def _apply_color_grading(self, frames: List[Path], config: Dict[str, Any]) -> List[Path]:
        """Apply color grading to video frames"""
        try:
            from PIL import Image, ImageEnhance
            import tempfile
            
            brightness = config.get("color_brightness", 1.0)
            contrast = config.get("color_contrast", 1.0)
            saturation = config.get("color_saturation", 1.0)
            
            processed_frames = []
            with tempfile.TemporaryDirectory() as tmpdir:
                tmp_path = Path(tmpdir)
                
                for i, frame_path in enumerate(frames):
                    img = Image.open(frame_path)
                    
                    # Apply enhancements
                    if brightness != 1.0:
                        enhancer = ImageEnhance.Brightness(img)
                        img = enhancer.enhance(brightness)
                    
                    if contrast != 1.0:
                        enhancer = ImageEnhance.Contrast(img)
                        img = enhancer.enhance(contrast)
                    
                    if saturation != 1.0:
                        enhancer = ImageEnhance.Color(img)
                        img = enhancer.enhance(saturation)
                    
                    # Save processed frame
                    processed_path = tmp_path / f"graded_{i:06d}.png"
                    img.save(processed_path)
                    processed_frames.append(processed_path)
                
                # Copy back to original location
                for i, (original, processed) in enumerate(zip(frames, processed_frames)):
                    import shutil
                    shutil.copy2(processed, original)
            
            return frames
            
        except Exception as e:
            logger.warning(f"Color grading error: {e}")
            return frames
    
    def _stabilize_video(self, frames: List[Path], config: Dict[str, Any]) -> List[Path]:
        """Stabilize video frames"""
        try:
            import cv2
            import numpy as np
            import tempfile
            
            # Use OpenCV video stabilization
            # This is a simplified version - full stabilization would use feature detection
            logger.info("Applying video stabilization...")
            
            # For now, return original frames
            # Full stabilization requires more complex algorithms
            return frames
            
        except Exception as e:
            logger.warning(f"Video stabilization error: {e}")
            return frames
    
    def multi_stage_upscale(self, image_path: str, target_factor: int = 8) -> str:
        """
        Multi-stage upscaling (2x → 4x → 8x) for maximum quality
        
        Args:
            image_path: Path to input image
            target_factor: Target upscale factor (2, 4, or 8)
        
        Returns:
            Path to upscaled image
        """
        from PIL import Image
        
        current_image = Image.open(image_path)
        current_factor = 1
        
        # Stage 1: 2x upscale
        if target_factor >= 2:
            logger.info("Stage 1: 2x upscaling...")
            current_image = self._upscale_with_model(current_image, factor=2, model="RealESRGAN_x2plus")
            current_factor = 2
        
        # Stage 2: 4x upscale (from 2x)
        if target_factor >= 4:
            logger.info("Stage 2: 4x upscaling (from 2x)...")
            current_image = self._upscale_with_model(current_image, factor=2, model="RealESRGAN_x4plus")
            current_factor = 4
        
        # Stage 3: 8x upscale (from 4x)
        if target_factor >= 8:
            logger.info("Stage 3: 8x upscaling (from 4x)...")
            current_image = self._upscale_with_model(current_image, factor=2, model="4x-UltraSharp")
            current_factor = 8
        
        # Save result
        output_path = Path(image_path).parent / f"{Path(image_path).stem}_upscaled_{current_factor}x{Path(image_path).suffix}"
        current_image.save(str(output_path), quality=95)
        
        return str(output_path)
    
    def _upscale_with_model(self, image: Image.Image, factor: int, model: str) -> Image.Image:
        """Internal method to upscale with specific model"""
        try:
            from realesrgan import RealESRGANer
            
            model_paths = {
                "RealESRGAN_x2plus": self.upscale_models_path / "RealESRGAN_x2plus.pth",
                "RealESRGAN_x4plus": self.upscale_models_path / "RealESRGAN_x4plus.pth",
                "4x-UltraSharp": self.upscale_models_path / "4x-UltraSharp.pth"
            }
            
            model_path = model_paths.get(model, model_paths["RealESRGAN_x4plus"])
            if not model_path.exists():
                logger.warning(f"Model {model} not found, using default")
                model_path = self.upscale_models_path / "RealESRGAN_x4plus.pth"
            
            upscaler = RealESRGANer(
                scale=factor,
                model_path=str(model_path),
                model=model.replace("4x-UltraSharp", "RealESRGAN_x4plus")
            )
            
            return upscaler.enhance(image)
        except Exception as e:
            logger.error(f"Upscaling error: {e}")
            # Fallback: simple resize
            return image.resize((image.width * factor, image.height * factor), Image.LANCZOS)
    
    def hybrid_face_restoration(self, image_path: str, gfpgan_weight: float = 0.5) -> str:
        """
        Hybrid face restoration using both GFPGAN and CodeFormer
        
        Args:
            image_path: Path to input image
            gfpgan_weight: Weight for GFPGAN (0.0 = CodeFormer only, 1.0 = GFPGAN only)
        
        Returns:
            Path to restored image
        """
        from PIL import Image
        import numpy as np
        
        image = Image.open(image_path)
        image_array = np.array(image)
        
        # Apply GFPGAN
        gfpgan_result = None
        if gfpgan_weight > 0:
            try:
                from gfpgan import GFPGANer
                gfpgan = GFPGANer(model_path=str(self.face_restore_path / "GFPGANv1.4.pth"))
                gfpgan_result, _, _ = gfpgan.enhance(image_array, weight=0.5)
            except Exception as e:
                logger.warning(f"GFPGAN error: {e}")
        
        # Apply CodeFormer
        codeformer_result = None
        if gfpgan_weight < 1.0:
            try:
                from codeformer import CodeFormer
                codeformer = CodeFormer(model_path=str(self.face_restore_path / "codeformer.pth"))
                codeformer_result = codeformer.enhance(image_array)
            except Exception as e:
                logger.warning(f"CodeFormer error: {e}")
        
        # Blend results
        if gfpgan_result is not None and codeformer_result is not None:
            result = (gfpgan_result * gfpgan_weight + codeformer_result * (1 - gfpgan_weight)).astype(np.uint8)
        elif gfpgan_result is not None:
            result = gfpgan_result
        elif codeformer_result is not None:
            result = codeformer_result
        else:
            result = image_array
        
        # Save
        output_path = Path(image_path).parent / f"{Path(image_path).stem}_face_restored{Path(image_path).suffix}"
        Image.fromarray(result).save(str(output_path), quality=95)
        
        return str(output_path)
    
    def hdr_tone_mapping(self, image_path: str, strength: float = 0.5) -> str:
        """
        Apply HDR tone mapping for realistic lighting
        
        Args:
            image_path: Path to input image
            strength: Tone mapping strength (0.0-1.0)
        
        Returns:
            Path to processed image
        """
        try:
            from PIL import Image
            import numpy as np
            import cv2
            
            input_path = Path(image_path)
            output_path = input_path.parent / f"{input_path.stem}_hdr{input_path.suffix}"
            
            img = Image.open(input_path)
            img_array = np.array(img.convert('RGB'))
            
            # Convert to LAB color space for better tone mapping
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply tone mapping to L channel (lightness)
            # Reinhard tone mapping algorithm
            l_float = l.astype(np.float32) / 255.0
            l_tone_mapped = l_float / (1.0 + l_float * strength)
            l_tone_mapped = (l_tone_mapped * 255.0).astype(np.uint8)
            
            # Merge channels and convert back
            lab_tone_mapped = cv2.merge([l_tone_mapped, a, b])
            rgb_tone_mapped = cv2.cvtColor(lab_tone_mapped, cv2.COLOR_LAB2RGB)
            
            # Convert back to PIL and save
            result_img = Image.fromarray(rgb_tone_mapped)
            result_img.save(output_path)
            
            logger.info(f"HDR tone mapping completed: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"HDR tone mapping error: {e}")
            raise
    
    def skin_texture_enhancement(self, image_path: str, strength: float = 0.5) -> str:
        """
        Enhance skin texture with pore-level detail
        
        Args:
            image_path: Path to input image
            strength: Enhancement strength (0.0-1.0)
        
        Returns:
            Path to processed image
        """
        try:
            from PIL import Image, ImageFilter
            import numpy as np
            import cv2
            
            input_path = Path(image_path)
            output_path = input_path.parent / f"{input_path.stem}_skin_enhanced{input_path.suffix}"
            
            img = Image.open(input_path)
            img_array = np.array(img.convert('RGB'))
            
            # Convert to LAB for better skin processing
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            # Apply unsharp mask to L channel for texture enhancement
            l_float = l.astype(np.float32)
            
            # Create blurred version
            l_blur = cv2.GaussianBlur(l_float, (0, 0), 2.0)
            
            # Unsharp mask: original + (original - blurred) * strength
            l_enhanced = l_float + (l_float - l_blur) * strength * 2.0
            l_enhanced = np.clip(l_enhanced, 0, 255).astype(np.uint8)
            
            # Merge channels
            lab_enhanced = cv2.merge([l_enhanced, a, b])
            rgb_enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2RGB)
            
            # Convert back to PIL and save
            result_img = Image.fromarray(rgb_enhanced)
            result_img.save(output_path)
            
            logger.info(f"Skin texture enhancement completed: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"Skin texture enhancement error: {e}")
            raise
    
    def color_grading_presets(self, image_path: str, preset: str = "instagram") -> str:
        """
        Apply color grading presets
        
        Args:
            image_path: Path to input image
            preset: Preset name (instagram, onlyfans, professional)
        
        Returns:
            Path to graded image
        """
        from PIL import Image, ImageEnhance
        
        image = Image.open(image_path)
        
        presets = {
            "instagram": {
                "brightness": 1.05,
                "contrast": 1.1,
                "saturation": 1.15,
                "sharpness": 1.1
            },
            "onlyfans": {
                "brightness": 1.08,
                "contrast": 1.12,
                "saturation": 1.2,
                "sharpness": 1.15
            },
            "professional": {
                "brightness": 1.02,
                "contrast": 1.08,
                "saturation": 1.05,
                "sharpness": 1.2
            }
        }
        
        settings = presets.get(preset, presets["instagram"])
        
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(settings["brightness"])
        
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(settings["contrast"])
        
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(settings["saturation"])
        
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(settings["sharpness"])
        
        # Save
        output_path = Path(image_path).parent / f"{Path(image_path).stem}_{preset}{Path(image_path).suffix}"
        image.save(str(output_path), quality=95)
        
        return str(output_path)
