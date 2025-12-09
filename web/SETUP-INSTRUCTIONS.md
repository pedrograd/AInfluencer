# Web Application Setup Instructions

## Quick Start

1. **Install Dependencies**
   ```bash
   cd web
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm run dev
   ```

3. **Access the Application**
   - Open http://localhost:3000 in your browser
   - Ensure ComfyUI is running on http://localhost:8188

## Important Notes

### ComfyUI Integration

The web app connects directly to ComfyUI. Make sure:
- ComfyUI is running on `http://localhost:8188`
- Required models are installed
- IP-Adapter models are available for face consistency features

### Environment

- Copy `env.local.example` to `.env.local` to mirror the default demo-safe API settings.
- `NEXT_PUBLIC_*` variables are browser-visible; keep server-only values in the backend `.env`.

### Workflow Configuration

The workflow builder in `hooks/useGeneration.ts` uses a simplified structure. You may need to:
1. Export your actual ComfyUI workflow JSON
2. Update the `buildImageWorkflow` function to match your workflow structure
3. Ensure node IDs and connections match your ComfyUI setup

### Face Reference Upload

Face references are uploaded to ComfyUI's input folder. The workflow builder includes IP-Adapter integration, but you need to:
1. Ensure IP-Adapter nodes are properly configured in your workflow
2. Adjust node IDs in the workflow builder to match your setup
3. Test face consistency with a known working workflow

### Backend (Optional)

The FastAPI backend in `/backend` is optional but provides:
- File upload handling
- Media management
- Character persistence
- WebSocket support

To use the backend:
```bash
cd backend
pip install -r requirements.txt
python main.py
```

Then update the API client to use `http://localhost:8000` instead of direct ComfyUI connection.

## Troubleshooting

### "ComfyUI Disconnected" Error
- Check if ComfyUI is running
- Verify the URL in `lib/api/comfyui.ts`
- Check browser console for CORS errors

### Generation Not Starting
- Check ComfyUI console for errors
- Verify workflow JSON structure
- Ensure all required models are loaded

### Face Consistency Not Working
- Verify IP-Adapter models are installed
- Check workflow includes IP-Adapter nodes
- Ensure face reference is properly uploaded

## Next Steps

1. **Customize Workflow**: Update the workflow builder to match your ComfyUI setup
2. **Add Models**: Configure model selection in the UI
3. **Enhance Features**: Add video generation, post-processing, etc.
4. **Backend Integration**: Connect to FastAPI backend for full feature set
5. **Testing**: Test all features with real ComfyUI instance

## Development Tips

- Use browser DevTools to inspect API calls
- Check ComfyUI console for workflow errors
- Test with simple prompts first
- Gradually add complexity (face references, batch generation, etc.)
