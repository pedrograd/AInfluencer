# Project Standards & Best Practices

## Code Quality Standards

### Python (Backend)
- Use Python 3.11+ with type hints for all functions
- Follow PEP 8 style guide with 100-character line limit
- Use `black` formatter with default settings
- Use `ruff` for linting (replaces flake8 + isort)
- Always use async/await for I/O operations (FastAPI)
- Include docstrings for all classes and functions (Google style)
- Maximum function complexity: 15 (use smaller functions if exceeded)

### TypeScript/JavaScript (Frontend)
- Use TypeScript strict mode
- Prefer functional components with hooks
- Use `eslint` with Next.js recommended config
- Use `prettier` for code formatting
- Maximum component file size: 300 lines
- Extract reusable logic to custom hooks or utilities

### File Organization
- One class/component per file
- Use descriptive file names: `character-generator.service.ts` not `gen.ts`
- Group related files in feature folders
- Keep imports organized: external → internal → relative

## Architecture Principles

### Microservices Pattern
- Each service is independent and can run separately
- Services communicate via REST API or message queue
- Database access is scoped to service-specific schemas
- Configuration is environment-based (no hardcoded values)

### Error Handling
- Always use try-catch blocks for async operations
- Log errors with context (user, action, error details)
- Return meaningful error messages to users (never expose internals)
- Use custom exception classes for different error types
- Implement retry logic for transient failures

### Security
- Never commit API keys, secrets, or credentials
- Use environment variables for all configuration
- Validate and sanitize all user inputs
- Use parameterized queries (SQLAlchemy ORM handles this)
- Implement rate limiting on all public endpoints
- Use HTTPS in production (always)

### Testing
- Write unit tests for business logic (80%+ coverage goal)
- Write integration tests for API endpoints
- Use fixtures for test data
- Mock external services (AI APIs, social media APIs)
- Run tests before committing (pre-commit hook)

## UI/UX Standards

### Design System
- Use shadcn/ui components as base
- Follow Tailwind CSS utility-first approach
- Maintain consistent spacing (4px grid system)
- Use system fonts initially, add custom fonts later
- Dark mode support from day one

### Accessibility
- All interactive elements must be keyboard accessible
- Use semantic HTML elements
- Provide ARIA labels where needed
- Ensure color contrast meets WCAG AA standards
- Test with screen readers

### Performance
- Lazy load images and components
- Code split routes (Next.js automatic)
- Optimize images (use next/image)
- Minimize bundle size (keep under 500KB initial load)
- Implement proper loading states

## AI Model Integration

### Model Selection Priority
1. **Free & Open Source** (preferred) - Realistic Vision, InstantID, Ollama
2. **Free with API** (secondary) - Hugging Face Inference API
3. **Paid Services** (optional) - OpenAI, Anthropic (user configurable)

### Face Consistency
- Use InstantID for best results (priority over IP-Adapter)
- Support multiple reference images (3-5 recommended)
- Store face embeddings in database for reuse
- Cache embeddings to avoid recalculation

### Content Generation Pipeline
1. Generate base content (image/video)
2. Apply face consistency (InstantID/IP-Adapter)
3. Post-process (upscale, face restoration, color grading)
4. Quality check (automated + optional manual review)
5. Store in content library

## Database Design

### Schema Principles
- Use UUIDs for all primary keys (better for distributed systems)
- Add `created_at` and `updated_at` timestamps to all tables
- Use soft deletes (deleted_at) instead of hard deletes
- Normalize where appropriate, denormalize for performance when needed
- Use indexes on foreign keys and frequently queried fields
- Document all relationships and constraints

### Naming Conventions
- Tables: plural, snake_case (`characters`, `content_items`)
- Columns: snake_case (`created_at`, `user_id`)
- Foreign keys: `{table_name}_id` (`character_id`)
- Indexes: `idx_{table}_{column}` (`idx_content_character_id`)

## Documentation

### Code Comments
- Explain WHY, not WHAT (code should be self-documenting)
- Document complex algorithms and business logic
- Include examples for complex functions
- Update comments when code changes

### API Documentation
- Use OpenAPI/Swagger for all endpoints (FastAPI automatic)
- Include request/response examples
- Document error responses
- Specify required vs optional parameters

### README Files
- Keep root README updated with quick start
- Add README to each service/module explaining its purpose
- Include setup instructions for local development
- Document environment variables required

## Git Workflow

### Commit Messages
- Format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- Example: `feat(character): add face consistency validation`
- Keep descriptions under 72 characters
- Use imperative mood ("add" not "added")

### Branch Strategy
- `main`: Production-ready code only
- `develop`: Integration branch for features
- `feature/*`: Feature development branches
- `fix/*`: Bug fixes
- `hotfix/*`: Critical production fixes

## Performance Optimization

### Backend
- Use database connection pooling
- Implement caching (Redis) for frequently accessed data
- Use async operations for I/O-bound tasks
- Batch database operations when possible
- Profile code to find bottlenecks

### Frontend
- Implement virtual scrolling for long lists
- Debounce search/input handlers
- Use React.memo for expensive components
- Lazy load routes and heavy components
- Optimize images (WebP format, appropriate sizes)

## Logging & Monitoring

### Log Levels
- `ERROR`: System errors requiring attention
- `WARN`: Potential issues (rate limits, deprecated features)
- `INFO`: Important events (character created, post published)
- `DEBUG`: Detailed information for debugging (development only)

### Log Format
- JSON format for structured logging
- Include: timestamp, level, service, message, context
- Never log sensitive information (passwords, tokens)
- Use correlation IDs for request tracing

## Deployment

### Environment Variables
- Separate `.env` files for dev, staging, prod
- Document all variables in `.env.example`
- Never commit `.env` files
- Use secrets management in production

### Docker
- Use multi-stage builds for smaller images
- Pin base image versions (no `latest` tag)
- Run as non-root user when possible
- Use .dockerignore to exclude unnecessary files

## Code Review Checklist

Before requesting review:
- [ ] Code follows style guide
- [ ] Tests pass locally
- [ ] No console.logs or debug code
- [ ] Documentation updated
- [ ] No hardcoded values
- [ ] Error handling implemented
- [ ] Security considerations addressed
