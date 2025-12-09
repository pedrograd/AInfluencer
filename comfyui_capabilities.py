"""
ComfyUI Server Capability Detection
Queries the running ComfyUI server to determine which nodes are actually available.
This is the source of truth - not folder existence checks.
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
import requests
import argparse
from typing import Set, Optional, Dict

def get_comfyui_capabilities(server_address: str = "127.0.0.1:8188") -> Dict[str, Set[str]]:
    """
    Query ComfyUI server for available nodes.
    
    Returns:
        Dict with keys:
            - 'nodes': Set of available node class names
            - 'objects': Full object_info dict if available
    """
    capabilities = {
        'nodes': set(),
        'objects': {}
    }
    
    # Try both common endpoint patterns
    endpoints = [
        f"http://{server_address}/object_info",
        f"http://{server_address}/api/object_info"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # Extract node class names from object_info
                if isinstance(data, dict):
                    capabilities['objects'] = data
                    # object_info structure: { "NodeClassName": { "input": {...}, "output": [...] } }
                    capabilities['nodes'] = set(data.keys())
                    return capabilities
        except requests.exceptions.RequestException:
            continue
        except json.JSONDecodeError:
            continue
    
    return capabilities

def check_node_exists(node_class: str, server_address: str = "127.0.0.1:8188") -> bool:
    """Check if a specific node class exists on the server."""
    capabilities = get_comfyui_capabilities(server_address)
    return node_class in capabilities['nodes']

def check_instantid_available(server_address: str = "127.0.0.1:8188") -> bool:
    """Check if InstantID nodes are available on the server."""
    required_nodes = [
        "InstantIDModelLoader",
        "InsightFaceLoader",
        "InstantIDApply"
    ]
    
    capabilities = get_comfyui_capabilities(server_address)
    available_nodes = capabilities['nodes']
    
    # Check if all required nodes exist
    for node in required_nodes:
        if node not in available_nodes:
            return False
    
    return True

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Query ComfyUI server for available nodes'
    )
    parser.add_argument(
        '--server',
        type=str,
        default='127.0.0.1:8188',
        help='ComfyUI server address'
    )
    parser.add_argument(
        '--print',
        action='store_true',
        help='Print all available node class names'
    )
    parser.add_argument(
        '--check',
        type=str,
        help='Check if a specific node class exists (e.g., InstantIDModelLoader)'
    )
    parser.add_argument(
        '--check-instantid',
        action='store_true',
        help='Check if InstantID extension is available'
    )
    
    args = parser.parse_args()
    
    try:
        capabilities = get_comfyui_capabilities(args.server)
        
        if args.check:
            exists = args.check in capabilities['nodes']
            print("YES" if exists else "NO")
            sys.exit(0 if exists else 1)
        
        if args.check_instantid:
            available = check_instantid_available(args.server)
            print("YES" if available else "NO")
            sys.exit(0 if available else 1)
        
        if args.print:
            if capabilities['nodes']:
                for node in sorted(capabilities['nodes']):
                    print(node)
            else:
                print("[!] No nodes found or server unreachable", file=sys.stderr)
                sys.exit(1)
        else:
            # Default: show summary
            node_count = len(capabilities['nodes'])
            instantid_available = check_instantid_available(args.server)
            
            print(f"Server: {args.server}")
            print(f"Available nodes: {node_count}")
            print(f"InstantID available: {'YES' if instantid_available else 'NO'}")
            
            if instantid_available:
                print("\nInstantID nodes found:")
                for node in ["InstantIDModelLoader", "InsightFaceLoader", "InstantIDApply"]:
                    if node in capabilities['nodes']:
                        print(f"  [OK] {node}")
            
    except Exception as e:
        print(f"[X] Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
