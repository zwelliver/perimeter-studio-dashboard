#!/usr/bin/env python3
"""
Test script for FLUX.2 Pro backdrop generation
Creates a sample virtual production backdrop to verify quality
"""

import os
import base64
import requests
import replicate
from dotenv import load_dotenv

# Load environment
load_dotenv(".env")

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

# Test prompts (similar to what Claude Opus would generate)
test_prompts = [
    "Modern office space with large windows, soft natural lighting, minimalist furniture, neutral tones, photorealistic, no people",
    "Cozy living room with warm ambient lighting, comfortable sofa, wood floors, indoor plants, photorealistic, no people",
    "Professional studio environment, white walls, soft diffused lighting, clean minimal design, photorealistic, no people"
]

def generate_flux_image(prompt, filename):
    """Generate a single image with FLUX.2 Pro"""
    print(f"\n{'='*60}")
    print(f"Generating: {filename}")
    print(f"Prompt: {prompt[:80]}...")
    print(f"{'='*60}")

    try:
        print("⏳ Calling FLUX.2 Pro API...")
        output = replicate.run(
            "black-forest-labs/flux-2-max",
            input={
                "prompt": prompt,
                "aspect_ratio": "16:9",  # Wide format for virtual production
                "output_format": "png",
                "output_quality": 100,
                "safety_tolerance": 2,
            }
        )

        # Download the image
        if output:
            image_url = str(output)
            print(f"📥 Downloading from: {image_url[:50]}...")

            img_response = requests.get(image_url, timeout=30)
            img_response.raise_for_status()

            # Save to file
            with open(filename, 'wb') as f:
                f.write(img_response.content)

            file_size = len(img_response.content) / 1024  # KB
            print(f"✅ SUCCESS! Saved to {filename} ({file_size:.1f} KB)")
            return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

    return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("FLUX.2 Pro Virtual Production Backdrop Test")
    print("="*60)
    print("\nGenerating 3 test backdrops for Marble 3D environment creation...")
    print("This will take ~30-60 seconds per image.\n")

    success_count = 0

    for i, prompt in enumerate(test_prompts, 1):
        filename = f"test_backdrop_{i}_flux.png"
        if generate_flux_image(prompt, filename):
            success_count += 1

    print("\n" + "="*60)
    print(f"RESULTS: {success_count}/{len(test_prompts)} images generated successfully")
    print("="*60)

    if success_count > 0:
        print("\n✅ Test images saved in current directory:")
        print("   - test_backdrop_1_flux.png (office)")
        print("   - test_backdrop_2_flux.png (living room)")
        print("   - test_backdrop_3_flux.png (studio)")
        print("\n💡 Next step: Upload these to Marble to test 3D environment generation quality!")
    else:
        print("\n❌ No images generated. Check your REPLICATE_API_TOKEN in .env file.")
