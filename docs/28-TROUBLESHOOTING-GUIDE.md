# Troubleshooting Guide

**Version:** 1.0  
**Last Updated:** 2025-12-17  
**Purpose:** Comprehensive troubleshooting guide for common issues and solutions

---

## Quick Navigation

- [Installation & Setup Issues](#installation--setup-issues)
- [Service Startup Problems](#service-startup-problems)
- [Database & Redis Issues](#database--redis-issues)
- [ComfyUI Integration Issues](#comfyui-integration-issues)
- [Image Generation Problems](#image-generation-problems)
- [Character & Face Consistency Issues](#character--face-consistency-issues)
- [API & Backend Errors](#api--backend-errors)
- [Frontend Issues](#frontend-issues)
- [Performance Problems](#performance-problems)
- [General Diagnostics](#general-diagnostics)

---

## Installation & Setup Issues

### Python Not Found

**Symptoms:**
- Launcher fails to start backend
- Error: "Python not found" or "python: command not found"

**Solutions:**

1. **Verify Python Installation:**
   ```bash
   python --version
   # or
   python3 --version
   ```
   Should show Python 3.12 or 3.13

2. **Install Python:**
   - **Windows:** Run `scripts/setup/install_python_windows.ps1`
   - **macOS:** Run `scripts/setup/install_python_macos.sh`
   - **Linux:** `sudo apt-get install python3.12` (or use your package manager)

3. **Verify PATH:**
   - Ensure Python is in your system PATH
   - Windows: Check System Environment Variables
   - macOS/Linux: Check `echo $PATH`

4. **Use Dashboard:**
   - Open dashboard Setup tab
   - Click "Fix All" to auto-install missing dependencies

**Prevention:** System check should catch this before launcher runs

---

### Node.js Not Found

**Symptoms:**
- Launcher fails to start frontend
- Error: "Node.js not found" or "node: command not found"

**Solutions:**

1. **Verify Node.js Installation:**
   ```bash
   node --version
   npm --version
   ```
   Should show Node.js LTS version (18.x or 20.x)

2. **Install Node.js:**
   - **Windows:** Run `scripts/setup/install_node_windows.ps1`
   - **macOS:** Run `scripts/setup/install_node_macos.sh`
   - **Linux:** Use NodeSource repository or nvm

3. **Verify Installation:**
   ```bash
   which node
   which npm
   ```

4. **Use Dashboard:**
   - Open dashboard Setup tab
   - Click "Fix All" to auto-install missing dependencies

**Prevention:** System check should catch this before launcher runs

---

### Missing Dependencies

**Symptoms:**
- Import errors in Python
- Module not found errors
- npm package errors

**Solutions:**

1. **Backend Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   # or
   pip3 install -r requirements.txt
   ```

2. **Frontend Dependencies:**
   ```bash
   cd frontend
   npm install
   ```

3. **Verify Installation:**
   ```bash
   # Backend
   python -m pip list | grep fastapi
   
   # Frontend
   npm list --depth=0
   ```

---

## Service Startup Problems

### Port Already in Use

**Symptoms:**
- Backend fails to start: "Port 8000 already in use"
- Frontend fails to start: "Port 3000 already in use"
- ComfyUI fails to start: "Port 8188 already in use"

**Solutions:**

1. **Find Process Using Port:**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   netstat -ano | findstr :3000
   netstat -ano | findstr :8188
   
   # macOS/Linux
   lsof -i :8000
   lsof -i :3000
   lsof -i :8188
   ```

2. **Stop the Process:**
   ```bash
   # Windows (replace PID with actual process ID)
   taskkill /PID <PID> /F
   
   # macOS/Linux
   kill -9 <PID>
   ```

3. **Change Port (Alternative):**
   - Edit `.env` file to change port assignments
   - Update `BACKEND_PORT`, `FRONTEND_PORT`, or `COMFYUI_PORT`

4. **Prevention:**
   - Launcher should check port availability before starting
   - Use port scanning before service startup

---

### Backend Health Check Failed

**Symptoms:**
- Backend starts but `/api/health` returns error
- Dashboard shows backend as unhealthy
- 500 errors from backend API

**Solutions:**

1. **Check Backend Logs:**
   ```bash
   # View latest logs
   tail -f runs/latest/backend.log
   
   # Or check dashboard Logs tab
   ```

2. **Common Issues:**
   - **Import Errors:** Missing Python dependencies
     ```bash
     cd backend
     pip install -r requirements.txt
     ```
   - **Database Connection:** See [Database & Redis Issues](#database--redis-issues)
   - **Environment Variables:** Check `.env` file configuration

3. **Verify Backend Service:**
   ```bash
   curl http://localhost:8000/api/health
   # Should return: {"status":"healthy"}
   ```

4. **Restart Backend:**
   - Stop launcher
   - Check logs for errors
   - Fix issues
   - Restart launcher

---

### Frontend Health Check Failed

**Symptoms:**
- Frontend starts but doesn't respond
- Dashboard shows frontend as unhealthy
- Browser shows connection errors

**Solutions:**

1. **Check Frontend Logs:**
   ```bash
   # View latest logs
   tail -f runs/latest/frontend.log
   
   # Or check dashboard Logs tab
   ```

2. **Common Issues:**
   - **Build Errors:** Check for TypeScript/compilation errors
     ```bash
     cd frontend
     npm run build
     ```
   - **Missing Dependencies:**
     ```bash
     cd frontend
     npm install
     ```
   - **Port Conflicts:** See [Port Already in Use](#port-already-in-use)

3. **Verify Frontend Service:**
   ```bash
   curl http://localhost:3000
   # Should return HTML content
   ```

4. **Clear Next.js Cache:**
   ```bash
   cd frontend
   rm -rf .next
   npm run dev
   ```

---

### ComfyUI Not Starting

**Symptoms:**
- ComfyUI service fails to start
- Image generation fails
- ComfyUI health check fails

**Solutions:**

1. **Check ComfyUI Logs:**
   ```bash
   tail -f runs/latest/comfyui.log
   ```

2. **Verify ComfyUI Installation:**
   - Check if ComfyUI directory exists
   - Verify Python environment for ComfyUI
   - Check ComfyUI requirements

3. **Common Issues:**
   - **Missing Models:** Ensure required models are installed
   - **GPU Issues:** Check GPU availability and drivers
   - **Port Conflicts:** See [Port Already in Use](#port-already-in-use)

4. **Verify ComfyUI Service:**
   ```bash
   curl http://localhost:8188
   # Should return ComfyUI interface
   ```

5. **Manual Start (Testing):**
   ```bash
   cd <comfyui_directory>
   python main.py --port 8188
   ```

---

## Database & Redis Issues

### PostgreSQL Connection Errors

**Symptoms:**
- Backend can't connect to database
- Error: "could not connect to server"
- Database connection timeout

**Solutions:**

1. **Verify PostgreSQL is Running:**
   ```bash
   # macOS
   brew services list | grep postgresql
   
   # Linux
   sudo systemctl status postgresql
   
   # Windows
   # Check Services panel
   ```

2. **Start PostgreSQL:**
   ```bash
   # macOS
   brew services start postgresql
   
   # Linux
   sudo systemctl start postgresql
   
   # Windows
   # Start from Services panel
   ```

3. **Check Connection String:**
   - Verify `.env` file has correct `AINFLUENCER_DATABASE_URL`
   - Format: `postgresql+asyncpg://user:password@localhost:5432/ainfluencer`
   - Verify username, password, host, port, and database name

4. **Verify Database Exists:**
   ```bash
   psql -l | grep ainfluencer
   
   # If not exists, create it:
   createdb ainfluencer
   ```

5. **Test Connection:**
   ```bash
   psql -h localhost -U <username> -d ainfluencer
   ```

6. **Check Database Logs:**
   - PostgreSQL logs location varies by OS
   - Check for authentication or permission errors

---

### Redis Connection Errors

**Symptoms:**
- Backend can't connect to Redis
- Cache operations fail
- Error: "Connection refused" or "ECONNREFUSED"

**Solutions:**

1. **Check if Redis is Running:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

2. **Start Redis:**
   ```bash
   # macOS
   brew services start redis
   
   # Linux
   sudo systemctl start redis
   
   # Windows
   # Use Redis for Windows or WSL
   ```

3. **Verify Redis Configuration:**
   - Check `.env` file for `REDIS_URL` or `REDIS_HOST`/`REDIS_PORT`
   - Default: `localhost:6379`

4. **Test Redis Connection:**
   ```bash
   redis-cli
   # Then type: PING
   # Should return: PONG
   ```

5. **Check Redis Logs:**
   - Redis logs location varies by OS
   - Check for configuration errors

---

### Database Migration Issues

**Symptoms:**
- Database schema errors
- Missing tables
- Migration failures

**Solutions:**

1. **Check Migration Status:**
   ```bash
   # Check if migrations are needed
   cd backend
   alembic current
   ```

2. **Run Migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```

3. **Create New Migration:**
   ```bash
   cd backend
   alembic revision --autogenerate -m "description"
   alembic upgrade head
   ```

4. **Reset Database (Development Only):**
   ```bash
   # WARNING: This deletes all data
   dropdb ainfluencer
   createdb ainfluencer
   cd backend
   alembic upgrade head
   ```

---

## ComfyUI Integration Issues

### ComfyUI Not Responding

**Symptoms:**
- Image generation requests timeout
- ComfyUI health check fails
- 500 errors from ComfyUI endpoints

**Solutions:**

1. **Check ComfyUI Status:**
   ```bash
   curl http://localhost:8188
   # Should return HTML
   ```

2. **Verify ComfyUI Logs:**
   ```bash
   tail -f runs/latest/comfyui.log
   # Look for errors or warnings
   ```

3. **Check GPU Availability:**
   ```bash
   # Check if GPU is available
   nvidia-smi  # For NVIDIA GPUs
   # or check ComfyUI logs for GPU errors
   ```

4. **Restart ComfyUI:**
   - Stop launcher
   - Manually restart ComfyUI
   - Check logs for startup errors

5. **Verify Workflow Files:**
   - Check if ComfyUI workflow files exist
   - Verify workflow JSON is valid
   - Check for missing custom nodes

---

### Missing ComfyUI Models

**Symptoms:**
- Image generation fails with "model not found"
- ComfyUI errors about missing checkpoints
- Generation jobs fail immediately

**Solutions:**

1. **Check Model Directory:**
   - Verify models are in ComfyUI `models/` directory
   - Check model file paths in configuration

2. **Verify Required Models:**
   - Check documentation for required models
   - Ensure checkpoint models are installed
   - Verify VAE models if needed

3. **Model Sync:**
   - Use dashboard model management
   - Sync models with ComfyUI
   - Check model status in dashboard

4. **Manual Model Installation:**
   - Download models to ComfyUI `models/checkpoints/`
   - Restart ComfyUI after adding models
   - Verify models are detected

---

## Image Generation Problems

### Images Not Generating

**Symptoms:**
- Generation jobs stuck in queue
- Jobs fail without error messages
- No output images created

**Solutions:**

1. **Check Generation Service Logs:**
   ```bash
   tail -f runs/latest/backend.log | grep -i generation
   ```

2. **Verify ComfyUI Connection:**
   - Check ComfyUI is running and accessible
   - Test ComfyUI health endpoint
   - Verify workflow can be submitted

3. **Check Job Status:**
   - Use dashboard to view generation jobs
   - Check job status and error messages
   - Review job details for failures

4. **Common Issues:**
   - **Queue Full:** Wait for previous jobs to complete
   - **Invalid Prompt:** Check prompt syntax and parameters
   - **Model Issues:** Verify required models are available
   - **GPU Memory:** Check GPU VRAM availability

5. **Test Generation:**
   ```bash
   # Use API to test generation
   curl -X POST http://localhost:8000/api/generate/image \
     -H "Content-Type: application/json" \
     -d '{"prompt": "test image", "character_id": 1}'
   ```

---

### Poor Image Quality

**Symptoms:**
- Generated images are low quality
- Images have artifacts or distortions
- Inconsistent results

**Solutions:**

1. **Check Generation Parameters:**
   - Verify resolution settings
   - Check quality/CFG scale settings
   - Review sampling method and steps

2. **Model Quality:**
   - Use higher quality models
   - Verify model is appropriate for use case
   - Check model version and updates

3. **Prompt Quality:**
   - Use detailed, specific prompts
   - Include quality keywords
   - Test different prompt variations

4. **Hardware Limitations:**
   - Check GPU VRAM availability
   - Verify sufficient system RAM
   - Consider batch size limitations

---

### Generation Timeout

**Symptoms:**
- Generation jobs timeout
- Long wait times for images
- Jobs cancelled due to timeout

**Solutions:**

1. **Increase Timeout Settings:**
   - Check timeout configuration in `.env`
   - Increase `GENERATION_TIMEOUT` if needed
   - Adjust ComfyUI timeout settings

2. **Optimize Generation:**
   - Reduce image resolution
   - Lower sampling steps
   - Use faster models

3. **Check System Resources:**
   - Monitor GPU utilization
   - Check CPU and RAM usage
   - Verify disk I/O performance

4. **Queue Management:**
   - Limit concurrent generations
   - Process jobs sequentially if needed
   - Clear stuck jobs from queue

---

## Character & Face Consistency Issues

### Face Not Consistent Across Images

**Symptoms:**
- Generated images don't match character face
- Face looks different in each image
- Face consistency service errors

**Solutions:**

1. **Verify Face Reference:**
   - Check character has face reference image uploaded
   - Ensure face reference is clear and high quality
   - Verify face is properly detected in reference

2. **Check Face Embeddings:**
   - Verify face embeddings were extracted successfully
   - Check character detail page for embedding status
   - Re-extract embeddings if needed

3. **Face Consistency Service:**
   ```bash
   # Check service logs
   tail -f runs/latest/backend.log | grep -i face
   ```

4. **Re-upload Face Reference:**
   - Upload new, clearer face reference
   - Ensure good lighting and front-facing angle
   - Wait for embedding extraction to complete

5. **Verify Generation Parameters:**
   - Check if `face_embedding_id` is being used
   - Verify face consistency method in generation request
   - Review generation service logs

---

### Face Embedding Extraction Fails

**Symptoms:**
- Face embeddings not created
- Extraction errors in logs
- Character shows "no embedding" status

**Solutions:**

1. **Check Face Reference Quality:**
   - Ensure image is clear and well-lit
   - Verify face is visible and front-facing
   - Check image format (PNG, JPG supported)

2. **Verify Face Detection:**
   - Check if face is detected in image
   - Try different face reference image
   - Ensure single face in image

3. **Check Extraction Service:**
   ```bash
   # Check logs for extraction errors
   tail -f runs/latest/backend.log | grep -i embedding
   ```

4. **Manual Extraction:**
   - Use API to trigger extraction
   - Check extraction endpoint response
   - Review error messages

5. **Dependencies:**
   - Verify face detection libraries installed
   - Check Python dependencies for face processing
   - Update face processing libraries if needed

---

## API & Backend Errors

### 500 Internal Server Error

**Symptoms:**
- API endpoints return 500 errors
- Backend crashes on requests
- Error messages in logs

**Solutions:**

1. **Check Backend Logs:**
   ```bash
   tail -f runs/latest/backend.log
   # Look for stack traces and error messages
   ```

2. **Common Causes:**
   - **Database Connection:** See [Database Issues](#postgresql-connection-errors)
   - **Missing Dependencies:** Install required packages
   - **Invalid Request Data:** Check request payload
   - **Service Errors:** Check individual service logs

3. **Verify Environment:**
   - Check `.env` file configuration
   - Verify all required environment variables
   - Test database and Redis connections

4. **Restart Backend:**
   - Stop and restart backend service
   - Check for startup errors
   - Verify health endpoint after restart

---

### 404 Not Found

**Symptoms:**
- API endpoints return 404
- Routes not found
- Frontend can't reach backend

**Solutions:**

1. **Verify API Routes:**
   - Check API router configuration
   - Verify endpoint paths match frontend calls
   - Review API documentation

2. **Check Base URL:**
   - Verify frontend `NEXT_PUBLIC_API_URL`
   - Check backend is running on correct port
   - Test API base URL directly

3. **CORS Issues:**
   - Check CORS configuration in backend
   - Verify allowed origins
   - Check browser console for CORS errors

---

### Authentication Errors

**Symptoms:**
- 401 Unauthorized errors
- Authentication failures
- Token validation errors

**Solutions:**

1. **Check Authentication Configuration:**
   - Verify JWT secret in `.env`
   - Check token expiration settings
   - Review authentication middleware

2. **Verify Tokens:**
   - Check token format and validity
   - Verify token hasn't expired
   - Test token generation

3. **Session Management:**
   - Clear browser cookies/storage
   - Re-authenticate if needed
   - Check session configuration

---

## Frontend Issues

### Build Errors

**Symptoms:**
- Frontend fails to build
- TypeScript compilation errors
- Next.js build failures

**Solutions:**

1. **Check Build Logs:**
   ```bash
   cd frontend
   npm run build
   # Review error messages
   ```

2. **TypeScript Errors:**
   - Fix type errors shown in build
   - Check `tsconfig.json` configuration
   - Verify type definitions installed

3. **Dependency Issues:**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

4. **Clear Next.js Cache:**
   ```bash
   cd frontend
   rm -rf .next
   npm run build
   ```

---

### Runtime Errors

**Symptoms:**
- Frontend crashes in browser
- JavaScript errors in console
- Pages not loading

**Solutions:**

1. **Check Browser Console:**
   - Open browser developer tools
   - Review error messages
   - Check network tab for failed requests

2. **Verify API Connection:**
   - Check `NEXT_PUBLIC_API_URL` in `.env`
   - Test backend health endpoint
   - Verify CORS configuration

3. **Clear Browser Cache:**
   - Clear browser cache and cookies
   - Try incognito/private mode
   - Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

4. **Check Environment Variables:**
   - Verify frontend `.env.local` or `.env`
   - Ensure variables prefixed with `NEXT_PUBLIC_`
   - Restart frontend after changes

---

### UI Not Updating

**Symptoms:**
- Dashboard not showing latest data
- UI stuck on loading state
- State not refreshing

**Solutions:**

1. **Check API Responses:**
   - Verify API is returning data
   - Check network tab for responses
   - Review response format

2. **State Management:**
   - Check React state updates
   - Verify data fetching hooks
   - Review component re-renders

3. **Cache Issues:**
   - Clear browser cache
   - Check Next.js cache
   - Verify no stale data

---

## Performance Problems

### Slow Image Generation

**Symptoms:**
- Generation takes too long
- Queue processing is slow
- System feels sluggish during generation

**Solutions:**

1. **Check GPU Utilization:**
   ```bash
   nvidia-smi  # For NVIDIA GPUs
   # Check GPU usage and memory
   ```

2. **Optimize Generation Settings:**
   - Reduce image resolution
   - Lower sampling steps
   - Use faster models

3. **System Resources:**
   - Check CPU and RAM usage
   - Close unnecessary applications
   - Ensure sufficient disk space

4. **Queue Management:**
   - Limit concurrent generations
   - Process jobs sequentially
   - Clear stuck or old jobs

---

### High Memory Usage

**Symptoms:**
- System running out of memory
- Services crashing
- Slow system performance

**Solutions:**

1. **Monitor Memory:**
   ```bash
   # Check memory usage
   free -h  # Linux
   top  # General
   ```

2. **Optimize Services:**
   - Reduce batch sizes
   - Limit concurrent operations
   - Clear caches regularly

3. **Service Configuration:**
   - Adjust memory limits in configuration
   - Restart services periodically
   - Monitor memory leaks

---

### Database Performance

**Symptoms:**
- Slow database queries
- Timeout errors
- High database CPU usage

**Solutions:**

1. **Check Database Performance:**
   ```sql
   -- Check active connections
   SELECT count(*) FROM pg_stat_activity;
   
   -- Check slow queries
   SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
   ```

2. **Optimize Queries:**
   - Add database indexes
   - Review query patterns
   - Use connection pooling

3. **Database Maintenance:**
   ```sql
   -- Vacuum database
   VACUUM ANALYZE;
   
   -- Check table sizes
   SELECT pg_size_pretty(pg_total_relation_size('table_name'));
   ```

---

## General Diagnostics

### System Check

Run comprehensive system check:

```bash
# Windows
.\launch.ps1 --doctor

# macOS/Linux
./launch.sh --doctor
```

This checks:
- Python and Node.js versions
- Required dependencies
- Port availability
- Database and Redis connectivity
- Disk space
- Service health

---

### Log Analysis

1. **View Latest Logs:**
   ```bash
   # Backend
   tail -f runs/latest/backend.log
   
   # Frontend
   tail -f runs/latest/frontend.log
   
   # ComfyUI
   tail -f runs/latest/comfyui.log
   ```

2. **Check Event Log:**
   ```bash
   # View structured events
   cat runs/latest/events.jsonl | jq
   ```

3. **Summary File:**
   ```bash
   # View run summary
   cat runs/latest/summary.txt
   ```

---

### Debug Bundle

Generate debug bundle from dashboard:

1. Open dashboard
2. Go to "Logs" tab
3. Click "Copy Debug Bundle"
4. Includes:
   - System check results
   - Installer status
   - Service logs
   - Configuration (sanitized)

---

### Health Checks

Verify all services are healthy:

```bash
# Backend
curl http://localhost:8000/api/health
# Expected: {"status":"healthy"}

# Frontend
curl http://localhost:3000
# Expected: HTML content

# ComfyUI
curl http://localhost:8188
# Expected: HTML content
```

---

## Getting Help

If issues persist:

1. **Check Documentation:**
   - Review this troubleshooting guide
   - Check [ERROR_PLAYBOOK.md](./06_ERROR_PLAYBOOK.md) for specific errors
   - Review [USER-MANUAL.md](./USER-MANUAL.md) for usage guidance

2. **Collect Information:**
   - Generate debug bundle from dashboard
   - Collect relevant log files
   - Note error messages and steps to reproduce

3. **Community Support:**
   - Check GitHub issues for similar problems
   - Search existing discussions
   - Create new issue with debug information

4. **Review Logs:**
   - Check `runs/latest/` directory
   - Review service-specific logs
   - Look for error patterns

---

## Quick Reference

### Common Commands

```bash
# Check service status
curl http://localhost:8000/api/health
curl http://localhost:3000
curl http://localhost:8188

# View logs
tail -f runs/latest/backend.log
tail -f runs/latest/frontend.log
tail -f runs/latest/comfyui.log

# Restart services
# Stop launcher and restart

# Check ports
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Database
psql -l | grep ainfluencer
redis-cli ping

# System check
./launch.sh --doctor  # macOS/Linux
.\launch.ps1 --doctor  # Windows
```

### File Locations

- **Logs:** `runs/latest/`
- **Configuration:** `.env` (root directory)
- **Backend:** `backend/`
- **Frontend:** `frontend/`
- **Documentation:** `docs/`

---

**Last Updated:** 2025-12-17  
**Version:** 1.0
