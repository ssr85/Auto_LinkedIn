import json
import os
import time
from agents.creative_agent import CreativeAgent
from config import Settings
from utils.logger import log

def test_layered_generation():
    settings = Settings()
    creative_agent = CreativeAgent(settings)
    
    post_content = """
    🚀 Excited to announce our new AI-powered LinkedIn automation pipeline!
    
    We've just integrated Qwen2.5-Coder to generate editable Figma layers for every creative.
    No more flat images. Total flexibility for designers.
    
    #AI #Automation #LinkedIn #Figma #Design
    """
    
    brand_file = "brand_guidelines/default.json"
    # Ensure brand file exists
    if not os.path.exists(brand_file):
        os.makedirs("brand_guidelines", exist_ok=True)
        with open(brand_file, "w") as f:
            json.dump({
                "name": "Antigravity AI",
                "primary_color": "#000000",
                "secondary_color": "#FFD700",
                "visual_style": "Futuristic and high-tech",
                "palette": {
                    "primary": ["#000000", "#1A1A1A"],
                    "accent": ["#FFD700"]
                }
            }, f)

    log.info("Starting layered creative generation test...")
    result = creative_agent.generate_creative(post_content, brand_file)
    
    if result["status"] == "success":
        log.info("✅ Layered Creative Generated Successfully!")
        log.info(f"Image Path: {result['local_path']}")
        log.info(f"Figma Import JSON: {result['figma_import_json']}")
        
        # Verify JSON content
        with open(result['figma_import_json'], 'r') as f:
            payload = json.load(f)
            layers = payload.get("layers", [])
            log.info(f"Generated {len(layers)} layers (including background image).")
            for i, layer in enumerate(layers):
                log.info(f"Layer {i}: {layer.get('type')} - {layer.get('name', 'N/A')}")
    else:
        log.error(f"❌ Generation Failed: {result.get('error')}")

if __name__ == "__main__":
    test_layered_generation()
