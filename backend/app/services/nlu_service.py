# backend/app/services/nlu_service.py
import json
from openai import AsyncOpenAI
from app.core.config import settings
from typing import List, Optional
client = AsyncOpenAI(api_key=settings.LLM_API_KEY)

VALID_CATEGORIES= [
  "Shop All Products",
  "Light bulbs",
  "Traditional Light Bulbs",
  "LED HID Retrofit Bulbs",
  "Tube Lights",
  "LED Retrofit Kits and Components",
  "Decorative Lighting",
  "Recessed",
  "LED Recessed Lights",
  "Chandeliers",
  "1-Tier Chandeliers",
  "2-Tier + Chandeliers",
  "Globe Chandeliers",
  "Drum Chandeliers",
  "Crystal Chandeliers",
  "Cord Chandeliers",
  "Rod Chandeliers",
  "Chain Chandeliers",
  "Linear Chandeliers",
  "Fandelier",
  "Pendant Lights",
  "Mini Pendants",
  "Barn Pendant Lights",
  "Lantern Pendants",
  "Drum-Shaped Pendant Lights",
  "Bowl Pendants",
  "Rod Pendants",
  "Cord Pendants",
  "Chain Dual Mount Pendants",
  "Island Lights",
  "Ceiling Lights",
  "Flush Mounts",
  "Surface Mount",
  "Track Lights",
  "Linear tracks",
  "Fixed track lights",
  "Adjustable track lights",
  "Track heads",
  "Track parts",
  "Low Profile Ceiling Lights",
  "Wall Lights",
  "Indoor Wall Sconces",
  "Vertical Wall Sconces",
  "Bathroom Sconces",
  "Ambient Wall Lights",
  "Bathroom Vanity Lighting",
  "Semi-Flush Mounts",
  "Track Lighting",
  "Undercabinet Lights",
  "Outdoor Lights",
  "Ceiling Fans",
  "Ceiling fans 36\" and less",
  "Ceiling fans 42\"",
  "Ceiling fans 48\"",
  "Ceiling fans 52\" +",
  "Commercial Ceiling Fans",
  "Fan Accessories",
  "Mirrors",
  "Light Fixture Accessories",
  "Glassware and Canopies",
  "Lamp Accessories",
  "Lamps",
  "Table Lamps",
  "Floor Lamps",
  "Wall Lamp",
  "LED Extrusions",
  "Architectural Cylinders",
  "Lighting Ballasts, Drivers and Transformers",
  "Ballasts Fluorescents",
  "Electronic",
  "Magnetic",
  "HID Lamp Ballasts",
  "Metal Halide",
  "High Pressure Sodium",
  "Drivers",
  "Transformers",
  "Commercial Fixtures",
  "Ceiling",
  "Wall",
  "Outdoor",
  "Troffers",
  "1' x 1' LED Troffers",
  "1' x 4' LED Troffers",
  "2' x 2' LED Troffers",
  "2' x 4' LED Troffers",
  "Fluorescent Troffers",
  "Strip Lights",
  "2 feet | 18\"- 24\" Fixtures",
  "1 feet | 6\"- 12\" Fixtures",
  "3 feet | 30\"- 36\" Fixtures",
  "4 feet | 42\"- 48\" Fixtures",
  "8 feet | 90\"- 96\" Fixtures",
  "Wraparound",
  "LED wraparound",
  "Fluorescent wraparound",
  "Suspended linear lights",
  "Exit & Emergency Lights",
  "Architectural lighting",
  "Wallwashers",
  "Sign Lighting",
  "Exit Signs",
  "Emergency Lights",
  "Exit & Emergency Combinations",
  "Accessoires",
  "Accessories",
  "Architectural Lights",
  "Landscape Lighting",
  "Surface Mount Fixtures",
  "Lighting Control",
  "Dimmers",
  "Switches",
  "Switch Accessories",
  "Sensors",
  "Remote",
  "Control Module / Controllers",
  "Wireless Hub",
  "Smart Home Lighting",
  "Smart Home Kits",
  "Smart Lighting",
  "Home Monitoring",
  "Plug and Accessories",
  "Wire Accessories",
  "Specialty Lighting",
  "Solar Lights",
  "Marine lighting",
  "Marine lanterns",
  "Solar marine lanterns",
  "Port harbour lighting",
  "Grow lighting",
  "Portable Work Lights",
  "Hazardous Lighting",
  "Explosion Proof",
  "Outdoor Lighting",
  "Light Fixtures",
  "Wall Mounts",
  "Recessed Lights",
  "Bulbs",
  "LED Bulbs",
  "In-Ground Lights",
  "Pathlight",
  "Halogen Bulbs",
  "ALR Aluminum Reflector"
]

