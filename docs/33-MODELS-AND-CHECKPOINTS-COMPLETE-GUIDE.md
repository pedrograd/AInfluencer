# Models and Checkpoints Complete Guide
## Comprehensive AI Model Recommendations for Ultra-Realistic Content

**Version:** 1.0  
**Date:** January 2025  
**Status:** Active Reference  
**Document Owner:** CTO/ML Engineer

---

## Executive Summary

This document provides a comprehensive guide to all recommended AI models, checkpoints, and tools for generating ultra-realistic images and videos. Each model is evaluated based on quality, speed, realism, and use case.

### Quick Reference
- **Best Overall Quality**: Flux.1 [dev], Realistic Vision V6.0
- **Best Speed**: Flux.1 [schnell], SDXL Turbo
- **Best for Faces**: Realistic Vision V6.0, Juggernaut XL V9
- **Best for Video**: Stable Video Diffusion (SVD), AnimateDiff
- **Best for Control**: ControlNet, IP-Adapter Plus

---

## Image Generation Models

### Tier 1: Ultra-Realistic (Highest Quality)

#### 1. Flux.1 [dev]
- **Quality**: ⭐⭐⭐⭐⭐ (10/10)
- **Speed**: ⭐⭐ (Slow - 3-5 min/image)
- **Realism**: ⭐⭐⭐⭐⭐ (Exceptional)
- **Use Case**: Final production, highest quality needs
- **VRAM**: 12GB+ required
- **Download**: https://huggingface.co/black-forest-labs/FLUX.1-dev
- **Size**: ~24GB
- **Best For**: Professional photography, OnlyFans content, premium content
- **Notes**: Latest and greatest, requires significant VRAM

#### 2. Realistic Vision V6.0
- **Quality**: ⭐⭐⭐⭐⭐ (9.5/10)
- **Speed**: ⭐⭐⭐⭐ (Fast - 1-2 min/image)
- **Realism**: ⭐⭐⭐⭐⭐ (Excellent)
- **Use Case**: General purpose, ultra-realistic images
- **VRAM**: 8GB+ required
- **Download**: https://civitai.com/models/4201/realistic-vision-v60-b1
- **Size**: ~7GB
- **Best For**: Instagram posts, general content, face consistency
- **Notes**: Most popular realistic model, excellent face quality

#### 3. Juggernaut XL V9
- **Quality**: ⭐⭐⭐⭐⭐ (9.5/10)
- **Speed**: ⭐⭐⭐⭐ (Fast - 1-2 min/image)
- **Realism**: ⭐⭐⭐⭐⭐ (Excellent)
- **Use Case**: Professional content, high detail
- **VRAM**: 8GB+ required
- **Download**: https://civitai.com/models/133005/juggernaut-xl-v9
- **Size**: ~7GB
- **Best For**: Professional photography, detailed content
- **Notes**: Excellent detail and quality

#### 4. DreamShaper XL
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐⭐ (Fast - 1-2 min/image)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: Artistic realism, creative content
- **VRAM**: 8GB+ required
- **Download**: https://civitai.com/models/112902/dreamshaper-xl
- **Size**: ~7GB
- **Best For**: Artistic content, creative variations
- **Notes**: Good balance of realism and artistry

### Tier 2: High Quality (Fast Generation)

#### 5. Flux.1 [schnell]
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐⭐⭐ (Very Fast - 30-60 sec/image)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: Quick generation, batch processing
- **VRAM**: 12GB+ required
- **Download**: https://huggingface.co/black-forest-labs/FLUX.1-schnell
- **Size**: ~24GB
- **Best For**: Rapid prototyping, batch generation
- **Notes**: Fast version of Flux, still excellent quality

#### 6. SDXL Turbo
- **Quality**: ⭐⭐⭐⭐ (8.5/10)
- **Speed**: ⭐⭐⭐⭐⭐ (Very Fast - 20-40 sec/image)
- **Realism**: ⭐⭐⭐⭐ (Good)
- **Use Case**: Fast generation, real-time preview
- **VRAM**: 8GB+ required
- **Download**: https://huggingface.co/stabilityai/sdxl-turbo
- **Size**: ~7GB
- **Best For**: Quick iterations, testing prompts
- **Notes**: Fastest SDXL variant, good quality

