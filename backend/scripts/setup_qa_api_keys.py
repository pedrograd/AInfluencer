#!/usr/bin/env python3
"""
Setup QA API Keys
Configures API keys for detection tools (Hive, Sensity, AIOrNot)
"""
import os
import sys
from pathlib import Path
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db, init_db
from models import DetectionToolConfig


def setup_api_keys():
    """Setup API keys for detection tools"""
    print("=" * 60)
    print("QA Detection Tools API Key Setup")
    print("=" * 60)
    print()
    print("This script will help you configure API keys for:")
    print("  - Hive Moderation (https://thehive.ai/)")
    print("  - Sensity AI (https://sensity.ai/)")
    print("  - AIOrNot (https://aiornot.com/)")
    print()
    print("You can skip any tool by pressing Enter without entering a key.")
    print()
    
    # Initialize database
    init_db()
    db = next(get_db())
    
    tools = [
        {
            "name": "hive",
            "display_name": "Hive Moderation",
            "url": "https://thehive.ai/",
            "env_var": "HIVE_API_KEY"
        },
        {
            "name": "sensity",
            "display_name": "Sensity AI",
            "url": "https://sensity.ai/",
            "env_var": "SENSITY_API_KEY"
        },
        {
            "name": "ai_or_not",
            "display_name": "AIOrNot",
            "url": "https://aiornot.com/",
            "env_var": "AI_OR_NOT_API_KEY"
        }
    ]
    
    configured = []
    
    for tool in tools:
        print(f"\n{tool['display_name']} ({tool['url']})")
        print("-" * 60)
        
        # Check if already configured
        existing = db.query(DetectionToolConfig).filter(
            DetectionToolConfig.tool_name == tool["name"]
        ).first()
        
        if existing:
            print(f"Already configured. Current key: {existing.api_key[:10]}...")
            update = input("Update? (y/N): ").strip().lower()
            if update != 'y':
                configured.append(tool["name"])
                continue
        
        # Check environment variable
        env_key = os.getenv(tool["env_var"])
        if env_key:
            print(f"Found environment variable {tool['env_var']}")
            use_env = input("Use this key? (Y/n): ").strip().lower()
            if use_env != 'n':
                api_key = env_key
            else:
                api_key = getpass(f"Enter {tool['display_name']} API key: ").strip()
        else:
            api_key = getpass(f"Enter {tool['display_name']} API key: ").strip()
        
        if not api_key:
            print(f"Skipping {tool['display_name']}")
            continue
        
        # Save to database
        if existing:
            existing.api_key = api_key
            existing.enabled = True
            db.commit()
        else:
            config = DetectionToolConfig(
                tool_name=tool["name"],
                api_key=api_key,
                enabled=True,
                threshold=0.3
            )
            db.add(config)
            db.commit()
        
        # Also set environment variable
        print(f"Setting environment variable {tool['env_var']}")
        os.environ[tool["env_var"]] = api_key
        
        configured.append(tool["name"])
        print(f"✅ {tool['display_name']} configured successfully")
    
    print("\n" + "=" * 60)
    print("Configuration Summary")
    print("=" * 60)
    print(f"Configured tools: {', '.join(configured) if configured else 'None'}")
    print()
    print("To use these keys in production, set them as environment variables:")
    for tool in tools:
        if tool["name"] in configured:
            print(f"  export {tool['env_var']}=<your_key>")
    print()
    print("Or add them to your .env file:")
    for tool in tools:
        if tool["name"] in configured:
            print(f"  {tool['env_var']}=<your_key>")


def verify_api_keys():
    """Verify API keys are working"""
    print("\n" + "=" * 60)
    print("Verifying API Keys")
    print("=" * 60)
    
    db = next(get_db())
    configs = db.query(DetectionToolConfig).filter(
        DetectionToolConfig.enabled == True
    ).all()
    
    if not configs:
        print("No API keys configured")
        return
    
    from services.anti_detection_service import HiveModeration, SensityAI, AIOrNot
    from pathlib import Path
    import tempfile
    from PIL import Image
    
    # Create a test image
    test_image = Image.new('RGB', (100, 100), color='red')
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        test_image.save(tmp.name, 'JPEG')
        test_path = Path(tmp.name)
    
    try:
        for config in configs:
            print(f"\nTesting {config.tool_name}...")
            try:
                if config.tool_name == "hive":
                    tool = HiveModeration(api_key=config.api_key)
                elif config.tool_name == "sensity":
                    tool = SensityAI(api_key=config.api_key)
                elif config.tool_name == "ai_or_not":
                    tool = AIOrNot(api_key=config.api_key)
                else:
                    print(f"  ⚠️  Unknown tool: {config.tool_name}")
                    continue
                
                result = tool.detect(test_path)
                if "error" in result:
                    print(f"  ❌ Error: {result['error']}")
                else:
                    print(f"  ✅ API key is valid")
                    print(f"     Score: {result.get('score', 'N/A')}")
            except Exception as e:
                print(f"  ❌ Error: {e}")
    finally:
        # Clean up test image
        if test_path.exists():
            test_path.unlink()


if __name__ == '__main__':
    try:
        setup_api_keys()
        verify = input("\nVerify API keys? (Y/n): ").strip().lower()
        if verify != 'n':
            verify_api_keys()
        print("\n✅ Setup complete!")
    except KeyboardInterrupt:
        print("\n\nSetup cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
