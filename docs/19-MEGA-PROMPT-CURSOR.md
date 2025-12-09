# Mega Prompt for Cursor AI
## Generate Comprehensive Documentation Files

**Purpose:** Copy and paste this prompt into Cursor AI to generate additional comprehensive documentation files for the AInfluencer project.

**Usage:** Paste this entire prompt into Cursor AI chat, and it will generate the requested documentation files.

---

## PROMPT START (Copy Everything Below)

```
You are an expert technical writer, CPO, CTO, and CEO working on the AInfluencer platform project. 
I need you to create comprehensive, detailed documentation files in Markdown format.

PROJECT CONTEXT:
- AInfluencer is a fully automated, self-hosted platform for creating and managing AI-generated influencer characters
- Focus: Ultra-realistic AI content generation for Instagram and OnlyFans
- Technology: Python/FastAPI backend, Next.js frontend, Stable Diffusion, NVIDIA GPU required
- Goal: Create content indistinguishable from real human photos and videos

EXISTING DOCUMENTATION STRUCTURE:
The project already has these documents in the docs/ folder:
- 01-PRD.md (Product Requirements Document)
- 02-TECHNICAL-ARCHITECTURE.md (Tech stack and architecture)
- 04-AI-MODELS-REALISM.md (AI models and realism strategies)
- 18-AI-TOOLS-NVIDIA-SETUP.md (Complete NVIDIA GPU setup guide)

YOUR TASK:
Create the following comprehensive documentation files. Each file should be:
1. Extremely detailed and thorough
2. Professional and well-structured
3. Include step-by-step instructions where applicable
4. Include code examples, configurations, and best practices
5. Follow the same format and style as existing documentation
6. Include tables, checklists, and visual structure where helpful
7. Target audience: Developers, AI engineers, and technical users

FILES TO CREATE:

1. FILE: docs/20-ADVANCED-PROMPT-ENGINEERING.md
   CONTENT: Comprehensive guide on prompt engineering for ultra-realistic content
   - Prompt structure and components
   - Character description templates
   - Style and quality modifiers
   - Negative prompts (what to avoid)
   - Platform-specific prompts (Instagram vs OnlyFans)
   - Prompt optimization techniques
   - Examples of excellent prompts
   - Common mistakes and how to avoid them
   - Prompt testing and iteration
   - Advanced techniques (weighting, attention, etc.)

2. FILE: docs/21-FACE-CONSISTENCY-MASTER-GUIDE.md
   CONTENT: Complete guide to maintaining face consistency
   - Comparison of all face consistency methods (IP-Adapter, InstantID, FaceID, LoRA)
   - Step-by-step setup for each method
   - When to use which method
   - Creating perfect face reference images
   - Troubleshooting face consistency issues
   - Advanced techniques (multiple reference images, style transfer)
   - Quality metrics for face consistency
   - Best practices and tips

3. FILE: docs/22-VIDEO-GENERATION-COMPLETE-GUIDE.md
   CONTENT: Comprehensive video generation guide
   - All video generation methods (AnimateDiff, SVD, ModelScope)
   - Setup and installation for each
   - Face consistency in videos
   - Video quality optimization
   - Frame interpolation techniques
   - Audio synchronization
   - Video post-processing pipeline
   - Platform-specific video requirements (Instagram Reels, OnlyFans videos)
   - Troubleshooting video generation issues
   - Best practices for realistic video content

4. FILE: docs/23-POST-PROCESSING-MASTER-WORKFLOW.md
   CONTENT: Complete post-processing workflow guide
   - Image upscaling techniques (Real-ESRGAN, 4x-UltraSharp, etc.)
   - Face restoration methods (GFPGAN, CodeFormer)
   - Color grading and correction
   - Artifact removal techniques
   - Metadata removal (critical for undetectability)
   - Batch processing workflows
   - Automation scripts
   - Quality assurance checklists
   - Tools and software recommendations
   - Workflow optimization

5. FILE: docs/24-ANTI-DETECTION-ADVANCED-TECHNIQUES.md
   CONTENT: Advanced anti-detection strategies
   - AI detection tool analysis
   - How detection works (technical deep dive)
   - Techniques to avoid detection
   - Content humanization methods
   - Metadata manipulation
   - Image fingerprinting avoidance
   - Testing against detection tools
   - Continuous improvement strategies
   - Red teaming your own content
   - Legal and ethical considerations

6. FILE: docs/25-AUTOMATION-WORKFLOWS.md
   CONTENT: Complete automation workflow documentation
   - Automated content generation pipelines
   - Batch processing workflows
   - Quality control automation
   - Content approval workflows
   - Scheduling and posting automation
   - Error handling and retry logic
   - Monitoring and alerting
   - Performance optimization
   - Scaling strategies
   - Code examples and scripts

7. FILE: docs/26-CHARACTER-MANAGEMENT-SYSTEM.md
   CONTENT: Character creation and management guide
   - Character persona development
   - Appearance configuration
   - Style guide creation
   - Content preferences
   - Character consistency rules
   - Multi-character management
   - Character templates
   - Export/import functionality
   - Best practices
   - Examples and templates

8. FILE: docs/27-PLATFORM-INTEGRATION-DETAILED.md
   CONTENT: Detailed platform integration guides
   - Instagram integration (API + browser automation)
   - Twitter/X integration
   - Facebook integration
   - Telegram integration
   - OnlyFans integration (browser automation focus)
   - YouTube integration
   - Rate limiting strategies
   - Error handling per platform
   - Authentication methods
   - Best practices for each platform

9. FILE: docs/28-QUALITY-ASSURANCE-SYSTEM.md
   CONTENT: Quality assurance and testing framework
   - Automated quality scoring
   - Realism checklists
   - AI detection testing
   - Manual review processes
   - Quality metrics and KPIs
   - Rejection criteria
   - Quality improvement workflows
   - Testing tools and scripts
   - Quality dashboard
   - Continuous improvement

10. FILE: docs/29-PRODUCTION-DEPLOYMENT.md
    CONTENT: Production deployment guide
    - Server setup and configuration
    - GPU optimization
    - Database setup and optimization
    - Security hardening
    - Monitoring and logging
    - Backup strategies
    - Scaling strategies
    - Performance tuning
    - Disaster recovery
    - Maintenance procedures

11. FILE: docs/30-TROUBLESHOOTING-COMPLETE.md
    CONTENT: Comprehensive troubleshooting guide
    - Common issues and solutions
    - GPU-related problems
    - Model loading issues
    - Generation quality problems
    - Performance issues
    - Integration problems
    - Error codes and meanings
    - Diagnostic tools
    - Getting help and support
    - FAQ section

12. FILE: docs/31-BEST-PRACTICES-COMPLETE.md
    CONTENT: Complete best practices guide
    - Content creation best practices
    - Technical best practices
    - Workflow optimization
    - Quality standards
    - Security best practices
    - Performance best practices
    - Legal compliance
    - Ethical considerations
    - Community guidelines
    - Success stories and case studies

FORMATTING REQUIREMENTS:
- Use proper Markdown formatting
- Include code blocks with syntax highlighting
- Use tables for comparisons
- Include checklists where appropriate
- Add section dividers (---)
- Include table of contents for long documents
- Use consistent heading hierarchy
- Include code examples with explanations
- Add warnings and important notes where needed
- Include links to related documentation

TONE AND STYLE:
- Professional and technical
- Clear and concise
- Step-by-step where applicable
- Include practical examples
- Assume technical competence but explain complex concepts
- Be thorough and comprehensive
- Include both theory and practical application

SPECIFIC REQUIREMENTS:
- Each file should be 2000-5000 words minimum
- Include real, working code examples
- Include configuration examples
- Include troubleshooting sections
- Include best practices sections
- Include references to other documentation files
- Include version numbers and dates
- Include document metadata (purpose, reading order, related documents)

CRITICAL FOCUS AREAS:
1. Ultra-realism: Content must be indistinguishable from real photos/videos
2. Face consistency: Same character face across all content
3. Anti-detection: Content must pass AI detection tests
4. Quality: Only high-quality content (8+ rating)
5. Automation: Minimize manual work
6. Free tools: Focus on free, open-source solutions
7. NVIDIA GPU: All guides assume NVIDIA GPU usage

Now, create all 12 documentation files as specified above. Each file should be comprehensive, detailed, and ready for production use.
```

