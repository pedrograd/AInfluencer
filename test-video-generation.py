#!/usr/bin/env python3
"""
Test Video Generation Setup
Verifies all components are ready for video generation
"""

import sys
import os
from pathlib import Path

def check_python_packages():
    """Check if required Python packages are installed"""
    print("\n[1/5] Checking Python packages...")
    packages = {
        "cv2": "opencv-python",
        "imageio": "imageio",
        "moviepy": "moviepy",
        "diffusers": "diffusers",
        "transformers": "transformers",
        "accelerate": "accelerate"
    }
    
    all_ok = True
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_ffmpeg():
    """Check if FFmpeg is available"""
    print("\n[2/5] Checking FFmpeg...")
    import subprocess
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"  ✓ FFmpeg found: {version_line}")
            return True
        else:
            print("  ✗ FFmpeg not working properly")
            return False
    except FileNotFoundError:
        print("  ✗ FFmpeg not found in PATH")
        print("    Install with: choco install ffmpeg")
        return False
    except Exception as e:
        print(f"  ✗ Error checking FFmpeg: {e}")
        return False

def check_comfyui():
    """Check ComfyUI setup"""
    print("\n[3/5] Checking ComfyUI setup...")
    base_path = Path(__file__).parent
    comfyui_path = base_path / "ComfyUI"
    
    if not comfyui_path.exists():
        print("  ✗ ComfyUI directory not found")
        return False
    
    print("  ✓ ComfyUI directory exists")
    
    # Check AnimateDiff extension
    animatediff_ext = comfyui_path / "custom_nodes" / "ComfyUI-AnimateDiff-Evolved"
    if animatediff_ext.exists():
        print("  ✓ AnimateDiff extension installed")
    else:
        print("  ✗ AnimateDiff extension not found")
        print("    Run: setup-comfyui-video-models.ps1")
    
    return True

def check_models():
    """Check if models are downloaded"""
    print("\n[4/5] Checking models...")
    base_path = Path(__file__).parent
    comfyui_path = base_path / "ComfyUI"
    
    # Check AnimateDiff models
    animatediff_path = comfyui_path / "models" / "animatediff"
    if animatediff_path.exists():
        models = list(animatediff_path.glob("*.safetensors")) + list(animatediff_path.glob("*.ckpt"))
        if models:
            print(f"  ✓ Found {len(models)} AnimateDiff model(s):")
            for model in models:
                size_mb = model.stat().st_size / (1024 * 1024)
                print(f"    - {model.name} ({size_mb:.2f} MB)")
        else:
            print("  ✗ No AnimateDiff models found")
            print("    Download from: https://huggingface.co/guoyww/animatediff-motion-adapter-v1-5-2")
    else:
        print("  ✗ AnimateDiff models directory not found")
    
    # Check SVD models
    svd_path = comfyui_path / "models" / "svd"
    if svd_path.exists():
        models = list(svd_path.glob("*.safetensors")) + list(svd_path.glob("*.ckpt"))
        if models:
            print(f"  ✓ Found {len(models)} SVD model(s):")
            for model in models:
                size_mb = model.stat().st_size / (1024 * 1024)
                print(f"    - {model.name} ({size_mb:.2f} MB)")
        else:
            print("  ⚠ No SVD models found (optional)")
    else:
        print("  ⚠ SVD models directory not found (optional)")

def check_backend_services():
    """Check backend service files"""
    print("\n[5/5] Checking backend services...")
    base_path = Path(__file__).parent
    backend_path = base_path / "backend" / "services"
    
    required_services = [
        "video_generation_service.py",
        "frame_interpolation_service.py",
        "audio_sync_service.py",
        "platform_optimization_service.py"
    ]
    
    all_ok = True
    for service in required_services:
        service_path = backend_path / service
        if service_path.exists():
            print(f"  ✓ {service}")
        else:
            print(f"  ✗ {service} - NOT FOUND")
            all_ok = False
    
    return all_ok

def main():
    """Run all checks"""
    print("=" * 50)
    print("Video Generation Setup Verification")
    print("=" * 50)
    
    results = {
        "Python Packages": check_python_packages(),
        "FFmpeg": check_ffmpeg(),
        "ComfyUI": check_comfyui(),
        "Backend Services": check_backend_services()
    }
    
    check_models()  # Just info, not blocking
    
    print("\n" + "=" * 50)
    if all(results.values()):
        print("✓ Setup Verification: PASSED")
        print("=" * 50)
        print("\nReady to generate videos!")
        print("\nNext steps:")
        print("  1. Start backend: cd backend && python main.py")
        print("  2. Start frontend: cd web && npm run dev")
        print("  3. Visit: http://localhost:3000/generate/video")
        return 0
    else:
        print("⚠ Setup Verification: INCOMPLETE")
        print("=" * 50)
        print("\nPlease fix the issues above:")
        for check, result in results.items():
            if not result:
                print(f"  - {check}")
        print("\nRun setup scripts:")
        print("  .\\setup-video-generation.ps1")
        return 1

if __name__ == "__main__":
    sys.exit(main())