#### 7. ZavyChromaXL
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐⭐ (Fast - 1-2 min/image)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: Vibrant, colorful content
- **VRAM**: 8GB+ required
- **Download**: https://civitai.com/models/119229/zavychromaxl
- **Size**: ~7GB
- **Best For**: Colorful content, vibrant images
- **Notes**: Excellent color reproduction

#### 8. CrystalClearXL
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐⭐ (Fast - 1-2 min/image)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: Sharp, detailed content
- **VRAM**: 8GB+ required
- **Download**: https://civitai.com/models/123456/crystalclear-xl
- **Size**: ~7GB
- **Best For**: Detailed content, sharp images
- **Notes**: Excellent detail and sharpness

### Tier 3: Standard Models (Good Quality)

#### 9. SDXL Base
- **Quality**: ⭐⭐⭐ (8/10)
- **Speed**: ⭐⭐⭐⭐ (Fast - 1-2 min/image)
- **Realism**: ⭐⭐⭐ (Good)
- **Use Case**: General purpose, baseline
- **VRAM**: 8GB+ required
- **Download**: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
- **Size**: ~7GB
- **Best For**: General content, starting point
- **Notes**: Official SDXL, good baseline

#### 10. Stable Diffusion 3.0
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐ (Medium - 2-3 min/image)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: Latest SD technology
- **VRAM**: 10GB+ required
- **Download**: https://huggingface.co/stabilityai/stable-diffusion-3-medium-diffusers
- **Size**: ~5GB
- **Best For**: Latest features, advanced generation
- **Notes**: New architecture, excellent quality

#### 11. Stable Cascade
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐ (Medium - 2-3 min/image)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: High quality, detailed content
- **VRAM**: 10GB+ required
- **Download**: https://huggingface.co/stabilityai/stable-cascade
- **Size**: ~15GB
- **Best For**: Detailed content, high quality
- **Notes**: Multi-stage generation, excellent quality

### Tier 4: Specialized Models

#### 12. PixArt Alpha
- **Quality**: ⭐⭐⭐ (8/10)
- **Speed**: ⭐⭐⭐⭐⭐ (Very Fast - 20-30 sec/image)
- **Realism**: ⭐⭐⭐ (Good)
- **Use Case**: Fast generation, lower VRAM
- **VRAM**: 6GB+ required
- **Download**: https://huggingface.co/PixArt-alpha/PixArt-alpha
- **Size**: ~5GB
- **Best For**: Quick generation, lower-end GPUs
- **Notes**: Fast, efficient model

#### 13. HunyuanDiT
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐ (Medium - 2-3 min/image)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: Chinese model, good quality
- **VRAM**: 10GB+ required
- **Download**: https://huggingface.co/Tencent/HunyuanDiT
- **Size**: ~10GB
- **Best For**: Alternative to SDXL, good quality
- **Notes**: Tencent model, excellent results

#### 14. Lumina Image 2.0
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐ (Medium - 2-3 min/image)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: Advanced generation
- **VRAM**: 10GB+ required
- **Download**: https://huggingface.co/black-forest-labs/Lumina-T2I-2.0
- **Size**: ~10GB
- **Best For**: High-quality content
- **Notes**: Advanced architecture

---

## Video Generation Models

### Tier 1: Best Quality

#### 1. Stable Video Diffusion (SVD)
- **Quality**: ⭐⭐⭐⭐⭐ (9.5/10)
- **Speed**: ⭐⭐⭐ (Medium - 3-5 min/30s video)
- **Realism**: ⭐⭐⭐⭐⭐ (Excellent)
- **Use Case**: High-quality video generation
- **VRAM**: 12GB+ required
- **Download**: https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt
- **Size**: ~5GB
- **Best For**: Professional videos, high quality
- **Notes**: Best overall video quality

