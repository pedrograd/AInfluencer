"""
Character Service
Complete character management system as per Character Management System documentation
"""
import logging
import shutil
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Character, FaceReference, MediaItem

logger = logging.getLogger(__name__)


class CharacterManager:
    """
    Character Manager class for multi-character management
    As specified in Character Management System documentation
    """
    
    def __init__(self, base_path: Path = None):
        if base_path is None:
            base_path = Path("characters")
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.characters: Dict[str, Character] = {}
    
    def load_characters(self, db: Session):
        """Load all characters from database"""
        characters = db.query(Character).filter(Character.deleted_at.is_(None)).all()
        for char in characters:
            self.characters[char.id] = char
            # Ensure character directory exists
            char_dir = self.base_path / char.id
            char_dir.mkdir(exist_ok=True)
            (char_dir / "face_references").mkdir(exist_ok=True)
            (char_dir / "content").mkdir(exist_ok=True)
        return self.characters
    
    def get_character(self, character_id: str) -> Optional[Character]:
        """Get a character by ID"""
        return self.characters.get(character_id)
    
    def list_characters(self) -> List[str]:
        """List all character IDs"""
        return list(self.characters.keys())
    
    def get_character_directory(self, character_id: str) -> Path:
        """Get the directory path for a character"""
        return self.base_path / character_id