# VALID_CATEGORIES=[
#   {"id": 3, "name": "Shop All Products"},
#   {"id": 16, "name": "Light bulbs"},
#   {"id": 92, "name": "Traditional Light Bulbs"},
#   {"id": 91, "name": "LED HID Retrofit Bulbs"},
#   {"id": 90, "name": "Tube Lights"},
#   {"id": 77, "name": "LED Retrofit Kits and Components"},
#   {"id": 13, "name": "Decorative Lighting"},
#   {"id": 88, "name": "Recessed"},
#   {"id": 320, "name": "LED Recessed Lights"},
#   {"id": 47, "name": "Chandeliers"},
#   {"id": 184, "name": "1-Tier Chandeliers"},
#   {"id": 185, "name": "2-Tier + Chandeliers"},
#   {"id": 163, "name": "Globe Chandeliers"},
#   {"id": 164, "name": "Drum Chandeliers"},
#   {"id": 165, "name": "Crystal Chandeliers"},
#   {"id": 187, "name": "Cord Chandeliers"},
#   {"id": 188, "name": "Rod Chandeliers"},
#   {"id": 191, "name": "Chain Chandeliers"},
#   {"id": 308, "name": "Linear Chandeliers"},
#   {"id": 319, "name": "Fandelier"},
#   {"id": 40, "name": "Pendant Lights"},
#   {"id": 170, "name": "Mini Pendants"},
#   {"id": 171, "name": "Barn Pendant Lights"},
#   {"id": 172, "name": "Lantern Pendants"},
#   {"id": 173, "name": "Drum-Shaped Pendant Lights"},
#   {"id": 174, "name": "Bowl Pendants"},
#   {"id": 190, "name": "Rod Pendants"},
#   {"id": 189, "name": "Cord Pendants"},
#   {"id": 192, "name": "Chain Dual Mount Pendants"},
#   {"id": 309, "name": "Island Lights"},
#   {"id": 38, "name": "Ceiling Lights"},
#   {"id": 175, "name": "Flush Mounts"},
#   {"id": 300, "name": "Surface Mount"},
#   {"id": 220, "name": "Track Lights"},
#   {"id": 335, "name": "Linear tracks"},
#   {"id": 332, "name": "Fixed track lights"},
#   {"id": 333, "name": "Adjustable track lights"},
#   {"id": 334, "name": "Track heads"},
#   {"id": 336, "name": "Track parts"},
#   {"id": 186, "name": "Low Profile Ceiling Lights"},
#   {"id": 37, "name": "Wall Lights"},
#   {"id": 167, "name": "Indoor Wall Sconces"},
#   {"id": 168, "name": "Vertical Wall Sconces"},
#   {"id": 166, "name": "Bathroom Sconces"},
#   {"id": 169, "name": "Ambient Wall Lights"},
#   {"id": 87, "name": "Bathroom Vanity Lighting"},
#   {"id": 49, "name": "Semi-Flush Mounts"},
#   {"id": 95, "name": "Track Lighting"},
#   {"id": 94, "name": "Undercabinet Lights"},
#   {"id": 39, "name": "Outdoor Lights"},
#   {"id": 144, "name": "Ceiling Lights"},
#   {"id": 145, "name": "Wall Mounts"},
#   {"id": 146, "name": "Pendants"},
#   {"id": 36, "name": "Ceiling Fans"},
#   {"id": 141, "name": "Ceiling fans 36\" and less"},
#   {"id": 142, "name": "Ceiling fans 42\""},
#   {"id": 143, "name": "Ceiling fans 48\""},
#   {"id": 182, "name": "Ceiling fans 52\" +"},
#   {"id": 202, "name": "Commercial Ceiling Fans"},
#   {"id": 181, "name": "Fan Accessories"},
#   {"id": 81, "name": "Mirrors"},
#   {"id": 51, "name": "Light Fixture Accessories"},
#   {"id": 214, "name": "Glassware and Canopies"},
#   {"id": 215, "name": "Lamp Accessories"},
#   {"id": 48, "name": "Lamps"},
#   {"id": 176, "name": "Table Lamps"},
#   {"id": 177, "name": "Floor Lamps"},
#   {"id": 213, "name": "Wall Lamp"},
#   {"id": 100, "name": "LED Extrusions"},
#   {"id": 105, "name": "Architectural Cylinders"},
#   {"id": 18, "name": "Lighting Ballasts, Drivers and Transformers"},
#   {"id": 96, "name": "Ballasts Fluorescents"},
#   {"id": 208, "name": "Electronic"},
#   {"id": 209, "name": "Magnetic"},
#   {"id": 73, "name": "HID Lamp Ballasts"},
#   {"id": 229, "name": "Metal Halide"},
#   {"id": 230, "name": "High Pressure Sodium"},
#   {"id": 98, "name": "Drivers"},
#   {"id": 99, "name": "Transformers"},
#   {"id": 15, "name": "Commercial Fixtures"},
#   {"id": 82, "name": "Ceiling"},
#   {"id": 83, "name": "Wall"},
#   {"id": 84, "name": "Outdoor"},
#   {"id": 68, "name": "Troffers"},
#   {"id": 243, "name": "1' x 1' LED Troffers"},
#   {"id": 244, "name": "1' x 4' LED Troffers"},
#   {"id": 245, "name": "2' x 2' LED Troffers"},
#   {"id": 246, "name": "2' x 4' LED Troffers"},
#   {"id": 247, "name": "Fluorescent Troffers"},
#   {"id": 80, "name": "Strip Lights"},
#   {"id": 236, "name": "2 feet | 18\"- 24\" Fixtures"},
#   {"id": 235, "name": "1 feet | 6\"- 12\" Fixtures"},
#   {"id": 237, "name": "3 feet | 30\"- 36\" Fixtures"},
#   {"id": 238, "name": "4 feet | 42\"- 48\" Fixtures"},
#   {"id": 239, "name": "8 feet | 90\"- 96\" Fixtures"},
#   {"id": 72, "name": "Wraparound"},
#   {"id": 195, "name": "LED wraparound"},
#   {"id": 198, "name": "Fluorescent wraparound"},
#   {"id": 69, "name": "Suspended linear lights"},
#   {"id": 97, "name": "Exit & Emergency Lights"},
#   {"id": 201, "name": "Architectural lighting"},
#   {"id": 343, "name": "Wallwashers"},
#   {"id": 344, "name": "Sign Lighting"},
#   {"id": 231, "name": "Exit Signs"},
#   {"id": 232, "name": "Emergency Lights"},
#   {"id": 233, "name": "Exit & Emergency Combinations"},
#   {"id": 234, "name": "Accessoires"},
#   {"id": 71, "name": "Accessories"},
#   {"id": 20, "name": "Architectural Lights"},
#   {"id": 93, "name": "Landscape Lighting"},
#   {"id": 85, "name": "Surface Mount Fixtures"},
#   {"id": 21, "name": "Lighting Control"},
#   {"id": 86, "name": "Dimmers"},
#   {"id": 226, "name": "Switches"},
#   {"id": 76, "name": "Switch Accessories"},
#   {"id": 101, "name": "Sensors"},
#   {"id": 102, "name": "Remote"},
#   {"id": 103, "name": "Control Module / Controllers"},
#   {"id": 104, "name": "Wireless Hub"},
#   {"id": 22, "name": "Smart Home Lighting"},
#   {"id": 221, "name": "Smart Home Kits"},
#   {"id": 222, "name": "Smart Lighting"},
#   {"id": 223, "name": "Home Monitoring"},
#   {"id": 224, "name": "Plug and Accessories"},
#   {"id": 216, "name": "Wire Accessories"},
#   {"id": 19, "name": "Specialty Lighting"},
#   {"id": 50, "name": "Solar Lights"},
#   {"id": 30, "name": "Marine lighting"},
#   {"id": 131, "name": "Marine lanterns"},
#   {"id": 132, "name": "Solar marine lanterns"},
#   {"id": 162, "name": "Port harbour lighting"},
#   {"id": 74, "name": "Grow lighting"},
#   {"id": 118, "name": "Portable Work Lights"},
#   {"id": 123, "name": "Hazardous Lighting"},
#   {"id": 41, "name": "Explosion Proof"},
#   {"id": 6, "name": "Outdoor Lighting"},
#   {"id": 32, "name": "Light Fixtures"},
#   {"id": 130, "name": "Wall Mounts"},
#   {"id": 160, "name": "Ceiling Lights"},
#   {"id": 161, "name": "Pendant Lights"},
#   {"id": 35, "name": "Recessed Lights"},
#   {"id": 149, "name": "LED Recessed Lights"},
#   {"id": 33, "name": "Bulbs"},
#   {"id": 148, "name": "LED Bulbs"},
#   {"id": 34, "name": "Landscape Lighting"},
#   {"id": 137, "name": "In-Ground Lights"},
#   {"id": 207, "name": "Pathlight"}
# ]


 
tools = [
    {
        "type": "function",
        "function": {
            "name": "product_query",
            "description": "The primary tool to handle any user request about finding, counting, or getting details about products.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": { "type": "string", "enum": ["search", "count", "details","clarify"]},
                    "keywords": { "type": "object",
                                 "description": "Normalized product attributes. Keys MUST be valid Magento attribute codes (snake_case, no spaces). Values MUST be normalized."
                                 },
                    "sku": { "type": "string", "description": "The specific product SKU, if mentioned."},
                    "brand": { "type": "string", "description": "The brand name, if mentioned."},
                    "category": {
                        "type": "string",
                        "enum": VALID_CATEGORIES,
                        "description": "The product category or subcategory name, if mentioned by the user."
                    },
                    "question": { "type": "string", "description": "The original user text, used ONLY when task is 'clarify' or 'details'."},
                    "on_sale": { "type": "boolean", "description": "Set to true for products on sale or with special prices."},
                    "limit": { 
                        "type": "integer", 
                        "description": "The quantity of products to return. If user says 'one', 'a single', or 'top 5', set this integer value."
                    },
                    "attributes": { "type": "object", "description": "A dictionary of specific product attributes to filter by."}
                },
                "required": ["task"],
            },
        },
    }
]

