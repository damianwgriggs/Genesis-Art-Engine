import google.generativeai as genai
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageColor
import io
import json

# --- CONFIGURATION ---
GEMINI_API_KEY = "YOURAPIKEY"

genai.configure(api_key=GEMINI_API_KEY)
# Using the pro model for better grasp of complex instructions like transparency
model = genai.GenerativeModel('gemini-2.5-flash') 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/generate")
def generate_art(prompt: str = "creation of light"):
    print(f"🎤 Genesis Command: '{prompt}'")
    
    # 1. The "Genesis" Prompt
    # We teach the AI about the 8-digit HEX code for transparency (Alpha Channel).
    ai_instruction = f"""
    You are the "Genesis Engine," a creator of ethereal, vector-based universes.
    Visualize this concept: "{prompt}".

    Crucial Upgrade: You now control OPACITY.
    Use 8-digit HEX codes (#RRGGBBAA). The last two digits (AA) control transparency:
    - "FF" = Solid (e.g., #FF0000FF is solid red)
    - "80" = 50% transparent (e.g., #0000FF80 is see-through blue water)
    - "20" = Mostly ghostly transparent

    Create a complex scene by layering transparent shapes over each other to create depth, light, and atmosphere.

    Return JSON with:
    1. "background_color": 8-digit hex string representing the void/sky.
    2. "shapes": A list of shape objects, ordered from back to front. Each has:
       - "color": 8-digit hex string representing fill and opacity.
       - "points": A list of [x, y] coordinates defining the polygon.

    CANVAS: 800x600.
    Let your polygons overlap to create new colors.
    Return ONLY valid JSON.
    """
    
    try:
        response = model.generate_content(ai_instruction)
        cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(cleaned_text)
        print("🤖 Ethereal geometry calculated.")
        
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        data = {"background_color": "#000000FF", "shapes": []}

    # --- THE HIGH-DEFINITION RENDERER ---
    width, height = 800, 600
    
    # 1. Start with a fully transparent base canvas (RGBA mode)
    base_image = Image.new('RGBA', (width, height), (0,0,0,0))

    # 2. Draw the background as the first layer
    bg_color_hex = data.get("background_color", "#000000FF")
    # We create a layer just for the background
    bg_layer = Image.new('RGBA', (width, height), (0,0,0,0))
    bg_draw = ImageDraw.Draw(bg_layer)
    bg_draw.rectangle([0, 0, width, height], fill=bg_color_hex)
    # Composite base + background
    base_image = Image.alpha_composite(base_image, bg_layer)

    # 3. Layer every shape on top using Alpha Composition
    for shape in data.get("shapes", []):
        color_hex = shape.get("color", "#FFFFFF80")
        raw_points = shape.get("points", [])
        polygon_points = [tuple(p) for p in raw_points]
        
        if len(polygon_points) > 2:
            # A. Create a temporary transparent layer for this one shape
            shape_layer = Image.new('RGBA', (width, height), (0,0,0,0))
            shape_draw = ImageDraw.Draw(shape_layer)
            
            # B. Draw the shape onto the temporary layer
            # Pillow handles the 8-digit hex string automatically here
            shape_draw.polygon(polygon_points, fill=color_hex)
            
            # C. Merge this layer down onto the main image
            base_image = Image.alpha_composite(base_image, shape_layer)

    # 4. Final Export (Convert back to RGB for standard PNG viewing)
    final_image = base_image.convert('RGB')
    
    buffer = io.BytesIO()
    final_image.save(buffer, format="PNG")
    buffer.seek(0)
    return Response(content=buffer.getvalue(), media_type="image/png")