#### 2. SVD XT (Extended)
- **Quality**: ⭐⭐⭐⭐⭐ (9.5/10)
- **Speed**: ⭐⭐⭐ (Medium - 4-6 min/30s video)
- **Realism**: ⭐⭐⭐⭐⭐ (Excellent)
- **Use Case**: Longer videos, extended duration
- **VRAM**: 12GB+ required
- **Download**: https://huggingface.co/stabilityai/stable-video-diffusion-img2vid-xt-1-1
- **Size**: ~5GB
- **Best For**: Longer videos, extended content
- **Notes**: Extended version of SVD

#### 3. AnimateDiff
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐⭐ (Fast - 2-4 min/30s video)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: Smooth animations, character movement
- **VRAM**: 10GB+ required
- **Download**: https://huggingface.co/guoyww/animatediff-motion-adapter-v1-5-2
- **Size**: ~200MB
- **Best For**: Character animations, smooth motion
- **Notes**: Excellent for character consistency

### Tier 2: Good Quality

#### 4. ModelScope
- **Quality**: ⭐⭐⭐⭐ (8.5/10)
- **Speed**: ⭐⭐⭐ (Medium - 3-5 min/30s video)
- **Realism**: ⭐⭐⭐⭐ (Good)
- **Use Case**: Chinese video model, good quality
- **VRAM**: 10GB+ required
- **Download**: https://huggingface.co/damo-vilab/modelscope-damo-text-to-video-synthesis
- **Size**: ~3GB
- **Best For**: Alternative to SVD, good results
- **Notes**: Chinese model, good quality

#### 5. HunyuanVideo
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐ (Medium - 3-5 min/30s video)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: Tencent video model
- **VRAM**: 12GB+ required
- **Download**: https://huggingface.co/Tencent/HunyuanVideo
- **Size**: ~8GB
- **Best For**: High-quality video, Tencent model
- **Notes**: Excellent quality, large model

#### 6. Cosmos T2V
- **Quality**: ⭐⭐⭐⭐ (8.5/10)
- **Speed**: ⭐⭐⭐ (Medium - 3-5 min/30s video)
- **Realism**: ⭐⭐⭐⭐ (Good)
- **Use Case**: Text-to-video generation
- **VRAM**: 10GB+ required
- **Download**: https://huggingface.co/black-forest-labs/Cosmos-T2V
- **Size**: ~5GB
- **Best For**: Text-to-video, good quality
- **Notes**: Direct text-to-video

#### 7. WAN22 T2V
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐ (Medium - 3-5 min/30s video)
- **Realism**: ⭐⭐⭐⭐ (Very Good)
- **Use Case**: Advanced video generation
- **VRAM**: 12GB+ required
- **Download**: https://huggingface.co/wan-research/wan22-t2v
- **Size**: ~6GB
- **Best For**: Advanced video, high quality
- **Notes**: Latest WAN model

---

## Face Consistency Models

### 1. IP-Adapter Plus
- **Quality**: ⭐⭐⭐⭐⭐ (9.5/10)
- **Speed**: ⭐⭐⭐⭐ (Fast)
- **Compatibility**: All SD models
- **Download**: https://huggingface.co/lllyasviel/sd-controlnet
- **Size**: ~200MB
- **Best For**: General face consistency
- **Notes**: Most versatile, works with all models

### 2. InstantID
- **Quality**: ⭐⭐⭐⭐⭐ (10/10)
- **Speed**: ⭐⭐⭐⭐ (Fast)
- **Compatibility**: SDXL, SD 1.5
- **Download**: https://huggingface.co/InstantX/InstantID
- **Size**: ~500MB
- **Best For**: Best face consistency quality
- **Notes**: Superior face control, requires InsightFace

### 3. FaceID
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐⭐ (Fast)
- **Compatibility**: SDXL
- **Download**: https://huggingface.co/lllyasviel/faceid
- **Size**: ~300MB
- **Best For**: Alternative to InstantID
- **Notes**: Good alternative option

