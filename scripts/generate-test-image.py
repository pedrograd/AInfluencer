"""
Generate Test Image for Anti-Detection Testing
Creates a test image that can be used for detection testing
"""
import sys
from pathlib import Path
from PIL import Image
import numpy as np

def generate_test_image(output_path: Path, size: tuple = (1024, 1024), complexity: str = "medium"):
    """Generate a test image with specified complexity"""
    
    print(f"Generating test image: {output_path}")
    print(f"Size: {size[0]}x{size[1]}")
    print(f"Complexity: {complexity}")
    
    # Create base image
    img = Image.new("RGB", size, color=(128, 128, 128))
    pixels = np.array(img)
    
    if complexity == "simple":
        # Simple gradient
        for y in range(size[1]):
            for x in range(size[0]):
                pixels[y, x] = [
                    int(255 * x / size[0]),
                    int(255 * y / size[1]),
                    128
                ]
    
    elif complexity == "medium":
        # Medium complexity with patterns
        for y in range(size[1]):
            for x in range(size[0]):
                r = int(128 + 127 * np.sin(x * 0.01) * np.cos(y * 0.01))
                g = int(128 + 127 * np.sin((x + y) * 0.01))
                b = int(128 + 127 * np.cos(x * 0.01) * np.sin(y * 0.01))
                pixels[y, x] = [r, g, b]
    
    elif complexity == "complex":
        # Complex patterns
        for y in range(size[1]):
            for x in range(size[0]):
                r = int(128 + 127 * np.sin(x * 0.02) * np.cos(y * 0.02) * np.sin((x + y) * 0.01))
                g = int(128 + 127 * np.cos(x * 0.015) * np.sin(y * 0.015) * np.cos((x - y) * 0.01))
                b = int(128 + 127 * np.sin((x + y) * 0.02) * np.cos((x - y) * 0.015))
                pixels[y, x] = [r, g, b]
    
    img = Image.fromarray(pixels.astype(np.uint8))
    img.save(output_path, "PNG", optimize=True)
    
    print(f"✓ Test image saved: {output_path}")
    print(f"  File size: {output_path.stat().st_size / 1024:.2f} KB")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test image for anti-detection testing")
    parser.add_argument(
        "--output",
        type=str,
        default="test_image.png",
        help="Output file path (default: test_image.png)"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1024,
        help="Image width (default: 1024)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1024,
        help="Image height (default: 1024)"
    )
    parser.add_argument(
        "--complexity",
        type=str,
        choices=["simple", "medium", "complex"],
        default="medium",
        help="Image complexity (default: medium)"
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    generate_test_image(
        output_path,
        size=(args.width, args.height),
        complexity=args.complexity
    )


if __name__ == "__main__":
    main()
