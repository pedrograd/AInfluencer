# Development Environment Setup

**Complete guide for setting up the AInfluencer development environment.**

---

## Prerequisites

### Required Software

- **Python**: 3.12 or 3.13
- **Node.js**: LTS version (20.x or later)
- **PostgreSQL**: 15+ (or use Docker)
- **Redis**: 7+ (or use Docker)
- **Git**: Latest version
- **Docker** (optional): For containerized development

### System Requirements

- **Minimum**: 4 cores, 16GB RAM, 8GB GPU VRAM, 500GB SSD
- **Recommended**: 8 cores, 32GB RAM, 24GB GPU VRAM, 1TB NVMe SSD
- **OS**: macOS, Linux, or Windows (WSL2 recommended for Windows)

---

## Installation Methods

### Option 1: Local Development (Recommended for Development)

#### Step 1: Clone Repository

```bash
git clone <repository-url>
cd AInfluencer
```

#### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install
```

#### Step 4: Database Setup

**PostgreSQL:**
```bash
# Create database
createdb ainfluencer

# Or using psql:
psql -U postgres
CREATE DATABASE ainfluencer;
CREATE USER ainfluencer_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ainfluencer TO ainfluencer_user;
```

**Redis:**
```bash
# macOS (using Homebrew):
brew install redis
brew services start redis

# Linux:
sudo apt-get install redis-server
sudo systemctl start redis

# Windows:
# Download from https://redis.io/download
# Or use WSL2
```

#### Step 5: Environment Configuration

Create `.env` file in `backend/` directory:

```bash
# Backend .env
AINFLUENCER_APP_ENV=dev
AINFLUENCER_LOG_LEVEL=INFO
AINFLUENCER_COMFYUI_BASE_URL=http://localhost:8188
AINFLUENCER_DATABASE_URL=postgresql+asyncpg://ainfluencer_user:password@localhost:5432/ainfluencer
AINFLUENCER_REDIS_URL=redis://localhost:6379/0
```

Create `.env.local` file in `frontend/` directory:

```bash
# Frontend .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

#### Step 6: Run Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - PostgreSQL (if not running as service):**
```bash
# macOS/Linux:
postgres -D /usr/local/var/postgres

# Or use system service
```

**Terminal 4 - Redis (if not running as service):**
```bash
redis-server
```

Access:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Option 2: Docker Development (Recommended for Consistency)

#### Prerequisites

- Docker Desktop installed and running
- Docker Compose v2

#### Setup

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

Services:
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Backend: `localhost:8000`
- Frontend: `localhost:3000`

#### Environment Variables

Create `.env` file in project root for Docker Compose:

```bash
# .env (for docker-compose)
POSTGRES_DB=ainfluencer
POSTGRES_USER=ainfluencer_user
POSTGRES_PASSWORD=secure_password
```

---

## Development Workflow

### Running Tests

**Backend:**
```bash
cd backend
source venv/bin/activate
pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

### Code Quality

**Backend:**
```bash
# Format code
black backend/

# Lint code
ruff check backend/

# Type checking
mypy backend/
```

**Frontend:**
```bash
# Lint
npm run lint

# Type check
npm run type-check
```

### Database Migrations

```bash
# Create migration (when Alembic is set up)
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

---

## Common Issues & Troubleshooting

### Backend Issues

**Problem: Module not found**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

**Problem: Database connection error**
- Check PostgreSQL is running: `pg_isready`
- Verify connection string in `.env`
- Check database exists: `psql -l | grep ainfluencer`

**Problem: Port already in use**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or change port in uvicorn command
```

### Frontend Issues

**Problem: Module not found**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Problem: Cannot connect to backend**
- Verify backend is running on port 8000
- Check `NEXT_PUBLIC_API_BASE_URL` in `.env.local`
- Check CORS settings in backend

### Database Issues

**Problem: PostgreSQL connection refused**
```bash
# Check if PostgreSQL is running
# macOS:
brew services list | grep postgresql

# Linux:
sudo systemctl status postgresql

# Start if needed
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux
```

**Problem: Redis connection refused**
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start if needed
redis-server
```

### Docker Issues

**Problem: Port conflicts**
- Stop local services or change ports in `docker-compose.yml`
- Check: `docker ps` to see running containers

**Problem: Container won't start**
```bash
# View logs
docker-compose logs <service-name>

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

---

## Project Structure

```
AInfluencer/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core configuration
│   │   ├── services/      # Business logic
│   │   └── main.py       # FastAPI app entry
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities
│   ├── package.json
│   └── Dockerfile
├── docs/                 # Documentation
├── docker-compose.yml    # Docker services
└── README.md
```

---

## Next Steps

1. **Read Documentation**: Start with `docs/PRD.md` for product overview
2. **Review Architecture**: Check `docs/02_ARCHITECTURE.md` for system design
3. **Follow Roadmap**: See `docs/03-FEATURE-ROADMAP.md` for development phases
4. **API Reference**: Visit http://localhost:8000/docs when backend is running

---

## Additional Resources

- **Quick Start**: `docs/QUICK-START.md`
- **How to Start**: `HOW-TO-START.md`
- **Deployment**: `docs/15-DEPLOYMENT-DEVOPS.md`
- **Testing**: `docs/14-TESTING-STRATEGY.md`

---

**Last Updated**: 2025-12-15

