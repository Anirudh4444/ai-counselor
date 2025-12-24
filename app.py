from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from google import genai
import os
import traceback
import asyncio
import json
import time
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
    get_recent_summaries,
    generate_summary_from_messages,
    delete_user_history
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
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError(
        "GOOGLE_API_KEY environment variable is not set. "
        "Please set it in your .env file or environment variables."
    )
client = genai.Client(api_key=api_key)

# System prompt - optimized for speed with built-in chain-of-thought
SYSTEM_PROMPT = """You are a compassionate, professional AI counselor. Your goal is to provide a safe, non-judgmental space for users to explore their feelings.

Persona & Tone:
- Warm, empathetic, and professional
- Patient and active listener
- Uses "we" language to build partnership (e.g., "Let's explore this together")

Guidelines:
1. Validate feelings first: Always acknowledge and validate the user's emotions before offering advice.
2. Suggest practical exercises: When appropriate, suggest:
   - Breathing exercises (e.g., 4-7-8 breathing)
   - Grounding techniques (e.g., 5-4-3-2-1)
   - Mindfulness or brief meditation
3. NO MEDICATION: Never recommend, prescribe, or give advice about medication. If asked, state clearly that you cannot provide medical advice and suggest consulting a doctor.
4. Crisis Safety: If the user mentions self-harm or suicide, prioritize safety and provide emergency resources immediately.
5. After every 5 questions asked by you in the whole conversation context. Give some advice .Try to be empathetic and give pratical advice.
6.You can also try to understand youself others perspective involved in users' trauma or stress and tell user about what you think about the other other people 
6. Keep responses concise (under 200 words) but meaningful.

Respond directly to the user as if you are sitting in the room with them."""

# Reduced few-shot examples (2 instead of 5 for faster processing)
FEW_SHOT_EXAMPLES = """
Example 1:
User: "I feel like I'm drowning in work and I can't keep up."
Counselor: "What you're experiencing sounds incredibly overwhelming, and your feelings are completely valid. Feeling like you're 'falling apart' is your mind telling you that you need support. This isn't weakness - it's being human. Can you tell me more about what's been weighing on you most?"

Example 2:
User: "I had a panic attack today and I'm scared it will happen again."
Counselor: "I'm sorry you went through that - panic attacks can be terrifying. You're safe now, and what you experienced, while frightening, wasn't dangerous. When you feel one coming, try the 5-4-3-2-1 technique: name 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste. Would you like to talk about what triggered it?"
"""

