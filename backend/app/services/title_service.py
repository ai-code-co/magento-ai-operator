# backend/app/services/title_service.py
from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.LLM_API_KEY)

TITLE_SYSTEM_PROMPT = """
You are a helpful assistant for an e-commerce lighting store. 
Your task is to generate a short, concise, and professional title for a chat session based on the user's first message.

RULES:
1. Maximum 4-6 words.
2. Do NOT use quotation marks.
3. Summarize the user's intent (e.g., "12V Halogen Bulb Search", "Tracking Order #123", "Warranty Inquiry").
4. If the input is just "hi" or "hello", return "General Inquiry".
"""

async def generate_chat_title(user_message: str) -> str:
    """
    Generates a short title for the chat session based on the first message.
    """
    if not user_message or len(user_message.strip()) == 0:
        return "New Chat"

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL_NAME, 
            messages=[
                {"role": "system", "content": TITLE_SYSTEM_PROMPT},
                {"role": "user", "content": f"User message: {user_message}"}
            ],
            max_tokens=15,
            temperature=0.5
        )
        
        title = response.choices[0].message.content.strip()
        

        title = title.replace('"', '').replace("'", "")
        
        return title

    except Exception as e:
        print(f"Error generating title: {e}")
       
        words = user_message.split()
        return " ".join(words[:4]) + "..." if words else "New Chat"