# Personality System Design

## 📋 Document Metadata

### Purpose
Complete design specification for the character personality system. This document explains how personality traits affect content generation, how personas are managed, and how the system integrates with LLM-based content generation.

### Reading Order
**Read After:** [09-DATABASE-SCHEMA.md](./09-DATABASE-SCHEMA.md), [10-API-DESIGN.md](./10-API-DESIGN.md)  
**Read Before:** Implementing personality-based content generation, persona templates, export functionality

### Related Documents
**Prerequisites:**
- [09-DATABASE-SCHEMA.md](./09-DATABASE-SCHEMA.md) - CharacterPersonality table schema
- [PRD.md](./PRD.md) - FR-002: Character Persona System requirements
- [10-API-DESIGN.md](./10-API-DESIGN.md) - API endpoints for personality management

**Used By:**
- Content generation service - Uses personality to generate text, captions, comments
- Frontend UI - Personality configuration interface
- API implementation - Personality CRUD operations

---

## Overview

The personality system allows each AI influencer character to have a unique persona that affects all generated content. Personality traits are stored in the database and used to construct prompts for LLM-based content generation.

### Key Features
- **Personality Traits**: Five core traits (0.0-1.0 scale) that define character behavior
- **Communication Style**: Text-based style descriptors (casual, professional, friendly, etc.)
- **Content Tone**: Overall tone of generated content (positive, neutral, edgy, etc.)
- **LLM Integration**: Personality traits are converted to prompts for content generation
- **Persona Templates**: Pre-configured personality profiles for quick setup
- **Export Functionality**: Export persona as JSON or text prompt for other AI tools

---

## Personality Traits

### Core Traits (0.0 to 1.0 scale)

Each character has five core personality traits stored in the `character_personalities` table:

1. **Extroversion** (0.0 = introverted, 1.0 = extroverted)
   - Affects: Social engagement, post frequency, interaction style
   - Low (0.0-0.3): Reserved, thoughtful, minimal social interaction
   - Medium (0.4-0.6): Balanced social presence
   - High (0.7-1.0): Outgoing, frequent posts, high engagement

2. **Creativity** (0.0 = conventional, 1.0 = highly creative)
   - Affects: Content originality, artistic expression, experimental posts
   - Low (0.0-0.3): Traditional, straightforward content
   - Medium (0.4-0.6): Balanced creativity
   - High (0.7-1.0): Innovative, artistic, experimental content

3. **Humor** (0.0 = serious, 1.0 = very humorous)
   - Affects: Use of jokes, memes, lighthearted content
   - Low (0.0-0.3): Serious, professional tone
   - Medium (0.4-0.6): Occasional humor
   - High (0.7-1.0): Frequent jokes, memes, playful content

4. **Professionalism** (0.0 = casual, 1.0 = highly professional)
   - Affects: Formality, business content, brand partnerships
   - Low (0.0-0.3): Very casual, personal content
   - Medium (0.4-0.6): Balanced professional/casual
   - High (0.7-1.0): Professional, business-focused content

5. **Authenticity** (0.0 = curated, 1.0 = very authentic)
   - Affects: Personal stories, vulnerability, real experiences
   - Low (0.0-0.3): Highly curated, polished content
   - Medium (0.4-0.6): Balanced authenticity
   - High (0.7-1.0): Raw, personal, vulnerable content

### Communication Style

Text-based descriptors that define how the character communicates:

- **casual**: Relaxed, informal language
- **professional**: Formal, business-appropriate language
- **friendly**: Warm, approachable, welcoming
- **sassy**: Bold, confident, slightly provocative
- **witty**: Clever, quick, humorous
- **thoughtful**: Reflective, deep, contemplative
- **energetic**: High-energy, enthusiastic, upbeat
- **calm**: Peaceful, serene, composed

### Content Tone

Overall emotional tone of generated content:

- **positive**: Optimistic, uplifting, encouraging
- **neutral**: Balanced, factual, objective
- **edgy**: Bold, provocative, boundary-pushing
- **inspirational**: Motivating, empowering, aspirational
- **humorous**: Lighthearted, funny, entertaining
- **serious**: Thoughtful, important, meaningful

### Preferred Topics

Array of topics the character is interested in and posts about:

- Examples: fitness, travel, fashion, technology, food, lifestyle, beauty, gaming, etc.
- Used to guide content generation toward relevant topics
- Can be updated based on character interests

---

## LLM Integration

### Personality Prompt Generation

Personality traits are converted into a structured prompt for LLM-based content generation:

```python
def generate_personality_prompt(personality: CharacterPersonality) -> str:
    """Generate LLM prompt from personality traits."""
    traits = []
    
    # Map traits to descriptions
    if personality.extroversion > 0.7:
        traits.append("outgoing and social")
    elif personality.extroversion < 0.3:
        traits.append("reserved and thoughtful")
    
    if personality.creativity > 0.7:
        traits.append("highly creative and artistic")
    elif personality.creativity < 0.3:
        traits.append("practical and conventional")
    
    if personality.humor > 0.7:
        traits.append("humorous and playful")
    elif personality.humor < 0.3:
        traits.append("serious and focused")
    
    if personality.professionalism > 0.7:
        traits.append("professional and business-oriented")
    elif personality.professionalism < 0.3:
        traits.append("casual and personal")
    
    if personality.authenticity > 0.7:
        traits.append("authentic and vulnerable")
    elif personality.authenticity < 0.3:
        traits.append("curated and polished")
    
    # Build prompt
    prompt = f"You are a {personality.communication_style} character with a {personality.content_tone} tone. "
    prompt += f"Your personality is: {', '.join(traits)}. "
    
    if personality.preferred_topics:
        prompt += f"You are interested in: {', '.join(personality.preferred_topics)}. "
    
    if personality.llm_personality_prompt:
        prompt += personality.llm_personality_prompt
    
    return prompt
```

### Temperature Setting

The `temperature` field (0.0-2.0) controls LLM randomness:
- **0.0-0.5**: Very deterministic, consistent responses
- **0.6-0.9**: Balanced creativity and consistency (default: 0.7)
- **1.0-2.0**: High creativity, more varied responses

### Custom Personality Prompt

Users can provide a custom `llm_personality_prompt` that is appended to the generated prompt. This allows for fine-grained control over character behavior.

---

## Persona Templates

Pre-configured personality profiles for quick character setup:

### Template: "The Influencer"
- Extroversion: 0.8
- Creativity: 0.7
- Humor: 0.6
- Professionalism: 0.6
- Authenticity: 0.7
- Communication Style: friendly
- Content Tone: positive
- Preferred Topics: lifestyle, fashion, travel

### Template: "The Professional"
- Extroversion: 0.5
- Creativity: 0.4
- Humor: 0.3
- Professionalism: 0.9
- Authenticity: 0.5
- Communication Style: professional
- Content Tone: neutral
- Preferred Topics: business, technology, career

### Template: "The Creative"
- Extroversion: 0.6
- Creativity: 0.9
- Humor: 0.7
- Professionalism: 0.4
- Authenticity: 0.8
- Communication Style: witty
- Content Tone: inspirational
- Preferred Topics: art, design, creativity

### Template: "The Authentic"
- Extroversion: 0.5
- Creativity: 0.5
- Humor: 0.4
- Professionalism: 0.3
- Authenticity: 0.9
- Communication Style: thoughtful
- Content Tone: positive
- Preferred Topics: personal growth, wellness, relationships

### Template: "The Entertainer"
- Extroversion: 0.9
- Creativity: 0.8
- Humor: 0.9
- Professionalism: 0.3
- Authenticity: 0.6
- Communication Style: energetic
- Content Tone: humorous
- Preferred Topics: entertainment, memes, pop culture

---

## Export Functionality

### JSON Export

Export personality as structured JSON for use in other systems:

```json
{
  "personality": {
    "extroversion": 0.7,
    "creativity": 0.8,
    "humor": 0.6,
    "professionalism": 0.5,
    "authenticity": 0.7
  },
  "communication_style": "friendly",
  "content_tone": "positive",
  "preferred_topics": ["fitness", "travel", "lifestyle"],
  "llm_temperature": 0.7,
  "custom_prompt": "Always be encouraging and supportive."
}
```

### Text Prompt Export

Export as a ready-to-use LLM prompt:

```
You are a friendly character with a positive tone. Your personality is: outgoing and social, highly creative and artistic, humorous and playful, casual and personal, authentic and vulnerable. You are interested in: fitness, travel, lifestyle. Always be encouraging and supportive.
```

---

## API Integration

### Personality Management Endpoints

- **GET /api/characters/{character_id}** - Returns personality data
- **PUT /api/characters/{character_id}** - Updates personality traits
- **POST /api/characters** - Creates character with personality
- **GET /api/characters/{character_id}/personality/export** - Export personality (future)
- **GET /api/personality/templates** - List persona templates (future)

### Content Generation Integration

When generating content (text, captions, comments), the content generation service:

1. Retrieves character personality from database
2. Generates personality prompt using `generate_personality_prompt()`
3. Combines personality prompt with content-specific prompt
4. Uses LLM with specified temperature to generate content
5. Returns generated content that matches character personality

---

## Implementation Notes

### Database Schema

Personality data is stored in `character_personalities` table:
- One-to-one relationship with `characters` table
- Traits stored as DECIMAL(3,2) for precision
- Communication style and tone as VARCHAR fields
- Preferred topics as TEXT[] array
- Custom prompt as TEXT field

### Validation

- All trait values must be between 0.0 and 1.0
- Temperature must be between 0.0 and 2.0
- Communication style and content tone should match predefined values
- Preferred topics should be non-empty strings

### Default Values

If personality is not provided during character creation:
- All traits default to 0.5 (balanced)
- Communication style: null (no specific style)
- Content tone: null (no specific tone)
- Temperature: 0.7 (balanced creativity)

---

## Future Enhancements

1. **Personality Analytics**: Track which personality traits generate most engagement
2. **A/B Testing**: Test different personality configurations
3. **Dynamic Personality**: Personality traits that evolve based on performance
4. **Multi-Personality**: Characters with different personas for different platforms
5. **Personality Recommendations**: AI-suggested personality based on target audience

---

**Last Updated:** 2025-12-15  
**Version:** 1.0