### 4. InsightFace (Required for InstantID)
- **Purpose**: Face analysis and embedding
- **Download**: https://github.com/deepinsight/insightface
- **Size**: ~100MB
- **Required**: Yes (for InstantID)
- **Notes**: Must be installed for InstantID

---

## Post-Processing Models

### Upscaling Models

#### 1. Real-ESRGAN x4plus
- **Quality**: ⭐⭐⭐⭐⭐ (9.5/10)
- **Speed**: ⭐⭐⭐⭐ (Fast)
- **Use Case**: General upscaling
- **Download**: https://github.com/xinntao/Real-ESRGAN/releases
- **Size**: ~70MB
- **Best For**: General purpose upscaling
- **Notes**: Most popular upscaler

#### 2. 4x-UltraSharp
- **Quality**: ⭐⭐⭐⭐⭐ (10/10)
- **Speed**: ⭐⭐⭐ (Medium)
- **Use Case**: Maximum quality upscaling
- **Download**: https://github.com/tsurumeso/4x-UltraSharp
- **Size**: ~100MB
- **Best For**: Highest quality upscaling
- **Notes**: Best quality, slower

#### 3. ESRGAN
- **Quality**: ⭐⭐⭐⭐ (9/10)
- **Speed**: ⭐⭐⭐⭐ (Fast)
- **Use Case**: Fast upscaling
- **Download**: https://github.com/xinntao/ESRGAN
- **Size**: ~70MB
- **Best For**: Quick upscaling
- **Notes**: Fast alternative

### Face Restoration Models

#### 1. GFPGAN
- **Quality**: ⭐⭐⭐⭐⭐ (9.5/10)
- **Speed**: ⭐⭐⭐⭐ (Fast)
- **Use Case**: Face restoration
- **Download**: https://github.com/TencentARC/GFPGAN
- **Size**: ~350MB
- **Best For**: General face restoration
- **Notes**: Most popular face restorer

#### 2. CodeFormer
- **Quality**: ⭐⭐⭐⭐⭐ (10/10)
- **Speed**: ⭐⭐⭐ (Medium)
- **Use Case**: Highest quality face restoration
- **Download**: https://github.com/sczhou/CodeFormer
- **Size**: ~200MB
- **Best For**: Maximum quality restoration
- **Notes**: Best quality, slower

---

## Control Models

### ControlNet Models

#### 1. ControlNet OpenPose
- **Purpose**: Pose control
- **Download**: https://huggingface.co/lllyasviel/sd-controlnet-openpose
- **Use Case**: Control character poses
- **Notes**: Essential for pose control

#### 2. ControlNet Depth
- **Purpose**: Depth map control
- **Download**: https://huggingface.co/lllyasviel/sd-controlnet-depth
- **Use Case**: Control scene depth
- **Notes**: Great for composition control

#### 3. ControlNet Canny
- **Purpose**: Edge detection control
- **Download**: https://huggingface.co/lllyasviel/sd-controlnet-canny
- **Use Case**: Control edges and shapes
- **Notes**: Good for structure control

---

## Recommended Model Combinations

### Best Quality Setup
1. **Primary Model**: Flux.1 [dev] or Realistic Vision V6.0
2. **Face Consistency**: InstantID + InsightFace
3. **Upscaling**: 4x-UltraSharp
4. **Face Restoration**: CodeFormer
5. **Control**: ControlNet (as needed)

### Best Speed Setup
1. **Primary Model**: Flux.1 [schnell] or SDXL Turbo
2. **Face Consistency**: IP-Adapter Plus
3. **Upscaling**: Real-ESRGAN x4plus
4. **Face Restoration**: GFPGAN
5. **Control**: ControlNet (as needed)

### Balanced Setup
1. **Primary Model**: Realistic Vision V6.0 or Juggernaut XL V9
2. **Face Consistency**: IP-Adapter Plus or InstantID
3. **Upscaling**: Real-ESRGAN x4plus
4. **Face Restoration**: GFPGAN
5. **Control**: ControlNet (as needed)

