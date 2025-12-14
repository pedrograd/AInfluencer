# Cursor IDE Advanced Usage Guide

## Project Rules System

This project uses Cursor's Project Rules (`.cursor/rules/`) instead of deprecated `.cursorrules` files.

### Rule Types

1. **Always Rules** - Always included in AI context
   - Project standards, coding conventions
   - Architecture decisions

2. **Auto Attached Rules** - Included when matching files are referenced
   - File-specific patterns (e.g., `**/*.test.ts` → testing rules)
   - Technology-specific (e.g., `**/api/**` → API design rules)

3. **Agent Requested Rules** - AI decides when to include
   - Optional best practices
   - Advanced techniques

4. **Manual Rules** - Only when explicitly mentioned with `@ruleName`
   - Rarely used patterns
   - Legacy code guidelines

## Cursor Usage Workflow

### 1. Chat with Cursor (Cmd/Ctrl + L)
- Use for high-level questions: "How should I structure the character service?"
- Ask for code reviews: "Review this function for security issues"
- Get explanations: "Explain how InstantID works"
- Request refactoring: "Refactor this to use async/await properly"

### 2. Composer (Cmd/Ctrl + I)
- Use for multi-file changes: "Add error handling to all API endpoints"
- Create features: "Create a new character creation form component"
- Refactor across files: "Extract common validation logic to utils"

### 3. Inline Editing (Cmd/Ctrl + K)
- Quick fixes: "Add type hints to this function"
- Single file changes: "Optimize this database query"
- Code improvements: "Add error handling to this block"

### 4. Tab Autocomplete
- Let it suggest code as you type
- Accept suggestions that match project patterns
- Use Tab to accept, Esc to dismiss

## Prompt Engineering for Cursor

### Effective Prompt Patterns

#### For New Features
```
Create a [component/service] that [does X] with [requirements]:
- Requirement 1
- Requirement 2
- Requirement 3

Follow the [specific pattern/architecture] from [reference file].
Use [specific library/technology] for [reason].
```

#### For Refactoring
```
Refactor [target code] to:
- [Improvement 1]
- [Improvement 2]
- Maintain [existing behavior]

Follow [project standard] and update tests accordingly.
```

#### For Debugging
```
Debug [issue description]:
- Expected: [expected behavior]
- Actual: [actual behavior]
- Error: [error message if any]

Investigate [specific area] and suggest fix.
```

#### For Code Review
```
Review [code/file] for:
- Security vulnerabilities
- Performance issues
- Code quality (follows project standards)
- Test coverage

Suggest improvements.
```

### Context Management

#### Provide Context Explicitly
- Reference specific files: "See `src/services/character.service.ts`"
- Mention patterns: "Follow the same pattern as the image generation service"
- Specify constraints: "Must work with existing database schema"

#### Use @ Mentions
- `@filename` - Include file in context
- `@foldername` - Include folder contents
- `@codebase` - Search entire codebase
- `@docs` - Search documentation

### Multi-Step Tasks

Break complex tasks into steps:
```
Step 1: Create database schema for [feature]
Step 2: Create API endpoints following REST conventions
Step 3: Create frontend components using shadcn/ui
Step 4: Add error handling and validation
Step 5: Write tests for all new code
```

## Code Generation Best Practices

### Request Specific Patterns
- ✅ "Create a FastAPI endpoint following the pattern in `user_routes.py`"
- ❌ "Create an endpoint"

### Specify Dependencies
- ✅ "Use SQLAlchemy ORM with async session, following `database.py` patterns"
- ❌ "Use a database"

### Request Error Handling
- ✅ "Add comprehensive error handling with custom exceptions, logging, and user-friendly messages"
- ❌ "Add error handling"

### Request Testing
- ✅ "Create unit tests using pytest, mocking external dependencies"
- ❌ "Add tests"

## Advanced Cursor Features

### 1. Codebase Indexing
- Cursor automatically indexes your codebase
- Use `@codebase` to search across all files
- Ask questions like: "Where is character validation logic?"

### 2. Terminal Integration
- Cursor can run commands for you
- Use: "Run the test suite and fix any failures"
- Specify: "Run pytest with coverage report"

### 3. Git Integration
- Ask: "What files changed in the last commit?"
- Request: "Create a commit message for these changes"
- Use: "Show me the diff for this file"

### 4. Documentation Generation
- Request: "Generate API documentation for this endpoint"
- Ask: "Create a README for this module"
- Use: "Document this function with examples"

