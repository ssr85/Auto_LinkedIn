import re
from typing import Dict

class TransformationService:
    """Service for professional LinkedIn content formatting according to OG standards."""
    
    @staticmethod
    def transform_linkedin(content: str) -> str:
        """
        Applies LinkedIn-specific-formatting:
        1. Professional paragraph spacing (double line breaks).
        2. Bullet point cleaning for mobile readability.
        3. Character limit enforcement (3000 chars).
        """
        # 1. Normalize line breaks
        text = content.strip()
        
        # 2. Convert common bullet markers to clean list items with spacing
        # Handles: -, *, •, 1., etc.
        text = re.sub(r'^[ \t]*[-*•][ \t]+', '• ', text, flags=re.MULTILINE)
        
        # 3. Ensure double spacing between paragraphs but keep list items together
        paragraphs = text.split('\n')
        formatted_paragraphs = []
        
        for i, line in enumerate(paragraphs):
            line = line.strip()
            if not line:
                continue
                
            formatted_paragraphs.append(line)
            
            # If next line exists and current line is not a list item, add double spacing
            if i < len(paragraphs) - 1:
                next_line = paragraphs[i+1].strip()
                if next_line and not (line.startswith('•') or next_line.startswith('•')):
                    formatted_paragraphs.append("")

        final_text = '\n'.join(formatted_paragraphs)
        
        # 4. Limit to 3000 characters
        if len(final_text) > 3000:
            final_text = final_text[:2997] + "..."
            
        return final_text

    @staticmethod
    def prepare_layered_figma_payload(image_url: str, layout: Dict) -> Dict:
        """
        Generates a dynamic multi-layered JSON payload for Figma.
        The LLM has full control over the layer stack.
        """
        raw_layers = layout.get("layers", [])
        final_layers = []

        for layer in raw_layers:
            # Type-specific mapping
            l_type = layer.get("type", "RECTANGLE")
            
            # Base node properties
            node = {
                "type": l_type,
                "name": layer.get("name", f"{l_type} Layer"),
                "x": layer.get("x", 0),
                "y": layer.get("y", 0),
                "width": layer.get("width", 100),
                "height": layer.get("height", 100),
                "opacity": layer.get("opacity", 1.0),
                "visible": layer.get("visible", True)
            }

            # Handle Fills & Background Image Substitution
            fills = layer.get("fills", [])
            if not fills:
                # Fallback to simple color if provided at root
                default_color = layer.get("color", {"r": 1, "g": 1, "b": 1})
                if layer.get("imageUrl") == "IMAGE_URL":
                    fills = [{ "type": "IMAGE", "scaleMode": "FILL", "image_url": image_url }]
                else:
                    fills = [{ "type": "SOLID", "color": default_color }]
            else:
                # Substitution loop for IMAGE_URL placeholder
                for f in fills:
                    if f.get("type") == "IMAGE" and f.get("image_url") == "IMAGE_URL":
                        f["image_url"] = image_url

            node["fills"] = fills

            # Handle Text specific properties
            if l_type == "TEXT":
                node["characters"] = layer.get("text", "")
                node["fontSize"] = layer.get("fontSize", 48)
                node["textAlignHorizontal"] = layer.get("align", "LEFT")
                node["textAlignVertical"] = layer.get("textAlignVertical", "TOP")
                if "lineHeight" in layer:
                    node["lineHeight"] = layer["lineHeight"]

            final_layers.append(node)

        return {"layers": final_layers}
