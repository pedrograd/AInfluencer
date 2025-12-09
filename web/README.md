# AInfluencer Web Application

Ultra-Realistic AI Media Generator Web Application built with Next.js 14+.

## Features

- 🎨 **Image Generation**: Create ultra-realistic images with AI
- 🎬 **Video Generation**: Generate videos (coming soon)
- 👤 **Face Consistency**: Maintain character consistency across generations using IP-Adapter
- 📚 **Media Library**: Browse and manage all your generated and uploaded media
- 🎭 **Character Management**: Create and manage character profiles with face references
- ⚡ **Real-Time Updates**: WebSocket integration for live generation progress

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI)
- **State Management**: Zustand
- **API Client**: Axios
- **Backend**: ComfyUI (running on `http://localhost:8188`)

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- ComfyUI running on `http://localhost:8188`
- Python 3.8+ (for backend, if needed)

### Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
```

2. Run the development server:
```bash
npm run dev
# or
yarn dev
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
web/
├── app/                    # Next.js app router pages
│   ├── generate/          # Generation pages
│   ├── library/           # Media library
│   ├── characters/        # Character management
│   └── api/               # API routes
├── components/            # React components
│   ├── ui/               # Base UI components
│   ├── generation/       # Generation components
│   ├── media/            # Media components
│   ├── character/        # Character components
│   └── layout/           # Layout components
├── lib/                   # Utilities and API clients
│   ├── api/              # API wrappers
│   ├── utils/            # Utility functions
│   └── stores/           # Zustand stores
├── types/                 # TypeScript type definitions
└── hooks/                # Custom React hooks
```

## Configuration

### ComfyUI Connection

The app connects to ComfyUI at `http://localhost:8188` by default. To change this, update the base URL in `lib/api/comfyui.ts`.

### Environment Variables

Create a `.env.local` file for environment-specific configuration:

```env
NEXT_PUBLIC_COMFYUI_URL=http://localhost:8188
```

## Features in Detail

### Image Generation

- Text-to-image generation with advanced controls
- Face reference upload for consistency
- Batch generation support
- Real-time progress tracking
- Quality presets (Fast/Balanced/Ultra)

### Face Consistency

- Upload face reference images
- IP-Adapter integration
- Adjustable face strength (0.0-1.0)
- Character-based face management

### Media Library

- Grid and list view modes
- Filter by type, source, date
- Search functionality
- Bulk operations
- Full-screen preview

### Character Management

- Create character profiles
- Upload multiple face references
- Track generation statistics
- Use characters in generation

## Development

### Adding New Components

Components follow the shadcn/ui pattern. Use the CLI or create components manually in `components/ui/`.

### API Integration

The ComfyUI API wrapper is in `lib/api/comfyui.ts`. Extend this for additional functionality.

### Styling

The app uses Tailwind CSS with a custom dark theme. Colors and styles are defined in `app/globals.css` and `tailwind.config.js`.

## Building for Production

```bash
npm run build
npm start
```

## Troubleshooting

### ComfyUI Connection Issues

- Ensure ComfyUI is running on `http://localhost:8188`
- Check firewall settings
- Verify WebSocket support

### Generation Failures

- Check ComfyUI console for errors
- Verify model files are installed
- Ensure IP-Adapter models are available for face consistency

## License

Private project - All rights reserved.