class CharacterService:
    """Service for managing characters with full Character Management System features"""
    
    def __init__(self, db: Session, characters_root: Path):
        self.db = db
        self.characters_root = Path(characters_root)
        self.characters_root.mkdir(parents=True, exist_ok=True)
        self.manager = CharacterManager(characters_root)
        self.manager.load_characters(db)
    
    def create_character(
        self,
        name: str,
        age: Optional[int] = None,
        description: Optional[str] = None,
        persona: Optional[Dict[str, Any]] = None,
        appearance: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None,
        content_preferences: Optional[Dict[str, Any]] = None,
        consistency_rules: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Character:
        """Create a new character with full Character Management System support"""
        character = Character(
            name=name,
            age=age,
            description=description or "",
            persona=persona or {},
            appearance=appearance or {},
            style=style or {},
            content_preferences=content_preferences or {},
            consistency_rules=consistency_rules or {},
            settings=settings or {},
            metadata=metadata or {}
        )
        
        self.db.add(character)
        self.db.commit()
        self.db.refresh(character)
        
        # Create character directory structure
        char_dir = self.characters_root / character.id
        char_dir.mkdir(exist_ok=True)
        (char_dir / "face_references").mkdir(exist_ok=True)
        (char_dir / "content").mkdir(exist_ok=True)
        
        # Save character config to file
        self._save_character_config(character)
        
        # Update manager
        self.manager.characters[character.id] = character
        
        return character
    
    def create_character_from_template(
        self,
        template_name: str,
        name: str,
        **overrides
    ) -> Character:
        """Create a character from a pre-built template"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Merge template with overrides
        config = {
            "name": name,
            "persona": {**template.get("persona", {}), **overrides.get("persona", {})},
            "appearance": {**template.get("appearance", {}), **overrides.get("appearance", {})},
            "style": {**template.get("style", {}), **overrides.get("style", {})},
            "content_preferences": {**template.get("content_preferences", {}), **overrides.get("content_preferences", {})},
            "consistency_rules": {**template.get("consistency_rules", {}), **overrides.get("consistency_rules", {})},
        }
        
        return self.create_character(
            name=config["name"],
            persona=config["persona"],
            appearance=config["appearance"],
            style=config["style"],
            content_preferences=config["content_preferences"],
            consistency_rules=config["consistency_rules"]
        )
    
    def get_character(self, character_id: str) -> Optional[Character]:
        """Get a character by ID"""
        return self.db.query(Character).filter(
            Character.id == character_id,
            Character.deleted_at.is_(None)
        ).first()
    
    def get_character_by_name(self, name: str) -> Optional[Character]:
        """Get a character by name"""
        return self.db.query(Character).filter(
            Character.name == name,
            Character.deleted_at.is_(None)
        ).first()
    
    def list_characters(
        self,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """List all characters with optional search"""
        query = self.db.query(Character).filter(Character.deleted_at.is_(None))
        
        if search:
            # SQLite LIKE is case-insensitive for ASCII, but we'll use lower() for consistency
            search_lower = search.lower()
            query = query.filter(
                (func.lower(Character.name).like(f"%{search_lower}%")) |
                (func.lower(Character.description).like(f"%{search_lower}%"))
            )
        
        total = query.count()
        offset = (page - 1) * limit
        characters = query.offset(offset).limit(limit).all()
        
        # Add statistics and directory info
        for char in characters:
            char.face_reference_count = len([fr for fr in char.face_references if not fr.deleted_at])
            char.media_count = len([m for m in char.media_items if not m.deleted_at])
            char.directory_path = str(self.characters_root / char.id)
        
        return {
            "characters": characters,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    
    def update_character(
        self,
        character_id: str,
        name: Optional[str] = None,
        age: Optional[int] = None,
        description: Optional[str] = None,
        persona: Optional[Dict[str, Any]] = None,
        appearance: Optional[Dict[str, Any]] = None,
        style: Optional[Dict[str, Any]] = None,
        content_preferences: Optional[Dict[str, Any]] = None,
        consistency_rules: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Character]:
        """Update a character with full Character Management System support"""
        character = self.get_character(character_id)
        if not character:
            return None
        
        if name is not None:
            character.name = name
        if age is not None:
            character.age = age
        if description is not None:
            character.description = description
        if persona is not None:
            character.persona = {**character.persona, **persona}
        if appearance is not None:
            character.appearance = {**character.appearance, **appearance}
        if style is not None:
            character.style = {**character.style, **style}
        if content_preferences is not None:
            character.content_preferences = {**character.content_preferences, **content_preferences}
        if consistency_rules is not None:
            character.consistency_rules = {**character.consistency_rules, **consistency_rules}
        if settings is not None:
            character.settings = {**character.settings, **settings}
        if metadata is not None:
            character.meta_data = {**character.meta_data, **metadata}
        
        character.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(character)
        
        # Update character config file
        self._save_character_config(character)
        
        return character
    
    def delete_character(self, character_id: str, hard_delete: bool = False) -> bool:
        """Delete a character (soft delete by default)"""
        character = self.get_character(character_id)
        if not character:
            return False
        
        if hard_delete:
            # Hard delete - remove from database and filesystem
            char_dir = self.characters_root / character.id
            if char_dir.exists():
                shutil.rmtree(char_dir)
            self.db.delete(character)
            if character.id in self.manager.characters:
                del self.manager.characters[character.id]
        else:
            # Soft delete
            character.deleted_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def add_face_reference(
        self,
        character_id: str,
        file_path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[FaceReference]:
        """Add a face reference to a character"""
        character = self.get_character(character_id)
        if not character:
            return None
        
        # Ensure character directory exists
        char_dir = self.characters_root / character.id
        face_ref_dir = char_dir / "face_references"
        face_ref_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy file to character directory
        dest_path = face_ref_dir / file_path.name
        if file_path != dest_path:
            shutil.copy2(file_path, dest_path)
        
        # Get file info
        from PIL import Image
        file_name = dest_path.name
        file_size = dest_path.stat().st_size
        
        # Get image dimensions
        width = None
        height = None
        try:
            with Image.open(dest_path) as img:
                width, height = img.size
        except Exception as e:
            logger.error(f"Failed to get image dimensions: {e}")
        
        # Determine MIME type
        ext = dest_path.suffix.lower()
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp"
        }.get(ext, "image/jpeg")
        
        # Create face reference
        face_ref = FaceReference(
            character_id=character_id,
            file_path=str(dest_path),
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            width=width,
            height=height,
            metadata=metadata or {}
        )
        
        self.db.add(face_ref)
        self.db.commit()
        self.db.refresh(face_ref)
        
        return face_ref
    
    def remove_face_reference(self, character_id: str, face_reference_id: str) -> bool:
        """Remove a face reference"""
        face_ref = self.db.query(FaceReference).filter(
            FaceReference.id == face_reference_id,
            FaceReference.character_id == character_id,
            FaceReference.deleted_at.is_(None)
        ).first()
        
        if face_ref:
            face_ref.deleted_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def get_character_statistics(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Get character statistics"""
        character = self.get_character(character_id)
        if not character:
            return None
        
        # Count media items
        media_items = [m for m in character.media_items if not m.deleted_at]
        total_generations = len(media_items)
        total_images = len([m for m in media_items if m.type == "image"])
        total_videos = len([m for m in media_items if m.type == "video"])
        
        # Calculate average quality
        quality_scores = []
        for media in media_items:
            for score in media.quality_scores:
                quality_scores.append(score.overall_score)
        
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Face reference count
        face_ref_count = len([fr for fr in character.face_references if not fr.deleted_at])
        
        return {
            "total_generations": total_generations,
            "total_images": total_images,
            "total_videos": total_videos,
            "face_reference_count": face_ref_count,
            "average_quality": average_quality,
            "last_generation": max([m.created_at for m in media_items], default=None)
        }
    
    def export_character(self, character_id: str, output_path: Path) -> bool:
        """Export character to a JSON file with all data"""
        character = self.get_character(character_id)
        if not character:
            return False
        
        char_dir = self.characters_root / character.id
        
        # Prepare export data
        export_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "character": {
                "id": character.id,
                "name": character.name,
                "age": character.age,
                "description": character.description,
                "persona": character.persona,
                "appearance": character.appearance,
                "style": character.style,
                "content_preferences": character.content_preferences,
                "consistency_rules": character.consistency_rules,
                "settings": character.settings,
                "metadata": character.meta_data,
                "created_at": character.created_at.isoformat() if character.created_at else None,
                "updated_at": character.updated_at.isoformat() if character.updated_at else None,
            },
            "face_references": [],
            "style_guide": character.style
        }
        
        # Add face reference metadata
        for face_ref in character.face_references:
            if not face_ref.deleted_at:
                export_data["face_references"].append({
                    "id": face_ref.id,
                    "file_name": face_ref.file_name,
                    "width": face_ref.width,
                    "height": face_ref.height,
                    "metadata": face_ref.meta_data
                })
        
        # Write export file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Copy face reference images to references folder
        if export_data["face_references"]:
            ref_dir = output_path.parent / "references"
            ref_dir.mkdir(exist_ok=True)
            
            for face_ref in character.face_references:
                if not face_ref.deleted_at and Path(face_ref.file_path).exists():
                    shutil.copy2(face_ref.file_path, ref_dir / face_ref.file_name)
        
        return True
    
    def import_character(self, import_path: Path) -> Optional[Character]:
        """Import character from a JSON file"""
        import_path = Path(import_path)
        if not import_path.exists():
            return None
        
        with open(import_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        char_data = data.get("character", {})
        
        # Create character
        character = self.create_character(
            name=char_data.get("name", "Imported Character"),
            age=char_data.get("age"),
            description=char_data.get("description"),
            persona=char_data.get("persona", {}),
            appearance=char_data.get("appearance", {}),
            style=char_data.get("style", {}),
            content_preferences=char_data.get("content_preferences", {}),
            consistency_rules=char_data.get("consistency_rules", {}),
            settings=char_data.get("settings", {}),
            metadata=char_data.get("metadata", {})
        )
        
        # Import face references if available
        ref_dir = import_path.parent / "references"
        if ref_dir.exists():
            for ref_info in data.get("face_references", []):
                ref_file = ref_dir / ref_info["file_name"]
                if ref_file.exists():
                    self.add_face_reference(character.id, ref_file, ref_info.get("metadata"))
        
        return character
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a pre-built character template"""
        templates = self.get_templates()
        return templates.get(template_name)
    
    def get_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get all available character templates"""
        return {
            "fashion_influencer": {
                "name": "Fashion Influencer",
                "persona": {
                    "personality": {
                        "traits": ["confident", "creative", "fashion-forward"],
                        "voice": "polished and aspirational",
                        "tone": "elegant and inspiring"
                    },
                    "interests": ["fashion", "lifestyle", "photography"],
                    "values": ["self-expression", "aesthetics", "trend-setting"]
                },
                "appearance": {
                    "face": {
                        "age": 25,
                        "ethnicity": "diverse",
                        "eyes": "expressive",
                        "skin": "flawless"
                    },
                    "hair": {
                        "style": "trendy",
                        "color": "varied"
                    },
                    "body": {
                        "build": "slender, model-like"
                    }
                },
                "style": {
                    "photography": "professional fashion photography",
                    "color_palette": {
                        "primary": "warm tones",
                        "secondary": "vibrant colors",
                        "accent": "sophisticated neutrals"
                    },
                    "lighting": "studio lighting with soft shadows",
                    "composition": "centered subject, fashion-forward poses",
                    "mood": "aspirational, elegant, confident"
                },
                "content_preferences": {
                    "image_types": ["fashion photography", "lifestyle photography", "editorial"],
                    "video_types": ["fashion content", "style tips", "behind-the-scenes"],
                    "topics": ["fashion", "style", "trends", "lifestyle"],
                    "themes": ["aspirational", "trendy", "sophisticated"]
                },
                "consistency_rules": {
                    "face": {
                        "method": "InstantID",
                        "strength": 0.8,
                        "quality_threshold": 8.0
                    },
                    "style": {
                        "must_match": True,
                        "color_grading": "warm tones",
                        "photography_style": "professional fashion"
                    },
                    "persona": {
                        "voice_consistency": "high",
                        "personality_traits": "strict",
                        "content_alignment": "required"
                    }
                }
            },
            "fitness_influencer": {
                "name": "Fitness Influencer",
                "persona": {
                    "personality": {
                        "traits": ["energetic", "motivated", "authentic"],
                        "voice": "encouraging and real",
                        "tone": "motivational and relatable"
                    },
                    "interests": ["fitness", "health", "wellness"],
                    "values": ["health", "discipline", "authenticity"]
                },
                "appearance": {
                    "face": {
                        "age": 28,
                        "ethnicity": "diverse",
                        "eyes": "bright and energetic",
                        "skin": "healthy, glowing"
                    },
                    "hair": {
                        "style": "athletic, practical",
                        "color": "natural"
                    },
                    "body": {
                        "build": "athletic, toned, strong"
                    }
                },
                "style": {
                    "photography": "athletic, energetic style",
                    "color_palette": {
                        "primary": "natural tones",
                        "secondary": "vibrant activewear colors",
                        "accent": "energetic"
                    },
                    "lighting": "natural lighting, outdoor or gym",
                    "composition": "dynamic poses, action shots",
                    "mood": "energetic, motivational, authentic"
                },
                "content_preferences": {
                    "image_types": ["fitness photography", "lifestyle", "athletic"],
                    "video_types": ["workout videos", "fitness tips", "transformation stories"],
                    "topics": ["fitness", "health", "workouts", "nutrition"],
                    "themes": ["motivational", "authentic", "energetic"]
                },
                "consistency_rules": {
                    "face": {
                        "method": "InstantID",
                        "strength": 0.8,
                        "quality_threshold": 8.0
                    },
                    "style": {
                        "must_match": True,
                        "color_grading": "natural",
                        "photography_style": "athletic"
                    },
                    "persona": {
                        "voice_consistency": "high",
                        "personality_traits": "strict",
                        "content_alignment": "required"
                    }
                }
            },
            "lifestyle_influencer": {
                "name": "Lifestyle Influencer",
                "persona": {
                    "personality": {
                        "traits": ["authentic", "relatable", "friendly"],
                        "voice": "casual and authentic",
                        "tone": "warm and relatable"
                    },
                    "interests": ["lifestyle", "travel", "food", "wellness"],
                    "values": ["authenticity", "connection", "wellness"]
                },
                "appearance": {
                    "face": {
                        "age": 26,
                        "ethnicity": "diverse",
                        "eyes": "warm and friendly",
                        "skin": "natural, healthy"
                    },
                    "hair": {
                        "style": "casual, natural",
                        "color": "natural"
                    },
                    "body": {
                        "build": "natural, healthy"
                    }
                },
                "style": {
                    "photography": "casual, authentic style",
                    "color_palette": {
                        "primary": "natural colors",
                        "secondary": "warm tones",
                        "accent": "soft pastels"
                    },
                    "lighting": "natural lighting, golden hour",
                    "composition": "candid, lifestyle moments",
                    "mood": "authentic, relatable, warm"
                },
                "content_preferences": {
                    "image_types": ["lifestyle photography", "casual", "candid"],
                    "video_types": ["lifestyle vlogs", "day-in-the-life", "tutorials"],
                    "topics": ["lifestyle", "travel", "food", "wellness"],
                    "themes": ["authentic", "relatable", "aspirational"]
                },
                "consistency_rules": {
                    "face": {
                        "method": "InstantID",
                        "strength": 0.8,
                        "quality_threshold": 8.0
                    },
                    "style": {
                        "must_match": True,
                        "color_grading": "natural",
                        "photography_style": "casual lifestyle"
                    },
                    "persona": {
                        "voice_consistency": "high",
                        "personality_traits": "moderate",
                        "content_alignment": "required"
                    }
                }
            }
        }
    
    def _save_character_config(self, character: Character):
        """Save character configuration to file"""
        char_dir = self.characters_root / character.id
        char_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = char_dir / "config.json"
        config = {
            "id": character.id,
            "name": character.name,
            "age": character.age,
            "description": character.description,
            "persona": character.persona,
            "appearance": character.appearance,
            "style": character.style,
            "content_preferences": character.content_preferences,
            "consistency_rules": character.consistency_rules,
            "settings": character.settings,
            "metadata": character.meta_data,
            "created_at": character.created_at.isoformat() if character.created_at else None,
            "updated_at": character.updated_at.isoformat() if character.updated_at else None,
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def batch_generate(
        self,
        character_ids: List[str],
        count_per_character: int = 10,
        generation_service=None
    ) -> Dict[str, Any]:
        """Batch generate content for multiple characters"""
        results = {}
        
        for char_id in character_ids:
            character = self.get_character(char_id)
            if not character:
                results[char_id] = {"error": "Character not found"}
                continue
            
            # This would integrate with generation service
            # For now, return placeholder
            results[char_id] = {
                "character_id": char_id,
                "character_name": character.name,
                "requested_count": count_per_character,
                "status": "pending"
            }
        
        return results
    
    def compare_characters(self, character_ids: List[str]) -> Dict[str, Any]:
        """
        Compare multiple characters side-by-side
        
        Args:
            character_ids: List of character IDs to compare
        
        Returns:
            Comparison data with similarities and differences
        """
        characters = []
        for char_id in character_ids:
            char = self.get_character(char_id)
            if char:
                characters.append(char)
        
        if len(characters) < 2:
            return {"error": "Need at least 2 characters to compare"}
        
        comparison = {
            "characters": [
                {
                    "id": char.id,
                    "name": char.name,
                    "age": char.age,
                    "description": char.description,
                    "persona_summary": char.persona.get("summary", "") if char.persona else "",
                    "style_summary": char.style.get("photography", "") if char.style else "",
                    "face_references_count": len([fr for fr in char.face_references if not fr.deleted_at]) if hasattr(char, 'face_references') else 0
                }
                for char in characters
            ],
            "similarities": [],
            "differences": []
        }
        
        # Compare personas
        if all(char.persona for char in characters):
            personas = [char.persona for char in characters]
            # Find common traits
            common_traits = set()
            if personas:
                first_traits = set(personas[0].get("personality_traits", []))
                for persona in personas[1:]:
                    first_traits &= set(persona.get("personality_traits", []))
                common_traits = first_traits
            comparison["similarities"].append({
                "category": "personality",
                "common_traits": list(common_traits)
            })
        
        # Compare styles
        if all(char.style for char in characters):
            styles = [char.style for char in characters]
            # Find common style elements
            comparison["similarities"].append({
                "category": "style",
                "note": "Style comparison available"
            })
        
        return comparison
    
    def clone_character(
        self,
        character_id: str,
        new_name: str,
        variations: Optional[Dict[str, Any]] = None
    ) -> Character:
        """
        Clone character with optional variations
        
        Args:
            character_id: ID of character to clone
            new_name: Name for cloned character
            variations: Optional dict of variations to apply
        
        Returns:
            New cloned character
        """
        original = self.get_character(character_id)
        if not original:
            raise ValueError(f"Character not found: {character_id}")
        
        variations = variations or {}
        
        # Create new character with copied data
        cloned = Character(
            name=new_name,
            age=variations.get("age", original.age),
            description=variations.get("description", original.description),
            persona=variations.get("persona", original.persona.copy() if original.persona else {}),
            appearance=variations.get("appearance", original.appearance.copy() if original.appearance else {}),
            style=variations.get("style", original.style.copy() if original.style else {}),
            content_preferences=variations.get("content_preferences", original.content_preferences.copy() if original.content_preferences else {}),
            consistency_rules=variations.get("consistency_rules", original.consistency_rules.copy() if original.consistency_rules else {}),
            settings=variations.get("settings", original.settings.copy() if original.settings else {}),
            metadata={
                **(original.meta_data.copy() if original.meta_data else {}),
                "cloned_from": character_id,
                "cloned_at": datetime.utcnow().isoformat()
            }
        )
        
        self.db.add(cloned)
        self.db.commit()
        self.db.refresh(cloned)
        
        # Copy face references
        if hasattr(original, 'face_references'):
            for face_ref in original.face_references:
                if not face_ref.deleted_at:
                    # Copy face reference file
                    import shutil
                    original_ref_path = Path(face_ref.file_path)
                    if original_ref_path.exists():
                        char_dir = self.characters_root / cloned.id / "face_references"
                        char_dir.mkdir(parents=True, exist_ok=True)
                        new_ref_path = char_dir / original_ref_path.name
                        shutil.copy2(original_ref_path, new_ref_path)
                        
                        # Create new face reference
                        from models import FaceReference
                        new_face_ref = FaceReference(
                            character_id=cloned.id,
                            file_path=str(new_ref_path),
                            method=face_ref.method,
                            strength=face_ref.strength
                        )
                        self.db.add(new_face_ref)
        
        self.db.commit()
        self._save_character_config(cloned)
        
        return cloned
    
    def create_character_version(
        self,
        character_id: str,
        version_name: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a version snapshot of character
        
        Args:
            character_id: Character ID
            version_name: Name for this version
            notes: Optional notes about this version
        
        Returns:
            Version information
        """
        character = self.get_character(character_id)
        if not character:
            raise ValueError(f"Character not found: {character_id}")
        
        # Save version snapshot
        char_dir = self.characters_root / character_id / "versions"
        char_dir.mkdir(parents=True, exist_ok=True)
        
        version_path = char_dir / f"{version_name}.json"
        version_data = {
            "version_name": version_name,
            "created_at": datetime.utcnow().isoformat(),
            "notes": notes,
            "character": {
                "id": character.id,
                "name": character.name,
                "persona": character.persona,
                "appearance": character.appearance,
                "style": character.style,
                "content_preferences": character.content_preferences,
                "consistency_rules": character.consistency_rules,
                "settings": character.settings
            }
        }
        
        with open(version_path, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)
        
        return version_data
    
    def get_character_versions(self, character_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a character"""
        char_dir = self.characters_root / character_id / "versions"
        if not char_dir.exists():
            return []
        
        versions = []
        for version_file in char_dir.glob("*.json"):
            try:
                with open(version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    versions.append(version_data)
            except Exception as e:
                logger.error(f"Error reading version file {version_file}: {e}")
        
        return sorted(versions, key=lambda v: v.get("created_at", ""), reverse=True)
    
    def restore_character_version(
        self,
        character_id: str,
        version_name: str
    ) -> Character:
        """Restore character to a specific version"""
        char_dir = self.characters_root / character_id / "versions"
        version_path = char_dir / f"{version_name}.json"
        
        if not version_path.exists():
            raise ValueError(f"Version not found: {version_name}")
        
        with open(version_path, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
        
        character = self.get_character(character_id)
        if not character:
            raise ValueError(f"Character not found: {character_id}")
        
        # Restore character data from version
        char_data = version_data.get("character", {})
        character.persona = char_data.get("persona", {})
        character.appearance = char_data.get("appearance", {})
        character.style = char_data.get("style", {})
        character.content_preferences = char_data.get("content_preferences", {})
        character.consistency_rules = char_data.get("consistency_rules", {})
        character.settings = char_data.get("settings", {})
        
        self.db.commit()
        self.db.refresh(character)
        self._save_character_config(character)
        
        return character
    
    def add_character_tags(self, character_id: str, tags: List[str]) -> Character:
        """Add tags to character"""
        character = self.get_character(character_id)
        if not character:
            raise ValueError(f"Character not found: {character_id}")
        
        if not character.meta_data:
            character.meta_data = {}
        
        existing_tags = character.meta_data.get("tags", [])
        new_tags = [tag for tag in tags if tag not in existing_tags]
        character.meta_data["tags"] = existing_tags + new_tags
        
        self.db.commit()
        self.db.refresh(character)
        
        return character
    
    def get_characters_by_tag(self, tag: str) -> List[Character]:
        """Get all characters with a specific tag"""
        characters = self.db.query(Character).filter(
            Character.deleted_at.is_(None)
        ).all()
        
        matching = []
        for char in characters:
            tags = char.meta_data.get("tags", []) if char.meta_data else []
            if tag in tags:
                matching.append(char)
        
        return matching
