from typing import Any, Dict
import json
from app.services.nlu_service import classify_intent, client as openai_client
from typing import Any, Dict
from app.core.config import settings

async def generate_smart_reply(
    task: str, 
    user_message: str, 
    context_data: Dict[str, Any]
) -> str:
    """
    Generates a natural language response based on the task and data found.
    """
    
    system_instruction = (
        "You are a helpful, professional, and concise e-commerce assistant for 'Lumenco'. "
        "Your goal is to formulate a natural response to the user based on the system's findings. "
        "Do NOT make up data. Use only the context provided."
    )

    # Tailor instructions based on task
    if task == "clarify":
        specific_instruction = (
            "The user asked about a Brand or Category, but didn't specify an action (Search/Count). "
            "1. Acknowledge the brand/category. "
            "2. If 'is_unknown' is True in context, apologize and ask for spelling. "
            "3. If known, politely ask if they want to see 'products on sale', 'check availability', or 'browse all'."
        )
    elif task == "count":
        specific_instruction = (
            "The system performed a count. "
            "State the number clearly. "
            "If the count is 0, offer to help find alternatives."
        )
    elif task == "search":
        specific_instruction = (
            "The system performed a search. "
            "Briefly introduce the results (e.g., 'I found these great options for you...'). "
            "Mention if they are on sale if the context indicates 'on_sale' was requested."
        )
    elif task == "details":
        specific_instruction = (
            "The user asked a specific question about a product. "
            "Answer the question directly using the 'product_data' provided. "
            "Be persuasive but honest."
        )
    else:
        specific_instruction = "Answer politely."

    prompt = f"""
    TASK: {task}
    USER MESSAGE: "{user_message}"
    
    SYSTEM DATA / CONTEXT:
    {json.dumps(context_data, indent=2)}
    
    INSTRUCTION:
    {specific_instruction}
    
    Write the response text (do not include JSON, just the text):
    """

    try:
        response = await openai_client.chat.completions.create(
            model=settings.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7 
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating AI reply: {e}")
        return "Here is the information you requested."