BASE_SYSTEM_PROMPT = f"""
You are an e-commerce product intent classifier.
Your goal is to map user input into ONE of 4 tasks: "count", "details", "search", or "clarify".

====================
VALID LISTS
====================
Categories: {", ".join(str(VALID_CATEGORIES))}

====================
ATTRIBUTE NORMALIZATION RULES (STRICT)
====================
You MUST normalize user inputs to match the database catalog format exactly.

1. **ATTRIBUTE KEYS (Variable Names)**
   - MUST be snake_case (lowercase, underscores).
   - "Base" -> "bulb_base"
   - "Bulb Base" -> "bulb_base"
   - "Lamp Type" -> "lamp_type"
   - "Color Temperature" -> "color_temperature"
   - "Power" -> "power"
   - "Dimmable" -> `dimmable` (NOT 'features')

2. **ATTRIBUTE VALUES**
   - **Voltage**: "12 v" -> "12V"
   - **Power**: "20 w" -> "20 Watt"
   - **Dimmable**: "dimmable", "yes" -> "Dimmable"
   - **Color Temp**: "3000 k" -> "3000K"
   - **Brightness**: "300 lm" -> "300 Lumens"
   - **Base**: "g4" -> "G4"

====================
DECISION LOGIC (Follow in Order)
====================

1. **CHECK FOR "COUNT"**
   - TRIGGER: Does the user ask "how many", "total", "count", or "number of"?
   - ACTION: Set task="count". Extract brand/category if present.

2. **CHECK FOR "DETAILS"**
   - TRIGGER: Specific SKU or technical question about a specific product.
   - ACTION: Set task="details".

2b. **ATTRIBUTE-BASED SEARCH**
   - TRIGGER: User mentions specific product attributes.
   - ACTION: Set task="search".
   - **Populate `keywords` object**: Use valid snake_case KEYS and normalized VALUES.
   - **CHECK FOR LIMITS**: If the user says "one", "a single", "just one", "top 5", set the `limit` parameter.
   - **CRITICAL**: Do NOT assign a `category` unless the user explicitly names one.
   - EXAMPLE: "Give me one 12 v light with base G4" ->
    {{
      "task": "search",
      "limit": 1,
      "keywords": {{"voltage": "12V", "bulb_base": "G4"}},
      "category": null 
    }}

3. **SEARCH** (Intent: Retrieval & Browsing)
   - User command to view/list products.
   - **CHECK FOR LIMITS**: If the user says "give me one", "show me 5", set `limit`.
   - EXAMPLE: "Show me 5 outdoor lights" -> {{ "task": "search", "category": "Outdoor Lights", "limit": 5 }}

4. **CLARIFY**
   - Use only if request is vague or brand/category is unknown.

====================
CRITICAL RULES
====================
- **NO GUESSING:** If the user asks for "12V products", `category` MUST be null. Only set `category` if the user says "12V LED Bulbs".
- **Brand/Category Spelling:** Match loosely (e.g., "aaled" -> "Aaled").
- **Attributes:** Put normalized specs into `keywords` dictionary.
"""

