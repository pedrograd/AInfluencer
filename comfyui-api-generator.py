"""
ComfyUI API ile Otomatik Görüntü Üretimi
ComfyUI'ı API üzerinden kontrol ederek otomatik görüntü üretir
"""

# PHASE 1: UTF-8 encoding enforcement - MUST be at the very top
import os
import sys

# Set UTF-8 environment variables before any other imports
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Reconfigure stdout/stderr to UTF-8 with error replacement
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    # Fallback for older Python versions
    try:
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")
    except Exception:
        pass

import json
import time
import uuid
import websocket
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import urllib.parse
from datetime import datetime
import os

# ============================================================================
# PHASE 1 & 2: Safe error handling utilities
# ============================================================================

def normalize_error_payload(payload: Any) -> Tuple[str, Any]:
    """
    Converts any payload (dict, list, string, etc.) to a safe string form
    that can be used with .lower() and substring checks.
    
    Returns:
        Tuple of (text_form, raw_object) for logging
    """
    if payload is None:
        return ("", None)
    if isinstance(payload, str):
        return (payload, payload)
    try:
        # dict/list/anything JSON-serializable
        text = json.dumps(payload, ensure_ascii=False, indent=2)
        return (text, payload)
    except Exception:
        # last resort
        s = str(payload)
        return (s, payload)

def read_error_response(resp) -> Any:
    """
    Tries JSON first, falls back to text.
    """
    try:
        return resp.json()
    except Exception:
        try:
            return resp.text
        except Exception:
            return None

def extract_message(err_raw: Any) -> str:
    """
    Extract human-readable error message from various error formats.
    Handles dict with keys like: type, message, details, error, detail.
    """
    if isinstance(err_raw, dict):
        # Try common error message keys
        for k in ("message", "error", "detail", "details", "type"):
            v = err_raw.get(k)
            if isinstance(v, str) and v.strip():
                return v
        # Fallback to JSON string representation
    text, _ = normalize_error_payload(err_raw)
    return text

def safe_str(x: Any) -> str:
    """
    Safely convert any value to string for .lower() operations.
    """
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    try:
        return json.dumps(x, ensure_ascii=False)
    except Exception:
        return str(x)

# ============================================================================
# PHASE 3: Forensic logging utilities
# ============================================================================

def log_event(run_dir: Optional[Path], level: str, stage: str, **data):
    """
    Log an event to run_log.jsonl in the run directory.
    
    Args:
        run_dir: Directory to save logs (None = no logging)
        level: Log level (info, warning, error)
        stage: Stage name (queue, generate, etc.)
        **data: Additional data to include in log entry
    """
    if not run_dir:
        return
    
    log_file = run_dir / "run_log.jsonl"
    entry = {
        "ts": datetime.now().isoformat(),
        "level": level,
        "stage": stage,
        **data
    }
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Don't fail if logging fails

# ============================================================================

