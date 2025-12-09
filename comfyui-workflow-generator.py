"""
ComfyUI Workflow JSON Generator
Ultra realistic OnlyFans model workflow'u otomatik olusturur
"""

# PHASE 1: UTF-8 encoding enforcement
import os
import sys
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import json
import re
from pathlib import Path
from typing import Dict, Set, Optional, List, Any

# Try to import requests, but don't fail if unavailable
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

def fetch_object_info(server_address: str = "127.0.0.1:8188") -> Optional[Dict[str, Any]]:
    """
    PHASE 1: Fetch object_info from ComfyUI server.
    Returns full object_info dict or None if unavailable.
    """
    # Re-check requests availability (in case module was imported dynamically)
    try:
        import requests
        has_requests = True
    except ImportError:
        has_requests = False
    
    if not has_requests:
        print(f"[!] WARNING: requests library not available, cannot fetch object_info", flush=True)
        return None
    
    # Try both endpoints
    endpoints = [
        f"http://{server_address}/object_info",
        f"http://{server_address}/api/object_info"
    ]
    
    last_error = None
    for endpoint in endpoints:
        try:
            print(f"[WF] Trying endpoint: {endpoint}", flush=True)
            response = requests.get(endpoint, timeout=10)
            print(f"[WF] Response status: {response.status_code}", flush=True)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    print(f"[WF] Successfully fetched object_info with {len(data)} node types", flush=True)
                    return data
                else:
                    print(f"[!] WARNING: object_info response is not a dict: {type(data)}", flush=True)
            else:
                print(f"[!] WARNING: Endpoint returned status {response.status_code}", flush=True)
                last_error = f"HTTP {response.status_code}"
        except requests.exceptions.ConnectionError as e:
            print(f"[!] Connection error to {endpoint}: {e}", flush=True)
            last_error = str(e)
            continue
        except requests.exceptions.Timeout as e:
            print(f"[!] Timeout connecting to {endpoint}: {e}", flush=True)
            last_error = str(e)
            continue
        except requests.exceptions.RequestException as e:
            print(f"[!] Request error to {endpoint}: {e}", flush=True)
            last_error = str(e)
            continue
        except json.JSONDecodeError as e:
            print(f"[!] JSON decode error from {endpoint}: {e}", flush=True)
            last_error = str(e)
            continue
        except Exception as e:
            print(f"[!] Unexpected error fetching {endpoint}: {e}", flush=True)
            last_error = str(e)
            continue
    
    print(f"[!] WARNING: Could not fetch object_info from any endpoint. Last error: {last_error}", flush=True)
    return None

def get_comfyui_capabilities(server_address: str = "127.0.0.1:8188") -> Set[str]:
    """
    PHASE 2: Query ComfyUI server for available nodes.
    Returns set of available node class names.
    """
    obj_info = fetch_object_info(server_address)
    if obj_info:
        return set(obj_info.keys())
    return set()

def get_allowed_values(obj_info: Optional[Dict[str, Any]], class_type: str, input_name: str) -> Optional[List[str]]:
    """
    PHASE 1: Extract allowed enum values from object_info.
    
    Args:
        obj_info: Full object_info dict from server
        class_type: Node class name (e.g., "CheckpointLoaderSimple", "KSampler")
        input_name: Input parameter name (e.g., "ckpt_name", "sampler_name")
    
    Returns:
        List of allowed string values, or None if not discoverable
    """
    if not obj_info:
        print(f"[WF] get_allowed_values: obj_info is None", flush=True)
        return None
    
    cls = obj_info.get(class_type)
    if not isinstance(cls, dict):
        print(f"[WF] get_allowed_values: {class_type} not found or not a dict", flush=True)
        return None
    
    # ComfyUI object_info structure: { "NodeClass": { "input": {...}, "output": [...] } }
    inputs = cls.get("input") or cls.get("inputs") or {}
    if not isinstance(inputs, dict):
        print(f"[WF] get_allowed_values: inputs not found or not a dict for {class_type}", flush=True)
        # Debug: Show what keys are available
        print(f"[WF] Available keys in {class_type}: {list(cls.keys())}", flush=True)
        return None
    
    # Debug: Show available input keys
    if input_name not in inputs:
        print(f"[WF] get_allowed_values: {input_name} not found in inputs for {class_type}", flush=True)
        print(f"[WF] Available input keys: {list(inputs.keys())[:10]}", flush=True)
    
    cfg = inputs.get(input_name)
    if cfg is None:
        # For CheckpointLoaderSimple, ComfyUI might not expose enum in object_info
        # We'll need to extract from error response instead
        print(f"[WF] get_allowed_values: {input_name} not found in inputs for {class_type} - will need error-based extraction", flush=True)
        return None
    
    print(f"[WF] get_allowed_values: cfg type={type(cfg)}, cfg={cfg}", flush=True)
    
    # Pattern 1: cfg is a list where [0] is the allowed list
    # ComfyUI format: [ [list of values], {metadata} ]
    if isinstance(cfg, list) and len(cfg) > 0:
        if isinstance(cfg[0], list):
            result = cfg[0]
            print(f"[WF] get_allowed_values: Found list in list, returning {len(result)} values", flush=True)
            return result
        # Sometimes it's a tuple or other iterable
        if len(cfg) > 0 and isinstance(cfg[0], (list, tuple)):
            result = list(cfg[0])
            print(f"[WF] get_allowed_values: Found tuple/list in list, returning {len(result)} values", flush=True)
            return result
    
    # Pattern 2: cfg is a dict with "values" or "enum" key
    if isinstance(cfg, dict):
        vals = cfg.get("values") or cfg.get("enum")
        if isinstance(vals, list):
            print(f"[WF] get_allowed_values: Found values in dict, returning {len(vals)} values", flush=True)
            return vals
    
    print(f"[WF] get_allowed_values: Could not extract allowed values from cfg", flush=True)
    return None

