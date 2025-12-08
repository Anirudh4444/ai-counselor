from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from google import genai
import os
import traceback
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid

# Import authentication and database modules
from auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user
)
from db_config import users_collection
from vector_db import (
    store_chat_message,
    retrieve_relevant_history,
    get_session_history,
    create_session_summary,
    get_recent_summaries,
    generate_summary_from_messages
)

# Load environment variables from .env file (for local development)
load_dotenv()

app = FastAPI(title="AI Counselor API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API key from environment variable
api_key = "AIzaSyDe31S3jhYpkW3HyJimbVGQe-GKgxQv-Fs"
if not api_key:
    raise ValueError(
        "GOOGLE_API_KEY environment variable is not set. "
        "Please set it in your .env file or environment variables."
    )
client = genai.Client(api_key=api_key)

# System prompt and few-shot examples
SYSTEM_PROMPT = """You are a compassionate AI counselor specializing in mental health support for depression and anxiety. 

Your approach:
1. Listen actively and validate feelings without judgment
2. Use chain-of-thought reasoning to deeply understand the person's situation
3. Show empathy and emotional intelligence
4. Provide thoughtful, personalized responses
5. Suggest coping strategies when appropriate
6. Recognize when professional help is needed
7. Keep responses concise and focused (maximum 300 words)

IMPORTANT: Always think through your response step-by-step before answering:
- What is the person really feeling?
- What might be the underlying cause?
- What do they need most right now (validation, advice, or just to be heard)?
- How can I respond with maximum empathy and helpfulness?

IMPORTANT: Keep your response under 300 words. Be concise while maintaining warmth and empathy.
"""

FEW_SHOT_EXAMPLES = """
Example 1:
User: "I feel like I'm drowning in work and I can't keep up. Everyone else seems fine but I'm falling apart."

Counselor's thought process:
- Feeling: Overwhelmed, inadequate, isolated
- Underlying issue: Possible burnout, comparison with others, lack of support
- Need: Validation that their feelings are real and normal
- Response approach: Normalize their experience, validate feelings, offer perspective

Counselor: "What you're experiencing sounds incredibly overwhelming, and I want you to know that your feelings are completely valid. It's important to remember that what you see of others is often just the surface - many people struggle privately. Feeling like you're 'falling apart' is actually your mind and body telling you that you need support and rest. This isn't a weakness; it's a sign that you're human and that you've been carrying too much. Can you tell me more about what's been weighing on you most?"

Example 2:
User: "I don't see the point anymore. Nothing makes me happy."

Counselor's thought process:
- Feeling: Hopelessness, anhedonia (loss of pleasure), possible depression
- Underlying issue: This could indicate clinical depression - serious concern
- Need: Immediate validation, gentle exploration, professional help recommendation
- Response approach: Take seriously, show care, assess safety, encourage professional support

Counselor: "Thank you for sharing something so difficult with me. What you're describing - this feeling of emptiness and loss of joy - is a real symptom that many people with depression experience, and it's not your fault. These feelings can feel permanent, but they're not. I'm concerned about you and I want to help. First, I need to ask: are you having thoughts of hurting yourself? Also, have you been able to talk to a mental health professional? You deserve support from someone who can work with you regularly. In the meantime, I'm here to listen."

Example 3:
User: "I had a panic attack today and I'm scared it will happen again."

Counselor's thought process:
- Feeling: Fear, anxiety about anxiety, loss of control
- Underlying issue: Panic disorder symptoms, fear of recurrence
- Need: Reassurance, education about panic attacks, coping tools
- Response approach: Normalize the experience, provide psychoeducation, teach grounding

Counselor: "I'm sorry you went through that - panic attacks can be terrifying, especially when they're unexpected. First, I want you to know that you're safe now, and what you experienced, while frightening, wasn't dangerous. The fear of having another panic attack is very common and actually has a name: 'anticipatory anxiety.' Here's something that might help: panic attacks always pass, usually within 10-20 minutes. When you feel one coming, try the 5-4-3-2-1 grounding technique: name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, and 1 you taste. This helps bring you back to the present moment. Would you like to talk about what was happening before the panic attack occurred?"

Example 4:
User: "I avoid social situations because I'm terrified people will judge me. I canceled plans again today and now I feel like a failure."

Counselor's thought process:
- Feeling: Social anxiety, shame, self-criticism, isolation
- Underlying issue: Fear of negative evaluation, avoidance cycle reinforcing anxiety
- Need: Validation without enabling avoidance, gentle challenge to negative self-talk
- Response approach: Normalize the fear, address self-criticism, explore small steps forward

Counselor: "First, I want to acknowledge how brave it is that you're sharing this with me. Social anxiety is incredibly common, and the fear of judgment can feel paralyzing. But I want to gently challenge the idea that you're a 'failure' - you're someone dealing with anxiety, and that's not a character flaw. The tricky thing about avoidance is that while it brings short-term relief, it can actually strengthen the anxiety over time. Your brain learns that social situations are dangerous, even though they're not. What if we thought about this differently? Instead of 'I'm a failure for canceling,' what if it's 'I'm struggling with anxiety, and I'm working on it.' Can you tell me what specifically worries you most about these social situations?"

Example 5:
User: "My partner and I keep fighting about the same things. I don't think they understand how I feel."

Counselor's thought process:
- Feeling: Frustration, feeling unheard, relationship distress
- Underlying issue: Communication breakdown, possible unmet needs
- Need: Help identifying patterns, communication tools, validation of both perspectives
- Response approach: Explore the pattern, teach communication skills, avoid taking sides

Counselor: "Relationship conflicts, especially recurring ones, can be really exhausting and lonely. It sounds like you're feeling unheard, which is painful. I'm curious - when you say they don't understand how you feel, have you been able to express your feelings using 'I' statements? For example, instead of 'You always...' trying 'I feel... when... because...' This can help your partner hear your feelings without becoming defensive. Also, it might help to ask yourself: what need of mine isn't being met? Is it connection, respect, support, or something else? Understanding this can help you communicate more clearly. Would you be willing to tell me about one of these recurring conflicts so we can explore it together?"

"""

# Store conversation history per session
conversations = {}

# Request/Response models
class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    task: str  # "PLAN" or "ANSWER"
    prompt: str
    session_id: str
    context: Optional[str] = None

class ResetRequest(BaseModel):
    session_id: str = "default"

class EndSessionRequest(BaseModel):
    session_id: str

from pathlib import Path

# Get the directory where this script is located
BASE_DIR = Path(__file__).resolve().parent

@app.get("/")
async def read_root():
    return FileResponse(BASE_DIR / "index.html")

@app.get("/styles.css")
async def get_styles():
    return FileResponse(BASE_DIR / "styles.css")

@app.get("/script.js")
async def get_script():
    return FileResponse(BASE_DIR / "script.js")

@app.get("/login")
async def login_page():
    return FileResponse(BASE_DIR / "login.html")

@app.get("/signup")
async def signup_page():
    return FileResponse(BASE_DIR / "signup.html")

@app.get("/auth.js")
async def get_auth_script():
    return FileResponse(BASE_DIR / "auth.js")

@app.get("/auth_styles.css")
async def get_auth_styles():
    return FileResponse(BASE_DIR / "auth_styles.css")

# Authentication endpoints
@app.post("/api/signup")
async def signup(request: SignupRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = users_collection.find_one({"username": request.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        existing_email = users_collection.find_one({"email": request.email})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Hash password
        hashed_password = get_password_hash(request.password)
        
        # Create user document
        user_doc = {
            "username": request.username,
            "email": request.email,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Insert into database
        result = users_collection.insert_one(user_doc)
        user_id = str(result.inserted_id)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": request.username, "user_id": user_id}
        )
        
        return {
            "message": "User created successfully",
            "access_token": access_token,
            "token_type": "bearer",
            "username": request.username
        }
    
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/login")
async def login(request: LoginRequest):
    """Login user and return JWT token"""
    try:
        # Authenticate user
        user = authenticate_user(request.username, request.password)
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password"
            )
        
        # Update last login
        users_collection.update_one(
            {"username": request.username},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Create access token
        user_id = str(user["_id"])
        access_token = create_access_token(
            data={"sub": request.username, "user_id": user_id}
        )
        
        # Get recent summaries for context
        recent_summaries = get_recent_summaries(user_id, limit=2)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": request.username,
            "recent_summaries": recent_summaries
        }
    
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Chat endpoint with authentication and vector database integration"""
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="No message provided")
        
        user_id = current_user["_id"]
        username = current_user["username"]
        
        # Generate or use provided session ID
        session_id = request.session_id if request.session_id else str(uuid.uuid4())
        
        # Get or create conversation history for this session
        if session_id not in conversations:
            conversations[session_id] = []
            
            # Retrieve relevant past context using vector search
            relevant_history = retrieve_relevant_history(
                user_id=user_id,
                current_message=request.message,
                limit=3,
                similarity_threshold=0.7
            )
            # print("relevant_history1",relevant_history)
            
            # Get recent session summaries for context
            recent_summaries = get_recent_summaries(user_id, limit=2)
            # print("recent_summaries",recent_summaries)
            
            # Build context string
            context_parts = []
            
            if recent_summaries:
                context_parts.append("Previous session summaries:")
                for summary in recent_summaries:
                    context_parts.append(f"- {summary.get('summary', '')}")
            
            if relevant_history:
                context_parts.append("\nRelevant past conversations:")
                for item in relevant_history:
                    msg = item.get('message', {})
                    # Handle both 'content' (old) and 'contents' (new) for backward compatibility
                    message_text = msg.get('contents') or msg.get('content', '')
                    context_parts.append(f"- {msg.get('role', '').title()}: {message_text}")
            
            context = "\n".join(context_parts) if context_parts else ""
            if context:
                print(f"\n{'='*60}")
                print("CONTEXT RETRIEVED FOR NEW SESSION:")
                print(f"{'='*60}")
                print(context)
                print(f"{'='*60}\n")
            else:
                print("\n⚠️  No context retrieved - check if embeddings are being generated\n")
        else:
            context = ""
        
        conversation_history = "\n".join(conversations[session_id])
        
        # Step 1: Generate PLAN (thinking process)
        context_section = f"Context from previous sessions:\n{context}" if context else ""
        
        plan_prompt = f"""{SYSTEM_PROMPT}

{FEW_SHOT_EXAMPLES}

{context_section}

{conversation_history}

User: "{request.message}"

Think through the following step-by-step and write out your thought process:
1. What are they feeling?
2. What might be the underlying cause?
3. What do they need right now?
4. How should I respond?

Provide your internal thought process in a clear, structured way:"""
        
        # Get thinking process from Gemini
        plan_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=plan_prompt,
            config={
                "temperature": 0.7,
                "max_output_tokens": 1024,
            }
        )
        
        # Validate response
        if plan_response is None or not hasattr(plan_response, 'text') or plan_response.text is None:
            thinking_process = "Unable to generate thinking process."
        else:
            thinking_process = plan_response.text.strip()
        
        # Step 2: Generate ANSWER (final response)
        answer_prompt = f"""{SYSTEM_PROMPT}

{FEW_SHOT_EXAMPLES}

{context_section}

{conversation_history}

User: "{request.message}"

Your thought process:
{thinking_process}

Based on your analysis above, provide ONLY your compassionate counselor response directly to the user, without showing your thought process or any labels:"""
        
        # Get final response from Gemini
        answer_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=answer_prompt,
            config={
                "temperature": 0.7,
                "max_output_tokens": 1024,  # ~200 words limit
            }
        )
        
        # Validate response
        if answer_response is None or not hasattr(answer_response, 'text') or answer_response.text is None:
            counselor_response = "I apologize, but I'm having trouble generating a response right now. Please try again in a moment."
        else:
            counselor_response = answer_response.text.strip()
        
        # Store messages in vector database
        store_chat_message(user_id, session_id, "user", request.message)
        store_chat_message(user_id, session_id, "counselor", counselor_response)
        
        # Update in-memory conversation history
        conversations[session_id].append(f"User: {request.message}")
        conversations[session_id].append(f"Counselor: {counselor_response}")
        
        # Keep only last 10 exchanges to avoid token limits
        if len(conversations[session_id]) > 20:
            conversations[session_id] = conversations[session_id][-20:]
        data= {
            "task": "ANSWER",
            "prompt": counselor_response,
            "session_id": session_id,
            "context": context if context else None
        }
        # print("data1",data)    
        
        # Return response
        return {
            "task": "ANSWER",
            "prompt": counselor_response,
            "session_id": session_id,
            "context": context if context else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Print full traceback for debugging
        print("\n" + "="*60)
        print("ERROR in /chat endpoint:")
        print("="*60)
        traceback.print_exc()
        print("="*60 + "\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/end")
async def end_session(request: EndSessionRequest, current_user: dict = Depends(get_current_user)):
    """End a session and create a summary"""
    try:
        user_id = current_user["_id"]
        session_id = request.session_id
        
        # Get session history from database
        session = get_session_history(user_id, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        messages = session.get("messages", [])
        
        if len(messages) == 0:
            return {"message": "No messages to summarize"}
        
        print(f"\n{'='*60}")
        print(f"ENDING SESSION: {session_id}")
        print(f"Message count: {len(messages)}")
        print(f"First message sample: {messages[0] if messages else 'None'}")
        print(f"{'='*60}\n")
        
        # Generate summary
        summary_text = generate_summary_from_messages(messages)
        
        # Store summary in database
        create_session_summary(user_id, session_id, summary_text)
        
        # Clear in-memory conversation
        if session_id in conversations:
            del conversations[session_id]
        
        return {
            "message": "Session ended successfully",
            "summary": summary_text
        }
    
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
async def reset(request: ResetRequest):
    if request.session_id in conversations:
        del conversations[request.session_id]
    return {"message": "Conversation reset"}

if __name__ == "__main__":
    import uvicorn
   # port = int(os.environ.get("PORT", 8000))
    port=8000
    print("\n" + "="*60)
    print("AI Counselor Web Server Starting...")
    print("="*60)
    print(f"\nServer running on port: {port}")
    print("\nAPI Documentation: /docs")
    print("\nPress Ctrl+C to stop the server\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
