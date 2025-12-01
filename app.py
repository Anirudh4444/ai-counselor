from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai
import os
import traceback
from dotenv import load_dotenv

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

# System prompt and few-shot examples
SYSTEM_PROMPT = """You are a compassionate AI counselor specializing in mental health support for depression and anxiety. 

Your approach:
1. Listen actively and validate feelings without judgment
2. Use chain-of-thought reasoning to deeply understand the person's situation
3. Show empathy and emotional intelligence
4. Provide thoughtful, personalized responses
5. Suggest coping strategies when appropriate
6. Recognize when professional help is needed

IMPORTANT: Always think through your response step-by-step before answering:
- What is the person really feeling?
- What might be the underlying cause?
- What do they need most right now (validation, advice, or just to be heard)?
- How can I respond with maximum empathy and helpfulness?
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
"""

# Store conversation history per session
conversations = {}

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ChatResponse(BaseModel):
    task: str  # "PLAN" or "ANSWER"
    prompt: str
    session_id: str

class ResetRequest(BaseModel):
    session_id: str = "default"

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

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="No message provided")
        
        # Get or create conversation history
        if request.session_id not in conversations:
            conversations[request.session_id] = []
        
        conversation_history = "\n".join(conversations[request.session_id])
        
        # Step 1: Generate PLAN (thinking process)
        plan_prompt = f"""{SYSTEM_PROMPT}

{FEW_SHOT_EXAMPLES}

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
                "max_output_tokens": 512,
            }
        )
        
        # Validate response
        if plan_response is None or not hasattr(plan_response, 'text') or plan_response.text is None:
            print("Warning: PLAN response is None or invalid")
            print(f"plan_response type: {type(plan_response)}")
            print(f"plan_response value: {plan_response}")
            if plan_response is not None:
                print(f"plan_response attributes: {dir(plan_response)}")
            thinking_process = "Unable to generate thinking process."
        else:
            thinking_process = plan_response.text.strip()
            print(f"✓ PLAN generated successfully ({len(thinking_process)} chars)")
        
        # Step 2: Generate ANSWER (final response)
        answer_prompt = f"""{SYSTEM_PROMPT}

{FEW_SHOT_EXAMPLES}

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
                "max_output_tokens": 1024,
            }
        )
        
        # Validate response
        if answer_response is None or not hasattr(answer_response, 'text') or answer_response.text is None:
            print("Error: ANSWER response is None or invalid")
            print(f"answer_response type: {type(answer_response)}")
            print(f"answer_response value: {answer_response}")
            if answer_response is not None:
                print(f"answer_response attributes: {dir(answer_response)}")
            counselor_response = "I apologize, but I'm having trouble generating a response right now. Please try again in a moment."
        else:
            counselor_response = answer_response.text.strip()
            print(f"✓ ANSWER generated successfully ({len(counselor_response)} chars)")
        
        # Update conversation history (only with the final answer, not the thinking)
        conversations[request.session_id].append(f"User: {request.message}")
        conversations[request.session_id].append(f"Counselor: {counselor_response}")
        
        # Keep only last 10 exchanges to avoid token limits
        if len(conversations[request.session_id]) > 20:
            conversations[request.session_id] = conversations[request.session_id][-20:]
        
        # Return only the ANSWER (PLAN was used internally to generate better response)
        return {
            "task": "ANSWER",
            "prompt": counselor_response,
            "session_id": request.session_id
        }
        
    except Exception as e:
        # Print full traceback for debugging
        print("\n" + "="*60)
        print("ERROR in /chat endpoint:")
        print("="*60)
        traceback.print_exc()
        print("="*60 + "\n")
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