## Common Workflows

### Creating a New Feature

1. **Plan with Chat**
   ```
   "I want to add [feature]. What components do I need?
   Check existing codebase for similar patterns."
   ```

2. **Create Structure with Composer**
   ```
   "Create the basic structure for [feature]:
   - Database model
   - API endpoints
   - Service layer
   - Frontend components
   
   Follow existing patterns in [similar feature]."
   ```

3. **Implement Details with Inline**
   - Use inline editing for specific functions
   - Tab autocomplete for boilerplate

4. **Review with Chat**
   ```
   "Review this implementation for:
   - Security issues
   - Performance problems
   - Code quality
   - Test coverage"
   ```

### Debugging Workflow

1. **Describe Issue**
   ```
   "Debug this error: [error message]
   Expected: [expected behavior]
   File: [file path]
   Function: [function name]"
   ```

2. **Investigate**
   ```
   "Investigate [specific area]. Check related files
   using @codebase search."
   ```

3. **Fix**
   ```
   "Fix this issue following project standards.
   Add error handling and logging."
   ```

4. **Test**
   ```
   "Add tests to prevent regression of this bug."
   ```

### Refactoring Workflow

1. **Identify Targets**
   ```
   "Find all places where [pattern] is used
   that should be refactored."
   ```

2. **Plan Refactoring**
   ```
   "Plan refactoring to [improvement]:
   - What needs to change?
   - What files are affected?
   - How to maintain backward compatibility?"
   ```

3. **Execute with Composer**
   ```
   "Refactor [target] following [new pattern].
   Update all affected files. Maintain tests."
   ```

4. **Verify**
   ```
   "Verify refactoring didn't break anything.
   Run tests and check for type errors."
   ```

## Tips for Maximum Productivity

### 1. Be Specific
- ✅ "Create a POST endpoint at `/api/characters` that accepts JSON with fields: name (string, required), bio (string, optional), persona (object, required)"
- ❌ "Create an endpoint"

### 2. Reference Existing Code
- ✅ "Follow the same pattern as `user_service.py` but for characters"
- ❌ "Create a service"

### 3. Specify Constraints
- ✅ "Must validate input using Pydantic, handle errors gracefully, log all operations, and return consistent JSON responses"
- ❌ "Create an API"

### 4. Request Documentation
- ✅ "Generate OpenAPI documentation, include examples, and add docstrings"
- ❌ "Document this"

### 5. Ask for Explanations
- "Why did you choose this approach?"
- "What are the trade-offs of this solution?"
- "How does this relate to the existing architecture?"

## Avoiding Common Mistakes

### Don't
- ❌ Accept generated code without review
- ❌ Skip understanding what was generated
- ❌ Ignore project standards in generated code
- ❌ Forget to test generated code
- ❌ Commit AI-generated code without manual review

### Do
- ✅ Review all generated code
- ✅ Understand what was created
- ✅ Verify it follows project standards
- ✅ Test thoroughly
- ✅ Refactor if needed
- ✅ Document complex logic

## Keyboard Shortcuts Reference

- `Cmd/Ctrl + L` - Open Chat
- `Cmd/Ctrl + I` - Open Composer
- `Cmd/Ctrl + K` - Inline edit
- `Tab` - Accept autocomplete
- `Esc` - Dismiss autocomplete
- `Cmd/Ctrl + Enter` - Submit in Chat/Composer
- `@` - Mention files/folders/rules
- `Cmd/Ctrl + Shift + P` - Command palette

## Project-Specific Cursor Usage

### For This Project

1. **Always mention**: AI models, face consistency, character management
2. **Reference patterns**: Stability Matrix/ComfyUI workflow system
3. **Specify requirements**: Windows + Mac support, one-click setup
4. **Emphasize**: Ultra-realism, undetectability, automation

### Example Prompts for This Project

```
Create a model manager component similar to Stability Matrix:
- List available models with metadata
- Show download progress
- Support drag-and-drop import
- Organize by type (checkpoint, LoRA, embedding)
- Auto-detect GPU compatibility
```

```
Implement InstantID face consistency node:
- Extract face embeddings from reference images
- Apply to image generation pipeline
- Support weight adjustment (0.5-0.9)
- Cache embeddings for reuse
- Follow ComfyUI node pattern
```

```
Create one-click installer dashboard:
- Check system requirements (GPU, RAM, storage)
- Download and install all dependencies
- Configure environment variables
- Test installation
- Show setup progress with logs
- Support Windows and Mac
```
