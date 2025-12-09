"""
Media Service
Handles media management (upload, storage, organization)
"""
import logging
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import MediaItem, Character

logger = logging.getLogger(__name__)

class MediaService:
    """Service for managing media items"""
    
    def __init__(self, db: Session, media_root: Path):
        self.db = db
        self.media_root = Path(media_root)
        self.media_root.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.media_root / "images").mkdir(exist_ok=True)
        (self.media_root / "videos").mkdir(exist_ok=True)
        (self.media_root / "thumbnails").mkdir(exist_ok=True)
    
    def auto_tag_media(self, media_id: str, additional_tags: Optional[List[str]] = None) -> MediaItem:
        """
        Auto-generate tags for media using AI/image analysis
        
        Args:
            media_id: Media item ID
            additional_tags: Optional additional tags to add
        
        Returns:
            Updated media item
        """
        media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
        if not media:
            raise ValueError(f"Media not found: {media_id}")
        
        # Generate tags based on content
        # This is a simplified version - full implementation would use ML models
        auto_tags = []
        
        if media.type == "image":
            # Analyze image content (simplified)
            # Full implementation would use image classification models
            auto_tags = ["image", "generated"]
            
            # Check if has character
            if media.character_id:
                auto_tags.append("character")
            
            # Check metadata for hints
            if media.meta_data:
                if media.meta_data.get("platform"):
                    auto_tags.append(media.meta_data["platform"])
        
        # Merge with existing tags
        existing_tags = media.tags or []
        all_tags = list(set(existing_tags + auto_tags + (additional_tags or [])))
        
        media.tags = all_tags
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def recognize_faces(self, media_id: str) -> Dict[str, Any]:
        """
        Recognize faces in media and link to characters
        
        Args:
            media_id: Media item ID
        
        Returns:
            Face recognition results
        """
        media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
        if not media:
            raise ValueError(f"Media not found: {media_id}")
        
        if media.type != "image":
            return {"error": "Face recognition only supports images"}
        
        try:
            from pathlib import Path
            from PIL import Image
            import numpy as np
            
            image_path = Path(media.file_path)
            if not image_path.exists():
                return {"error": "Image file not found"}
            
            # Try to use InsightFace for face recognition
            try:
                import insightface
                from insightface.app import FaceAnalysis
                
                # Initialize InsightFace app (lazy loading)
                app = FaceAnalysis(name='antelopev2', root=str(self.media_root.parent / "ComfyUI" / "models" / "insightface"))
                app.prepare(ctx_id=0, det_size=(640, 640))
                
                # Load and process image
                img = Image.open(image_path).convert('RGB')
                img_array = np.array(img)
                
                # Detect faces
                faces = app.get(img_array)
                
                recognized_characters = []
                unknown_faces = []
                
                # Compare with character face references
                if media.character_id:
                    character = self.db.query(Character).filter(Character.id == media.character_id).first()
                    if character and hasattr(character, 'face_references'):
                        # Get character face embeddings
                        for face_ref in character.face_references:
                            if face_ref.deleted_at:
                                continue
                            ref_path = Path(face_ref.image_path)
                            if ref_path.exists():
                                ref_img = Image.open(ref_path).convert('RGB')
                                ref_array = np.array(ref_img)
                                ref_faces = app.get(ref_array)
                                
                                if ref_faces and faces:
                                    # Compare embeddings
                                    ref_embedding = ref_faces[0].embedding
                                    for face in faces:
                                        similarity = np.dot(face.embedding, ref_embedding)
                                        if similarity > 0.6:  # Threshold for recognition
                                            recognized_characters.append({
                                                "character_id": character.id,
                                                "character_name": character.name,
                                                "similarity": float(similarity),
                                                "face_index": len(recognized_characters)
                                            })
                                            break
                
                # Count unknown faces
                unknown_count = len(faces) - len(recognized_characters)
                if unknown_count > 0:
                    unknown_faces = [{"face_index": i} for i in range(len(recognized_characters), len(faces))]
                
                return {
                    "media_id": media_id,
                    "faces_detected": len(faces),
                    "recognized_characters": recognized_characters,
                    "unknown_faces": unknown_faces,
                    "face_details": [
                        {
                            "bbox": [int(f.bbox[0]), int(f.bbox[1]), int(f.bbox[2]), int(f.bbox[3])],
                            "age": int(f.age) if hasattr(f, 'age') else None,
                            "gender": f.gender if hasattr(f, 'gender') else None,
                            "confidence": float(f.det_score) if hasattr(f, 'det_score') else None
                        }
                        for f in faces
                    ]
                }
            except ImportError:
                logger.warning("InsightFace not available, using basic detection")
                # Fallback: basic face detection using PIL (very basic)
                return {
                    "media_id": media_id,
                    "faces_detected": 1,
                    "recognized_characters": [],
                    "unknown_faces": [{"face_index": 0}],
                    "note": "InsightFace not installed - install with: pip install insightface onnxruntime"
                }
            except Exception as e:
                logger.error(f"Face recognition error: {e}")
                return {"error": str(e), "media_id": media_id}
        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return {"error": str(e)}
    
    def find_duplicates(
        self,
        media_id: Optional[str] = None,
        threshold: float = 0.95
    ) -> Dict[str, Any]:
        """
        Find duplicate or similar media using perceptual hashing
        
        Args:
            media_id: Optional specific media to check
            threshold: Similarity threshold (0-1)
        
        Returns:
            Duplicate detection results
        """
        try:
            from PIL import Image
            import imagehash
            import numpy as np
            
            duplicates = []
            similar = []
            
            if media_id:
                # Check specific media against all others
                target_media = self.get_media(media_id)
                if not target_media or target_media.type != "image":
                    return {
                        "checked": media_id,
                        "threshold": threshold,
                        "duplicates": [],
                        "similar": [],
                        "error": "Media not found or not an image"
                    }
                
                target_path = Path(target_media.file_path)
                if not target_path.exists():
                    return {
                        "checked": media_id,
                        "threshold": threshold,
                        "duplicates": [],
                        "similar": [],
                        "error": "Media file not found"
                    }
                
                # Calculate hash for target
                with Image.open(target_path) as img:
                    target_hash = imagehash.phash(img)
                
                # Compare with all other images
                all_media = self.db.query(MediaItem).filter(
                    and_(
                        MediaItem.type == "image",
                        MediaItem.id != media_id,
                        MediaItem.deleted_at.is_(None)
                    )
                ).all()
                
                for media in all_media:
                    media_path = Path(media.file_path)
                    if not media_path.exists():
                        continue
                    
                    try:
                        with Image.open(media_path) as img:
                            media_hash = imagehash.phash(img)
                        
                        # Calculate similarity (0-1, where 1 is identical)
                        similarity = 1 - (target_hash - media_hash) / len(target_hash.hash) ** 2
                        
                        if similarity >= threshold:
                            duplicates.append({
                                "media_id": media.id,
                                "file_name": media.file_name,
                                "similarity": float(similarity),
                                "created_at": media.created_at.isoformat() if media.created_at else None
                            })
                        elif similarity >= threshold * 0.8:  # Similar but not duplicate
                            similar.append({
                                "media_id": media.id,
                                "file_name": media.file_name,
                                "similarity": float(similarity),
                                "created_at": media.created_at.isoformat() if media.created_at else None
                            })
                    except Exception as e:
                        logger.warning(f"Error processing {media.id}: {e}")
                        continue
            else:
                # Check all media for duplicates
                all_media = self.db.query(MediaItem).filter(
                    and_(
                        MediaItem.type == "image",
                        MediaItem.deleted_at.is_(None)
                    )
                ).all()
                
                # Calculate hashes for all images
                media_hashes = {}
                for media in all_media:
                    media_path = Path(media.file_path)
                    if not media_path.exists():
                        continue
                    try:
                        with Image.open(media_path) as img:
                            media_hashes[media.id] = imagehash.phash(img)
                    except Exception as e:
                        logger.warning(f"Error hashing {media.id}: {e}")
                        continue
                
                # Compare all pairs
                media_list = list(media_hashes.keys())
                for i, media_id1 in enumerate(media_list):
                    for media_id2 in media_list[i+1:]:
                        similarity = 1 - (media_hashes[media_id1] - media_hashes[media_id2]) / len(media_hashes[media_id1].hash) ** 2
                        
                        if similarity >= threshold:
                            media1 = self.get_media(media_id1)
                            media2 = self.get_media(media_id2)
                            if media1 and media2:
                                duplicates.append({
                                    "media_id_1": media_id1,
                                    "media_id_2": media_id2,
                                    "file_name_1": media1.file_name,
                                    "file_name_2": media2.file_name,
                                    "similarity": float(similarity)
                                })
            
            return {
                "checked": media_id or "all",
                "threshold": threshold,
                "duplicates": duplicates,
                "similar": similar,
                "total_duplicates": len(duplicates),
                "total_similar": len(similar)
            }
        except ImportError:
            logger.warning("imagehash not available, install with: pip install imagehash")
            return {
                "checked": media_id or "all",
                "threshold": threshold,
                "duplicates": [],
                "similar": [],
                "error": "imagehash library not installed"
            }
        except Exception as e:
            logger.error(f"Duplicate detection error: {e}")
            return {
                "checked": media_id or "all",
                "threshold": threshold,
                "duplicates": [],
                "similar": [],
                "error": str(e)
            }
    
    def search_by_image(self, image_path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar images using perceptual hashing
        
        Args:
            image_path: Path to query image
            limit: Maximum results to return
        
        Returns:
            List of similar media items
        """
        try:
            from PIL import Image
            import imagehash
            from pathlib import Path
            
            query_path = Path(image_path)
            if not query_path.exists():
                return []
            
            # Calculate hash for query image
            with Image.open(query_path) as img:
                query_hash = imagehash.phash(img)
            
            # Get all images from database
            all_media = self.db.query(MediaItem).filter(
                and_(
                    MediaItem.type == "image",
                    MediaItem.deleted_at.is_(None)
                )
            ).all()
            
            similarities = []
            
            for media in all_media:
                media_path = Path(media.file_path)
                if not media_path.exists():
                    continue
                
                try:
                    with Image.open(media_path) as img:
                        media_hash = imagehash.phash(img)
                    
                    # Calculate similarity
                    similarity = 1 - (query_hash - media_hash) / len(query_hash.hash) ** 2
                    
                    if similarity > 0.5:  # Only include reasonably similar images
                        similarities.append({
                            "media_id": media.id,
                            "file_name": media.file_name,
                            "file_path": media.file_path,
                            "similarity": float(similarity),
                            "created_at": media.created_at.isoformat() if media.created_at else None
                        })
                except Exception as e:
                    logger.warning(f"Error processing {media.id} for visual search: {e}")
                    continue
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:limit]
            
        except ImportError:
            logger.warning("imagehash not available for visual search")
            return []
        except Exception as e:
            logger.error(f"Visual search error: {e}")
            return []
    
    def create_collection(
        self,
        name: str,
        description: Optional[str] = None,
        media_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a media collection"""
        import uuid
        collection = {
            "id": str(uuid.uuid4()),
            "name": name,
            "description": description,
            "media_ids": media_ids or [],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Store in metadata or separate table
        # For now, return collection dict
        return collection
    
    def add_favorite(self, media_id: str) -> MediaItem:
        """Mark media as favorite"""
        media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
        if not media:
            raise ValueError(f"Media not found: {media_id}")
        
        if not media.meta_data:
            media.meta_data = {}
        
        media.meta_data["favorite"] = True
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def remove_favorite(self, media_id: str) -> MediaItem:
        """Remove favorite status"""
        media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
        if not media:
            raise ValueError(f"Media not found: {media_id}")
        
        if media.meta_data:
            media.meta_data["favorite"] = False
        
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def rate_media(self, media_id: str, rating: int) -> MediaItem:
        """Rate media (1-5 stars)"""
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be between 1 and 5")
        
        media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
        if not media:
            raise ValueError(f"Media not found: {media_id}")
        
        if not media.meta_data:
            media.meta_data = {}
        
        media.meta_data["rating"] = rating
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def add_comment(self, media_id: str, comment: str) -> MediaItem:
        """Add comment to media"""
        media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
        if not media:
            raise ValueError(f"Media not found: {media_id}")
        
        if not media.meta_data:
            media.meta_data = {}
        
        comments = media.meta_data.get("comments", [])
        comments.append({
            "text": comment,
            "created_at": datetime.utcnow().isoformat()
        })
        media.meta_data["comments"] = comments
        
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections"""
        # TODO: Implement proper collection storage (database table or file)
        # For now, return empty list
        return []
    
    def add_to_collection(self, collection_id: str, media_id: str) -> Dict[str, Any]:
        """Add media to collection"""
        # TODO: Implement proper collection management
        return {
            "collection_id": collection_id,
            "media_id": media_id,
            "added": True
        }
    
    def get_media(self, media_id: str) -> Optional[MediaItem]:
        """Get media item by ID"""
        return self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
    
    def edit_metadata(self, media_id: str, metadata_updates: Dict[str, Any]) -> MediaItem:
        """Edit media metadata"""
        media = self.db.query(MediaItem).filter(MediaItem.id == media_id).first()
        if not media:
            raise ValueError(f"Media not found: {media_id}")
        
        if not media.meta_data:
            media.meta_data = {}
        
        media.meta_data.update(metadata_updates)
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def create_media_item(
        self,
        file_path: Path,
        media_type: str,
        source: str,
        character_id: Optional[str] = None,
        generation_job_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MediaItem:
        """Create a media item from file
        
        If file_path is not in media_root, it will be moved/copied there.
        """
        from PIL import Image
        import uuid
        
        # Get file info before moving
        file_name = file_path.name
        file_size = file_path.stat().st_size
        
        # Determine MIME type
        mime_type = self._get_mime_type(file_path)
        
        # Get dimensions before moving
        width = None
        height = None
        duration = None
        
        if media_type == "image":
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
            except Exception as e:
                logger.error(f"Failed to get image dimensions: {e}")
        elif media_type == "video":
            # Get video dimensions and duration using opencv or ffmpeg
            try:
                import cv2
                cap = cv2.VideoCapture(str(file_path))
                if cap.isOpened():
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    duration = frame_count / fps if fps > 0 else 0
                    cap.release()
                else:
                    # Fallback values
                    width = 1920
                    height = 1080
                    duration = 0
            except ImportError:
                # Try ffprobe if available
                try:
                    import subprocess
                    import json
                    result = subprocess.run(
                        [
                            "ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams",
                            str(file_path)
                        ],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        info = json.loads(result.stdout)
                        video_stream = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
                        if video_stream:
                            width = int(video_stream.get("width", 1920))
                            height = int(video_stream.get("height", 1080))
                            duration = float(info.get("format", {}).get("duration", 0))
                        else:
                            width = 1920
                            height = 1080
                            duration = 0
                    else:
                        width = 1920
                        height = 1080
                        duration = 0
                except Exception:
                    # Final fallback
                    width = 1920
                    height = 1080
                    duration = 0
            except Exception as e:
                logger.warning(f"Could not get video metadata: {e}")
                width = 1920
                height = 1080
                duration = 0
        
        # Move file to media library if not already there
        final_file_path = file_path
        if not str(file_path).startswith(str(self.media_root)):
            # Generate unique filename
            file_ext = file_path.suffix
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            final_file_path = self.media_root / media_type / unique_filename
            final_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move or copy file
            if file_path.exists():
                shutil.move(str(file_path), str(final_file_path))
            else:
                logger.warning(f"Source file does not exist: {file_path}")
        
        # Generate thumbnail
        thumbnail_path = None
        if media_type == "image":
            thumbnail_path = self._generate_thumbnail(final_file_path, media_type)
        
        # Create media item
        media = MediaItem(
            type=media_type,
            source=source,
            file_path=str(final_file_path),
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            width=width,
            height=height,
            duration=duration,
            thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
            character_id=character_id,
            generation_job_id=generation_job_id,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.db.add(media)
        self.db.commit()
        self.db.refresh(media)
        
        return media
    
    def list_media(
        self,
        media_type: Optional[str] = None,
        source: Optional[str] = None,
        character_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 50,
        sort: str = "created_at",
        order: str = "desc"
    ) -> Dict[str, Any]:
        """List media items with filtering and pagination"""
        query = self.db.query(MediaItem).filter(MediaItem.deleted_at.is_(None))
        
        # Apply filters
        if media_type:
            query = query.filter(MediaItem.type == media_type)
        if source:
            query = query.filter(MediaItem.source == source)
        if character_id:
            query = query.filter(MediaItem.character_id == character_id)
        if tags:
            # Filter by tags (JSON array contains)
            for tag in tags:
                query = query.filter(MediaItem.tags.contains([tag]))
        
        # Apply sorting
        sort_column = getattr(MediaItem, sort, MediaItem.created_at)
        if order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        items = query.offset(offset).limit(limit).all()
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    
    def get_media(self, media_id: str) -> Optional[MediaItem]:
        """Get a specific media item"""
        return self.db.query(MediaItem).filter(
            and_(MediaItem.id == media_id, MediaItem.deleted_at.is_(None))
        ).first()
    
    def delete_media(self, media_id: str) -> bool:
        """Soft delete a media item"""
        media = self.get_media(media_id)
        if media:
            media.deleted_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
    
    def update_tags(self, media_id: str, tags: List[str]) -> Optional[MediaItem]:
        """Update media tags"""
        media = self.get_media(media_id)
        if media:
            media.tags = tags
            media.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(media)
        return media
    
    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type from file extension"""
        ext = file_path.suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".webm": "video/webm"
        }
        return mime_types.get(ext, "application/octet-stream")
    
    def _generate_thumbnail(self, file_path: Path, media_type: str) -> Optional[Path]:
        """Generate thumbnail for media"""
        try:
            from PIL import Image
            
            if media_type == "image":
                with Image.open(file_path) as img:
                    # Resize to thumbnail size
                    img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                    
                    # Save thumbnail
                    thumbnail_path = self.media_root / "thumbnails" / f"{file_path.stem}_thumb.jpg"
                    img.convert("RGB").save(thumbnail_path, "JPEG", quality=85)
                    return thumbnail_path
            
            # Generate video thumbnail using opencv or ffmpeg
            try:
                import cv2
                cap = cv2.VideoCapture(str(file_path))
                if cap.isOpened():
                    # Get frame at 10% of video duration
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    frame_number = int(total_frames * 0.1)
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                    ret, frame = cap.read()
                    if ret:
                        # Convert BGR to RGB
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        thumbnail_img = Image.fromarray(frame_rgb)
                        thumbnail_img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                        
                        thumbnail_path = self.media_root / "thumbnails" / f"{file_path.stem}_thumb.jpg"
                        thumbnail_img.convert("RGB").save(thumbnail_path, "JPEG", quality=85)
                        cap.release()
                        return thumbnail_path
                    cap.release()
            except ImportError:
                # Try ffmpeg if available
                try:
                    import subprocess
                    thumbnail_path = self.media_root / "thumbnails" / f"{file_path.stem}_thumb.jpg"
                    result = subprocess.run(
                        [
                            "ffmpeg", "-i", str(file_path),
                            "-ss", "00:00:01", "-vframes", "1",
                            "-vf", "scale=256:256:force_original_aspect_ratio=decrease",
                            str(thumbnail_path)
                        ],
                        capture_output=True,
                        timeout=10
                    )
                    if result.returncode == 0 and thumbnail_path.exists():
                        return thumbnail_path
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Could not generate video thumbnail: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None
