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

Example 6:
User: "It's been six months since my mom passed away and I still cry every day. People say I should be moving on by now."

Counselor's thought process:
- Feeling: Grief, sadness, pressure from others, possibly guilt
- Underlying issue: Normal grief process being invalidated by others
- Need: Permission to grieve, normalization of timeline, validation
- Response approach: Strongly validate grief, educate about grief process, challenge "should"

Counselor: "I'm so sorry for the loss of your mom. What you're experiencing is completely normal and valid. There's no timeline for grief, and anyone who suggests you 'should' be over it by six months doesn't understand how grief works. Grief isn't linear - it comes in waves, and six months is still very recent. Crying every day is your heart processing an enormous loss. Some people grieve intensely for years, and that's okay. What matters is that you're allowing yourself to feel. Grief is love with nowhere to go, and the depth of your pain reflects the depth of your love for your mom. How are you taking care of yourself during this time? And do you have people in your life who allow you to grieve without judgment?"

Example 7:
User: "I look in the mirror and hate what I see. I feel ugly and worthless compared to everyone else."

Counselor's thought process:
- Feeling: Low self-esteem, self-hatred, comparison, body image issues
- Underlying issue: Negative self-perception, possibly influenced by social media/society
- Need: Compassionate challenge to distorted thinking, self-worth beyond appearance
- Response approach: Validate pain, challenge comparison, explore self-worth sources

Counselor: "Thank you for trusting me with something so painful. The relationship we have with ourselves can be the hardest one, and I hear how much you're struggling right now. I want to ask you something: if a friend came to you and said they felt ugly and worthless, what would you say to them? Often we're much kinder to others than to ourselves. Comparison is a trap - we compare our behind-the-scenes to everyone else's highlight reel, especially on social media. But here's the truth: your worth has nothing to do with how you look. Your worth is inherent - it exists because you exist. What are some things about yourself that have nothing to do with appearance? What do you value in others - is it really just how they look, or is it their kindness, humor, intelligence, creativity?"

Example 8:
User: "I have so much to do and I can't focus on anything. My mind keeps racing and I'm getting nothing done."

Counselor's thought process:
- Feeling: Overwhelmed, scattered, anxious, possibly paralyzed by stress
- Underlying issue: Cognitive overload, possible anxiety, lack of prioritization
- Need: Grounding, practical strategies, validation of difficulty
- Response approach: Validate, provide concrete stress management tools, break down tasks

Counselor: "What you're describing is a really common response to stress and overwhelm - when we have too much to do, our brain can go into overdrive and actually make it harder to do anything. It's like having too many browser tabs open. First, take a breath with me. Let's try to calm your nervous system. Can you name three things you can see right now? Good. Now, let's make this manageable. Instead of looking at everything at once, can you identify just ONE thing that absolutely must get done today? Just one. We're going to ignore everything else for now. Once you have that one thing, break it into the smallest possible first step - something you can do in 5 minutes. Sometimes we just need to build momentum. Also, your racing mind might benefit from a 'brain dump' - write down everything you're worried about, just to get it out of your head. Does this feel doable?"
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