def normalize_key(s: str) -> str:
    """
    PHASE 1: Normalize string for fuzzy matching.
    Removes spaces, dashes, dots, underscores, and converts to lowercase.
    """
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r"[\s\-\._]+", "", s)
    return s

def fuzzy_pick(preferred: str, allowed: List[str]) -> Optional[str]:
    """
    PHASE 1: Fuzzy match preferred value against allowed list.
    
    Returns:
        Matched value from allowed list, or None if no match
    """
    if not preferred or not allowed:
        return None
    
    p = normalize_key(preferred)
    
    # Exact normalized match
    for a in allowed:
        if normalize_key(a) == p:
            return a
    
    # PHASE 8: Improved matching - extract key words from preferred
    # "Realistic Vision V6.0" -> look for "realistic", "vision", "v6", "60"
    preferred_words = set()
    # Extract version numbers (V6.0, V60, 6.0, etc.)
    version_match = re.search(r'v?\s*(\d+)[\.\s]*(\d*)', preferred.lower())
    if version_match:
        major = version_match.group(1)
        minor = version_match.group(2) if version_match.group(2) else ""
        preferred_words.add(f"v{major}{minor}")
        preferred_words.add(f"v{major}")
        preferred_words.add(f"{major}{minor}")
        preferred_words.add(major)
    
    # Extract key descriptive words
    words = re.findall(r'\b\w+\b', preferred.lower())
    for word in words:
        if len(word) > 3:  # Skip short words like "a", "v6"
            preferred_words.add(word)
    
    # Score each allowed checkpoint based on word matches
    best_match = None
    best_score = 0
    
    for a in allowed:
        a_norm = normalize_key(a)
        a_lower = a.lower()
        
        # Substring match (original heuristic)
        if p in a_norm or a_norm in p:
            return a
        
        # Word-based scoring
        score = 0
        for word in preferred_words:
            if word in a_lower or word in a_norm:
                score += 1
        
        # Bonus for version number matches
        if version_match:
            major = version_match.group(1)
            if major in a_lower:
                score += 2
        
        if score > best_score:
            best_score = score
            best_match = a
    
    # Return best match if score is reasonable (at least 2 matches)
    if best_match and best_score >= 2:
        return best_match
    
    return None

def resolve_comfyui_root() -> Path:
    """
    PHASE 2: Resolve absolute path to ComfyUI root directory.
    
    Returns:
        Path to ComfyUI directory
    """
    script_dir = Path(__file__).parent
    comfyui_path = script_dir / "ComfyUI"
    if not comfyui_path.exists():
        comfyui_path = script_dir.parent / "ComfyUI"
    return comfyui_path.resolve()

def resolve_comfyui_checkpoint_dir(comfyui_path: Optional[Path] = None) -> Path:
    """
    PHASE 2: Resolve absolute path to ComfyUI checkpoint directory.
    
    Args:
        comfyui_path: Path to ComfyUI root (auto-resolved if None)
    
    Returns:
        Path to ComfyUI/models/checkpoints directory
    """
    if comfyui_path is None:
        comfyui_path = resolve_comfyui_root()
    checkpoint_dir = Path(comfyui_path) / "models" / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    return checkpoint_dir.resolve()

def local_checkpoint_candidates(comfyui_path: Optional[Path] = None) -> List[Path]:
    """
    PHASE 2: Scan for checkpoint files in alternative locations.
    
    Checks:
    - <repo>/models/checkpoints/ (if exists)
    - <repo>/checkpoints/ (if exists)
    - Any path referenced in config.json
    
    Returns:
        List of Path objects to candidate checkpoint files
    """
    if comfyui_path is None:
        comfyui_path = resolve_comfyui_root()
    
    script_dir = Path(__file__).parent
    candidates = []
    
    # Check repo-level models folder (if exists)
    repo_models = script_dir / "models" / "checkpoints"
    if repo_models.exists():
        candidates.extend(repo_models.glob("*.safetensors"))
        candidates.extend(repo_models.glob("*.ckpt"))
    
    # Check repo-level checkpoints folder (if exists)
    repo_checkpoints = script_dir / "checkpoints"
    if repo_checkpoints.exists():
        candidates.extend(repo_checkpoints.glob("*.safetensors"))
        candidates.extend(repo_checkpoints.glob("*.ckpt"))
    
    return candidates

def ensure_checkpoint_present_in_comfyui(config_ckpt: str, comfyui_path: Optional[Path] = None) -> bool:
    """
    PHASE 2: Auto-sync checkpoint into ComfyUI if found elsewhere.
    
    Logic:
    - If config_ckpt exists in ComfyUI folder -> OK
    - Else search candidate dirs:
        <repo>/models/checkpoints/
        <repo>/checkpoints/
    - If found elsewhere: copy into ComfyUI folder
    - If not found anywhere: log warning but continue
    
    Args:
        config_ckpt: Configured checkpoint filename or label
        comfyui_path: Path to ComfyUI directory (auto-resolved if None)
    
    Returns:
        True if checkpoint is now present in ComfyUI, False otherwise
    """
    import shutil
    
    if comfyui_path is None:
        comfyui_path = resolve_comfyui_root()
    
    comfyui_checkpoint_dir = resolve_comfyui_checkpoint_dir(comfyui_path)
    comfyui_checkpoint_path = comfyui_checkpoint_dir / config_ckpt
    
    # If already in ComfyUI, no sync needed
    if comfyui_checkpoint_path.exists():
        return True
    
    # If config_ckpt doesn't look like a filename, try to find it by fuzzy matching
    # First, check if it's a label that needs to be resolved to a filename
    candidates = local_checkpoint_candidates(comfyui_path)
    
    # Try to find matching checkpoint in alternative locations
    found_candidate = None
    for candidate in candidates:
        # Exact filename match
        if candidate.name == config_ckpt:
            found_candidate = candidate
            break
        # Fuzzy match on name (normalized)
        if normalize_key(candidate.name) == normalize_key(config_ckpt):
            found_candidate = candidate
            break
    
    # If found, copy to ComfyUI
    if found_candidate:
        try:
            shutil.copy2(found_candidate, comfyui_checkpoint_path)
            print(f"[WF] Auto-synced checkpoint into ComfyUI: {found_candidate} -> {comfyui_checkpoint_path}")
            return True
        except Exception as e:
            print(f"[!] WARNING: Failed to sync checkpoint {config_ckpt}: {e}")
            return False
    
    # Not found anywhere - log warning but don't fail
    print(f"[!] WARNING: Checkpoint '{config_ckpt}' not found in ComfyUI or alternative locations")
    print(f"    ComfyUI checkpoint dir: {comfyui_checkpoint_dir}")
    return False

