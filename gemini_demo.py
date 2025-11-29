from google import genai
import os

# Get API key from environment or use hardcoded (environment is more secure)
api_key = os.environ.get("GOOGLE_API_KEY", "AIzaSyAbG9DmKFSc-4oWI3yrXS557JyigXSN2pU")
client = genai.Client(api_key=api_key)

# System prompt with counselor role and chain-of-thought instructions
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

# Few-shot examples demonstrating empathetic responses
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

def get_counselor_response(user_message, conversation_history=""):
    """
    Get empathetic counselor response using chain-of-thought and few-shot prompting
    """
    
    # Construct the full prompt with system instructions, examples, and user message
    full_prompt = f"""{SYSTEM_PROMPT}

{FEW_SHOT_EXAMPLES}

Now, respond to this person with the same level of empathy and thoughtfulness. First, think through:
1. What are they feeling?
2. What might be the underlying cause?
3. What do they need right now?
4. How should I respond?

Then provide your compassionate response.

{conversation_history}

User: "{user_message}"

Counselor's thought process:"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )
        print("-------")
        print(response)
        return response.text
    except Exception as e:
        return f"I apologize, but I'm having trouble connecting right now. Error: {e}\nPlease try again, and if you're in crisis, please reach out to a crisis helpline immediately."


def interactive_counselor():
    """
    Interactive counseling session
    """
    print("\n" + "="*60)
    print("AI Counselor - Mental Health Support Assistant")
    print("="*60)
    print("\nHello! I'm here to listen and support you.")
    print("You can talk to me about depression, anxiety, or anything on your mind.")
    print("Type 'quit' or 'exit' to end the session.\n")
    print("⚠️  Note: I'm an AI assistant, not a replacement for professional help.")
    print("If you're in crisis, please contact a crisis helpline immediately.\n")
    
    conversation_history = ""
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\nCounselor: Thank you for sharing with me today. Remember, seeking help is a sign of strength. Take care of yourself. 💙\n")
            break
        
        if not user_input:
            continue
        
        print("\nCounselor: ", end="", flush=True)
        response = get_counselor_response(user_input, conversation_history)
        print(response + "\n")
        
        # Update conversation history for context
        conversation_history += f"\nUser: {user_input}\nCounselor: {response}\n"


if __name__ == "__main__":
    # You can either run interactive mode or test with a single message
    
    # Interactive mode
    interactive_counselor()
    
    # Or test with a single message (comment out interactive_counselor() above)
    # test_message = "I've been feeling really anxious lately and can't sleep"
    # response = get_counselor_response(test_message)
    # print(f"\nUser: {test_message}")
    # print(f"\nCounselor:\n{response}")