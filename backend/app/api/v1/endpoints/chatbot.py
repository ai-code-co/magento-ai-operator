# backend/app/api/v1/endpoints/chatbot.py
import json
from fastapi import APIRouter
from app.schemas.chatbot import ChatRequest, ChatResponse
from app.services.nlu_service import classify_intent, client as openai_client
from app.services.magento_wrapper import magento_service
from app.services.title_service import generate_chat_title 
from app.core.config import settings
import traceback
from app.crud.crud import create_session,save_message,get_chats,get_sessions,delete_chat_session
from app.core.database import SessionLocal
from app.services.generate_smart_reply import generate_smart_reply
import json



router = APIRouter()
@router.post("/chat")
async def handle_chat(request: ChatRequest):
    if not request.credentials:
        return ChatResponse(response_text="Please connect to a store first.")

    new_session_id=None
    session_id = request.session_id or None

    # save a user messsage to db 
    db = SessionLocal()
    if not request.session_id:
        
        try:
            if request.title:
                session_title = request.title
            else:
                session_title = await generate_chat_title(request.message)
            new_session_id = create_session(
            db=db,
            userid=request.user_id,
            title=session_title
            )
            
            # save message
            save_message(
                db=db,
                sessionid=new_session_id,
                role="user",
                content=request.message
            )
        finally:
            db.close()    
    else:
       
        try:
            # save message
            save_message(
                db=db,
                sessionid=session_id,
                role="user",
                content=request.message
            )
        finally:
            db.close()    
    
    active_session_id = session_id or new_session_id
    brand_list = []
    try:
        brand_options = magento_service._make_request(
            method="GET",
            endpoint="/products/attributes/manufacturer/options",
            credentials=request.credentials.dict(),
            query_params="?searchCriteria[currentPage]=1" 
        )
        brand_list = [
           b["label"].strip().lower()
           for b in brand_options
           if isinstance(b, dict) and b.get("label")
        ]

    except Exception as e:
        print(f"Warning: Could not fetch brands: {e}")

    # print("75 session id",new_session_id or session_id)
    messages= get_chats(db,session_id=new_session_id or session_id)
    chatContext=[]
    for msg in messages:
         chatContext.append({
            "id":msg.id,
            "role":msg.role,
            "content":msg.content,
            "intent":msg.intent,
            "createdAt":msg.created_at
        })


    params = await classify_intent(request.message,brand_list,chatContext)
    task = params.get("task")

    if task == "clarify":
        brand_name = params.get("brand", None)
        unknown_brand= params.get("Unknown Brand",False)
        
        # if unknown_brand:
        #     response_text=(
        #         f"Sorry, we don’t carry products from **{brand_name}**. Can you check the brand name or choose another?"
        #     )
        # else:
        #     response_text = (
        #     f"I see you are interested in **{brand_name}**. \n\n"
        #     f"What would you like to know?\n"
        #     f"- Are you looking for **products on sale**?\n"
        #     f"- Do you want to see **what products are available**?\n"
        #     f"- Do you want to know **how many items** we carry?\n\n"
        #     f"Please let me know how I can help!"
        # )
        
        ai_reply = await generate_smart_reply(
            task="clarify",
            user_message=request.message,
            context_data={
                "brand_detected": brand_name,
                "is_unknown": unknown_brand
            }
        )
        
        # save message
        save_message(
            db=db,
            sessionid=active_session_id,
            role="ai",
            content=ai_reply
        )
        return ChatResponse(response_text=ai_reply, intent="clarification_needed",new_session_id=new_session_id)
        
    
    if task == "details" and not params.get("question"):
        task = "search"

    if task == "error":
        # save message
        save_message(
            db=db,
            sessionid=active_session_id,
            role="ai",
            content=f"Sorry, I had an issue understanding that. Details: {params.get('details')}"
        )
        return ChatResponse(response_text=f"Sorry, I had an issue understanding that. Details: {params.get('details')}",new_session_id=new_session_id)

    try:
        if task == "search" or task == "count":
            result = magento_service.product_query(params, request.credentials.dict())          
            
            if task == "count":
                count = result.get("total_count", 0)
                # summary_parts = []
                # if params.get("brand"): summary_parts.append(f"for the brand '{params['brand']}'")
                # if params.get("keywords"): summary_parts.append(f"matching '{params['keywords']}'")
                # summary_text = " ".join(summary_parts)
                # return ChatResponse(response_text=f"I found a total of **{count}** products {summary_text}.")
                
                # print("123 on_sale",params.get("on_sale"))
                # print("124 category_filter",params.get("brand"))
                # print("125 category_filter",params.get("category"))
                ai_reply = await generate_smart_reply(
                    task="count",
                    user_message=request.message,
                    context_data={
                        "count": count,
                        "brand_filter": params.get("brand"),
                        "category_filter": params.get("category"),
                        "on_sale": params.get("on_sale")
                    }
                )
                # save message
                save_message(
                  db=db,
                  sessionid=active_session_id,
                  role="ai",
                  content=ai_reply
                )
                return ChatResponse(response_text=ai_reply,new_session_id=new_session_id)

            else:
                # search
                products = result.get("items", [])
                # print("164 prouducts",products)
                total_count = result.get("total_count", 0)
                
                if not products and total_count==0:
                    # save message
                    save_message(
                    db=db,
                    sessionid=active_session_id,
                    role="ai",
                    content="I couldn't find any products matching your search."
                    )
                    return ChatResponse(response_text="I couldn't find any products matching your search.",new_session_id=new_session_id)
                
                # response_text = f"Here are the top {len(products)} of {total_count} results:"
                # return ChatResponse(response_text=response_text, intent="search_products_result", data=products)
                
                ai_reply = await generate_smart_reply(
                    task="search",
                    user_message=request.message,
                    context_data={
                        "results_count": len(products),
                        "total_available": total_count,
                        "brand_filter": params.get("brand"),
                        "on_sale": params.get("on_sale")
                    }
                )
                content = json.dumps({
                    "text": ai_reply,
                    "products": products
                })
                # save message
                save_message(
                    db=db,
                    sessionid=active_session_id,
                    role="ai",
                    content=content,
                    intent="search_products_result"
                )
                
                return ChatResponse(
                    response_text=ai_reply, 
                    intent="search_products_result", 
                    data=products,
                    new_session_id=new_session_id
                )

        elif task == "details":
            # ... (rest of the file is correct and unchanged)
            sku = params.get("sku") or params.get("keywords")
            if not sku and request.context:
                context = request.context
                if isinstance(context, list) and context: sku = context[0].get('sku')
                elif isinstance(context, dict): sku = context.get('sku')
            question = params.get("question", request.message)
           
            if not sku: 
                # save message
                save_message(
                    db=db,
                    sessionid=active_session_id,
                    role="ai",
                    content="Please specify a product SKU to get details, or ask about a product I just found."
                )
                return ChatResponse(response_text="Please specify a product SKU to get details, or ask about a product I just found.",new_session_id=new_session_id)
            
            product_data = magento_service.get_product_details_by_sku(sku, request.credentials.dict())
            
            if not product_data: 
                 # save message
                save_message(
                    db=db,
                    sessionid=active_session_id,
                    role="ai",
                    content=f"Sorry, I couldn't find data for SKU '{sku}'."
                )
                return ChatResponse(response_text=f"Sorry, I couldn't find data for SKU '{sku}'.",new_session_id=new_session_id)
            
            clean_attributes = { 
                attr.get("attribute_code"): attr.get("value") 
                for attr in product_data.get("custom_attributes", []) 
                if isinstance(attr, dict) 
            }
            ai_reply = await generate_smart_reply(
                task="details",
                user_message=question,
                context_data={
                    "name": product_data.get("name"),
                    "sku": product_data.get("sku"),
                    "price": product_data.get("price"),
                    "attributes": clean_attributes
                }
            )
            # save message
            save_message(
                db=db,
                sessionid=active_session_id,
                role="ai",
                content=ai_reply
            )
            return ChatResponse(response_text=ai_reply, data=product_data,new_session_id=new_session_id)
           
            # system_prompt = ("You are a friendly and knowledgeable e-commerce expert from Lumenco...")
            # context_summary = {"name": product_data.get("name"), "sku": product_data.get("sku"), "price": product_data.get("price"), "attributes": { attr.get("attribute_code"): attr.get("value") for attr in product_data.get("custom_attributes", []) if isinstance(attr, dict) }}
            # user_prompt = f"PRODUCT DATA:\n```json\n{json.dumps(context_summary, indent=2)}\n```\n\nUSER QUESTION:\n{question}"
            # response = await openai_client.chat.completions.create(model=settings.LLM_MODEL_NAME, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], temperature=0.2)
            # answer = response.choices[0].message.content
            #return ChatResponse(response_text=answer, data=product_data)
        
        else:
            # save message
            save_message(
                    db=db,
                    sessionid=active_session_id,
                    role="ai",
                    content="I'm not sure how to handle that task."
            )
            return ChatResponse(response_text="I'm not sure how to handle that task.",new_session_id=new_session_id)

    except Exception as e:
        print(f"An unexpected error occurred in the chat endpoint: {e}")
        traceback.print_exc()
         # save message
        save_message(
                    db=db,
                    sessionid=active_session_id if 'active_session_id' in locals() else None,
                    role="ai",
                    content=f"An error occurred. Please check the server logs for details."
        )
        return ChatResponse(response_text=f"An error occurred. Please check the server logs for details.",new_session_id=new_session_id)
    
    
@router.get("/allsessions") 
async def get_all_sessions():
    db = SessionLocal()
    return get_sessions(db)    

@router.get("/allchats/{session_id}")
async def get_all_chat(session_id:str):
    db=SessionLocal()
    return get_chats(db,session_id=session_id)

@router.delete("/delete/{session_id}")
async def delete_chat(session_id:str):
    try:
        db=SessionLocal()
        return delete_chat_session(db,session_id=session_id)
    finally:
        db.close()
    