async def classify_intent(user_message: str, brand_list: Optional[List[str]] = None,chatContext:Optional[List[str]]=None) -> dict:
    try:
        current_system_prompt = BASE_SYSTEM_PROMPT
        if brand_list:
            current_system_prompt += f"""
        ====================
        VALID BRANDS
        ====================
        {brand_list}
        ====================
        CHAT CONTEXT(if it's empty it means,user hasn't said anything yet)
        ====================
        {chatContext}
        """
       

        
        
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role":"system","content": current_system_prompt},
                {"role": "user", "content": user_message},
                
            ],
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "product_query"}}
        )
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        if tool_calls:
            arguments = json.loads(tool_calls[0].function.arguments)
            
            # strip whitespace
            if "brand" in arguments and isinstance(arguments["brand"], str):
                arguments["brand"] = arguments["brand"].strip()
                
            if brand_list and "brand" in arguments:
                user_brand = arguments["brand"].lower()
                valid_brands_lower = [b.lower().strip() for b in brand_list]
                
                if user_brand not in valid_brands_lower:
                    # Brand is  unknown
                    print(f"Brand '{user_brand}' not found in valid list.")
                    arguments = {"task": "clarify", "brand": arguments["brand"], "Unknown Brand": True}
                else:
                    pass

                    
            # delete category if it's not valid categories
            if "category" in arguments and arguments["category"] not in VALID_CATEGORIES:
                del arguments["category"]
           
            # Cleanup empty values
            for key in ["attributes", "keywords", "category", "brand"]:
                if key in arguments and not arguments[key]:
                    del arguments[key]
                   
            print("443",arguments)
            return arguments
        else:
            return {"task": "search", "keywords": user_message}
    except Exception as e:
        print(f"Error in LLM classification: {e}")
        return {"task": "error", "details": str(e)}