def sync_checkpoint_to_comfyui(checkpoint_filename: str, comfyui_path: Optional[Path] = None) -> bool:
    """
    PHASE 2: Auto-sync checkpoint from alternative location to ComfyUI folder.
    
    If checkpoint exists outside ComfyUI but not inside, copy it.
    
    Args:
        checkpoint_filename: Name of checkpoint file to sync
        comfyui_path: Path to ComfyUI directory (auto-resolved if None)
    
    Returns:
        True if sync was performed or file already exists, False if not found
    """
    import shutil
    
    if comfyui_path is None:
        comfyui_path = resolve_comfyui_root()
    
    comfyui_path = Path(comfyui_path)
    comfyui_checkpoint_dir = comfyui_path / "models" / "checkpoints"
    comfyui_checkpoint_path = comfyui_checkpoint_dir / checkpoint_filename
    
    # If already in ComfyUI, no sync needed
    if comfyui_checkpoint_path.exists():
        return True
    
    # Ensure ComfyUI checkpoint directory exists
    comfyui_checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # Search for checkpoint in alternative locations
    candidates = local_checkpoint_candidates(comfyui_path)
    
    for candidate in candidates:
        if candidate.name == checkpoint_filename:
            # Found it! Copy to ComfyUI
            try:
                shutil.copy2(candidate, comfyui_checkpoint_path)
                print(f"[WF] Synced checkpoint into ComfyUI: {candidate} -> {comfyui_checkpoint_path}")
                return True
            except Exception as e:
                print(f"[!] WARNING: Failed to sync checkpoint {checkpoint_filename}: {e}")
                return False
    
    return False

def list_local_checkpoints(comfyui_path: Optional[Path] = None) -> List[str]:
    """
    PHASE 1: List local checkpoint files from ComfyUI/models/checkpoints.
    
    Returns:
        List of checkpoint filenames (basenames only)
    """
    if comfyui_path is None:
        comfyui_path = resolve_comfyui_root()
    
    comfyui_path = Path(comfyui_path)
    base = comfyui_path / "models" / "checkpoints"
    
    if not base.exists():
        return []
    
    files = list(base.glob("*.safetensors")) + list(base.glob("*.ckpt"))
    return [f.name for f in files]

def resolve_ckpt_name(config_ckpt: str, allowed_ckpts: Optional[List[str]], comfyui_path: Optional[Path] = None) -> str:
    """
    PHASE 3: Server-truth checkpoint resolver with hard enforcement.
    
    Rules:
    1) If allowed_ckpts is non-empty:
         - DO NOT output config_ckpt unless it is exactly in allowed_ckpts
         - Try normalized fuzzy match
         - If a single best match exists -> use it
         - Else:
             if any allowed contains "realisticVision" -> choose that
             else choose allowed_ckpts[0]
         - Log: "[WF] ckpt_name resolved (server-truth): <config> -> <final>"
    2) If allowed_ckpts empty:
         - Fallback to listing files in comfy_dir
         - Choose config_ckpt if present else first file
    
    CRITICAL: The final ckpt_name to write into workflow MUST be one of allowed_ckpts
    whenever allowed_ckpts exists.
    
    Args:
        config_ckpt: Configured checkpoint name (may be friendly label or filename)
        allowed_ckpts: List of allowed checkpoints from server (None if unavailable)
        comfyui_path: Path to ComfyUI directory (for local fallback)
    
    Returns:
        Resolved checkpoint filename (guaranteed to be in allowed_ckpts if list exists)
    """
    if comfyui_path is None:
        comfyui_path = resolve_comfyui_root()
    
    configured_str = str(config_ckpt)
    
    # SERVER-TRUTH LAYER: If server list exists, MUST use a value from it
    if allowed_ckpts and len(allowed_ckpts) > 0:
        # First, try to ensure checkpoint is present in ComfyUI (auto-sync if needed)
        # This helps if the file exists elsewhere but server hasn't scanned it yet
        if configured_str.lower().endswith((".safetensors", ".ckpt")):
            ensure_checkpoint_present_in_comfyui(configured_str, comfyui_path)
        
        # Try exact match first
        if configured_str in allowed_ckpts:
            print(f"[WF] ckpt_name resolved (server-truth): '{configured_str}' -> '{configured_str}'")
            return configured_str
        
        # Try fuzzy match (normalized)
        picked = fuzzy_pick(configured_str, allowed_ckpts)
        if picked:
            print(f"[WF] ckpt_name resolved (server-truth): '{configured_str}' -> '{picked}'")
            return picked
        
        # More aggressive matching - try partial matches
        configured_lower = configured_str.lower()
        for word in configured_lower.split():
            if len(word) > 3:  # Skip short words
                for a in allowed_ckpts:
                    if word in a.lower():
                        print(f"[WF] ckpt_name resolved (server-truth): '{configured_str}' -> '{a}'")
                        return a
        
        # Prefer realisticVision if present (even if not exact match)
        rv = [a for a in allowed_ckpts if "realistic" in a.lower() and "vision" in a.lower()]
        if rv:
            print(f"[WF] ckpt_name resolved (server-truth): '{configured_str}' -> '{rv[0]}'")
            return rv[0]
        
        # Prefer any checkpoint with "realistic" in name
        realistic = [a for a in allowed_ckpts if "realistic" in a.lower()]
        if realistic:
            print(f"[WF] ckpt_name resolved (server-truth): '{configured_str}' -> '{realistic[0]}'")
            return realistic[0]
        
        # Hard fallback: first allowed (server truth is authoritative)
        final = allowed_ckpts[0]
        print(f"[WF] ckpt_name resolved (server-truth): '{configured_str}' -> '{final}' (fallback to first available)")
        return final
    
    # LOCAL-LAYER FALLBACK: Scan local folder (no server list available)
    comfyui_checkpoint_dir = resolve_comfyui_checkpoint_dir(comfyui_path)
    local = list_local_checkpoints(comfyui_path)
    
    # If configured looks like a filename, try to sync it first
    if configured_str.lower().endswith((".safetensors", ".ckpt")):
        # Try to sync from alternative locations
        ensure_checkpoint_present_in_comfyui(configured_str, comfyui_path)
        # Re-scan after potential sync
        local = list_local_checkpoints(comfyui_path)
    
    if local:
        picked = fuzzy_pick(configured_str, local)
        if picked:
            print(f"[WF] ckpt_name resolved (local-fallback): '{configured_str}' -> '{picked}'")
            return picked
        # If configured is a filename and not in local, return as-is (will fail but clear error)
        if configured_str.lower().endswith((".safetensors", ".ckpt")):
            print(f"[WF] ckpt_name resolved (local-fallback): '{configured_str}' -> '{configured_str}' (as-is)")
            return configured_str
    
    # Last resort: return configured (will likely fail validation, but better than nothing)
    print(f"[WF] ckpt_name resolved (local-fallback): '{configured_str}' -> '{configured_str}' (last resort)")
    return configured_str