### Video Setup
1. **Video Model**: Stable Video Diffusion (SVD)
2. **Face Consistency**: IP-Adapter Plus (for video)
3. **Upscaling**: Real-ESRGAN x4plus (for video)
4. **Frame Interpolation**: RIFE or DAIN
5. **Post-Processing**: FFmpeg

---

## Model Download Instructions

### Automatic Download (Recommended)
```powershell
# Run the automatic download script
.\download-models-auto.ps1
```

### Manual Download
1. Visit the model's Hugging Face or Civitai page
2. Download the model file (.safetensors or .ckpt)
3. Place in appropriate folder:
   - Checkpoints: `ComfyUI/models/checkpoints/`
   - ControlNet: `ComfyUI/models/controlnet/`
   - Upscalers: `ComfyUI/models/upscale_models/`
   - Face Restore: `ComfyUI/models/face_restore/`
   - IP-Adapter: `ComfyUI/models/ipadapter/`

### Model Organization
```
ComfyUI/models/
├── checkpoints/          # Main generation models
├── controlnet/          # ControlNet models
├── upscale_models/      # Upscaling models
├── face_restore/        # Face restoration
├── ipadapter/           # IP-Adapter models
├── instantid/           # InstantID models
└── insightface/         # InsightFace models
```

---

## Model Comparison Table

| Model | Quality | Speed | VRAM | Size | Best For |
|-------|---------|-------|------|------|----------|
| Flux.1 [dev] | 10/10 | Slow | 12GB+ | 24GB | Ultimate quality |
| Realistic Vision V6.0 | 9.5/10 | Fast | 8GB+ | 7GB | General purpose |
| Juggernaut XL V9 | 9.5/10 | Fast | 8GB+ | 7GB | Professional |
| Flux.1 [schnell] | 9/10 | Very Fast | 12GB+ | 24GB | Fast generation |
| SDXL Turbo | 8.5/10 | Very Fast | 8GB+ | 7GB | Quick iterations |
| SVD (Video) | 9.5/10 | Medium | 12GB+ | 5GB | Video generation |
| AnimateDiff | 9/10 | Fast | 10GB+ | 200MB | Character animation |

---

## Usage Recommendations

### For Instagram Content
- **Primary Model**: Realistic Vision V6.0
- **Face Consistency**: InstantID
- **Upscaling**: Real-ESRGAN x4plus
- **Aspect Ratio**: 1:1 or 4:5

### For OnlyFans Content
- **Primary Model**: Flux.1 [dev] or Realistic Vision V6.0
- **Face Consistency**: InstantID
- **Upscaling**: 4x-UltraSharp
- **Face Restoration**: CodeFormer
- **Aspect Ratio**: 9:16 or 16:9

### For Video Content
- **Video Model**: Stable Video Diffusion (SVD)
- **Face Consistency**: IP-Adapter Plus
- **Frame Interpolation**: RIFE
- **Resolution**: 1080p minimum

### For Batch Generation
- **Primary Model**: Flux.1 [schnell] or SDXL Turbo
- **Face Consistency**: IP-Adapter Plus
- **Upscaling**: Real-ESRGAN x4plus (post-processing)
- **Batch Size**: 10-50 images

---

## Troubleshooting

### Model Loading Issues
- **Problem**: Model won't load
- **Solution**: Check VRAM requirements, reduce batch size

### Quality Issues
- **Problem**: Poor quality output
- **Solution**: Use higher quality model, increase steps, adjust CFG scale

### Speed Issues
- **Problem**: Generation too slow
- **Solution**: Use faster model (schnell/turbo), reduce steps, optimize settings

### Face Consistency Issues
- **Problem**: Face not consistent
- **Solution**: Use InstantID, improve face reference images, adjust face strength

---

## Model Updates

Models are constantly being updated. Check these sources regularly:
- **Hugging Face**: https://huggingface.co/models
- **Civitai**: https://civitai.com
- **GitHub**: Model repositories
- **Discord**: Community announcements

---

**Document Status**: ✅ Complete - Active Reference

**Last Updated**: January 2025

**Next Review**: Monthly (check for new models)
