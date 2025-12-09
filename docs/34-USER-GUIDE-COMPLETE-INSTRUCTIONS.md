# Complete User Guide & Instructions
## How to Use AInfluencer Platform - Step-by-Step Guide

**Version:** 1.0  
**Date:** January 2025  
**Status:** User Documentation  
**Document Owner:** CPO/Product Team

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Generating Images](#generating-images)
4. [Generating Videos](#generating-videos)
5. [Character Management](#character-management)
6. [Media Library](#media-library)
7. [Quality & Settings](#quality--settings)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)

---

## Getting Started

### First Time Setup

#### Step 1: Install the Application
1. Ensure you have:
   - Windows 10/11
   - NVIDIA GPU with 8GB+ VRAM (12GB+ recommended)
   - 100GB+ free disk space
   - Python 3.11+ installed

2. Run the setup script:
   ```powershell
   .\auto-complete-setup.ps1
   ```

3. Wait for installation to complete (30-60 minutes)

#### Step 2: Download AI Models
1. Run the model download script:
   ```powershell
   .\download-models-auto.ps1
   ```

2. Select which models to download:
   - **Essential**: Realistic Vision V6.0 (required)
   - **Recommended**: Flux.1 [schnell], IP-Adapter Plus
   - **Optional**: Additional models as needed

3. Wait for downloads to complete (depends on internet speed)

#### Step 3: Start the Application
1. Start all services:
   ```powershell
   .\start-all.ps1
   ```

2. Wait for services to start (1-2 minutes)

3. Open your browser and go to: `http://localhost:3000`

#### Step 4: Verify System Status
1. Check the Dashboard
2. Look for "ComfyUI Connected" status (green checkmark)
3. If disconnected, click "Retry" or check the backend service

---

## Dashboard Overview

### Main Dashboard

The dashboard is your home base. Here's what you'll see:

#### System Status Card
- **Green Checkmark**: System is ready
- **Red X**: System needs attention
- **Retry Button**: Reconnect to ComfyUI

#### Quick Actions
Four main action cards:
1. **Generate Image** - Create new images
2. **Generate Video** - Create new videos
3. **Media Library** - Browse all your content
4. **Characters** - Manage your characters

#### Statistics
- **Total Images**: Count of generated images
- **Total Videos**: Count of generated videos
- **Characters**: Number of active characters

### Navigation Menu

Located at the top of the page:
- **Dashboard** - Home page
- **Generate** - Image/Video generation
- **Library** - Media library
- **Characters** - Character management
- **Settings** - Application settings

---

## Generating Images

### Quick Start: Simple Mode

#### Step 1: Navigate to Image Generation
1. Click "Generate Image" from dashboard, OR
2. Go to `/generate/image` in the menu

#### Step 2: Enter Your Prompt
1. In the "Prompt" text area, describe what you want:
   ```
   Example: "A beautiful woman, 25 years old, long brown hair, 
   smiling, professional photography, high quality, realistic"
   ```

2. **Tips for Good Prompts**:
   - Be specific about appearance
   - Include quality keywords: "high quality", "realistic", "professional photography"
   - Describe the setting: "outdoor", "studio", "beach"
   - Mention style: "natural lighting", "soft focus"

#### Step 3: Select Character (Optional)
1. If you have characters created:
   - Click "Select Character"
   - Choose a character from the list
   - This ensures face consistency

2. If no characters:
   - You can create one later
   - Or generate without character (random face)

#### Step 4: Adjust Basic Settings
1. **Quality Preset**:
   - **Fast**: Quick generation (30-60 seconds)
   - **Balanced**: Good quality/speed (1-2 minutes)
   - **Ultra Quality**: Best quality (2-5 minutes)

2. **Aspect Ratio**:
   - **1:1** - Square (Instagram posts)
   - **4:5** - Portrait (Instagram stories)
   - **16:9** - Landscape (YouTube thumbnails)
   - **9:16** - Vertical (Stories, Reels)

#### Step 5: Generate
1. Click the "Generate Image" button
2. Wait for generation (progress bar shows status)
3. Image appears when complete
4. Click "Download" to save, or "Generate Another" to create more

### Advanced Mode: Full Control

#### Access Advanced Settings
1. Toggle "Advanced Mode" switch
2. Additional options appear

#### Advanced Options Explained

##### Model Selection
- **Primary Model**: Choose which AI model to use
  - **Realistic Vision V6.0**: Best for realism (recommended)
  - **Flux.1 [schnell]**: Fast generation
  - **Flux.1 [dev]**: Highest quality (slow)
  - **Juggernaut XL V9**: Professional quality

##### Generation Parameters
- **Steps**: Number of generation steps (20-100)
  - More steps = better quality but slower
  - Recommended: 30-50 for balanced
  - Ultra quality: 50-100

- **CFG Scale**: How closely to follow prompt (1-20)
  - Lower (1-7): More creative, less accurate
  - Balanced (7-12): Good balance (recommended)
  - Higher (12-20): Very accurate to prompt

- **Sampling Method**: Algorithm used
  - **DPM++ 2M Karras**: Best quality (recommended)
  - **Euler a**: Fast, good quality
  - **DDIM**: Stable, predictable

##### Face Consistency Settings
- **Face Reference**: Upload face image
- **Face Strength**: How strong face influence (0.0-1.0)
  - 0.5-0.7: Balanced (recommended)
  - 0.8-1.0: Very strong face match
  - 0.0-0.4: Subtle face influence

- **Face Method**:
  - **IP-Adapter Plus**: Works with all models (recommended)
  - **InstantID**: Best quality, requires setup

##### Post-Processing Options
- **Upscaling**: Increase image resolution
  - **2x**: Double resolution
  - **4x**: Quadruple resolution (recommended)
  - **8x**: Maximum resolution (slow)

- **Face Restoration**: Improve face quality
  - **GFPGAN**: Fast, good quality
  - **CodeFormer**: Best quality (slower)

- **Color Correction**: Auto-adjust colors
- **Noise Reduction**: Remove artifacts

##### Anti-Detection Settings
- **Remove Metadata**: Strip EXIF data (recommended)
- **Quality Variation**: Add natural variations
- **Artifact Removal**: Remove AI artifacts

#### Negative Prompt
Describe what you DON'T want:
```
Example: "blurry, low quality, distorted, ugly, 
deformed, bad anatomy, watermark, signature"
```

Common negative prompts:
- Quality issues: "blurry", "low quality", "pixelated"
- Anatomy issues: "bad anatomy", "deformed", "extra limbs"
- Artifacts: "watermark", "signature", "text"
- Style issues: "cartoon", "anime", "unrealistic"

---

## Generating Videos

### Quick Start: Simple Video Generation

#### Step 1: Navigate to Video Generation
1. Click "Generate Video" from dashboard, OR
2. Go to `/generate/video` in the menu

#### Step 2: Choose Video Type
1. **Text-to-Video**: Generate from text prompt
2. **Image-to-Video**: Animate an existing image (recommended)

#### Step 3: Enter Prompt or Upload Image
- **For Text-to-Video**: Enter description
- **For Image-to-Video**: Upload an image first

#### Step 4: Video Settings
1. **Duration**: 5, 10, 15, 30, or 60 seconds
2. **Resolution**: 720p, 1080p, or 4K
3. **Frame Rate**: 24fps, 30fps, or 60fps
4. **Quality**: Fast, Balanced, or Ultra Quality

#### Step 5: Generate
1. Click "Generate Video"
2. Wait for generation (progress shows frame-by-frame)
3. Video appears when complete
4. Click "Download" to save

### Advanced Video Settings

#### Video Model Selection
- **Stable Video Diffusion (SVD)**: Best quality (recommended)
- **AnimateDiff**: Smooth animations
- **ModelScope**: Alternative option

#### Motion Control
- **Motion Strength**: How much movement (0.0-1.0)
  - 0.3-0.5: Subtle movement
  - 0.6-0.8: Moderate movement (recommended)
  - 0.9-1.0: Strong movement

- **Motion Direction**: Control movement direction
- **Camera Movement**: Simulate camera motion

#### Face Consistency in Videos
- **Face Reference**: Upload face image
- **Temporal Consistency**: Maintain face across frames
- **Face Tracking**: Track face in motion

#### Post-Processing
- **Frame Interpolation**: Increase frame rate (60fps, 120fps)
- **Video Upscaling**: Increase resolution
- **Color Grading**: Apply color effects
- **Stabilization**: Remove camera shake

---

## Character Management

### Creating a Character

#### Step 1: Navigate to Characters
1. Click "Characters" from dashboard, OR
2. Go to `/characters` in the menu

#### Step 2: Create New Character
1. Click "Create New Character" button

#### Step 3: Character Information
1. **Name**: Give your character a name
2. **Description**: Describe the character
   - Age, appearance, personality
   - Style preferences
   - Content type

#### Step 4: Face Reference
1. **Upload Face Image**:
   - Click "Upload Face Reference"
   - Select a clear, front-facing photo
   - Best: High quality, good lighting, neutral expression
   - Avoid: Sunglasses, masks, side profiles

2. **Multiple References** (optional):
   - Upload 2-5 additional face images
   - Different angles, expressions
   - Improves face consistency

#### Step 5: Appearance Settings
1. **Hair Color**: Select or describe
2. **Eye Color**: Select or describe
3. **Body Type**: Select or describe
4. **Style Preferences**: Describe preferred style

#### Step 6: Save Character
1. Click "Save Character"
2. Character appears in your character list

### Using Characters

#### When Generating Content
1. Select character from dropdown
2. Face consistency automatically applied
3. All generated content uses this character's face

#### Managing Characters
- **Edit**: Click edit icon to modify
- **Delete**: Click delete icon (careful - cannot undo)
- **View Stats**: See generation count, quality scores
- **Export**: Download character config
- **Import**: Upload character config

---

## Media Library

### Browsing Your Media

#### View Options
1. **Grid View**: Thumbnail grid (default)
2. **List View**: Detailed list with metadata
3. **Full Screen**: Click image for full view

#### Filtering & Search
1. **Search Bar**: Search by filename, tags, or description
2. **Filters**:
   - **Type**: Images, Videos, All
   - **Date**: Today, This Week, This Month, All Time
   - **Quality**: High (8+), Medium (5-7), Low (<5)
   - **Character**: Filter by character
   - **Tags**: Filter by tags

#### Sorting
- **Date**: Newest first, Oldest first
- **Quality**: Highest first, Lowest first
- **Size**: Largest first, Smallest first
- **Name**: A-Z, Z-A

### Organizing Media

#### Creating Folders
1. Click "New Folder"
2. Enter folder name
3. Drag media into folder

#### Tagging Media
1. Select media (click checkbox)
2. Click "Add Tags"
3. Enter tags (comma-separated)
4. Tags help with search and organization

#### Collections
1. Create collections for specific projects
2. Add media to collections
3. Quick access to related content

### Media Actions

#### Single Media
- **View**: Click to view full size
- **Download**: Download original file
- **Edit**: Edit metadata, tags
- **Delete**: Remove from library
- **Share**: Generate shareable link

#### Bulk Actions
1. Select multiple media (checkboxes)
2. Choose action:
   - **Download**: Download as ZIP
   - **Delete**: Delete selected
   - **Move**: Move to folder
   - **Tag**: Add tags to all
   - **Export**: Export metadata

---

## Quality & Settings

### Quality Assurance

#### Automatic Quality Scoring
- Every generated image/video gets a quality score (0-10)
- Scores displayed in media library
- Filter by quality to find best content

#### Quality Improvement
1. **Use Better Models**: Flux.1 [dev], Realistic Vision V6.0
2. **Increase Steps**: 50-100 steps for ultra quality
3. **Adjust CFG Scale**: 7-12 for balanced quality
4. **Enable Post-Processing**: Upscaling, face restoration
5. **Use Face References**: Better face consistency = better quality

### Application Settings

#### Access Settings
1. Click "Settings" in navigation menu
2. Or go to `/settings` directly

#### Generation Settings
- **Default Model**: Set preferred model
- **Default Quality**: Fast, Balanced, or Ultra
- **Default Steps**: 20-100
- **Default CFG Scale**: 1-20
- **Auto-Upscale**: Enable/disable automatic upscaling
- **Auto-Face-Restore**: Enable/disable automatic face restoration

#### Storage Settings
- **Media Location**: Where files are stored
- **Auto-Organize**: Automatically organize by date/character
- **Cleanup**: Delete low-quality content automatically
- **Backup**: Enable automatic backups

#### Performance Settings
- **Batch Size**: How many images to generate at once
- **Queue Priority**: Priority system for jobs
- **GPU Memory**: Optimize GPU memory usage
- **Cache**: Enable/disable caching

#### UI Settings
- **Theme**: Dark or Light mode
- **Language**: Interface language
- **Notifications**: Enable/disable notifications
- **Keyboard Shortcuts**: Customize shortcuts

---

## Troubleshooting

### Common Issues

#### "ComfyUI Disconnected"
**Problem**: Backend service not running

**Solutions**:
1. Check if backend is running:
   ```powershell
   # Check backend process
   Get-Process python
   ```

2. Restart backend:
   ```powershell
   .\start-all.ps1
   ```

3. Check backend logs for errors
4. Verify ComfyUI is installed correctly

#### "Out of Memory" Error
**Problem**: GPU VRAM insufficient

**Solutions**:
1. Use smaller model (SDXL instead of Flux)
2. Reduce batch size
3. Lower resolution
4. Close other GPU applications
5. Use "Fast" quality preset

#### "Generation Failed"
**Problem**: Generation error occurred

**Solutions**:
1. Check error message for details
2. Try simpler prompt
3. Reduce steps or CFG scale
4. Try different model
5. Check system logs

#### "Poor Quality Results"
**Problem**: Generated content looks bad

**Solutions**:
1. Use better model (Realistic Vision V6.0, Flux.1)
2. Improve your prompt (be more specific)
3. Increase steps (50-100)
4. Adjust CFG scale (7-12)
5. Enable post-processing (upscaling, face restoration)
6. Use face reference for consistency

#### "Face Not Consistent"
**Problem**: Face changes between generations

**Solutions**:
1. Use InstantID (best face consistency)
2. Upload better face reference (clear, front-facing)
3. Increase face strength (0.7-1.0)
4. Use multiple face references
5. Check face reference quality

### Getting Help

1. **Check Documentation**: Read relevant guides
2. **Search FAQ**: Common questions answered
3. **Check Logs**: Review error logs for details
4. **Community**: Join Discord/forum for help
5. **Report Issue**: Submit bug report with details

---

## Best Practices

### Prompt Writing
1. **Be Specific**: Detailed descriptions = better results
2. **Use Quality Keywords**: "high quality", "realistic", "professional"
3. **Describe Lighting**: "natural lighting", "studio lighting"
4. **Mention Style**: "photography", "cinematic", "portrait"
5. **Avoid Negatives**: Focus on what you want, not what you don't

### Face Consistency
1. **Use Clear References**: High quality, front-facing photos
2. **Multiple References**: 2-5 images from different angles
3. **Use InstantID**: Best face consistency method
4. **Test First**: Generate test images before batch
5. **Adjust Strength**: Find optimal face strength (0.5-0.8)

### Quality Optimization
1. **Start with Good Model**: Realistic Vision V6.0 or Flux.1
2. **Use Appropriate Steps**: 30-50 for balanced, 50-100 for ultra
3. **Enable Post-Processing**: Upscaling and face restoration
4. **Batch Generate**: Generate multiple, pick best
5. **Review Quality Scores**: Filter by quality in library

### Workflow Efficiency
1. **Use Templates**: Save successful prompts as templates
2. **Batch Processing**: Generate multiple at once
3. **Organize Early**: Tag and folder from start
4. **Quality Filter**: Delete low-quality content regularly
5. **Backup Important**: Backup your best content

---

## FAQ

### General Questions

**Q: How long does image generation take?**
A: Depends on quality and model:
- Fast: 30-60 seconds
- Balanced: 1-2 minutes
- Ultra Quality: 2-5 minutes

**Q: What GPU do I need?**
A: Minimum 8GB VRAM, recommended 12GB+. NVIDIA GPU required.

**Q: Can I use this offline?**
A: Yes! All processing is local. No internet required after setup.

**Q: Is this free?**
A: Yes, completely free and open-source.

**Q: Can I use my own photos?**
A: Yes! Upload personal photos and mix with AI content.

### Technical Questions

**Q: Which model is best?**
A: For quality: Flux.1 [dev] or Realistic Vision V6.0. For speed: Flux.1 [schnell] or SDXL Turbo.

**Q: How do I improve face consistency?**
A: Use InstantID with clear face references. Upload 2-5 reference images.

**Q: Can I generate videos?**
A: Yes! Use Stable Video Diffusion (SVD) for best quality.

**Q: How do I upscale images?**
A: Enable "Upscaling" in post-processing settings. Use 4x for best results.

**Q: What's the maximum resolution?**
A: Depends on model and VRAM. Typically 1024x1024 to 2048x2048 for images.

### Content Questions

**Q: Can I use this for Instagram?**
A: Yes! Use 1:1 or 4:5 aspect ratio for Instagram posts.

**Q: Can I use this for OnlyFans?**
A: Yes! Use 9:16 or 16:9 aspect ratio for OnlyFans content.

**Q: How do I make content undetectable?**
A: Enable anti-detection settings, remove metadata, use quality variation.

**Q: Can I maintain character consistency?**
A: Yes! Create characters with face references for consistent faces.

**Q: How many characters can I create?**
A: Unlimited! Create as many characters as you want.

---

## Quick Reference

### Keyboard Shortcuts
- **Ctrl+G**: Generate image
- **Ctrl+V**: Generate video
- **Ctrl+L**: Open library
- **Ctrl+C**: Create character
- **Ctrl+S**: Save current settings
- **Esc**: Close dialogs

### Aspect Ratios by Platform
- **Instagram Post**: 1:1 (1080x1080)
- **Instagram Story**: 9:16 (1080x1920)
- **Instagram Reel**: 9:16 (1080x1920)
- **OnlyFans**: 16:9 or 9:16
- **YouTube Thumbnail**: 16:9 (1280x720)
- **Twitter**: 16:9 or 1:1

### Recommended Settings by Use Case

**Instagram Posts**:
- Model: Realistic Vision V6.0
- Quality: Balanced
- Aspect Ratio: 1:1
- Upscaling: 4x
- Face Restoration: GFPGAN

**OnlyFans Content**:
- Model: Flux.1 [dev] or Realistic Vision V6.0
- Quality: Ultra Quality
- Aspect Ratio: 9:16
- Upscaling: 4x
- Face Restoration: CodeFormer
- Anti-Detection: Enabled

**Batch Generation**:
- Model: Flux.1 [schnell] or SDXL Turbo
- Quality: Fast
- Batch Size: 10-50
- Post-Processing: After generation

---

**Document Status**: ✅ Complete - User Ready

**Last Updated**: January 2025

**Feedback**: Please report any unclear instructions or missing information