# Backward compatibility alias
def resolve_ckpt(configured: str, allowed_ckpts: Optional[List[str]], comfyui_path: Optional[Path] = None) -> str:
    """Backward compatibility alias for resolve_ckpt_name"""
    return resolve_ckpt_name(configured, allowed_ckpts, comfyui_path)

def check_instantid_available(server_address: str = "127.0.0.1:8188") -> bool:
    """PHASE 2: Check if InstantID nodes are available on the server."""
    if not HAS_REQUESTS:
        return False
    
    required_nodes = ["InstantIDModelLoader", "InsightFaceLoader", "InstantIDApply"]
    capabilities = get_comfyui_capabilities(server_address)
    return all(node in capabilities for node in required_nodes)

def check_model_availability(comfyui_path=None):
    """PHASE 4: Check which models are available"""
    if comfyui_path is None:
        comfyui_path = resolve_comfyui_root()
    
    comfyui_path = Path(comfyui_path)
    
    models = {
        "checkpoint": False,
        "instantid": False,
        "realesrgan": False,
        "gfpgan": False
    }
    
    # Check checkpoint
    checkpoint_dir = comfyui_path / "models" / "checkpoints"
    if checkpoint_dir.exists():
        checkpoint_files = list(checkpoint_dir.glob("*.safetensors")) + list(checkpoint_dir.glob("*.ckpt"))
        if checkpoint_files:
            models["checkpoint"] = True
    
    # Check InstantID
    instantid_model = comfyui_path / "models" / "instantid" / "ip-adapter.bin"
    if instantid_model.exists():
        models["instantid"] = True
    
    # Check RealESRGAN
    realesrgan_model = comfyui_path / "models" / "upscale_models" / "RealESRGAN_x4plus.pth"
    if realesrgan_model.exists():
        models["realesrgan"] = True
    
    # Check GFPGAN
    gfpgan_model = comfyui_path / "models" / "face_restore" / "GFPGANv1.4.pth"
    if gfpgan_model.exists():
        models["gfpgan"] = True
    
    return models

