"""
Otomatik Prompt Generator
Karakter konfigurasyonundan prompt olusturur
Enhanced with Advanced Prompt Engineering
"""

import json
import random
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from services.prompt_engineering_service import (
    PromptEngineeringService,
    Platform
)

class PromptGenerator:
    def __init__(self, character_config_path):
        """Karakter konfigurasyonunu yukle"""
        with open(character_config_path, 'r', encoding='utf-8-sig') as f:
            self.config = json.load(f)
        self.prompt_engineering = PromptEngineeringService()
    
    def build_prompt(self, variation='default', platform=None):
        """Prompt olustur - Enhanced with advanced prompt engineering"""
        platform_enum = None
        if platform:
            try:
                platform_enum = Platform(platform.lower())
            except ValueError:
                pass
        
        # Use advanced prompt engineering service
        prompt, negative = self.prompt_engineering.build_prompt_from_character_config(
            self.config,
            variation=variation,
            platform=platform_enum
        )
        
        return prompt
    
    def get_negative_prompt(self, platform=None):
        """Negative prompt dondur - Enhanced"""
        platform_enum = None
        if platform:
            try:
                platform_enum = Platform(platform.lower())
            except ValueError:
                pass
        
        # Use character config negative prompt if exists
        config_negative = self.config.get('negative_prompt', '')
        if config_negative:
            # Merge with platform-specific if needed
            if platform_enum:
                platform_negatives = self.prompt_engineering.PLATFORM_NEGATIVE_PROMPTS.get(platform_enum, '')
                if platform_negatives:
                    return f"{config_negative}, {platform_negatives}"
            return config_negative
        
        # Fallback to standard negative prompt
        return self.prompt_engineering.get_negative_prompt(platform=platform_enum)
    
    def generate_prompts(self, count=10, variation='default', platform=None):
        """Birden fazla prompt olustur - Enhanced"""
        prompts = []
        for i in range(count):
            prompt = self.build_prompt(variation=variation, platform=platform)
            prompts.append({
                'prompt': prompt,
                'negative_prompt': self.get_negative_prompt(platform=platform),
                'seed': random.randint(0, 2**32 - 1),
                'variation': variation,
                'platform': platform
            })
        return prompts
    
    def save_prompts(self, prompts, output_file):
        """Prompt'lari dosyaya kaydet"""
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, p in enumerate(prompts, 1):
                f.write(f"# Prompt {i}\n")
                f.write(f"PROMPT: {p['prompt']}\n")
                f.write(f"NEGATIVE: {p['negative_prompt']}\n")
                f.write(f"SEED: {p['seed']}\n")
                f.write("\n")
        print(f"✓ {len(prompts)} prompt kaydedildi: {output_file}")

if __name__ == "__main__":
    import sys
    
    # Karakter config dosyasi
    config_file = "character_template.json"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    
    if not Path(config_file).exists():
        print(f"HATA: {config_file} bulunamadi!")
        print("character_template.json dosyasini olusturun veya path verin.")
        sys.exit(1)
    
    # Generator olustur
    generator = PromptGenerator(config_file)
    
    # Prompt'lar olustur
    print("Prompt'lar olusturuluyor...")
    prompts = generator.generate_prompts(count=10, variation='default')
    
    # Kaydet
    output_file = "generated_prompts.txt"
    generator.save_prompts(prompts, output_file)
    
    print(f"\n✓ Tamamlandi! {output_file} dosyasini kontrol edin.")
