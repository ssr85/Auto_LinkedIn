import os
import json
from agents.creative_agent import CreativeAgent
from config import settings
from utils.logger import log

def test_creative_pipeline():
    log.info("Starting Creative Generation Smoke Test")
    
    # 1. Setup Agent
    settings.client_name = "Nugen"
    agent = CreativeAgent(settings)
    
    # 2. Define Test Inputs
    test_post = "Modern Digital Transformation strategies for 2026. #Innovation #Strategy"
    brand_file = "brand_guidelines/nugen.json"
    
    if not os.path.exists(brand_file):
        log.error(f"Brand file not found: {brand_file}")
        return

    # 3. Generate Creative
    log.info("Triggering generation (Hugging Face -> Local -> Figma)...")
    result = agent.generate_creative(test_post, brand_file)
    
    # 4. Results
    log.info("Test Results:")
    log.info(json.dumps(result, indent=2))
    
    if "error" in result:
        log.error(f"Test Failed: {result['error']}")
    else:
        log.info("✓ Test Successful!")
        log.info(f"Check your Figma Project for: {settings.client_name or 'Nugen'} LinkedIn Creatives")
        log.info(f"Local file saved at: {result.get('local_path')}")

if __name__ == "__main__":
    test_creative_pipeline()