def create_workflow_json(
    checkpoint_name="Realistic Vision V6.0",
    reference_image_path="",
    positive_prompt="",
    negative_prompt="",
    instantid_strength=0.8,
    steps=40,
    cfg_scale=8.0,
    width=768,
    height=768,
    seed=-1,
    comfyui_path=None,
    enable_instantid=None,  # None = auto-detect, True/False = force
    server_address="127.0.0.1:8188"  # PHASE 2: Server address for capability check
):
    """ComfyUI workflow JSON olustur
    
    PHASE 3: Capability-aware workflow generation
    - Queries live server for available nodes
    - If InstantID nodes not present: generates base workflow automatically
    - Never emits workflow referencing nodes not in capability list
    """
    
    # PHASE 3: Ensure checkpoint_name is a valid filename (not a label)
    # If it's a label like "Realistic Vision V6.0", it should have been resolved already
    # But if it hasn't, we'll resolve it here as a safety measure
    final_checkpoint_name = str(checkpoint_name)
    print(f"[WF] Creating workflow with checkpoint: {final_checkpoint_name}", flush=True)
    
    workflow = {
        "1": {
            "inputs": {
                "ckpt_name": final_checkpoint_name
            },
            "class_type": "CheckpointLoaderSimple",
            "_meta": {"title": "Load Checkpoint"}
        },
        "2": {
            "inputs": {
                "text": positive_prompt,
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "3": {
            "inputs": {
                "text": negative_prompt,
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Negative)"}
        },
        "4": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg_scale,
                "sampler_name": "dpmpp_2m_karras",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"}
        },
        "5": {
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage",
            "_meta": {"title": "Empty Latent Image"}
        },
        "6": {
            "inputs": {
                "samples": ["4", 0],
                "vae": ["1", 2]
            },
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"}
        },
        "7": {
            "inputs": {
                "filename_prefix": "ComfyUI",
                "images": ["6", 0]
            },
            "class_type": "SaveImage",
            "_meta": {"title": "Save Image"}
        }
    }
    
    # PHASE 3: Check server capabilities - this is the source of truth
    use_instantid = False
    if enable_instantid is None:
        # Auto-detect: check server for InstantID nodes AND model file AND reference image
        try:
            instantid_nodes_available = check_instantid_available(server_address)
        except Exception:
            instantid_nodes_available = False
        
        models = check_model_availability(comfyui_path)
        has_model_file = models.get("instantid", False)
        has_reference_image = reference_image_path and Path(reference_image_path).exists()
        
        # All three must be true: nodes registered, model file exists, reference image exists
        if instantid_nodes_available and has_model_file and has_reference_image:
            use_instantid = True
        else:
            if not instantid_nodes_available:
                print("[!] InstantID nodes not registered in server, using base workflow")
            elif not has_model_file:
                print("[!] InstantID model file not found, using base workflow")
                print("    Download: ComfyUI/models/instantid/ip-adapter.bin")
            elif not has_reference_image:
                print("[!] Reference image not found, using base workflow")
    else:
        use_instantid = enable_instantid
        if use_instantid:
            # Even if forced, verify nodes exist
            try:
                if not check_instantid_available(server_address):
                    print("[!] WARNING: InstantID forced but nodes not available on server!")
                    print("    Workflow may fail. Falling back to base workflow.")
                    use_instantid = False
            except Exception:
                print("[!] WARNING: Cannot verify InstantID nodes, falling back to base workflow")
                use_instantid = False
    
    # InstantID varsa ekle
    if use_instantid and reference_image_path and Path(reference_image_path).exists():
        workflow["8"] = {
            "inputs": {
                "model": ["1", 0],
                "instantid_file": "ip-adapter.bin"
            },
            "class_type": "InstantIDModelLoader",
            "_meta": {"title": "InstantID Model Loader"}
        }
        workflow["9"] = {
            "inputs": {
                "provider": "CPU"
            },
            "class_type": "InsightFaceLoader",
            "_meta": {"title": "InsightFace Loader"}
        }
        workflow["10"] = {
            "inputs": {
                "image": reference_image_path
            },
            "class_type": "LoadImage",
            "_meta": {"title": "Load Reference Image"}
        }
        workflow["11"] = {
            "inputs": {
                "weight": instantid_strength,
                "noise": 0.0,
                "weight_faceidv2": 0.0,
                "weight_type": "original",
                "combine_embeds": "concat",
                "start_at": 0.0,
                "end_at": 1.0,
                "embeds_scaling": "V only",
                "model": ["8", 0],
                "insightface": ["9", 0],
                "image": ["10", 0],
                "positive": ["2", 0],
                "negative": ["3", 0]
            },
            "class_type": "InstantIDApply",
            "_meta": {"title": "InstantID Apply"}
        }
        # KSampler'i guncelle
        workflow["4"]["inputs"]["positive"] = ["11", 0]
        workflow["4"]["inputs"]["negative"] = ["11", 1]
    
    return workflow

def patch_workflow_enums(workflow: Dict[str, Any], server_address: str = "127.0.0.1:8188") -> Dict[str, Any]:
    """
    PHASE 1: Patch workflow enum values using server object_info.
    
    Validates and patches:
    - CheckpointLoaderSimple.ckpt_name
    - KSampler.sampler_name
    - KSampler.scheduler
    
    Returns:
        Patched workflow dict
    """
    print(f"[WF] Fetching object_info from server: {server_address}", flush=True)
    obj_info = fetch_object_info(server_address)
    
    if obj_info is None:
        print(f"[!] WARNING: Could not fetch object_info from server {server_address}", flush=True)
        print(f"    This may mean the server is not accessible or object_info endpoint is unavailable", flush=True)
    else:
        print(f"[WF] Successfully fetched object_info from server", flush=True)
        # Debug: Check if CheckpointLoaderSimple exists
        if "CheckpointLoaderSimple" in obj_info:
            print(f"[WF] CheckpointLoaderSimple node found in object_info", flush=True)
        else:
            print(f"[!] WARNING: CheckpointLoaderSimple not found in object_info", flush=True)
            print(f"    Available nodes: {list(obj_info.keys())[:10]}...", flush=True)
    
    # Get allowed lists
    allowed_ckpts = get_allowed_values(obj_info, "CheckpointLoaderSimple", "ckpt_name")
    allowed_samplers = get_allowed_values(obj_info, "KSampler", "sampler_name")
    allowed_schedulers = get_allowed_values(obj_info, "KSampler", "scheduler")
    
    if allowed_ckpts:
        print(f"[WF] Server has {len(allowed_ckpts)} allowed checkpoint(s): {', '.join(allowed_ckpts)}", flush=True)
    else:
        print(f"[!] WARNING: Could not get allowed checkpoints from server (obj_info={obj_info is not None})", flush=True)
    
    # Fallback safe defaults if object_info missing
    sampler_fallback_order = ["euler", "euler_ancestral", "heun", "dpmpp_2m", "dpmpp_sde"]
    scheduler_fallback_order = ["normal", "karras", "simple", "exponential"]
    
    # Track what was patched for logging
    patches = {
        "ckpt_name": None,
        "sampler_name": None,
        "scheduler": None
    }
    
    # Iterate nodes in workflow
    # Workflow structure: { "1": { "class_type": "...", "inputs": {...} }, ... }
    nodes = workflow if isinstance(workflow, dict) else {}
    
    for node_id, node in nodes.items():
        if not isinstance(node, dict):
            continue
        
        ctype = node.get("class_type")
        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            continue
        
        # 1) Checkpoint name patch with auto-sync and server-truth enforcement
        if ctype == "CheckpointLoaderSimple" and "ckpt_name" in inputs:
            configured = inputs.get("ckpt_name")
            configured_str = str(configured)
            
            # PHASE 2: Resolve ComfyUI path
            comfyui_path = resolve_comfyui_root()
            
            # PHASE 3: Use server-truth resolver (enforces allowed_ckpts when available)
            print(f"[WF] Resolving checkpoint: '{configured_str}' with allowed_ckpts={allowed_ckpts is not None and len(allowed_ckpts) > 0 if allowed_ckpts else False}", flush=True)
            resolved = resolve_ckpt_name(configured_str, allowed_ckpts, comfyui_path)
            print(f"[WF] Resolved checkpoint: '{configured_str}' -> '{resolved}'", flush=True)
            
            # PHASE 3: CRITICAL - Never write a ckpt_name that is not in allowed_ckpts when list exists
            if allowed_ckpts and len(allowed_ckpts) > 0:
                print(f"[WF] Enforcing server-truth: resolved must be in allowed list", flush=True)
                if resolved not in allowed_ckpts:
                    print(f"[!] ERROR: Resolved checkpoint '{resolved}' not in allowed list!", flush=True)
                    print(f"    Allowed: {allowed_ckpts}", flush=True)
                if resolved not in allowed_ckpts:
                    # This should never happen if resolve_ckpt_name works correctly, but double-check
                    # Force pick from allowed list
                    picked = fuzzy_pick(resolved, allowed_ckpts)
                    if picked:
                        resolved = picked
                    else:
                        # Try more aggressive matching
                        configured_lower = configured_str.lower()
                        for word in configured_lower.split():
                            if len(word) > 3:
                                for a in allowed_ckpts:
                                    if word in a.lower():
                                        resolved = a
                                        break
                                if resolved in allowed_ckpts:
                                    break
                        
                        # If still not found, prefer realisticVision if present
                        if resolved not in allowed_ckpts:
                            rv = [a for a in allowed_ckpts if "realistic" in a.lower() and "vision" in a.lower()]
                            if rv:
                                resolved = rv[0]
                            else:
                                # Prefer any realistic model
                                realistic = [a for a in allowed_ckpts if "realistic" in a.lower()]
                                if realistic:
                                    resolved = realistic[0]
                                else:
                                    # Last resort: first available (server truth is authoritative)
                                    resolved = allowed_ckpts[0]
                    print(f"[WF] WARNING: Forced checkpoint resolution: '{configured_str}' -> '{resolved}'")
            
            if resolved != configured_str:
                inputs["ckpt_name"] = resolved
                patches["ckpt_name"] = (configured_str, resolved)
        
        # 2) Sampler patch with improved splitting logic
        if ctype == "KSampler" and "sampler_name" in inputs:
            configured = inputs.get("sampler_name")
            configured_str = str(configured)
            configured_lower = configured_str.lower()
            
            # PHASE 3: Improved splitting logic for legacy combined strings
            # Pattern: "dpmpp_2m_karras" -> sampler="dpmpp_2m", scheduler="karras"
            scheduler_from_sampler = None
            sampler_base = configured_str
            
            # Known scheduler suffixes (in order of specificity)
            scheduler_suffixes = [
                ("_karras", "karras"),
                ("_exponential", "exponential"),
                ("_normal", "normal"),
                ("_simple", "simple"),
                ("_sgm_uniform", "sgm_uniform")
            ]
            
            # Check if configured string ends with a scheduler suffix
            for suffix, scheduler_name in scheduler_suffixes:
                if configured_lower.endswith(suffix):
                    scheduler_from_sampler = scheduler_name
                    # Remove suffix to get base sampler name
                    sampler_base = configured_str[:-len(suffix)]
                    break
            
            # If no suffix found, check if it contains scheduler name as separate word
            if not scheduler_from_sampler:
                # Pattern: "DPM++ 2M Karras" (with spaces)
                words = configured_str.split()
                if len(words) > 1:
                    last_word = words[-1].lower()
                    if last_word in ["karras", "exponential", "normal", "simple", "sgm_uniform"]:
                        scheduler_from_sampler = last_word
                        sampler_base = " ".join(words[:-1])
            
            # Normalize sampler_base for matching
            sampler_base_lower = sampler_base.lower().strip()
            
            if allowed_samplers:
                # Try fuzzy match with cleaned name
                picked = fuzzy_pick(sampler_base_lower, allowed_samplers)
                if not picked:
                    # Try exact match on normalized base
                    for allowed in allowed_samplers:
                        if normalize_key(allowed) == normalize_key(sampler_base_lower):
                            picked = allowed
                            break
                
                if not picked:
                    # Try fallback order against allowed list
                    for fallback in sampler_fallback_order:
                        if fallback in allowed_samplers:
                            picked = fallback
                            break
                
                if not picked:
                    # Last resort: first allowed sampler
                    picked = allowed_samplers[0]
                
                if picked != configured:
                    inputs["sampler_name"] = picked
                    patches["sampler_name"] = (configured, picked)
                
                # If we extracted scheduler from sampler name, set it
                if scheduler_from_sampler and "scheduler" in inputs:
                    if allowed_schedulers:
                        # Validate scheduler against allowed list
                        if scheduler_from_sampler in allowed_schedulers:
                            inputs["scheduler"] = scheduler_from_sampler
                            patches["scheduler"] = (inputs.get("scheduler"), scheduler_from_sampler)
                        else:
                            # Try fuzzy match for scheduler
                            scheduler_picked = fuzzy_pick(scheduler_from_sampler, allowed_schedulers)
                            if scheduler_picked:
                                inputs["scheduler"] = scheduler_picked
                                patches["scheduler"] = (inputs.get("scheduler"), scheduler_picked)
                            else:
                                # Default to first allowed scheduler
                                inputs["scheduler"] = allowed_schedulers[0]
                                patches["scheduler"] = (inputs.get("scheduler"), allowed_schedulers[0])
                    else:
                        # No scheduler list, use extracted value
                        inputs["scheduler"] = scheduler_from_sampler
                        patches["scheduler"] = (inputs.get("scheduler"), scheduler_from_sampler)
            else:
                # No server list -> guard against known-bad suffix pattern
                if scheduler_from_sampler:
                    # Remove suffix (scheduler handles that)
                    if sampler_base_lower in sampler_fallback_order:
                        inputs["sampler_name"] = sampler_base_lower
                        patches["sampler_name"] = (configured, sampler_base_lower)
                        if "scheduler" in inputs:
                            inputs["scheduler"] = scheduler_from_sampler
                            patches["scheduler"] = (inputs.get("scheduler"), scheduler_from_sampler)
        
        # 3) Scheduler patch
        if ctype == "KSampler" and "scheduler" in inputs:
            configured = inputs.get("scheduler")
            if allowed_schedulers:
                picked = fuzzy_pick(str(configured), allowed_schedulers)
                if not picked:
                    picked = allowed_schedulers[0]
                
                if picked != configured:
                    inputs["scheduler"] = picked
                    patches["scheduler"] = (configured, picked)
            else:
                if isinstance(configured, str) and configured not in scheduler_fallback_order:
                    inputs["scheduler"] = "normal"
                    patches["scheduler"] = (configured, "normal")
        
        node["inputs"] = inputs
    
    # PHASE 1: Log what was patched with server-truth indicator
    if patches["ckpt_name"]:
        old, new = patches["ckpt_name"]
        source = "server-truth" if allowed_ckpts else "local-fallback"
        print(f"[WF] ckpt_name resolved ({source}): '{old}' -> '{new}'")
    if patches["sampler_name"]:
        old, new = patches["sampler_name"]
        print(f"[WF] sampler_name resolved: '{old}' -> '{new}'")
    if patches["scheduler"]:
        old, new = patches["scheduler"]
        print(f"[WF] scheduler resolved: '{old}' -> '{new}'")
    
    if not any(patches.values()):
        print("[WF] All enum values validated (no patching needed)")
    
    return workflow

def save_workflow(workflow, output_file="comfyui_workflow.json", base_file="comfyui_workflow_base.json", instantid_file="comfyui_workflow_instantid.json", is_instantid=False):
    """Workflow'u JSON dosyasina kaydet
    
    PHASE 3: Saves both base and InstantID versions for transparency
    """
    # Save the active workflow
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)
    print(f"[OK] Workflow kaydedildi: {output_file}")
    
    # Also save variant for reference
    if is_instantid:
        with open(instantid_file, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"[OK] InstantID variant saved: {instantid_file}")
    else:
        with open(base_file, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, indent=2, ensure_ascii=False)
        print(f"[OK] Base variant saved: {base_file}")

