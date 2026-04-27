import os
import json
import requests
import time
from typing import Dict, Optional
from utils.llm_factory import get_llm
from langchain_core.prompts import PromptTemplate
from huggingface_hub import InferenceClient
from integrations.figma_client import FigmaManager
from utils.logger import log
from utils.transformation import TransformationService

class CreativeAgent:
    """Agent responsible for generating creative assets and pushing to Figma."""

    def __init__(self, settings):
        self.settings = settings
        self.hf_client = None
        if self.settings.huggingface_api_token:
            # Initialize without default model to allow easy multi-model switching
            self.hf_client = InferenceClient(
                token=self.settings.huggingface_api_token
            )
        
        self.figma = None
        if self.settings.figma_access_token and self.settings.figma_project_id:
            self.figma = FigmaManager(
                self.settings.figma_access_token,
                self.settings.figma_project_id
            )
        
        # 3. LLM for Visual Concept Extraction
        self.visual_llm = get_llm(
            model_name=self.settings.ai_model,
            temperature=0.7
        )

        # 4. LLM for Layout Generation (Structured Design)
        # Using Qwen2.5-Coder-32B-Instruct for high-precision design JSON
        self.layout_model = "Qwen/Qwen2.5-Coder-32B-Instruct"

    def generate_creative(self, post_content: str, brand_file: str) -> Dict:
        """
        Generates a 1080x1080 creative and pushes to Figma.
        """
        try:
            if not self.hf_client:
                raise Exception("Hugging Face API token not configured")

            # 1. Load brand guidelines
            with open(brand_file, 'r') as f:
                brand = json.load(f)
            
            log.info(f"Generating creative for brand: {brand.get('name')}")

            # 2. Build Prompt
            prompt = self._build_prompt(post_content, brand)
            log.info(f"Creative Prompt: {prompt}")

            # 3. Call Hugging Face
            # text_to_image returns a PIL Image or bytes
            image = self.hf_client.text_to_image(
                prompt,
                model="black-forest-labs/FLUX.1-schnell"
            )
            
            # 4. Save locally
            client_name = self.settings.client_name or "default"
            timestamp = int(time.time())
            
            output_dir = os.path.join("output", "images", client_name)
            os.makedirs(output_dir, exist_ok=True)
            local_path = os.path.join(output_dir, f"creative_{timestamp}.png")
            
            image.save(local_path)
            log.info(f"Saved creative locally to: {local_path}")

            # 5. Generate Layered Layout (Design Schema)
            log.info("Generating editable layer layout...")
            layout = self._generate_layout(post_content, brand)

            # 6. Figma Integration (Link only)
            figma_url = "N/A"
            if self.figma:
                try:
                    file_key = self.figma.get_or_create_creatives_file(client_name)
                    figma_url = f"https://www.figma.com/file/{file_key}"
                    log.info(f"Figma file found/linked: {figma_url}")
                except Exception as fe:
                    log.error(f"Failed to link Figma: {str(fe)}")

            # 7. Generate Figma Import Payload (Plugin Bridge)
            server_url = "http://localhost:8080"
            relative_local_path = os.path.relpath(local_path, "output/images")
            plugin_image_url = f"{server_url}/{relative_local_path}"
            
            figma_payload = TransformationService.prepare_layered_figma_payload(plugin_image_url, layout)
            payload_path = os.path.join(output_dir, f"figma_import_{timestamp}.json")
            
            with open(payload_path, 'w') as f:
                json.dump(figma_payload, f, indent=2)
            log.info(f"Figma import payload generated: {payload_path}")

            return {
                "status": "success",
                "image_url": f"file://{os.path.abspath(local_path)}",
                "figma_url": figma_url,
                "local_path": local_path,
                "figma_import_json": payload_path,
                "plugin_image_url": plugin_image_url,
                "message": "Creative generated. Use the Figma Import JSON with the 'HTML to Figma' plugin."
            }

        except Exception as e:
            log.error(f"Creative generation failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "image_url": "N/A",
                "figma_url": "N/A"
            }

    def _generate_layout(self, post_content: str, brand: Dict) -> Dict:
        """
        Uses an LLM to generate spatial coordinates and styling for Figma layers.
        """
        try:
            prompt = f"""
            Task: Create a professional social media design layout for a 1080x1080 canvas.
            Brand: {brand.get('name')}
            Brand Colors: {brand.get('palette', {}).get('primary', ['#FFFFFF'])}
            Post Content: {post_content[:500]}

            Return a RAW JSON object with the following schema:
            {{
                "layers": [
                    {{
                        "type": "RECTANGLE",
                        "name": "Background",
                        "x": 0, "y": 0, "width": 1080, "height": 1080,
                        "imageUrl": "IMAGE_URL"
                    }},
                    {{
                        "type": "TEXT",
                        "name": "Headline",
                        "text": "Catchy short headline from post",
                        "x": 60, "y": 800, "width": 960, "fontSize": 72,
                        "color": {{ "r": 1, "g": 1, "b": 1 }},
                        "align": "LEFT"
                    }},
                    {{
                        "type": "RECTANGLE",
                        "name": "Glass Overlay",
                        "x": 40, "y": 780, "width": 1000, "height": 240,
                        "color": {{ "r": 1, "g": 1, "b": 1 }},
                        "opacity": 0.1
                    }}
                ]
            }}

            Rules:
            1. You MUST include one RECTANGLE with "imageUrl": "IMAGE_URL" to anchor the photographic asset.
            2. You have FULL CREATIVE FREEDOM to add more text layers, shapes, or overlays.
            3. Coordinates must be within 0-1080.
            4. JSON ONLY. No markdown. No comments.
            5. Ensure colors are in RGB (0.0-1.0).
            """

            # Call Hugging Face for layout (Qwen-Coder)
            if not self.hf_client:
                raise Exception("Hugging Face API token not configured")

            messages = [{"role": "user", "content": prompt}]
            
            # Use chat completions for better provider compatibility (e.g. nscale)
            response = self.hf_client.chat.completions.create(
                model=self.layout_model,
                messages=messages,
                max_tokens=800
            )

            # Clean and parse JSON
            clean_json = response.choices[0].message.content.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
            return json.loads(clean_json)

        except Exception as e:
            log.error(f"Failed to generate layout: {str(e)}")
            # Fallback to simple default layout
            return {
                "layers": [
                    {
                        "type": "RECTANGLE",
                        "name": "Background",
                        "x": 0, "y": 0, "width": 1080, "height": 1080,
                        "imageUrl": "IMAGE_URL"
                    },
                    {
                        "type": "TEXT",
                        "name": "Headline",
                        "text": brand.get('name', 'LinkedIn Post'),
                        "x": 50, "y": 850, "width": 980, "fontSize": 64,
                        "color": {"r": 1, "g": 1, "b": 1},
                        "align": "LEFT"
                    }
                ]
            }

    def _build_prompt(self, content: str, brand: dict) -> str:
        """Constructs a high-quality, LLM-guided prompt for FLUX.1."""
        # 1. Extract visual concept using LLM
        visual_description = self._extract_visual_concept(content, brand)
        log.info(f"Extracted Visual Concept: {visual_description}")

        # 2. Extract style and colors
        style = brand.get("visual_style", "Modern and professional")
        palette = brand.get("palette", {})
        colors = ", ".join(palette.get("primary", ["#000000"]))
        
        # 3. Assemble the final professional prompt
        prompt = f"1080x1080 professional social media creative. {visual_description}. "
        prompt += f"Visual Style: {style}. Color Palette: {colors}. "
        prompt += "High-end photography, 35mm lens, f/1.8, bokeh, cinematic volumetric lighting, "
        prompt += "hyper-realistic, 8k resolution, award-winning composition, premium feel, "
        prompt += "clean geometry, no distorted text, minimalist elegance."
        
        return prompt

    def _extract_visual_concept(self, content: str, brand: dict) -> str:
        """Uses LLM to turn abstract post content into a concrete visual scene."""
        prompt_template = PromptTemplate.from_template("""
        You are a world-class Art Director. Your goal is to convert a LinkedIn post into a 
        compelling, high-end visual scene description for an image generator (FLUX).

        **Post Content**:
        {content}

        **Brand Guidelines**:
        {brand_style}

        **Instructions**:
        1. Create a concrete, metaphorical, or industry-relevant visual scene that represents the core message.
        2. Focus on objects, lighting, and composition. 
        3. Do NOT include any text in the description (e.g., don't say "a sign that says X").
        4. Keep it high-end, premium, and professional.
        5. Describe the scene in 1-2 descriptive sentences.

        **Output Format**:
        Single descriptive sentence focusing on the visual scene.
        """)

        try:
            full_prompt = prompt_template.format(
                content=content[:1000], 
                brand_style=brand.get("visual_style", "Modern")
            )
            # Use .call() for CrewAI LLM instances
            response = self.visual_llm.call(full_prompt)
            # CrewAI LLM.call() usually returns a string directly
            return str(response).strip()
        except Exception as e:
            log.warning(f"Failed to extract visual concept: {str(e)}. Falling back to content slice.")
            return content[:200]
