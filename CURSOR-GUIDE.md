# 🚀 Cursor IDE Advanced Guide for AInfluencer Project

**CEO/CPO/CTO Level Guide** - How to Use Cursor 2.0 Auto Effectively

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Cursor Configuration](#cursor-configuration)
3. [Project Rules System](#project-rules-system)
4. [Workflow Strategies](#workflow-strategies)
5. [Best Practices](#best-practices)
6. [Project-Specific Guidance](#project-specific-guidance)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Initial Setup

1. **Open Project in Cursor**
   ```bash
   cd /Users/pedram/AInfluencer
   cursor .
   ```

2. **Verify Rules Are Loaded**
   - Cursor automatically loads `.cursor/rules/` files
   - Check bottom-right: Rules indicator should show active rules
   - Press `Cmd/Ctrl + Shift + P` → "Cursor: Show Rules"

3. **First AI Interaction**
   - Press `Cmd/Ctrl + L` to open Chat
   - Type: "Review project structure and suggest improvements"
   - Let Cursor analyze the codebase

---

## Cursor Configuration

### Project Rules Location

Rules are in `.cursor/rules/` (NOT `.cursorrules` - that's deprecated):

```
.cursor/
└── rules/
    ├── project-standards.md      # Always active
    ├── ai-models-workflow.md     # Auto-attached for AI files
    └── cursor-best-practices.md  # Agent-requested
```

### How Rules Work

1. **Always Rules** - Always in context (project standards)
2. **Auto-Attached** - Loaded when you open matching files
3. **Agent-Requested** - AI includes when relevant
4. **Manual** - Only with `@ruleName`

### Adding New Rules

Create a new file in `.cursor/rules/`:
```markdown
# My New Rule

This rule explains...
```

Cursor automatically detects and includes it.

---

## Workflow Strategies

### Strategy 1: High-Level Planning (Chat)

Use Chat (`Cmd/Ctrl + L`) for:

- **Architecture decisions**: "Design the dashboard installer system"
- **Feature planning**: "Plan the character creation flow"
- **Code review**: "Review the API design for security"
- **Learning**: "Explain how InstantID works"

**Example:**
```
You: "I need to create a one-click installer dashboard. 
     What components do I need? Reference Stability Matrix 
     architecture and check existing docs."
```

### Strategy 2: Multi-File Changes (Composer)

Use Composer (`Cmd/Ctrl + I`) for:

- **Creating features**: "Create character management API with CRUD operations"
- **Refactoring**: "Refactor all error handling to use custom exceptions"
- **Adding functionality**: "Add validation to all API endpoints"

**Example:**
```
You: "Create a model manager service:
     1. Database model for AI models
     2. Service to list/download models
     3. API endpoints following REST conventions
     4. Frontend component with drag-drop
     
     Follow patterns from character service."
```

### Strategy 3: Quick Fixes (Inline Edit)

Use Inline Edit (`Cmd/Ctrl + K`) for:

- **Single file changes**: "Add type hints to this function"
- **Quick improvements**: "Optimize this database query"
- **Bug fixes**: "Fix the error handling in this block"

**Example:**
```
Select code → Cmd/Ctrl + K → "Add comprehensive error 
handling with logging"
```

### Strategy 4: Tab Autocomplete

Just start typing - Cursor suggests:

- Function implementations
- Import statements
- Component structures
- API endpoint patterns

Accept with `Tab`, dismiss with `Esc`.

---

## Best Practices

### 1. Provide Context

**Good:**
```
"Create an image generation service following the pattern 
in src/services/character.service.ts. Use InstantID for 
face consistency, integrate with Stable Diffusion API, 
and add error handling."
```

**Bad:**
```
"Create a service"
```

### 2. Reference Existing Code

**Good:**
```
"Follow the same authentication pattern as user_routes.py 
but for character endpoints"
```

**Bad:**
```
"Add authentication"
```

### 3. Be Specific About Requirements

**Good:**
```
"Create a POST /api/characters endpoint that:
- Accepts JSON: {name, bio, persona, face_references[]}
- Validates with Pydantic
- Stores in PostgreSQL
- Returns 201 with created character
- Handles errors gracefully"
```

**Bad:**
```
"Create an endpoint"
```

### 4. Request Documentation

**Good:**
```
"Generate OpenAPI docs with examples, add docstrings to 
all functions, and create a README for this module"
```

**Bad:**
```
"Document this"
```

### 5. Break Down Complex Tasks

**Step-by-step approach:**
```
Step 1: "Design database schema for models table"
Step 2: "Create SQLAlchemy model"
Step 3: "Create service layer with download logic"
Step 4: "Create API endpoints"
Step 5: "Add frontend component"
Step 6: "Write tests"
```

---

## Project-Specific Guidance

### Key Project Requirements

When working on features, always mention:

1. **Ultra-realism**: "Content must be undetectable as AI"
2. **Face consistency**: "Use InstantID for character consistency"
3. **Automation**: "Everything should be automated, zero manual work"
4. **Cross-platform**: "Must work on Windows and Mac"
5. **One-click setup**: "Users shouldn't need technical knowledge"

### Example Prompts for This Project

#### Creating the Dashboard Installer

```
Create a one-click installer dashboard component:

Requirements:
- Check system requirements (GPU, RAM, storage, OS)
- Download Python, Node.js, PostgreSQL if missing
- Download AI models (Realistic Vision, InstantID, etc.)
- Install Python dependencies
- Setup database schema
- Configure environment variables
- Run installation tests
- Show progress with real-time logs
- Support Windows and Mac
- Handle errors gracefully with retry logic

UI Requirements:
- Modern, clean design using shadcn/ui
- Progress indicators for each step
- Collapsible log viewer
- System requirement checklist
- Error messages with solutions

Reference Stability Matrix's installer for inspiration.
```

#### Creating Model Manager

```
Create a model management system similar to Stability Matrix:

Features:
- List available models with metadata (size, quality, type)
- Show downloaded vs available models
- Download models from Hugging Face/Civitai
- Drag-and-drop model import
- Organize by type (checkpoints, LoRAs, embeddings)
- Model version management
- Auto-detect GPU compatibility
- Show download progress
- Verify model checksums

UI:
- Grid/list view toggle
- Filter by type, quality, size
- Search functionality
- Model details panel
- Download queue management

Use ComfyUI-style node organization.
```

#### Creating Face Consistency Node

```
Implement InstantID face consistency workflow node:

Technical Requirements:
- Extract face embeddings from reference images (1-5 images)
- Store embeddings in database for reuse
- Cache embeddings to avoid recalculation
- Apply embeddings during image generation
- Support weight adjustment (0.5-0.9)
- Compatible with ComfyUI workflow system
- Support batch processing

API:
- POST /api/face-embeddings/extract (upload images, get embedding)
- GET /api/face-embeddings/{id} (retrieve cached embedding)
- POST /api/images/generate (with face_embedding_id parameter)

Follow existing service patterns in the codebase.
```

---

## Common Workflows

### Creating a New Feature

1. **Plan** (Chat):
   ```
   "I want to add [feature]. What components do I need?
   Check existing codebase for similar patterns."
   ```

2. **Create Structure** (Composer):
   ```
   "Create basic structure:
   - Database model
   - Service layer
   - API endpoints
   - Frontend components
   
   Follow patterns from [similar feature]."
   ```

3. **Implement Details** (Inline + Tab):
   - Use inline editing for specific functions
   - Tab autocomplete for boilerplate

4. **Review** (Chat):
   ```
   "Review this implementation for:
   - Security issues
   - Performance
   - Code quality
   - Test coverage"
   ```

### Debugging

1. **Describe Issue**:
   ```
   "Debug this error: [error]
   Expected: [behavior]
   File: [path]"
   ```

2. **Investigate**:
   ```
   "Investigate [area]. Check related files using @codebase"
   ```

3. **Fix**:
   ```
   "Fix following project standards. Add error handling"
   ```

4. **Test**:
   ```
   "Add tests to prevent regression"
   ```

### Refactoring

1. **Identify**:
   ```
   "Find all places using [pattern] that need refactoring"
   ```

2. **Plan**:
   ```
   "Plan refactoring to [improvement]:
   - What changes?
   - What files affected?
   - Backward compatibility?"
   ```

3. **Execute** (Composer):
   ```
   "Refactor [target] following [pattern].
   Update all files. Maintain tests."
   ```

4. **Verify**:
   ```
   "Verify refactoring. Run tests and check types"
   ```

---

## Keyboard Shortcuts

| Action | Mac | Windows/Linux |
|--------|-----|---------------|
| Open Chat | `Cmd + L` | `Ctrl + L` |
| Open Composer | `Cmd + I` | `Ctrl + I` |
| Inline Edit | `Cmd + K` | `Ctrl + K` |
| Accept Suggestion | `Tab` | `Tab` |
| Dismiss Suggestion | `Esc` | `Esc` |
| Submit | `Cmd + Enter` | `Ctrl + Enter` |
| Command Palette | `Cmd + Shift + P` | `Ctrl + Shift + P` |
| Mention Files | `@` | `@` |

---

## Using @ Mentions

- `@filename.ts` - Include specific file
- `@foldername/` - Include folder
- `@codebase` - Search entire codebase
- `@docs` - Search documentation
- `@ruleName` - Include specific rule

**Example:**
```
"Review @character.service.ts and @database.py 
to understand the pattern, then create similar 
service for models"
```

---

## Troubleshooting

### Rules Not Loading

1. Check `.cursor/rules/` directory exists
2. Verify file extensions are `.md`
3. Restart Cursor
4. Check Rules indicator (bottom-right)

### AI Not Following Standards

1. Explicitly reference rule: "Follow @project-standards.md"
2. Provide example: "Like this: [code example]"
3. Specify: "Must follow TypeScript strict mode and use async/await"

### Generated Code Has Issues

1. Always review generated code
2. Test immediately after generation
3. Ask for explanation: "Explain this approach"
4. Request alternatives: "Show alternative implementation"

### Multi-File Changes Too Broad

1. Break into smaller steps
2. Use Composer for 2-5 files at a time
3. Review each step before continuing
4. Use Chat to plan before Composer

---

## Next Steps

1. **Start with Chat**: "Review current project structure and suggest first implementation steps"

2. **Set Up Project**: "Create initial project structure following the roadmap"

3. **Build Dashboard**: "Create the one-click installer dashboard component"

4. **Iterate**: Use Cursor's iterative workflow to build incrementally

---

## Resources

- **Cursor Docs**: https://docs.cursor.com
- **Project Rules**: `.cursor/rules/` directory
- **Best Practices**: See `.cursor/rules/cursor-best-practices.md`
- **Project Standards**: See `.cursor/rules/project-standards.md`

---

**Remember**: Cursor is a tool to amplify your productivity. Always review, understand, and test generated code. Use it to accelerate development, not replace thinking.
