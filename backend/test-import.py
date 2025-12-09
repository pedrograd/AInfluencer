#!/usr/bin/env python
"""Test imports to find the error"""
import sys
import traceback

print("=" * 60)
print("Testing Backend Imports")
print("=" * 60)

try:
    print("\n1. Testing database import...")
    from database import get_db, init_db
    print("   ✅ Database imported successfully")
except Exception as e:
    print(f"   ❌ Database import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n2. Testing models import...")
    from models import *
    print("   ✅ Models imported successfully")
except Exception as e:
    print(f"   ❌ Models import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n3. Testing service imports...")
    from services.comfyui_client import ComfyUIClient
    print("   ✅ ComfyUI client imported")
except Exception as e:
    print(f"   ⚠️  ComfyUI client import failed (may be OK): {e}")
    traceback.print_exc()

try:
    print("\n4. Testing main module import...")
    import main
    print("   ✅ Main module imported successfully")
    print(f"   ✅ App type: {type(main.app)}")
except Exception as e:
    print(f"   ❌ Main module import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All critical imports successful!")
print("=" * 60)
