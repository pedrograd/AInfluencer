# AI Models & Workflow Configuration

## Model Priority List (2025 Best Practices)

### Image Generation - Face Consistency Priority

#### Tier 1: Best Quality (Use First)
1. **InstantID** - Highest face consistency (9.5/10)
   - Best for: Character consistency across images
   - Setup: ComfyUI node or custom implementation
   - Requirements: Face embedding preprocessing
   - Weight: 0.7-0.9 for close-ups

2. **IP-Adapter Plus** - Excellent consistency (9/10)
   - Best for: General face consistency
   - Setup: ComfyUI or Automatic1111 extension
   - Weight: 0.7-0.85

#### Tier 2: Alternative Methods
3. **FaceID** - Good alternative (9/10)
4. **LoRA Training** - Best long-term (10/10, requires training)
5. **IP-Adapter + ControlNet** - Enhanced control (9/10)

### Image Generation - Base Models

#### Recommended Models (Download Priority)
1. **Realistic Vision V6.0** (PRIMARY)
   - Quality: 9.5/10 for realism
   - Size: ~6GB
   - Best for: Ultra-realistic portraits
   - Download: Hugging Face

2. **Juggernaut XL V9**
   - Quality: 9/10
   - Best for: Professional photography look

3. **DreamShaper XL**
   - Quality: 9/10
   - Best for: Versatile, various styles

4. **SDXL Base 1.0**
   - Quality: 8.5/10
   - Best for: Foundation/fine-tuning base

### Video Generation Models (2025)

#### Latest & Best Options
1. **Kling AI 2.5 Turbo** (RECOMMENDED)
   - Quality: 9.5/10 realism
   - Best for: Ultra-realistic human motion
   - API or local implementation
   - Excellent expression capture

2. **Veo 3** (Google DeepMind)
   - Quality: 9.5/10
   - Best for: 4K, long videos (1+ minute)
   - Latest: December 2025

3. **Runway Gen-4**
   - Quality: 9/10
   - Best for: 10-second clips, character consistency
   - Supports various aspect ratios

4. **Sora 2** (OpenAI)
   - Quality: 9/10
   - Best for: Short clips, extensions
   - Has digital watermarks

5. **Seedance** (ByteDance)
   - Quality: 9.5/10
   - Best for: Exceptional realism, affordability
   - Popular globally

#### Fallback Options (Open Source)
6. **Stable Video Diffusion (SVD)**
   - Quality: 9/10
   - Best for: Local, open-source solution

7. **AnimateDiff v2**
   - Quality: 8.5/10
   - Best for: Free, flexible generation

### Text Generation (LLM)

#### Primary: Ollama (Local, Free)
1. **Llama 3 8B** (RECOMMENDED)
   - Quality: 9/10 for creative content
   - Speed: Fast
   - Best for: Captions, personality simulation

2. **Llama 3 70B** (Higher Quality)
   - Quality: 9.5/10
   - Speed: Medium
   - Use when: Quality > Speed

3. **Mistral 7B**
   - Quality: 8.5/10
   - Speed: Very Fast
   - Best for: Quick responses

### Voice Generation (TTS)

#### Primary: Coqui TTS XTTS-v2
- Quality: 9/10 (very natural)
- Voice cloning: Yes (6 seconds audio needed)
- Languages: Multi-language
- Free: Open source
- Speed: Real-time capable

#### Alternative: Bark
- Quality: 9.5/10 (most natural)
- Speed: Slower
- Use when: Quality is critical

## Workflow Node System (ComfyUI-Style)

### Core Workflow Nodes

#### 1. Model Manager Node
- List available models
- Download models from Hugging Face/Civitai
- Switch between models
- Show model metadata (size, quality, type)

#### 2. Face Embedding Node
- Extract face embeddings from reference images
- Support multiple reference images
- Store embeddings in database
- Cache embeddings for reuse

#### 3. Image Generation Node
- Base model selection
- Face consistency application (InstantID/IP-Adapter)
- Prompt processing
- Parameter control (steps, CFG, sampler)
- Batch generation support