class ComfyUIAPIClient:
    def __init__(self, server_address="127.0.0.1:8188", run_dir: Optional[str] = None):
        """ComfyUI API client'ı başlat
        
        Args:
            server_address: ComfyUI server address
            run_dir: Optional directory for saving run artifacts
        """
        self.server_address = server_address
        self.client_id = str(uuid.uuid4())
        self.ws = None
        self.run_dir = Path(run_dir) if run_dir else None
        if self.run_dir:
            self.run_dir.mkdir(parents=True, exist_ok=True)
        
    def queue_prompt(self, prompt: Dict, workflow_file: Optional[str] = None) -> str:
        """Prompt'u queue'ya ekle ve prompt_id döndür
        
        PHASE 5: Auto-fallback on 400 errors with missing nodes
        PHASE 3: Auto-retry with patched checkpoint from error response
        """
        # Make a deep copy to avoid modifying the original
        workflow_copy = json.loads(json.dumps(prompt))
        
        try:
            p = {"prompt": workflow_copy, "client_id": self.client_id}
            data = json.dumps(p).encode('utf-8')
            
            response = requests.post(
                f"http://{self.server_address}/prompt",
                data=data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'prompt_id' in result:
                    return result['prompt_id']
                else:
                    raise Exception(f"API yanıtında prompt_id bulunamadı: {result}")
            else:
                # PHASE 1 & 2: Safe error handling
                error_raw = read_error_response(response)
                error_text, _ = normalize_error_payload(error_raw)
                error_message = extract_message(error_raw)
                
                # PHASE 3: Save error artifacts
                error_raw_file = None
                if self.run_dir:
                    error_index = len(list((self.run_dir).glob("error_raw_*.json"))) + 1
                    error_raw_file = self.run_dir / f"error_raw_{error_index}.json"
                    error_text_file = self.run_dir / f"error_text_{error_index}.txt"
                    
                    try:
                        with open(error_raw_file, 'w', encoding='utf-8') as f:
                            json.dump(error_raw, f, indent=2, ensure_ascii=False, default=str)
                        with open(error_text_file, 'w', encoding='utf-8') as f:
                            f.write(error_text)
                        
                        log_event(self.run_dir, "error", "queue", 
                                index=error_index,
                                status_code=response.status_code,
                                message=error_message,
                                raw_error_path=str(error_raw_file),
                                error_text_path=str(error_text_file))
                    except Exception:
                        pass  # Don't fail if artifact save fails
                
                # PHASE 3: Extract allowed values from error and retry with patched workflow
                # This is a fallback when object_info doesn't expose enum values
                allowed_ckpts_from_error = None
                if response.status_code == 400 and isinstance(error_raw, dict):
                    try:
                        with open(error_raw_file, 'r', encoding='utf-8') as f:
                            error_from_file = json.load(f)
                        # Try extraction again from file
                        error_obj = error_from_file.get("error", error_from_file)
                        node_errors = error_obj.get("node_errors", {})
                        if not node_errors:
                            node_errors = error_from_file.get("node_errors", {})
                        if isinstance(node_errors, dict):
                            for node_id, node_error in node_errors.items():
                                if isinstance(node_error, dict):
                                    input_errors = node_error.get("errors", [])
                                    for err in input_errors:
                                        if isinstance(err, dict) and err.get("input_name") == "ckpt_name":
                                            extra_info = err.get("extra_info", {})
                                            if isinstance(extra_info, dict):
                                                input_config = extra_info.get("input_config", [])
                                                if isinstance(input_config, list) and len(input_config) > 0:
                                                    if isinstance(input_config[0], list):
                                                        allowed_ckpts_from_error = input_config[0]
                                                        print(f"[WF] ✓ Extracted allowed checkpoints from error file: {allowed_ckpts_from_error}", flush=True)
                                                        break
                                    if allowed_ckpts_from_error:
                                        break
                    except Exception as file_read_error:
                        print(f"[!] Could not read error file: {file_read_error}", flush=True)
                
                    print(f"\n[WF] ===== ATTEMPTING TO EXTRACT ALLOWED CHECKPOINTS FROM ERROR =====", flush=True)
                    try:
                        # Try error.error.node_errors structure first (ComfyUI standard)
                        error_obj = error_raw.get("error", error_raw)
                        node_errors = error_obj.get("node_errors", {})
                        # Also try top-level node_errors (fallback)
                        if not node_errors or not isinstance(node_errors, dict):
                            node_errors = error_raw.get("node_errors", {})
                        
                        print(f"[WF] error_raw keys: {list(error_raw.keys()) if isinstance(error_raw, dict) else 'N/A'}", flush=True)
                        print(f"[WF] error_obj keys: {list(error_obj.keys()) if isinstance(error_obj, dict) else 'N/A'}", flush=True)
                        print(f"[WF] node_errors type: {type(node_errors)}, len: {len(node_errors) if isinstance(node_errors, dict) else 'N/A'}", flush=True)
                        
                        if isinstance(node_errors, dict) and len(node_errors) > 0:
                            for node_id, node_error in node_errors.items():
                                print(f"[WF] Processing node {node_id}...", flush=True)
                                if isinstance(node_error, dict):
                                    input_errors = node_error.get("errors", [])
                                    print(f"[WF] Node {node_id} has {len(input_errors)} errors", flush=True)
                                    for idx, err in enumerate(input_errors):
                                        if isinstance(err, dict):
                                            # input_name can be in err directly OR in extra_info
                                            input_name = err.get("input_name")
                                            if not input_name:
                                                extra_info_check = err.get("extra_info", {})
                                                if isinstance(extra_info_check, dict):
                                                    input_name = extra_info_check.get("input_name")
                                            # Also try parsing from details field: "ckpt_name: ..."
                                            if not input_name:
                                                details = err.get("details", "")
                                                if isinstance(details, str) and ":" in details:
                                                    input_name = details.split(":")[0].strip()
                                            
                                            print(f"[WF] Error {idx}: input_name='{input_name}' (from err={err.get('input_name')}, extra_info={err.get('extra_info', {}).get('input_name') if isinstance(err.get('extra_info'), dict) else 'N/A'})", flush=True)
                                            
                                            if input_name == "ckpt_name":
                                                print(f"[WF] ✓ Found ckpt_name error!", flush=True)
                                                extra_info = err.get("extra_info", {})
                                                print(f"[WF] extra_info type: {type(extra_info)}, keys: {list(extra_info.keys()) if isinstance(extra_info, dict) else 'N/A'}", flush=True)
                                                if isinstance(extra_info, dict):
                                                    input_config = extra_info.get("input_config", [])
                                                    print(f"[WF] input_config type: {type(input_config)}, len: {len(input_config) if isinstance(input_config, list) else 'N/A'}", flush=True)
                                                    if isinstance(input_config, list) and len(input_config) > 0:
                                                        print(f"[WF] input_config[0] type: {type(input_config[0])}", flush=True)
                                                        if isinstance(input_config[0], list):
                                                            allowed_ckpts_from_error = input_config[0]
                                                            print(f"\n[WF] ✓✓✓ EXTRACTED ALLOWED CHECKPOINTS: {allowed_ckpts_from_error}", flush=True)
                                                            break
                                                        else:
                                                            print(f"[WF] input_config[0] is {type(input_config[0])}, not a list", flush=True)
                                            elif input_name:
                                                print(f"[WF] Skipping error for input_name='{input_name}' (not ckpt_name)", flush=True)
                                    if allowed_ckpts_from_error:
                                        break
                        else:
                            print(f"[WF] node_errors is not a valid dict or is empty", flush=True)
                    except Exception as e:
                        print(f"[!] Exception during extraction: {e}", flush=True)
                        import traceback
                        traceback.print_exc()
                    print(f"[WF] ===== EXTRACTION COMPLETE: allowed_ckpts_from_error={allowed_ckpts_from_error is not None} =====", flush=True)
                    
                    # Fallback: Try to read from saved error file if in-memory extraction failed
                    if not allowed_ckpts_from_error and self.run_dir and error_raw_file and error_raw_file.exists():
                        print(f"[WF] Trying to extract from saved error file: {error_raw_file}", flush=True)
                        try:
                            with open(error_raw_file, 'r', encoding='utf-8') as f:
                                error_from_file = json.load(f)
                            # Try extraction again from file
                            error_obj = error_from_file.get("error", error_from_file)
                            node_errors = error_obj.get("node_errors", {})
                            if not node_errors:
                                node_errors = error_from_file.get("node_errors", {})
                            if isinstance(node_errors, dict):
                                for node_id, node_error in node_errors.items():
                                    if isinstance(node_error, dict):
                                        input_errors = node_error.get("errors", [])
                                        for err in input_errors:
                                            if isinstance(err, dict):
                                                # Check input_name in multiple places
                                                input_name = err.get("input_name")
                                                if not input_name:
                                                    extra_info_check = err.get("extra_info", {})
                                                    if isinstance(extra_info_check, dict):
                                                        input_name = extra_info_check.get("input_name")
                                                if not input_name:
                                                    details = err.get("details", "")
                                                    if isinstance(details, str) and ":" in details:
                                                        input_name = details.split(":")[0].strip()
                                                
                                                if input_name == "ckpt_name":
                                                    extra_info = err.get("extra_info", {})
                                                    if isinstance(extra_info, dict):
                                                        input_config = extra_info.get("input_config", [])
                                                        if isinstance(input_config, list) and len(input_config) > 0:
                                                            if isinstance(input_config[0], list):
                                                                allowed_ckpts_from_error = input_config[0]
                                                                print(f"[WF] ✓ Extracted allowed checkpoints from error file: {allowed_ckpts_from_error}", flush=True)
                                                                break
                                        if allowed_ckpts_from_error:
                                            break
                        except Exception as file_read_error:
                            print(f"[!] Could not read error file: {file_read_error}", flush=True)
                
                # PHASE 3: If we got allowed checkpoints from error, patch workflow and retry
                if allowed_ckpts_from_error and isinstance(workflow_copy, dict):
                    print(f"\n[WF] ✓✓✓ Patching workflow with extracted allowed checkpoints and retrying...", flush=True)
                    print(f"[WF] Allowed checkpoints: {allowed_ckpts_from_error}", flush=True)
                    try:
                        import importlib.util
                        workflow_gen_path = Path(__file__).parent / "comfyui-workflow-generator.py"
                        if workflow_gen_path.exists():
                            spec = importlib.util.spec_from_file_location("workflow_gen", workflow_gen_path)
                            workflow_gen = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(workflow_gen)
                            
                            # Patch checkpoint in workflow using extracted allowed list
                            patched = False
                            for node_id, node in workflow_copy.items():
                                if isinstance(node, dict) and node.get("class_type") == "CheckpointLoaderSimple":
                                    current_ckpt = node.get("inputs", {}).get("ckpt_name")
                                    print(f"[WF] Current checkpoint in workflow: {current_ckpt}", flush=True)
                                    if current_ckpt and current_ckpt not in allowed_ckpts_from_error:
                                        # Resolve to an allowed checkpoint
                                        resolved = workflow_gen.resolve_ckpt_name(str(current_ckpt), allowed_ckpts_from_error, None)
                                        print(f"[WF] Resolved checkpoint: {resolved}", flush=True)
                                        if resolved in allowed_ckpts_from_error:
                                            node["inputs"]["ckpt_name"] = resolved
                                            print(f"[WF] ✓✓✓ Patched checkpoint: '{current_ckpt}' -> '{resolved}'", flush=True)
                                            patched = True
                                        else:
                                            print(f"[!] Resolved checkpoint '{resolved}' not in allowed list!", flush=True)
                                    elif current_ckpt in allowed_ckpts_from_error:
                                        print(f"[WF] Current checkpoint already in allowed list, no patching needed", flush=True)
                            
                            if patched:
                                print(f"[WF] Retrying request with patched workflow...", flush=True)
                                # Retry with patched workflow
                                p = {"prompt": workflow_copy, "client_id": self.client_id}
                                data = json.dumps(p).encode('utf-8')
                                response = requests.post(
                                    f"http://{self.server_address}/prompt",
                                    data=data,
                                    headers={"Content-Type": "application/json"},
                                    timeout=30
                                )
                                if response.status_code == 200:
                                    result = response.json()
                                    if 'prompt_id' in result:
                                        print(f"[OK] ✓✓✓ Retry with patched workflow succeeded! Prompt ID: {result['prompt_id']}", flush=True)
                                        return result['prompt_id']
                                else:
                                    error_retry = read_error_response(response)
                                    print(f"[!] Retry still failed with status {response.status_code}", flush=True)
                                    print(f"[!] Error: {extract_message(error_retry)}", flush=True)
                            else:
                                print(f"[!] No checkpoint patching needed or patching failed", flush=True)
                        else:
                            print(f"[!] workflow_gen_path not found: {workflow_gen_path}", flush=True)
                    except Exception as retry_error:
                        print(f"[!] Retry with patched workflow failed: {retry_error}", flush=True)
                        import traceback
                        traceback.print_exc()
                elif response.status_code == 400:
                    print(f"[!] Could not extract allowed checkpoints from error (allowed_ckpts_from_error={allowed_ckpts_from_error})", flush=True)
                
                # PHASE 3: Detect validation errors and provide precise details
                error_lower = error_text.lower()  # error_text is already normalized to string
                
                # Check for prompt_outputs_failed_validation error
                if response.status_code == 400 and "prompt_outputs_failed_validation" in error_lower:
                    print("\n[VALIDATION]")
                    print("=" * 60)
                    
                    # Try to extract node and input info from error
                    try:
                        if isinstance(error_raw, dict):
                            # ComfyUI error structure: { "error": { "node_errors": {...} } }
                            error_obj = error_raw.get("error", error_raw)
                            
                            # Get node_errors from error object or top level
                            node_errors = error_obj.get("node_errors", {})
                            if not node_errors:
                                node_errors = error_raw.get("node_errors", {})
                            
                            if isinstance(node_errors, dict):
                                for node_id, node_error in list(node_errors.items())[:3]:  # First 3 errors
                                    # Get class_type
                                    class_type = "unknown"
                                    if isinstance(node_error, dict):
                                        class_type = node_error.get("class_type", "unknown")
                                    
                                    print(f" Node {node_id} ({class_type})")
                                    
                                    if isinstance(node_error, dict):
                                        input_errors = node_error.get("errors", [])
                                        if not input_errors:
                                            # Sometimes errors is at top level
                                            input_errors = [node_error]
                                        
                                        for err in input_errors[:2]:  # First 2 input errors
                                            if isinstance(err, dict):
                                                # PHASE 4: Robust extraction of input_name
                                                input_name = None
                                                # Try multiple paths for input_name
                                                input_name = err.get("input_name") or err.get("name")
                                                
                                                # Fallback: parse from details if it starts with "<name>:"
                                                if not input_name:
                                                    details = err.get("details", "")
                                                    if isinstance(details, str) and ":" in details:
                                                        input_name = details.split(":")[0].strip()
                                                
                                                # Last resort: check extra_info
                                                if not input_name:
                                                    extra_info = err.get("extra_info", {})
                                                    if isinstance(extra_info, dict):
                                                        input_name = extra_info.get("input_name")
                                                
                                                input_name = input_name or "unknown"
                                                
                                                # PHASE 4: Robust extraction of received_value
                                                received_value = None
                                                received_value = err.get("received_value") or err.get("received") or err.get("value")
                                                
                                                # Fallback: check extra_info
                                                if not received_value:
                                                    extra_info = err.get("extra_info", {})
                                                    if isinstance(extra_info, dict):
                                                        received_value = extra_info.get("received_value") or extra_info.get("received")
                                                
                                                received_value = received_value if received_value is not None else "unknown"
                                                
                                                # PHASE 4: Robust extraction of allowed values
                                                allowed_values = None
                                                extra_info = err.get("extra_info", {})
                                                if isinstance(extra_info, dict):
                                                    input_config = extra_info.get("input_config", [])
                                                    if isinstance(input_config, list) and len(input_config) > 0:
                                                        if isinstance(input_config[0], list):
                                                            allowed_values = input_config[0]
                                                        elif isinstance(input_config[0], (str, int, float)):
                                                            # Sometimes it's a flat list
                                                            allowed_values = input_config
                                                
                                                if not allowed_values:
                                                    allowed_values = err.get("allowed", []) or err.get("allowed_values", [])
                                                
                                                # PHASE 4: Format output with proper labels
                                                print(f"   input: {input_name}")
                                                print(f"   received: {received_value}")
                                                if allowed_values and isinstance(allowed_values, list) and len(allowed_values) > 0:
                                                    preview = ", ".join(str(a) for a in allowed_values[:3])
                                                    if len(allowed_values) > 3:
                                                        preview += f", ... ({len(allowed_values)} total)"
                                                    print(f"   allowed (preview): {preview}")
                                                else:
                                                    print(f"   allowed: (not provided)")
                                            elif isinstance(err, str):
                                                print(f"   {err}")
                                    elif isinstance(node_error, str):
                                        print(f"   {node_error}")
                    except Exception as parse_err:
                        # Fallback: show raw error structure
                        print(f" Error parsing failed: {parse_err}")
                        print(f" Raw error structure available in run artifacts")
                    
                    print("=" * 60)
                    print("\n[SOLUTION]")
                    print("  Run workflow generator with --validate-only to check enum values:")
                    print(f"    python comfyui-workflow-generator.py <config.json> --server {self.server_address} --validate-only")
                    print("  Or check run artifacts for full error details")
                    print("")
                
                # PHASE 5: Auto-fallback for missing node errors (with safe .lower())
                if response.status_code == 400 and ("does not exist" in error_lower or "invalid_prompt" in error_lower):
                    if workflow_file:
                        workflow_file_str = safe_str(workflow_file)  # PHASE 4: Safe string conversion
                        base_workflow_file = workflow_file_str.replace("comfyui_workflow.json", "comfyui_workflow_base.json")
                        if "instantid" in workflow_file_str.lower() and Path(base_workflow_file).exists():
                            print(f"  [!] Node missing error detected, trying base workflow: {base_workflow_file}")
                            try:
                                with open(base_workflow_file, 'r', encoding='utf-8') as f:
                                    base_workflow = json.load(f)
                                # Retry with base workflow
                                p = {"prompt": base_workflow, "client_id": self.client_id}
                                data = json.dumps(p).encode('utf-8')
                                response = requests.post(
                                    f"http://{self.server_address}/prompt",
                                    data=data,
                                    headers={"Content-Type": "application/json"},
                                    timeout=30
                                )
                                if response.status_code == 200:
                                    result = response.json()
                                    if 'prompt_id' in result:
                                        print("  [OK] Base workflow succeeded")
                                        return result['prompt_id']
                            except Exception as fallback_error:
                                print(f"  [X] Base workflow fallback failed: {fallback_error}")
                
                # PHASE 2: Use extracted message for better error reporting
                raise Exception(f"API Hatası ({response.status_code}): {error_message}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Bağlantı hatası: {e}")
        except Exception as e:
            raise Exception(f"Queue hatası: {e}")
    
    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Üretilen görüntüyü indir"""
        data = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        url_values = urllib.parse.urlencode(data)
        
        response = requests.get(
            f"http://{self.server_address}/view?{url_values}",
            stream=True
        )
        
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Görüntü indirme hatası: {response.status_code}")
    
    def get_history(self, prompt_id: str) -> Optional[Dict]:
        """Prompt geçmişini al"""
        response = requests.get(f"http://{self.server_address}/history/{prompt_id}")
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> bool:
        """Görüntü üretiminin tamamlanmasını bekle"""
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)
            
            if history and prompt_id in history:
                prompt_info = history[prompt_id]
                # Check for errors
                if 'errors' in prompt_info and prompt_info['errors']:
                    print(f"  [X] Hata tespit edildi: {prompt_info['errors']}")
                    return False
                # Check if completed successfully
                if 'outputs' in prompt_info:
                    return True
            
            # Check queue status periodically
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0 and elapsed != last_status:
                last_status = elapsed
                print(f"  → Bekleniyor... ({elapsed}s/{timeout}s)")
            
            time.sleep(1)
        
        return False
    
    def generate_image(
        self,
        workflow: Dict,
        output_dir: Path,
        filename_prefix: str = "generated",
        workflow_file: Optional[str] = None  # PHASE 5: For auto-fallback
    ) -> Optional[Path]:
        """Tek bir görüntü üret"""
        try:
            # Prompt'u queue'ya ekle
            prompt_id = self.queue_prompt(workflow, workflow_file)
            print(f"  → Prompt ID: {prompt_id}")
            
            # Tamamlanmasını bekle
            print("  -> Uretim bekleniyor...")
            if not self.wait_for_completion(prompt_id, timeout=300):
                print("  [X] Timeout! (300 saniye)")
                # Try to get error information
                try:
                    history = self.get_history(prompt_id)
                    if history and prompt_id in history:
                        # Check for errors
                        prompt_info = history[prompt_id]
                        if 'errors' in prompt_info:
                            print(f"  → Hata detayları: {prompt_info['errors']}")
                except:
                    pass
                return None
            
            # Geçmişi al
            history = self.get_history(prompt_id)
            if not history or prompt_id not in history:
                print("  [X] Gecmis bulunamadi!")
                return None
            
            # Görüntü bilgilerini al
            prompt_info = history[prompt_id]
            
            # Check for errors first
            if 'errors' in prompt_info and prompt_info['errors']:
                print(f"  [X] Hata: {prompt_info['errors']}")
                return None
            
            output_images = prompt_info.get('outputs', {})
            
            if not output_images:
                print("  [X] Goruntu ciktisi bulunamadi!")
                return None
            
            # İlk görüntüyü al
            for node_id in output_images:
                images = output_images[node_id].get('images', [])
                if images:
                    image_info = images[0]
                    filename = image_info['filename']
                    subfolder = image_info.get('subfolder', '')
                    
                    # Görüntüyü indir
                    image_data = self.get_image(filename, subfolder)
                    
                    # Kaydet
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f"{filename_prefix}_{prompt_id[:8]}.png"
                    
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    
                    print(f"  [OK] Kaydedildi: {output_path}")
                    return output_path
            
            print("  [X] Goruntu bulunamadi!")
            return None
            
        except Exception as e:
            # PHASE 6: Show error message but limit traceback output
            print(f"  [X] Hata: {e}")
            # Only print traceback for unexpected errors, not common queue failures
            if "Queue" not in str(e) and "timeout" not in str(e).lower():
                import traceback
                traceback.print_exc()
            return None
    
    def batch_generate(
        self,
        workflow_template: Dict,
        prompts: List[Dict],
        output_dir: Path,
        workflow_file: Optional[str] = None  # PHASE 5: For auto-fallback
    ) -> List[Path]:
        """Toplu görüntü üret"""
        print(f"\n{'='*60}")
        print(f"TOPLU GORUNTU URETIMI BASLIYOR")
        print(f"{'='*60}")
        print(f"Toplam prompt: {len(prompts)}")
        print(f"Cikis klasoru: {output_dir}")
        print(f"{'='*60}\n")
        
        # Validate workflow structure
        if not isinstance(workflow_template, dict):
            raise ValueError(f"Workflow must be a dict, got {type(workflow_template)}")
        
        if len(workflow_template) == 0:
            raise ValueError("Workflow is empty")
        
        generated_images = []
        
        for i, prompt_data in enumerate(prompts, 1):
            print(f"[{i}/{len(prompts)}]")
            
            try:
                # Workflow'u güncelle
                workflow = json.loads(json.dumps(workflow_template))  # Deep copy
                
                # Find prompt nodes
                positive_prompt_nodes = []
                negative_prompt_nodes = []
                sampler_nodes = []
                
                for node_id, node_data in workflow.items():
                    class_type = node_data.get('class_type', '')
                    # PHASE 4: Safe class_type handling
                    class_type_str = safe_str(class_type)
                    
                    if class_type_str == 'CLIPTextEncode':
                        inputs = node_data.get('inputs', {})
                        # Check if it's positive or negative prompt
                        # PHASE 4: Safe text handling (could be dict)
                        text_raw = inputs.get('text', '')
                        text = safe_str(text_raw)
                        # Typically negative prompts contain keywords like "low quality"
                        text_lower = text.lower()
                        if any(word in text_lower for word in ['low quality', 'worst quality', 'bad anatomy']):
                            negative_prompt_nodes.append(node_id)
                        else:
                            positive_prompt_nodes.append(node_id)
                    elif class_type_str == 'KSampler':
                        sampler_nodes.append(node_id)
                
                # Update positive prompts
                if positive_prompt_nodes and prompt_data.get('prompt'):
                    for node_id in positive_prompt_nodes:
                        workflow[node_id]['inputs']['text'] = prompt_data['prompt']
                
                # Update negative prompts
                if negative_prompt_nodes and prompt_data.get('negative_prompt'):
                    for node_id in negative_prompt_nodes:
                        workflow[node_id]['inputs']['text'] = prompt_data['negative_prompt']
                elif negative_prompt_nodes and not prompt_data.get('negative_prompt'):
                    # Use default negative prompt if not provided
                    default_negative = "low quality, worst quality, blurry, bad anatomy"
                    for node_id in negative_prompt_nodes:
                        workflow[node_id]['inputs']['text'] = default_negative
                
                # Update seed
                if sampler_nodes and 'seed' in prompt_data:
                    seed = prompt_data['seed']
                    if seed == -1:
                        import random
                        seed = random.randint(0, 2**32 - 1)
                    for node_id in sampler_nodes:
                        if 'inputs' in workflow[node_id]:
                            workflow[node_id]['inputs']['seed'] = seed
                
                # Debug: Show which nodes were found
                if i == 1:  # Only on first iteration
                    print(f"  -> Found {len(positive_prompt_nodes)} positive prompt node(s)")
                    print(f"  -> Found {len(negative_prompt_nodes)} negative prompt node(s)")
                    print(f"  -> Found {len(sampler_nodes)} sampler node(s)")
                    
                    # PHASE 6: Check for InstantID nodes in base workflow
                    if not any("InstantID" in safe_str(node.get('class_type', '')) for node in workflow.values()):
                        print("  -> Using base workflow (no InstantID nodes detected)")
                
                # PHASE 3: Save workflow snapshot before generation
                workflow_snapshot_path = None
                if self.run_dir:
                    workflow_snapshot_path = self.run_dir / f"workflow_used_{i}.json"
                    prompt_info = {
                        "index": i,
                        "seed": prompt_data.get('seed', -1),
                        "positive_prompt_nodes": positive_prompt_nodes,
                        "negative_prompt_nodes": negative_prompt_nodes,
                        "sampler_nodes": sampler_nodes,
                        "prompt": prompt_data.get('prompt', ''),
                        "negative_prompt": prompt_data.get('negative_prompt', '')
                    }
                    try:
                        with open(workflow_snapshot_path, 'w', encoding='utf-8') as f:
                            json.dump(workflow, f, indent=2, ensure_ascii=False)
                        prompt_info_file = self.run_dir / f"prompt_info_{i}.json"
                        with open(prompt_info_file, 'w', encoding='utf-8') as f:
                            json.dump(prompt_info, f, indent=2, ensure_ascii=False)
                        
                        log_event(self.run_dir, "info", "generate", 
                                index=i,
                                workflow_path=str(workflow_snapshot_path),
                                prompt_info_path=str(prompt_info_file))
                    except Exception:
                        pass  # Don't fail if artifact save fails
                
                # Görüntü üret
                filename_prefix = f"img_{i:03d}"
                
                # PHASE 3: Use saved workflow file path if available
                workflow_file_for_fallback = None
                if workflow_snapshot_path:
                    workflow_file_for_fallback = str(workflow_snapshot_path)
                elif workflow_file:  # workflow_file is the parameter from batch_generate method
                    workflow_file_for_fallback = workflow_file
                
                output_path = self.generate_image(
                    workflow,
                    output_dir,
                    filename_prefix,
                    workflow_file_for_fallback  # PHASE 5: Pass for auto-fallback
                )
                
                if output_path:
                    generated_images.append(output_path)
                else:
                    print(f"  [!] Goruntu uretilemedi")
                    
            except Exception as e:
                # PHASE 6: Reduce traceback spam - only show summary for repeated errors
                print(f"  [X] Hata: {e}")
                # Skip full traceback in batch mode to reduce noise
                # Full traceback only shown on first occurrence or critical errors
                # Continue with next prompt
            
            # Kısa bekleme (rate limiting için)
            if i < len(prompts):
                time.sleep(2)
        
        print(f"\n{'='*60}")
        print(f"TOPLU URETIM TAMAMLANDI")
        print(f"{'='*60}")
        print(f"Basarili: {len(generated_images)}/{len(prompts)}")
        print(f"{'='*60}\n")
        
        return generated_images

def check_comfyui_running(server_address="127.0.0.1:8188") -> bool:
    """ComfyUI çalışıyor mu kontrol et"""
    try:
        response = requests.get(f"http://{server_address}/system_stats", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Ana fonksiyon"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='ComfyUI API ile Otomatik Görüntü Üretimi'
    )
    parser.add_argument(
        '--workflow',
        type=str,
        required=True,
        help='Workflow JSON dosyası'
    )
    parser.add_argument(
        '--prompts',
        type=str,
        help='Prompt dosyası (generated_prompts.txt)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='ComfyUI/output',
        help='Çıkış klasörü'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Üretilecek görüntü sayısı'
    )
    parser.add_argument(
        '--server',
        type=str,
        default='127.0.0.1:8188',
        help='ComfyUI server adresi'
    )
    parser.add_argument(
        '--run-dir',
        type=str,
        default=None,
        help='Directory to save run artifacts (workflows, errors, logs)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate workflow and prompts, do not generate images'
    )
    
    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(1)
    
    # ComfyUI çalışıyor mu?
    print("ComfyUI baglantisi kontrol ediliyor...")
    try:
        if not check_comfyui_running(args.server):
            print(f"[X] HATA: ComfyUI calismiyor veya erisilemiyor: {args.server}")
            print("  Lutfen ComfyUI'i baslatin: cd ComfyUI && python main.py")
            sys.exit(1)
    except Exception as e:
        print(f"[X] HATA: Baglanti kontrolu basarisiz: {e}")
        sys.exit(1)
    
    print(f"[OK] ComfyUI baglantisi basarili: {args.server}\n")
    
    # PHASE 3: Setup run directory
    run_dir = None
    if args.run_dir:
        run_dir = Path(args.run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Run directory: {run_dir}\n")
    else:
        # Default to runs/<timestamp> in current directory
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        run_dir = Path("runs") / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"[OK] Run directory (auto): {run_dir}\n")
    
    # Workflow'u yükle
    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        print(f"[X] HATA: Workflow dosyasi bulunamadi: {workflow_path}")
        sys.exit(1)
    
    try:
        with open(workflow_path, 'r', encoding='utf-8-sig') as f:
            workflow = json.load(f)
        
        # Validate workflow structure
        if not isinstance(workflow, dict):
            print(f"[X] HATA: Workflow gecersiz format - dict bekleniyor")
            sys.exit(1)
        
        # PHASE 3: Runtime workflow patching - enforce server-truth checkpoint selection
        print("[VALIDATION] Patching workflow enums from server...", flush=True)
        patching_successful = False
        try:
            # Import patching function from workflow generator
            import importlib.util
            workflow_gen_path = Path(__file__).parent / "comfyui-workflow-generator.py"
            if workflow_gen_path.exists():
                spec = importlib.util.spec_from_file_location("workflow_gen", workflow_gen_path)
                workflow_gen = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(workflow_gen)
                
                # Debug: Show checkpoint before patching
                ckpt_before = None
                for node_id, node in workflow.items():
                    if isinstance(node, dict) and node.get("class_type") == "CheckpointLoaderSimple":
                        ckpt_before = node.get("inputs", {}).get("ckpt_name")
                        print(f"[DEBUG] Checkpoint before patching: {ckpt_before}", flush=True)
                        break
                
                # Patch workflow using server-truth
                workflow = workflow_gen.patch_workflow_enums(workflow, args.server)
                
                # Debug: Show checkpoint after patching
                ckpt_after = None
                for node_id, node in workflow.items():
                    if isinstance(node, dict) and node.get("class_type") == "CheckpointLoaderSimple":
                        ckpt_after = node.get("inputs", {}).get("ckpt_name")
                        print(f"[DEBUG] Checkpoint after patching: {ckpt_after}", flush=True)
                        if ckpt_before and ckpt_before != ckpt_after:
                            print(f"[OK] Checkpoint patched: '{ckpt_before}' -> '{ckpt_after}'", flush=True)
                            patching_successful = True
                        break
                
                if patching_successful:
                    print("[OK] Workflow patched with server-truth values", flush=True)
                else:
                    print("[!] WARNING: Workflow patching did not change checkpoint - may still be invalid", flush=True)
            else:
                print("[!] WARNING: comfyui-workflow-generator.py not found, skipping patching", flush=True)
        except Exception as e:
            print(f"[!] WARNING: Workflow patching failed: {e}", flush=True)
            import traceback
            traceback.print_exc()
            print("    Continuing with original workflow (may cause validation errors)", flush=True)
        
        # PHASE 6: Check for InstantID nodes and warn if not available
        has_instantid_nodes = any("InstantID" in safe_str(node.get('class_type', '')) for node in workflow.values())
        if has_instantid_nodes:
            print("[!] InstantID nodes detected in workflow")
            # Could check server capabilities here, but just warn for now
        
        print(f"[OK] Workflow yuklendi: {workflow_path}\n")
        
        # PHASE 3: Save initial workflow snapshot
        try:
            snapshot_file = run_dir / "workflow_initial.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2, ensure_ascii=False)
            log_event(run_dir, "info", "load", workflow_path=str(workflow_path), snapshot_path=str(snapshot_file))
        except Exception:
            pass
        
    except json.JSONDecodeError as e:
        print(f"[X] HATA: Workflow JSON parse hatasi: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[X] HATA: Workflow yukleme hatasi: {e}")
        sys.exit(1)
    
    # Prompt'ları yükle
    prompts = []
    
    if args.prompts:
        prompts_path = Path(args.prompts)
        if prompts_path.exists():
            # Prompt dosyasını parse et
            with open(prompts_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basit parsing (daha gelişmiş parser eklenebilir)
            current_prompt = {}
            for line in content.split('\n'):
                if line.startswith('PROMPT:'):
                    current_prompt['prompt'] = line.replace('PROMPT:', '').strip()
                elif line.startswith('NEGATIVE:'):
                    current_prompt['negative_prompt'] = line.replace('NEGATIVE:', '').strip()
                elif line.startswith('SEED:'):
                    current_prompt['seed'] = int(line.replace('SEED:', '').strip())
                    prompts.append(current_prompt.copy())
                    current_prompt = {}
        else:
            print(f"[!] Uyari: Prompt dosyasi bulunamadi: {prompts_path}")
    
    # Eğer prompt yoksa, varsayılan oluştur
    if not prompts:
        print("[!] Prompt dosyasi yok, varsayilan prompt kullaniliyor...")
        for i in range(args.count):
            prompts.append({
                'prompt': 'A beautiful woman, professional photography, 8k uhd, highly detailed, photorealistic',
                'negative_prompt': 'low quality, worst quality, blurry, bad anatomy',
                'seed': -1
            })
    
    # İlk N prompt'u al
    prompts = prompts[:args.count]
    
    # PHASE 7: Validate-only mode
    if args.validate_only:
        print("\n[VALIDATE MODE] Validating workflow and prompts...\n")
        
        # Scan workflow for nodes
        positive_prompt_nodes = []
        negative_prompt_nodes = []
        sampler_nodes = []
        
        for node_id, node_data in workflow.items():
            class_type_str = safe_str(node_data.get('class_type', ''))
            
            if class_type_str == 'CLIPTextEncode':
                inputs = node_data.get('inputs', {})
                text_raw = inputs.get('text', '')
                text = safe_str(text_raw)
                text_lower = text.lower()
                if any(word in text_lower for word in ['low quality', 'worst quality', 'bad anatomy']):
                    negative_prompt_nodes.append(node_id)
                else:
                    positive_prompt_nodes.append(node_id)
            elif class_type_str == 'KSampler':
                sampler_nodes.append(node_id)
        
        print(f"Found {len(positive_prompt_nodes)} positive prompt node(s)")
        print(f"Found {len(negative_prompt_nodes)} negative prompt node(s)")
        print(f"Found {len(sampler_nodes)} sampler node(s)")
        print(f"Loaded {len(prompts)} prompt(s)")
        
        # PHASE 6: Check InstantID
        has_instantid = any("InstantID" in safe_str(node.get('class_type', '')) for node in workflow.values())
        if has_instantid:
            print("[!] InstantID nodes found in workflow")
        else:
            print("[OK] Base workflow (no InstantID nodes)")
        
        print("\n[OK] Validation complete - workflow structure looks valid")
        sys.exit(0)
    
    # API client oluştur
    client = ComfyUIAPIClient(args.server, run_dir=str(run_dir))
    
    # Toplu üretim
    try:
        output_dir = Path(args.output)
        generated_images = client.batch_generate(
            workflow,
            prompts,
            output_dir,
            str(workflow_path)  # PHASE 5: Pass workflow file path for auto-fallback
        )
        
        print(f"\n[OK] Tamamlandi! {len(generated_images)} goruntu uretildi.")
        print(f"[DIR] Klasor: {output_dir}")
        
        # PHASE 3: Generate final run summary
        if run_dir:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "total_prompts": len(prompts),
                "generated_images": len(generated_images),
                "success_rate": f"{len(generated_images)}/{len(prompts)}",
                "output_dir": str(output_dir),
                "workflow_path": str(workflow_path)
            }
            summary_file = run_dir / "run_summary.json"
            try:
                with open(summary_file, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)
                print(f"[LOG] Run summary saved: {summary_file}")
            except Exception:
                pass
        
        if len(generated_images) == 0:
            print("[!] UYARI: Hic goruntu uretilemedi!")
            print("  Kontrol edin:")
            print("    - ComfyUI'in calistigindan emin olun")
            print("    - Workflow'un dogru yapilandirildigini kontrol edin")
            print("    - Modellerin yuklu oldugunu kontrol edin")
            if run_dir:
                print(f"    - Hata loglari: {run_dir / 'run_log.jsonl'}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[X] Kullanici tarafindan iptal edildi")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] HATA: Goruntu uretimi sirasinda hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