## PROMPT END

---

## How to Use This Prompt

### Step 1: Open Cursor AI
1. Open Cursor IDE
2. Navigate to your project
3. Open the chat/command panel (usually Ctrl+L or Cmd+L)

### Step 2: Paste the Prompt
1. Copy the entire prompt above (from "PROMPT START" to "PROMPT END")
2. Paste it into the Cursor AI chat
3. Press Enter to send

### Step 3: Wait for Generation
- Cursor AI will generate all 12 documentation files
- This may take several minutes
- Files will be created in the `docs/` folder

### Step 4: Review and Refine
1. Review each generated file
2. Check for accuracy and completeness
3. Add any missing information
4. Update with project-specific details
5. Test code examples if applicable

### Step 5: Integrate with Existing Docs
1. Update cross-references between documents
2. Ensure consistent formatting
3. Update table of contents in main README
4. Verify all links work

---

## Alternative: Generate Files Individually

If generating all files at once is too much, you can generate them one at a time:

### Example for Single File:
```
Create a comprehensive documentation file: docs/20-ADVANCED-PROMPT-ENGINEERING.md

This file should be a complete guide on prompt engineering for ultra-realistic AI content generation.

Include:
- Prompt structure and components
- Character description templates
- Style and quality modifiers
- Negative prompts
- Platform-specific prompts
- Examples and best practices

Format: Professional Markdown, 2000+ words, with code examples and tables.
```

---

## Tips for Best Results

1. **Be Specific:** The more specific your requirements, the better the output
2. **Provide Context:** Include relevant information about your project
3. **Request Examples:** Ask for code examples and configurations
4. **Iterate:** Generate, review, and refine
5. **Test:** Verify code examples work in your environment

---

## Expected Output

After running this prompt, you should have:
- 12 comprehensive documentation files
- Each file 2000-5000 words
- Professional formatting
- Code examples and configurations
- Step-by-step guides
- Best practices and troubleshooting

---

**Document Status:** ✅ Ready to Use

**Last Updated:** January 2025

