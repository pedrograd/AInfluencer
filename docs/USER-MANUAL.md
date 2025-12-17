# AInfluencer User Manual

**Version:** 1.0  
**Last Updated:** 2025-12-17  
**Platform:** AInfluencer v6

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Dashboard Overview](#dashboard-overview)
4. [Character Management](#character-management)
5. [Content Generation](#content-generation)
6. [Model Management](#model-management)
7. [Video Generation](#video-generation)
8. [Analytics & Insights](#analytics--insights)
9. [ComfyUI Management](#comfyui-management)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Introduction

### What is AInfluencer?

AInfluencer is a fully automated, self-hosted platform for creating and managing AI-generated influencer characters across multiple social media platforms. With AInfluencer, you can:

- Create unlimited AI influencer characters with unique personalities and appearances
- Generate ultra-realistic images and videos automatically
- Maintain character consistency across all content
- Manage multiple social media platforms from one dashboard
- Automate content creation, posting, and engagement

### Key Features

- ✅ **Fully Automated**: Zero manual intervention required
- ✅ **Free & Open-Source**: No costs, full source code access
- ✅ **Ultra-Realistic**: Indistinguishable from real content
- ✅ **Multi-Platform**: Instagram, Twitter, Facebook, Telegram, OnlyFans, YouTube
- ✅ **Character Consistency**: Advanced face/style consistency
- ✅ **Self-Hosted**: Privacy and data control

---

## Getting Started

### System Requirements

**Minimum Requirements:**
- 4 CPU cores
- 16GB RAM
- 8GB GPU VRAM
- 500GB SSD storage
- Python 3.11+ and Node.js 20+

**Recommended Requirements:**
- 8 CPU cores
- 32GB RAM
- 24GB GPU VRAM
- 1TB NVMe SSD
- Ubuntu 22.04+ LTS, macOS, or Windows (WSL2)

### Installation

#### Option 1: Using the Installer (Recommended)

1. **Access the Installer**
   - Open your browser and navigate to `http://localhost:3000/installer`
   - Or click "Installer" from the main dashboard

2. **System Check**
   - The installer will automatically check your system requirements
   - Review the checklist and ensure all requirements are met

3. **Start Installation**
   - Click "Start Installation" to begin
   - The installer will:
     - Install Python dependencies
     - Install Node.js dependencies
     - Set up PostgreSQL database
     - Configure Redis
     - Create necessary environment files
     - Run database migrations

4. **Monitor Progress**
   - Watch the real-time installation progress
   - Review installation logs if needed
   - Wait for completion confirmation

#### Option 2: Manual Installation

For detailed manual installation instructions, see [`docs/DEVELOPMENT-SETUP.md`](./DEVELOPMENT-SETUP.md).

### First Launch

1. **Start Services**
   - Backend: `cd backend && uvicorn app.main:app --reload --port 8000`
   - Frontend: `cd frontend && npm run dev`
   - Database: Ensure PostgreSQL is running
   - Redis: Ensure Redis is running

2. **Access Dashboard**
   - Open `http://localhost:3000` in your browser
   - You should see the main dashboard with system status

3. **Verify Services**
   - Check that all services show "Running" status:
     - Backend (port 8000)
     - Frontend (port 3000)
     - ComfyUI (port 8188)
     - Database connection

---

## Dashboard Overview

### Main Dashboard (`/`)

The main dashboard provides an overview of your entire AInfluencer system.

#### System Status Section

- **Backend Status**: Shows if the FastAPI backend is running
- **Frontend Status**: Shows if the Next.js frontend is running
- **ComfyUI Status**: Shows if ComfyUI service is running and reachable
- **System Health**: Overall system status (OK, Warning, or Error)

#### Quick Actions

- **Characters**: Navigate to character management
- **Generate**: Go to content generation page
- **Model Manager**: Access AI model management
- **Videos**: Navigate to video generation

#### Recent Activity

- View recent system logs
- Monitor errors and warnings
- Track service status changes

#### Error Monitoring

- View error aggregation by source and level
- See recent errors with timestamps
- Filter errors by source or severity

### Navigation

Use the navigation menu or quick action cards to access different sections:

- **Home**: Main dashboard
- **Characters**: Character management
- **Generate**: Image generation
- **Models**: AI model management
- **Videos**: Video generation
- **Analytics**: Performance analytics
- **ComfyUI**: ComfyUI service management

---

## Character Management

### Creating a Character

1. **Navigate to Characters**
   - Click "Characters" from the dashboard or navigate to `/characters`

2. **Create New Character**
   - Click "Create Character" button
   - Fill in character details:
     - **Name**: Character's display name
     - **Bio**: Character description
     - **Personality**: Personality traits and characteristics
     - **Appearance**: Physical description
     - **Face Reference**: Upload a reference image for face consistency

3. **Save Character**
   - Click "Create" to save the character
   - You'll be redirected to the character detail page

### Character List View

- **View All Characters**: See all your created characters in a grid or list view
- **Search**: Use the search bar to find specific characters
- **Filter**: Filter characters by various attributes
- **Quick Actions**: Edit or delete characters directly from the list

### Character Detail Page

Each character has a dedicated detail page (`/characters/[id]`) with:

#### Overview Tab
- Character information and statistics
- Recent activity
- Quick actions

#### Content Tab
- All generated content for this character
- Filter and search content
- Preview and download images

#### Styles Tab
- Manage character image styles
- Upload style reference images
- Configure style parameters

#### Activity Tab
- Character activity timeline
- Content generation history
- Platform posting history

### Editing a Character

1. Navigate to the character detail page
2. Click "Edit" button or go to `/characters/[id]/edit`
3. Update character information:
   - Basic information (name, bio)
   - Personality traits
   - Appearance details
   - Face reference images
4. Click "Save" to update

### Character Face Consistency

AInfluencer maintains character consistency using:

- **Face Embeddings**: Extracted from reference images
- **Normalized Storage**: Face images stored with metadata
- **Reusable Embeddings**: Use the same face across multiple generations

**To set up face consistency:**

1. Upload a clear face reference image when creating/editing a character
2. The system will automatically extract face embeddings
3. All future content generation will use these embeddings for consistency

---

## Content Generation

### Image Generation (`/generate`)

#### Basic Generation

1. **Navigate to Generate Page**
   - Click "Generate" from the dashboard

2. **Configure Generation**
   - **Prompt**: Enter your image generation prompt
   - **Character**: Select a character (optional, for face consistency)
   - **Model**: Choose an AI model
   - **Settings**: Adjust generation parameters:
     - Width/Height
     - Steps
     - CFG Scale
     - Seed (optional)

3. **Generate Image**
   - Click "Generate" button
   - Monitor progress in real-time
   - View generated image when complete

#### Batch Generation

- Generate multiple images at once
- Use batch prompts or variations
- Monitor all jobs in the queue

#### Job Management

- **View Status**: Check generation job status
- **View Results**: See generated images
- **Download**: Download generated images
- **Rank**: Rate and rank generated images
- **Stats**: View generation statistics

### Image Storage

All generated images are automatically:
- Saved to local storage
- Tagged with metadata
- Linked to characters (if applicable)
- Available in the content library

---

## Model Management

### Model Manager (`/models`)

The Model Manager allows you to browse, download, and manage AI models.

#### Browsing Models

1. **View Catalog**
   - Browse available models from the catalog
   - Filter by type (checkpoint, LoRA, embedding, etc.)
   - Search for specific models

2. **Model Information**
   - View model details (size, type, quality tier)
   - See model descriptions and use cases
   - Check download requirements

#### Downloading Models

1. **Select Model**
   - Click on a model from the catalog
   - Review model information

2. **Download**
   - Click "Download" button
   - Monitor download progress
   - View download queue

3. **Verify Installation**
   - Models are automatically verified after download
   - Check installation status in "Installed" tab

#### Managing Installed Models

- **View Installed**: See all installed models
- **Sync Models**: Sync with ComfyUI model directory
- **Delete Models**: Remove unused models
- **Import Models**: Import models from local files

#### Custom Models

- Add custom model URLs
- Import local model files
- Manage custom model catalog

---

## Video Generation

### Video Generation (`/videos`)

AInfluencer supports video generation for reels, shorts, and TikTok content.

#### Creating Videos

1. **Navigate to Videos Page**
   - Click "Videos" from the dashboard

2. **Configure Video**
   - Select character (for face consistency)
   - Choose video type (reel, short, TikTok)
   - Set video parameters:
     - Duration
     - Frame rate
     - Resolution

3. **Generate Video**
   - Click "Generate" button
   - Monitor generation progress
   - Preview video when complete

#### Video Management

- View all generated videos
- Preview videos in browser
- Download videos
- Manage video library

---

## Analytics & Insights

### Analytics Dashboard (`/analytics`)

The Analytics dashboard provides insights into your content and character performance.

#### Key Metrics

- **Content Statistics**: Total images/videos generated
- **Character Performance**: Engagement metrics per character
- **Generation Quality**: Average quality scores
- **Platform Metrics**: Performance across platforms

#### Reports

- View detailed analytics reports
- Export data for external analysis
- Track trends over time

---

## ComfyUI Management

### ComfyUI Manager (`/comfyui`)

Manage the ComfyUI service directly from the dashboard.

#### Installation

1. **Check Installation Status**
   - View if ComfyUI is installed
   - See installation path

2. **Install ComfyUI**
   - Click "Install" if not installed
   - Monitor installation progress

#### Service Control

- **Start ComfyUI**: Start the ComfyUI service
- **Stop ComfyUI**: Stop the running service
- **Restart**: Restart the service

#### Monitoring

- **View Logs**: Real-time ComfyUI logs
- **Check Status**: Service health and status
- **View Stats**: Service statistics and metrics

#### Model Sync

- Sync models with ComfyUI directory
- Verify model installation
- Manage model paths

---

## Troubleshooting

### Common Issues

#### Services Not Starting

**Problem**: Backend, frontend, or ComfyUI won't start

**Solutions**:
1. Check if ports are already in use:
   - Backend: `lsof -i :8000` (macOS/Linux) or `netstat -ano | findstr :8000` (Windows)
   - Frontend: `lsof -i :3000` (macOS/Linux) or `netstat -ano | findstr :3000` (Windows)
   - ComfyUI: `lsof -i :8188` (macOS/Linux) or `netstat -ano | findstr :8188` (Windows)

2. Verify environment variables in `.env` files
3. Check service logs for error messages
4. Ensure dependencies are installed

#### Database Connection Errors

**Problem**: Cannot connect to PostgreSQL

**Solutions**:
1. Verify PostgreSQL is running:
   - macOS: `brew services list | grep postgresql`
   - Linux: `sudo systemctl status postgresql`

2. Check connection string in `.env`:
   ```
   AINFLUENCER_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ainfluencer
   ```

3. Verify database exists:
   ```bash
   psql -l | grep ainfluencer
   ```

#### Redis Connection Errors

**Problem**: Cannot connect to Redis

**Solutions**:
1. Check if Redis is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. Start Redis if needed:
   - macOS: `brew services start redis`
   - Linux: `sudo systemctl start redis`

#### Image Generation Fails

**Problem**: Images not generating or errors during generation

**Solutions**:
1. Verify ComfyUI is running and reachable
2. Check that required models are installed
3. Review ComfyUI logs for errors
4. Verify GPU is available and has sufficient VRAM
5. Check generation service logs

#### Character Face Consistency Issues

**Problem**: Generated images don't maintain character face

**Solutions**:
1. Ensure face reference image is clear and high quality
2. Verify face embeddings were extracted successfully
3. Check character detail page for embedding status
4. Re-upload face reference if needed

### Getting Help

1. **Check Logs**: Review system logs in the dashboard
2. **Error Monitoring**: Check the error aggregation section
3. **Documentation**: Review technical documentation in `docs/`
4. **Community**: Check GitHub issues and discussions

---

## Best Practices

### Character Creation

- **Use High-Quality References**: Upload clear, well-lit face reference images
- **Detailed Descriptions**: Provide detailed personality and appearance descriptions
- **Consistent Naming**: Use consistent naming conventions for characters

### Content Generation

- **Clear Prompts**: Write detailed, specific prompts for better results
- **Test Settings**: Experiment with different generation parameters
- **Batch Generation**: Use batch generation for multiple variations
- **Quality Review**: Review and rank generated content regularly

### Model Management

- **Organize Models**: Keep models organized by type and purpose
- **Regular Sync**: Sync models with ComfyUI regularly
- **Storage Management**: Monitor disk space and remove unused models
- **Quality Tiers**: Use appropriate quality tier models for your needs

### Performance Optimization

- **GPU Utilization**: Ensure GPU is properly utilized for generation
- **Resource Monitoring**: Monitor system resources (CPU, RAM, GPU)
- **Queue Management**: Manage generation queues efficiently
- **Storage**: Keep sufficient disk space for generated content

### Security & Privacy

- **Self-Hosted**: Keep your instance self-hosted for privacy
- **Environment Variables**: Secure your `.env` files
- **Database Security**: Use strong database passwords
- **Regular Backups**: Backup your database and content regularly

---

## Additional Resources

### Documentation

- **Product Requirements**: [`docs/PRD.md`](./PRD.md)
- **Technical Architecture**: [`docs/02-TECHNICAL-ARCHITECTURE.md`](./02-TECHNICAL-ARCHITECTURE.md)
- **Development Setup**: [`docs/DEVELOPMENT-SETUP.md`](./DEVELOPMENT-SETUP.md)
- **API Reference**: [`docs/27-API-REFERENCE.md`](./27-API-REFERENCE.md)
- **Deployment Guide**: [`docs/15-DEPLOYMENT-DEVOPS.md`](./15-DEPLOYMENT-DEVOPS.md)

### Quick References

- **Quick Start**: [`docs/QUICK-START.md`](./QUICK-START.md)
- **Troubleshooting**: See [Troubleshooting](#troubleshooting) section above
- **Feature Roadmap**: [`docs/03-FEATURE-ROADMAP.md`](./03-FEATURE-ROADMAP.md)

---

## Support

For issues, questions, or contributions:

1. **GitHub Issues**: Report bugs and request features
2. **Documentation**: Check the `docs/` folder for detailed guides
3. **Community**: Join discussions and get help from the community

---

**Last Updated**: 2025-12-17  
**Version**: 1.0