if __name__ == "__main__":
    import sys
    
    # PHASE 4: Check for checkpoint before generating workflow
    comfyui_path = resolve_comfyui_root()
    models = check_model_availability(comfyui_path)
    
    if not models["checkpoint"]:
        # Print to both stdout and stderr to ensure PowerShell captures it
        error_msg = "[X] HATA: Checkpoint model bulunamadi!\n"
        error_msg += "    Lutfen bir checkpoint model indirin ve ComfyUI/models/checkpoints/ klasorune koyun\n"
        error_msg += "    Ornek: Realistic Vision V6.0\n"
        error_msg += "    Indirme: https://civitai.com/models/4201/realistic-vision-v60-b1"
        print(error_msg, file=sys.stdout)
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    # Ornek kullanim
    # PHASE 3: Parse command-line arguments
    config_file = None
    server_address = os.environ.get("COMFYUI_SERVER", "127.0.0.1:8188")
    validate_only = False
    
    # Simple argument parsing (support --server and --validate-only)
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--server" and i + 1 < len(args):
            server_address = args[i + 1]
            i += 2
        elif args[i] == "--validate-only":
            validate_only = True
            i += 1
        elif not args[i].startswith("--"):
            config_file = args[i]
            i += 1
        else:
            i += 1
    
    if config_file:
        # Config dosyasindan oku
        with open(config_file, 'r', encoding='utf-8-sig') as f:
            config = json.load(f)
        
        # PHASE 8: Resolve checkpoint name BEFORE creating workflow
        # Query server for available checkpoints first
        configured_model = config.get('generation_settings', {}).get('model', 'Realistic Vision V6.0')
        print(f"[WF] Config model name: {configured_model}")
        
        # Get allowed checkpoints from server
        obj_info = fetch_object_info(server_address)
        allowed_ckpts = get_allowed_values(obj_info, "CheckpointLoaderSimple", "ckpt_name")
        
        if allowed_ckpts and len(allowed_ckpts) > 0:
            print(f"[WF] Server has {len(allowed_ckpts)} checkpoint(s) available", flush=True)
            print(f"[WF] Allowed checkpoints: {', '.join(allowed_ckpts)}", flush=True)
            # PHASE 3: Ensure checkpoint is present in ComfyUI (auto-sync if needed)
            if configured_model.lower().endswith((".safetensors", ".ckpt")):
                ensure_checkpoint_present_in_comfyui(configured_model, comfyui_path)
            # Resolve configured model name to actual checkpoint filename using server-truth
            resolved_ckpt = resolve_ckpt_name(configured_model, allowed_ckpts, comfyui_path)
            print(f"[WF] Final resolved checkpoint: {resolved_ckpt}", flush=True)
            checkpoint_name = resolved_ckpt
        else:
            print(f"[WF] WARNING: Cannot query server for checkpoints, using local fallback")
            # Try to ensure checkpoint is present in ComfyUI
            if configured_model.lower().endswith((".safetensors", ".ckpt")):
                ensure_checkpoint_present_in_comfyui(configured_model, comfyui_path)
            # Use local fallback resolver
            resolved_ckpt = resolve_ckpt_name(configured_model, None, comfyui_path)
            checkpoint_name = resolved_ckpt
        
        workflow = create_workflow_json(
            checkpoint_name=checkpoint_name,
            reference_image_path=config.get('face_consistency', {}).get('reference_image', ''),
            positive_prompt=config.get('base_prompt', ''),
            negative_prompt=config.get('negative_prompt', ''),
            instantid_strength=config.get('face_consistency', {}).get('strength', 0.8),
            steps=config.get('generation_settings', {}).get('steps', 40),
            cfg_scale=config.get('generation_settings', {}).get('cfg_scale', 8.0),
            seed=config.get('generation_settings', {}).get('seed', -1),
            comfyui_path=comfyui_path,
            server_address=server_address
        )
        
        # Determine if InstantID was used
        is_instantid = any("InstantID" in str(node.get('class_type', '')) for node in workflow.values())
    else:
        # Varsayilan workflow
        workflow = create_workflow_json(
            positive_prompt="A 25-year-old woman, professional photography, 8k uhd, highly detailed, photorealistic",
            negative_prompt="low quality, worst quality, blurry, bad anatomy",
            comfyui_path=comfyui_path,
            server_address=server_address
        )
        is_instantid = False
    
    # PHASE 1: Save unpatched workflow for debugging (optional)
    unpatched_workflow = json.loads(json.dumps(workflow))  # Deep copy
    
    # PHASE 1 & 8: Patch workflow enums using server object_info
    print("\n[VALIDATE] Patching workflow enums from server...", flush=True)
    try:
        # Debug: Show checkpoint before patching
        for node_id, node in workflow.items():
            if isinstance(node, dict) and node.get("class_type") == "CheckpointLoaderSimple":
                ckpt_before = node.get("inputs", {}).get("ckpt_name")
                print(f"[DEBUG] Checkpoint before patching: {ckpt_before}", flush=True)
        workflow = patch_workflow_enums(workflow, server_address)
        # PHASE 8: Verify checkpoint was resolved correctly
        obj_info = fetch_object_info(server_address)
        allowed_ckpts = get_allowed_values(obj_info, "CheckpointLoaderSimple", "ckpt_name")
        if allowed_ckpts and len(allowed_ckpts) > 0:
            for node_id, node in workflow.items():
                if isinstance(node, dict) and node.get("class_type") == "CheckpointLoaderSimple":
                    ckpt_name = node.get("inputs", {}).get("ckpt_name")
                    if ckpt_name and ckpt_name not in allowed_ckpts:
                        print(f"[!] ERROR: Checkpoint '{ckpt_name}' not in allowed list after patching!")
                        print(f"    Available checkpoints: {', '.join(allowed_ckpts[:3])}...")
                        # Force resolution using server-truth resolver
                        resolved = resolve_ckpt_name(ckpt_name, allowed_ckpts, comfyui_path)
                        node["inputs"]["ckpt_name"] = resolved
                        print(f"    Forced resolution: '{ckpt_name}' -> '{resolved}'")
    except Exception as e:
        print(f"[!] WARNING: Enum patching failed: {e}")
        import traceback
        traceback.print_exc()
        print("    Workflow will be saved with original values (may cause validation errors)")
    
    # PHASE 4: Validate-only mode
    if validate_only:
        print("\n[VALIDATE-ONLY MODE]")
        print("=" * 60)
        
        # Extract resolved values for display
        obj_info = fetch_object_info(server_address)
        for node_id, node in workflow.items():
            if not isinstance(node, dict):
                continue
            
            ctype = node.get("class_type")
            inputs = node.get("inputs", {})
            
            if ctype == "CheckpointLoaderSimple" and "ckpt_name" in inputs:
                ckpt = inputs.get("ckpt_name")
                print(f"Checkpoint: {ckpt}")
                if obj_info:
                    allowed = get_allowed_values(obj_info, "CheckpointLoaderSimple", "ckpt_name")
                    if allowed:
                        print(f"  Allowed checkpoints: {len(allowed)} available")
                        if ckpt in allowed:
                            print(f"  [OK] Checkpoint validated")
                        else:
                            print(f"  [!] Checkpoint not in allowed list")
            
            if ctype == "KSampler":
                if "sampler_name" in inputs:
                    sampler = inputs.get("sampler_name")
                    print(f"Sampler: {sampler}")
                    if obj_info:
                        allowed = get_allowed_values(obj_info, "KSampler", "sampler_name")
                        if allowed:
                            print(f"  Allowed samplers: {len(allowed)} available")
                            if sampler in allowed:
                                print(f"  [OK] Sampler validated")
                            else:
                                print(f"  [!] Sampler not in allowed list")
                
                if "scheduler" in inputs:
                    scheduler = inputs.get("scheduler")
                    print(f"Scheduler: {scheduler}")
                    if obj_info:
                        allowed = get_allowed_values(obj_info, "KSampler", "scheduler")
                        if allowed:
                            print(f"  Allowed schedulers: {len(allowed)} available")
                            if scheduler in allowed:
                                print(f"  [OK] Scheduler validated")
                            else:
                                print(f"  [!] Scheduler not in allowed list")
        
        print("=" * 60)
        print("[OK] Validation complete - workflow enums resolved")
        sys.exit(0)
    
    # Save patched workflow
    save_workflow(workflow, is_instantid=is_instantid)
    
    # PHASE 1: Also save unpatched version for debugging
    try:
        unpatched_file = "comfyui_workflow_unpatched.json"
        with open(unpatched_file, 'w', encoding='utf-8') as f:
            json.dump(unpatched_workflow, f, indent=2, ensure_ascii=False)
        print(f"[OK] Unpatched workflow saved (debug): {unpatched_file}")
    except Exception:
        pass  # Don't fail if unpatched save fails