#### 4. Video Generation Node
- Video model selection (Kling, Veo 3, etc.)
- Frame generation
- Face consistency in video
- Audio integration
- Post-processing pipeline

#### 5. Post-Processing Node
- Upscaling (Real-ESRGAN, 4x-UltraSharp)
- Face restoration (GFPGAN, CodeFormer)
- Color grading
- Artifact removal
- Quality validation

#### 6. Text Generation Node
- LLM selection (Ollama models)
- Character persona injection
- Prompt templates
- Response generation
- Personality consistency

#### 7. Voice Generation Node
- Voice cloning from reference audio
- TTS generation
- Emotion control
- Background music mixing
- Audio normalization

#### 8. Quality Check Node
- Face detection validation
- Artifact detection
- Consistency check (compare to reference)
- Resolution validation
- Content appropriateness check

### Workflow Templates

#### Standard Image Generation Workflow
```
1. Model Manager → Select Realistic Vision V6.0
2. Face Embedding → Extract from character reference
3. Image Generation → Apply face + prompt
4. Post-Processing → Upscale + Face Restore
5. Quality Check → Validate output
6. Content Library → Store approved content
```

#### Video Generation Workflow
```
1. Model Manager → Select Kling 2.5 Turbo
2. Face Embedding → Extract from character
3. Video Generation → Generate frames with face consistency
4. Audio Generation → Generate voiceover (if needed)
5. Post-Processing → Frame interpolation + color grading
6. Quality Check → Validate video quality
7. Content Library → Store video
```

## Model Download & Management

### Automatic Model Management
- Check Hugging Face for model updates
- Download models on-demand or pre-download popular ones
- Verify model checksums
- Organize models by type (checkpoints, LoRAs, embeddings)
- Support drag-and-drop model import

### Model Organization Structure
```
models/
├── checkpoints/
│   ├── realistic-vision-v6.0.safetensors
│   ├── juggernaut-xl-v9.safetensors
│   └── ...
├── loras/
│   └── character-specific-loras/
├── embeddings/
│   └── face-embeddings/
├── video/
│   ├── kling-2.5-turbo/
│   ├── veo-3/
│   └── ...
└── audio/
    └── tts-models/
```

## Configuration Best Practices

### Face Consistency Settings
- **Close-up portraits**: Weight 0.8-0.9
- **Medium shots**: Weight 0.7-0.85
- **Full-body shots**: Weight 0.5-0.7
- Use multiple reference images (3-5) for better consistency

### Generation Parameters
- **Steps**: 25-30 for base, 50+ for final quality
- **CFG Scale**: 7-9 for realistic images
- **Sampler**: DPM++ 2M Karras or Euler a
- **Resolution**: 1024x1024 base, upscale to 2048x2048+

### Anti-Detection Techniques
- Vary generation parameters slightly between images
- Add natural imperfections (slight blur, natural lighting variations)
- Use different backgrounds and poses
- Remove metadata from generated images
- Slight color variations to avoid patterns

## Integration Priority

### Phase 1: Core Models
1. Realistic Vision V6.0 (Image)
2. InstantID (Face Consistency)
3. Ollama Llama 3 8B (Text)
4. Coqui XTTS-v2 (Voice)

### Phase 2: Video Models
1. Kling 2.5 Turbo (Primary)
2. Stable Video Diffusion (Fallback)

### Phase 3: Advanced Options
1. LoRA training pipeline
2. Paid API integrations (optional)
3. Advanced post-processing

## Testing & Validation

### Model Testing Checklist
- [ ] Face consistency across 10+ images
- [ ] Quality meets realism standards
- [ ] Generation speed acceptable
- [ ] GPU memory usage within limits
- [ ] Works with different character types
- [ ] Post-processing improves quality
- [ ] Passes basic AI detection tests

### Quality Metrics
- Face similarity score: > 0.85 (compared to reference)
- Artifact detection: < 5% false positives
- Generation time: < 30s per image
- Memory usage: < 12GB VRAM per generation
