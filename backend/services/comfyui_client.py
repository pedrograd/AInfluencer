"""
ComfyUI API Client Service
"""
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import websocket
from services.troubleshooting_service import ErrorCode

logger = logging.getLogger(__name__)

class ComfyUIClient:
    """Client for interacting with ComfyUI API"""
    
    def __init__(self, server_address: Optional[str] = None):
        resolved_server = server_address or os.getenv("COMFYUI_SERVER", "127.0.0.1:8188")
        self.server_address = resolved_server
        self.base_url = f"http://{resolved_server}"
        self.client_id = str(uuid.uuid4())
        self.ws = None
        
    def check_connection(self) -> bool:
        """Check if ComfyUI is running and accessible"""
        try:
            response = requests.get(
                f"{self.base_url}/system_stats",
                timeout=5
            )
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            logger.error("ComfyUI connection failed - server not running")
            return False
        except Exception as e:
            logger.error(f"ComfyUI connection check failed: {e}")
            return False
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get ComfyUI system statistics"""
        try:
            response = requests.get(
                f"{self.base_url}/system_stats",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}
    
    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Queue a prompt and return prompt_id"""
        try:
            payload = {
                "prompt": workflow,
                "client_id": self.client_id
            }
            response = requests.post(
                f"{self.base_url}/prompt",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'prompt_id' in result:
                    return result['prompt_id']
                else:
                    raise Exception(f"API response missing prompt_id: {result}")
            elif response.status_code == 401:
                raise Exception(f"Unauthorized: {response.text}")
            elif response.status_code == 429:
                raise Exception(f"Rate limited: {response.text}")
            else:
                error_text = response.text
                raise Exception(f"API error ({response.status_code}): {error_text}")
                
        except requests.exceptions.ConnectionError as e:
            raise Exception(f"ComfyUI not running or not accessible: {e}")
        except requests.exceptions.Timeout as e:
            raise Exception(f"ComfyUI request timeout: {e}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Connection error: {e}")
        except Exception as e:
            raise Exception(f"Queue error: {e}")
    
    def get_history(self, prompt_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get prompt history
        
        If prompt_id is provided, tries to get specific prompt history.
        If None, gets all history.
        """
        try:
            if prompt_id:
                # Try specific prompt ID first
                response = requests.get(
                    f"{self.base_url}/history/{prompt_id}",
                    timeout=10
                )
                if response.status_code == 200:
                    result = response.json()
                    # ComfyUI may return {prompt_id: {...}} or just {...}
                    if isinstance(result, dict) and prompt_id in result:
                        return result
                    elif isinstance(result, dict):
                        # Return as-is, might be the history entry
                        return {prompt_id: result}
                    return result
            
            # Get all history
            response = requests.get(
                f"{self.base_url}/history",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return None
    
    def get_image(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """Download generated image"""
        import urllib.parse
        
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        url_values = urllib.parse.urlencode(params)
        
        response = requests.get(
            f"{self.base_url}/view?{url_values}",
            stream=True,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"Image download error: {response.status_code}")
    
    def wait_for_completion(
        self,
        prompt_id: str,
        timeout: int = 300,
        progress_callback: Optional[callable] = None
    ) -> bool:
        """Wait for generation to complete"""
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)
            
            if history and prompt_id in history:
                prompt_info = history[prompt_id]
                
                # Check for errors
                if 'errors' in prompt_info and prompt_info['errors']:
                    logger.error(f"Generation errors: {prompt_info['errors']}")
                    return False
                
                # Check if completed successfully
                if 'outputs' in prompt_info:
                    if progress_callback:
                        progress_callback(1.0, "Completed")
                    return True
            
            # Periodic status updates
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0 and elapsed != last_status:
                last_status = elapsed
                progress = min(elapsed / timeout, 0.95)  # Estimate progress
                if progress_callback:
                    progress_callback(progress, f"Processing... ({elapsed}s)")
                logger.info(f"Waiting for completion... ({elapsed}s/{timeout}s)")
            
            time.sleep(1)
        
        logger.warning(f"Timeout waiting for completion: {prompt_id}")
        return False
    
    def get_output_images(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Get output images from completed generation"""
        history = self.get_history()
        if not history:
            return []
        
        # Handle different history formats
        prompt_info = None
        
        if isinstance(history, dict):
            # Try direct lookup first
            if prompt_id in history:
                prompt_info = history[prompt_id]
            else:
                # Search through all entries
                for key, value in history.items():
                    if isinstance(value, dict) and 'outputs' in value:
                        # Check if this matches our prompt_id
                        # ComfyUI history may have prompt array
                        if 'prompt' in value:
                            prompt_array = value.get('prompt', [])
                            if isinstance(prompt_array, list):
                                for p in prompt_array:
                                    if isinstance(p, list) and len(p) >= 2:
                                        if p[1] == prompt_id or p[0] == prompt_id:
                                            prompt_info = value
                                            break
                        # If no prompt array but has outputs, might be our job
                        if not prompt_info:
                            prompt_info = value
                            break
        
        if not prompt_info or 'outputs' not in prompt_info:
            return []
        
        output_images = []
        for node_id, node_output in prompt_info['outputs'].items():
            if isinstance(node_output, dict) and 'images' in node_output:
                for image_info in node_output['images']:
                    output_images.append({
                        'filename': image_info['filename'],
                        'subfolder': image_info.get('subfolder', ''),
                        'type': image_info.get('type', 'output'),
                        'node_id': node_id
                    })
        
        return output_images