FEW_SHOT_EXAMPLES="""
Example 1:
User: "I feel like I'm drowning in work and I can't keep up."
Counselor: "What you're experiencing sounds incredibly overwhelming, and your feelings are completely valid. Feeling like you're drowning is your mind telling you that you need support right now. This isn't weakness—it's being human under pressure. When we're stretched too thin, our nervous system gets overwhelmed. Can you tell me more about what's weighing on you most? Is it the volume of work, the expectations, or something else?"

Example 2:
User: "I had a panic attack today and I'm scared it will happen again."
Counselor: "I'm truly sorry you went through that—panic attacks can be absolutely terrifying, and your fear makes complete sense. You're safe now, and what you experienced, while frightening, wasn't dangerous. Your body was in survival mode, but it passed. When you feel one coming on, try this grounding technique: the 5-4-3-2-1 method. Name 5 things you see, 4 things you can touch, 3 things you hear, 2 things you smell, 1 thing you taste. This brings you back to the present moment. What do you think triggered it today?"

Example 3:
User: "My partner and I had a huge fight. They said I never listen, but I do. I don't know what to do."
Counselor: "Fights can leave us feeling hurt and misunderstood, and it sounds like you're both struggling to feel heard. When someone says 'you never listen,' what they're often expressing is 'I don't feel understood by you right now.' That's a painful place to be for both of you. Let me ask you something with curiosity, not judgment: when they were talking during the fight, what was going through your mind? Were you listening to understand, or were you thinking about how to respond?"

Example 4:
User: "I got promoted, but I feel like a fraud. Everyone else seems so confident. I don't deserve this."
Counselor: "First, congratulations—that's a real achievement. And what you're feeling? That's imposter syndrome, and it's incredibly common, especially among thoughtful, conscientious people like you. Here's the truth: the people who feel most like frauds are often the ones most committed to doing good work. Confidence and competence aren't the same thing. You were chosen for this because you have something to offer. Tell me—what specific moment or thought makes you feel most like you don't belong? Let's look at that together."

Example 5:
User: "My dad passed away 6 months ago and I still can't stop crying. Am I doing this wrong?"
Counselor: "There is no right way to grieve. Your tears are how you're honoring how much he meant to you—they're a sign of love, not weakness. Six months is actually no time at all in the journey of loss. Grief isn't linear; it comes in waves, and that's completely normal. Some days will be harder than others. I'm wondering: what do you miss most about him? And have you had moments where you've felt close to his memory, even in small ways?"

Example 6:
User: "I've been thinking about changing careers, but I'm so scared. What if I fail?"
Counselor: "The fear makes sense—change involves uncertainty, and our brains are wired to protect us from the unknown. But let me ask you something: what scares you more—taking the risk to change, or staying where you are and wondering what if? Both have costs, and both are valid. The fact that you keep thinking about this tells me something matters here. If you knew you couldn't fail, what would you want to do? And if you stayed in your current path, five years from now, would you regret not trying?"

Example 7:
User: "I feel so alone. Everyone else seems to have close friends, but I don't. What's wrong with me?"
Counselor: "Nothing is wrong with you. Loneliness is one of the most isolating feelings because it often makes us blame ourselves, but it's actually a signal that you're craving connection—which is deeply human. Many people feel this way, especially now. Connection isn't about having lots of friends; it's about depth. I'm curious: when was the last time you felt truly seen by someone? And what would it look like for you to reach out, even in a small way? Sometimes the first step toward connection is just showing up, imperfectly."

Example 8:
User: "I said something awful to my friend and now I feel terrible. They haven't replied to my apology text."
Counselor: "The fact that you feel bad tells me you care about this person and about doing right by them. That matters. Guilt—the feeling that 'I did something wrong'—is actually healthy; it's how we know our values have been crossed. What you're experiencing now is the discomfort of waiting, and that's genuinely hard. Here's what I'd gently suggest: you can control your actions (apologizing), but not their response or timeline. They may need space. In the meantime, what would it take for you to start forgiving yourself?"

Example 9:
User: "I can't seem to do anything. Even getting out of bed feels impossible. I don't know what's wrong with me."
Counselor: "What you're describing—the heaviness, the difficulty doing things—that's what depression feels like. And here's something crucial: that's not a character flaw or laziness. Depression is lying to you, telling you that you're incapable when what's actually true is that your system is depleted. You're not broken; you're struggling. Getting out of bed is an accomplishment right now. One small step—maybe opening the curtains, drinking water, or stepping outside for 30 seconds—isn't nothing. It's everything. What's one tiny thing that might feel manageable today?"

Example 10:
User: "My mom keeps criticizing everything I do. I want to set a boundary, but I feel guilty."
Counselor: "Guilt is often what keeps us stuck in unhealthy dynamics, and I want to gently challenge that: setting a boundary isn't selfish or wrong—it's actually an act of self-respect and respect for the relationship. When we allow people to treat us poorly, we're not protecting them; we're just building resentment. Your needs matter equally. What would you like to communicate to her? And more importantly, what do you need from her to feel respected? Let's think about how you might express that in a way that's honest but kind."
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
                "max_output_tokens": 2048,
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
                "max_output_tokens": 2048,  # ~200 words limit
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

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Streaming chat endpoint - optimized for speed with timing instrumentation"""
    
    async def generate_stream():
        timings = {}
        total_start = time.time()
        
        try:
            if not request.message:
                yield f"data: {json.dumps({'type': 'error', 'content': 'No message provided'})}\n\n"
                return
            
            user_id = current_user["_id"]
            session_id = request.session_id if request.session_id else str(uuid.uuid4())
            
            # Send session ID first
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            
            # Indicate thinking phase
            yield f"data: {json.dumps({'type': 'thinking', 'content': 'Thinking...'})}\n\n"
            
            # --- TIMING: Context retrieval ---
            context_start = time.time()
            
            context = ""
            if session_id not in conversations:
                conversations[session_id] = []
                
                # Retrieve relevant past context using vector search (reduced limit)
                relevant_history = retrieve_relevant_history(
                    user_id=user_id,
                    current_message=request.message,
                    limit=2,  # Reduced from 3
                    similarity_threshold=0.7
                )
                
                # Get recent session summaries for context (limit 1 for speed)
                recent_summaries = get_recent_summaries(user_id, limit=1)
                
                # Build context string (simplified)
                context_parts = []
                
                if recent_summaries:
                    context_parts.append(f"Last session: {recent_summaries[0].get('summary', '')}")
                
                if relevant_history:
                    for item in relevant_history[:2]:  # Limit to 2
                        msg = item.get('message', {})
                        message_text = msg.get('contents') or msg.get('content', '')
                        if message_text:
                            context_parts.append(f"{msg.get('role', '').title()}: {message_text[:100]}")
                
                context = "\n".join(context_parts) if context_parts else ""
            
            timings['context_retrieval'] = round(time.time() - context_start, 2)
            
            # Build conversation history (limit to last 5 exchanges for speed)
            conversation_history = "\n".join(conversations[session_id][-10:])  # Last 5 exchanges (10 lines)
            context_section = f"Previous context:\n{context}" if context else ""
            
            # --- Single optimized prompt (no separate plan step) ---
            prompt = f"""{SYSTEM_PROMPT}

{FEW_SHOT_EXAMPLES}

{context_section}

{conversation_history}

User: "{request.message}"

Counselor:"""
            
            # Signal start of response
            yield f"data: {json.dumps({'type': 'start', 'content': ''})}\n\n"
            
            # --- TIMING: Gemini API call ---
            gemini_start = time.time()
            time_to_first_token = None
            
            # Stream the response using single Gemini call
            full_response = ""
            try:
                stream_response = client.models.generate_content_stream(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={
                        "temperature": 0.7,
                        "max_output_tokens": 2048,  # Reduced from 1024
                    }
                )
                
                for chunk in stream_response:
                    if time_to_first_token is None:
                        time_to_first_token = round(time.time() - gemini_start, 2)
                    
                    if chunk.text:
                        full_response += chunk.text
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.text})}\n\n"
                        
            except Exception as stream_error:
                # Fallback to non-streaming if streaming fails
                print(f"Streaming failed, falling back: {stream_error}")
                answer_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={
                        "temperature": 0.7,
                        "max_output_tokens": 2048,
                    }
                )
                if answer_response and hasattr(answer_response, 'text') and answer_response.text:
                    full_response = answer_response.text.strip()
                    # Send in chunks for smooth appearance
                    words = full_response.split(' ')
                    for word in words:
                        yield f"data: {json.dumps({'type': 'chunk', 'content': word + ' '})}\n\n"
            
            timings['gemini_total'] = round(time.time() - gemini_start, 2)
            timings['time_to_first_token'] = time_to_first_token
            
            if not full_response:
                full_response = "I'm here to listen. Could you tell me more about what's on your mind?"
                yield f"data: {json.dumps({'type': 'chunk', 'content': full_response})}\n\n"
            
            # --- TIMING: Database writes (fire and forget, don't block) ---
            db_start = time.time()
            
            # Store messages (these run in background, don't block response)
            try:
                store_chat_message(user_id, session_id, "user", request.message)
                store_chat_message(user_id, session_id, "counselor", full_response)
            except Exception as db_error:
                print(f"DB write error (non-blocking): {db_error}")
            
            timings['db_writes'] = round(time.time() - db_start, 2)
            
            # Update in-memory conversation history (limit to 5 exchanges)
            conversations[session_id].append(f"User: {request.message}")
            conversations[session_id].append(f"Counselor: {full_response}")
            
            if len(conversations[session_id]) > 10:  # 5 exchanges = 10 lines
                conversations[session_id] = conversations[session_id][-10:]
            
            # Total time
            timings['total'] = round(time.time() - total_start, 2)
            
            # Log timing info
            print(f"\n[TIMING] Request completed:")
            print(f"  Context retrieval: {timings.get('context_retrieval', 'N/A')}s")
            print(f"  Time to first token: {timings.get('time_to_first_token', 'N/A')}s")
            print(f"  Gemini total: {timings.get('gemini_total', 'N/A')}s")
            print(f"  DB writes: {timings.get('db_writes', 'N/A')}s")
            print(f"  TOTAL: {timings.get('total', 'N/A')}s\n")
            
            # Send completion signal
            yield f"data: {json.dumps({'type': 'done', 'content': full_response})}\n\n"
            
        except Exception as e:
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

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

@app.post("/api/user/delete-history")
async def delete_history(current_user: dict = Depends(get_current_user)):
    """Delete all chat history and summaries for the current user"""
    try:
        user_id = current_user["_id"]
        
        # Delete from database
        delete_user_history(user_id)
        
        # Clear in-memory conversations for this user's sessions
        # Note: This is a simple cleanup; in a multi-worker setup, this might need a distributed cache
        sessions_to_remove = []
        for session_id, msgs in conversations.items():
            # This is an approximation since conversations dict doesn't store user_id directly
            # Ideally, we'd track user_id -> [session_ids] mapping
            pass 
        
        # For now, we rely on the client to clear the session ID and reload
        
        return {"status": "success", "message": "Chat history deleted"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

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

