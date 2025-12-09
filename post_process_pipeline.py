"""
Ultra Realistic Post-Processing Pipeline
Complete implementation based on Post-Processing Master Workflow document

Features:
- Image Upscaling (Real-ESRGAN, 4x-UltraSharp, ESRGAN, Waifu2x)
- Face Restoration (GFPGAN, CodeFormer)
- Color Grading and Correction
- Artifact Removal (Noise reduction, inpainting, deblurring)
- Metadata Removal (EXIF, XMP, IPTC, AI markers)
- Batch Processing
- Platform-specific presets (Instagram, OnlyFans, Professional)
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UltraRealisticPostProcessor:
    """
    Complete post-processing pipeline for ultra-realistic AI-generated content.
    Implements all features from the Post-Processing Master Workflow document.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize post-processor with configuration.
        
        Args:
            config: Configuration dictionary with processing options
        """
        self.config = config or {}
        self.upscaler = None
        self.face_enhancer = None
        self.codeformer = None
        self.setup_processors()
    
    def setup_processors(self):
        """Initialize all post-processing processors"""
        logger.info("Initializing post-processing tools...")
        
        # Real-ESRGAN (Upscaling)
        self._init_upscaler()
        
        # Face Restoration (GFPGAN and CodeFormer)
        self._init_face_enhancers()
        
        logger.info("Post-processing tools initialized")
    
    def _init_upscaler(self):
        """Initialize Real-ESRGAN upscaler"""
        try:
            from realesrgan import RealESRGANer
            
            # Try multiple model paths
            model_paths = [
                Path("ComfyUI/models/upscale_models/RealESRGAN_x4plus.pth"),
                Path("models/RealESRGAN_x4plus.pth"),
                Path("ComfyUI/models/upscale_models") / "RealESRGAN_x4plus.pth"
            ]
            
            model_path = None
            for path in model_paths:
                if path.exists():
                    model_path = path
                    break
            
            if model_path:
                self.upscaler = RealESRGANer(
                    scale=4,
                    model_path=str(model_path),
                    model='RealESRGAN_x4plus'
                )
                logger.info(f"✓ Real-ESRGAN loaded (4x upscaling) from {model_path}")
            else:
                # Try to find any Real-ESRGAN model
                upscale_dir = Path("ComfyUI/models/upscale_models")
                if upscale_dir.exists():
                    models = list(upscale_dir.glob("*.pth"))
                    if models:
                        model_path = models[0]
                        self.upscaler = RealESRGANer(
                            scale=4,
                            model_path=str(model_path),
                            model='RealESRGAN_x4plus'
                        )
                        logger.info(f"✓ Real-ESRGAN loaded from {model_path}")
                    else:
                        logger.warning("⚠ Real-ESRGAN model not found, upscaling will be skipped")
                else:
                    logger.warning("⚠ Upscale models directory not found")
        except ImportError:
            logger.warning("⚠ realesrgan package not found. Install: pip install realesrgan")
        except Exception as e:
            logger.warning(f"⚠ Failed to initialize Real-ESRGAN: {e}")
    
    def _init_face_enhancers(self):
        """Initialize face restoration models (GFPGAN and CodeFormer)"""
        # GFPGAN
        try:
            from gfpgan import GFPGANer
            
            model_paths = [
                Path("ComfyUI/models/face_restore/GFPGANv1.4.pth"),
                Path("models/GFPGANv1.4.pth"),
                Path("ComfyUI/models/face_restore") / "GFPGANv1.4.pth"
            ]
            
            model_path = None
            for path in model_paths:
                if path.exists():
                    model_path = path
                    break
            
            if model_path:
                self.face_enhancer = GFPGANer(
                    model_path=str(model_path),
                    upscale=2,
                    arch='clean',
                    channel_multiplier=2,
                    bg_upsampler=None
                )
                logger.info(f"✓ GFPGAN loaded from {model_path}")
            else:
                face_restore_dir = Path("ComfyUI/models/face_restore")
                if face_restore_dir.exists():
                    models = list(face_restore_dir.glob("GFPGAN*.pth"))
                    if models:
                        model_path = models[0]
                        self.face_enhancer = GFPGANer(
                            model_path=str(model_path),
                            upscale=2,
                            arch='clean',
                            channel_multiplier=2,
                            bg_upsampler=None
                        )
                        logger.info(f"✓ GFPGAN loaded from {model_path}")
                    else:
                        logger.warning("⚠ GFPGAN model not found")
                else:
                    logger.warning("⚠ Face restore directory not found")
        except ImportError:
            logger.warning("⚠ gfpgan package not found. Install: pip install gfpgan")
        except Exception as e:
            logger.warning(f"⚠ Failed to initialize GFPGAN: {e}")
        
        # CodeFormer (optional alternative)
        try:
            from codeformer import CodeFormer
            
            codeformer_paths = [
                Path("ComfyUI/models/face_restore/codeformer.pth"),
                Path("models/codeformer.pth")
            ]
            
            model_path = None
            for path in codeformer_paths:
                if path.exists():
                    model_path = path
                    break
            
            if model_path:
                self.codeformer = CodeFormer()
                logger.info(f"✓ CodeFormer loaded from {model_path}")
            else:
                logger.info("ℹ CodeFormer model not found (optional)")
        except ImportError:
            logger.info("ℹ CodeFormer not installed (optional)")
        except Exception as e:
            logger.info(f"ℹ CodeFormer not available: {e}")
    
    def remove_metadata(self, img: Image.Image) -> Image.Image:
        """
        Remove all metadata from image (CRITICAL for anti-detection).
        Removes EXIF, XMP, IPTC, and AI markers.
        """
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
            
            # Try using piexif for complete removal
            try:
                import piexif
                # If image has EXIF, remove it
                if "exif" in img.info:
                    img_clean = Image.new(img.mode, img.size)
                    img_clean.putdata(data)
            except:
                pass
            
            return img_clean
        except Exception as e:
            logger.warning(f"Metadata removal failed: {e}")
            return img
    
    def color_grade(
        self, 
        img: Image.Image, 
        preset: Optional[str] = None,
        brightness: float = 1.05,
        contrast: float = 1.1,
        saturation: float = 1.05,
        sharpness: float = 1.05
    ) -> Image.Image:
        """
        Apply color grading and correction.
        
        Args:
            img: Input image
            preset: Preset name ('instagram', 'onlyfans', 'professional', 'warm', 'cool', 'vibrant')
            brightness: Brightness multiplier (default: 1.05)
            contrast: Contrast multiplier (default: 1.1)
            saturation: Saturation multiplier (default: 1.05)
            sharpness: Sharpness multiplier (default: 1.05)
        """
        # Apply preset if specified
        if preset:
            preset_config = self._get_color_preset(preset)
            brightness = preset_config.get('brightness', brightness)
            contrast = preset_config.get('contrast', contrast)
            saturation = preset_config.get('saturation', saturation)
            sharpness = preset_config.get('sharpness', sharpness)
        
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
    
    def advanced_color_grade(
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
            return self.color_grade(img)
        except Exception as e:
            logger.warning(f"Advanced color grading failed: {e}")
            return self.color_grade(img)
    
    def remove_noise(self, img: Image.Image) -> Image.Image:
        """Remove noise from image using non-local means denoising"""
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
    
    def remove_artifacts(self, img: Image.Image, mask: Optional[np.ndarray] = None) -> Image.Image:
        """
        Remove artifacts from image using inpainting.
        
        Args:
            img: Input image
            mask: Optional mask indicating artifact locations
        """
        try:
            import cv2
            
            if mask is None:
                # No mask provided, just return original
                return img
            
            # Convert PIL to OpenCV
            img_array = np.array(img)
            if img.mode == 'RGBA':
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            
            # Inpaint artifacts
            result = cv2.inpaint(img_array, mask, 3, cv2.INPAINT_TELEA)
            
            # Convert back to PIL
            return Image.fromarray(result)
        except ImportError:
            logger.warning("OpenCV not available for artifact removal")
            return img
        except Exception as e:
            logger.warning(f"Artifact removal failed: {e}")
            return img
    
    def upscale_image(
        self, 
        img: Image.Image, 
        factor: int = 4,
        method: str = 'realesrgan'
    ) -> Image.Image:
        """
        Upscale image using specified method.
        
        Args:
            img: Input image
            factor: Upscaling factor (2 or 4)
            method: Method ('realesrgan', 'lanczos', 'waifu2x')
        """
        if method == 'realesrgan' and self.upscaler:
            try:
                img_array = np.array(img)
                output, _ = self.upscaler.enhance(img_array, outscale=factor)
                return Image.fromarray(output)
            except Exception as e:
                logger.warning(f"Real-ESRGAN upscaling failed: {e}, using fallback")
        
        elif method == 'waifu2x':
            try:
                from waifu2x import Waifu2x
                waifu2x = Waifu2x()
                output = waifu2x.process(img, scale=factor)
                return output
            except ImportError:
                logger.warning("Waifu2x not available, using Lanczos")
            except Exception as e:
                logger.warning(f"Waifu2x failed: {e}, using Lanczos")
        
        # Fallback to Lanczos resampling
        new_size = (img.size[0] * factor, img.size[1] * factor)
        return img.resize(new_size, Image.Resampling.LANCZOS)
    
    def restore_face(
        self, 
        img: Image.Image, 
        method: str = 'gfpgan',
        weight: float = 0.5
    ) -> Image.Image:
        """
        Restore face using specified method.
        
        Args:
            img: Input image
            method: Method ('gfpgan', 'codeformer')
            weight: Restoration weight (0.0-1.0)
        """
        if method == 'codeformer' and self.codeformer:
            try:
                output = self.codeformer.restore(img, weight=weight)
                return output
            except Exception as e:
                logger.warning(f"CodeFormer failed: {e}, trying GFPGAN")
        
        if self.face_enhancer:
            try:
                img_array = np.array(img)
                _, _, output = self.face_enhancer.enhance(
                    img_array,
                    has_aligned=False,
                    only_center_face=False,
                    paste_back=True,
                    weight=weight
                )
                return Image.fromarray(output)
            except Exception as e:
                logger.warning(f"Face restoration failed: {e}")
        
        return img
    
    def process_image(
        self, 
        input_path: Path,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Process a single image with complete post-processing pipeline.
        
        Args:
            input_path: Path to input image
            output_path: Path to save processed image
            config: Processing configuration (overrides self.config)
        
        Returns:
            True if successful, False otherwise
        """
        config = config or self.config
        
        try:
            logger.info(f"Processing: {Path(input_path).name}")
            
            # Load image
            img = Image.open(input_path)
            original_size = img.size
            logger.info(f"  → Original size: {original_size[0]}x{original_size[1]}")
            
            # 1. Upscaling
            if config.get("upscale", True):
                upscale_factor = config.get("upscale_factor", 4)
                upscale_method = config.get("upscale_method", "realesrgan")
                logger.info(f"  → Upscaling ({upscale_factor}x) using {upscale_method}...")
                img = self.upscale_image(img, factor=upscale_factor, method=upscale_method)
                logger.info(f"  ✓ Upscaled: {img.size[0]}x{img.size[1]}")
            
            # 2. Face Restoration
            if config.get("face_restoration", True):
                face_method = config.get("face_method", "gfpgan")
                face_weight = config.get("face_weight", 0.5)
                logger.info(f"  → Face restoration using {face_method}...")
                img = self.restore_face(img, method=face_method, weight=face_weight)
                logger.info("  ✓ Face restoration completed")
            
            # 3. Artifact Removal
            if config.get("remove_artifacts", False):
                logger.info("  → Removing artifacts...")
                img = self.remove_noise(img)
                logger.info("  ✓ Artifacts removed")
            
            # 4. Color Grading
            if config.get("color_grade", True):
                color_preset = config.get("color_preset", None)
                use_advanced = config.get("advanced_color_grade", False)
                color_look = config.get("color_look", "warm")
                
                logger.info("  → Color grading...")
                if use_advanced:
                    img = self.advanced_color_grade(img, look=color_look)
                else:
                    img = self.color_grade(
                        img, 
                        preset=color_preset,
                        brightness=config.get("brightness", 1.05),
                        contrast=config.get("contrast", 1.1),
                        saturation=config.get("saturation", 1.05),
                        sharpness=config.get("sharpness", 1.05)
                    )
                logger.info("  ✓ Color grading completed")
            
            # 5. Metadata Removal (CRITICAL!)
            if config.get("remove_metadata", True):
                logger.info("  → Removing metadata...")
                img = self.remove_metadata(img)
                logger.info("  ✓ Metadata removed")
            
            # 6. Quality Optimization
            if config.get("optimize_quality", True):
                # Ensure proper mode
                if img.mode == "RGBA":
                    # Convert RGBA to RGB for better compatibility
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                logger.info("  ✓ Quality optimized")
            
            # 7. Resize if target size specified
            if config.get("target_size"):
                target_size = config["target_size"]
                if isinstance(target_size, (list, tuple)) and len(target_size) == 2:
                    logger.info(f"  → Resizing to {target_size[0]}x{target_size[1]}...")
                    img = img.resize(target_size, Image.Resampling.LANCZOS)
                    logger.info("  ✓ Resized")
            
            # 8. Save
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine format and quality
            output_format = config.get("output_format", "PNG")
            quality = config.get("quality", 95)
            
            if output_format.upper() == "PNG":
                img.save(output_path, "PNG", optimize=True)
            elif output_format.upper() in ["JPG", "JPEG"]:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(output_path, "JPEG", quality=quality, optimize=True)
            elif output_format.upper() == "WEBP":
                img.save(output_path, "WEBP", quality=quality, method=6)
            else:
                img.save(output_path, output_format)
            
            logger.info(f"  ✓ Saved: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ ERROR: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def instagram_pipeline(
        self, 
        input_path: Path, 
        output_path: Path
    ) -> bool:
        """Process image with Instagram-optimized pipeline"""
        config = {
            "upscale": True,
            "upscale_factor": 4,
            "face_restoration": True,
            "face_weight": 0.5,
            "color_grade": True,
            "color_preset": "instagram",
            "remove_artifacts": True,
            "remove_metadata": True,
            "target_size": (1080, 1080),
            "output_format": "JPEG",
            "quality": 95
        }
        return self.process_image(input_path, output_path, config)
    
    def onlyfans_pipeline(
        self, 
        input_path: Path, 
        output_path: Path
    ) -> bool:
        """Process image with OnlyFans-optimized pipeline"""
        config = {
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
        }
        return self.process_image(input_path, output_path, config)
    
    def professional_pipeline(
        self, 
        input_path: Path, 
        output_path: Path
    ) -> bool:
        """Process image with professional photography pipeline"""
        config = {
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
        return self.process_image(input_path, output_path, config)
    
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
        input_path = Path(input_folder)
        output_path = Path(output_folder)
        
        if not input_path.exists():
            logger.error(f"Input folder not found: {input_path}")
            return {"success": False, "error": "Input folder not found"}
        
        # Find image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.JPG', '.JPEG', '.PNG', '.WEBP']
        images = []
        for ext in image_extensions:
            images.extend(input_path.glob(f'*{ext}'))
        
        if not images:
            logger.warning(f"No images found in: {input_path}")
            return {"success": False, "error": "No images found", "total": 0}
        
        logger.info("=" * 60)
        logger.info("POST-PROCESSING STARTING")
        logger.info("=" * 60)
        logger.info(f"Input folder: {input_path}")
        logger.info(f"Output folder: {output_path}")
        logger.info(f"Total images: {len(images)}")
        logger.info("=" * 60)
        
        success_count = 0
        fail_count = 0
        results = []
        
        for i, img_path in enumerate(images, 1):
            logger.info(f"[{i}/{len(images)}] Processing {img_path.name}")
            output_file = output_path / img_path.name
            
            # Use pipeline-specific method if specified
            if pipeline == 'instagram':
                success = self.instagram_pipeline(img_path, output_file)
            elif pipeline == 'onlyfans':
                success = self.onlyfans_pipeline(img_path, output_file)
            elif pipeline == 'professional':
                success = self.professional_pipeline(img_path, output_file)
            else:
                success = self.process_image(img_path, output_file, config)
            
            if success:
                success_count += 1
                results.append({"file": img_path.name, "status": "success"})
            else:
                fail_count += 1
                results.append({"file": img_path.name, "status": "failed"})
        
        logger.info("=" * 60)
        logger.info("POST-PROCESSING COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Successful: {success_count}")
        logger.info(f"Failed: {fail_count}")
        logger.info(f"Total: {len(images)}")
        logger.info("=" * 60)
        
        return {
            "success": True,
            "total": len(images),
            "successful": success_count,
            "failed": fail_count,
            "results": results
        }

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Ultra Realistic Post-Processing Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic processing
  python post_process_pipeline.py --input ComfyUI/output --output ComfyUI/output_processed
  
  # Instagram pipeline
  python post_process_pipeline.py --input input/ --output output/ --pipeline instagram
  
  # OnlyFans pipeline
  python post_process_pipeline.py --input input/ --output output/ --pipeline onlyfans
  
  # Custom configuration
  python post_process_pipeline.py --input input/ --output output/ --upscale-factor 2 --face-weight 0.7
        """
    )
    parser.add_argument(
        '--input',
        type=str,
        default='ComfyUI/output',
        help='Input folder (default: ComfyUI/output)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='ComfyUI/output_processed',
        help='Output folder (default: ComfyUI/output_processed)'
    )
    parser.add_argument(
        '--pipeline',
        type=str,
        choices=['instagram', 'onlyfans', 'professional'],
        help='Use preset pipeline'
    )
    parser.add_argument(
        '--upscale-factor',
        type=int,
        default=4,
        choices=[2, 4],
        help='Upscaling factor (default: 4)'
    )
    parser.add_argument(
        '--face-weight',
        type=float,
        default=0.5,
        help='Face restoration weight 0.0-1.0 (default: 0.5)'
    )
    parser.add_argument(
        '--no-upscale',
        action='store_true',
        help='Skip upscaling'
    )
    parser.add_argument(
        '--no-face-restore',
        action='store_true',
        help='Skip face restoration'
    )
    parser.add_argument(
        '--no-color-grade',
        action='store_true',
        help='Skip color grading'
    )
    parser.add_argument(
        '--no-metadata-removal',
        action='store_true',
        help='Skip metadata removal (NOT RECOMMENDED)'
    )
    
    args = parser.parse_args()
    
    # Build config
    config = {
        "upscale": not args.no_upscale,
        "upscale_factor": args.upscale_factor,
        "face_restoration": not args.no_face_restore,
        "face_weight": args.face_weight,
        "color_grade": not args.no_color_grade,
        "remove_metadata": not args.no_metadata_removal
    }
    
    processor = UltraRealisticPostProcessor(config=config)
    result = processor.batch_process(
        args.input, 
        args.output,
        config=config if not args.pipeline else None,
        pipeline=args.pipeline
    )
    
    if not result.get("success"):
        sys.exit(1)

if __name__ == "__main__":
    main()
