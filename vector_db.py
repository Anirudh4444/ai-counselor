from typing import List, Dict, Optional
from datetime import datetime
from google import genai
import os
from dotenv import load_dotenv
from db_config import chat_history_collection, session_summary_collection
from models import ChatMessage, ChatHistoryModel, SessionSummaryModel
import numpy as np

# Load environment variables
load_dotenv()

# Initialize Gemini client for embeddings
api_key = "AIzaSyDe31S3jhYpkW3HyJimbVGQe-GKgxQv-Fs"
if not api_key:
    raise ValueError("GOOGLE_API_KEY environment variable is not set")

client = genai.Client(api_key=api_key)


def generate_embedding(text: str) -> List[float]:
    """Generate vector embedding for text using Gemini API"""
    try:
        # Use Gemini's embedding model
        result = client.models.embed_content(
            model="models/text-embedding-004",
            contents=text
        )
        # print("embeddings",result, result.embeddings[0].values)
        return result.embeddings[0].values
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    if not vec1 or not vec2:
        return 0.0
    
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def store_chat_message(
    user_id: str,
    session_id: str,
    role: str,
    content: str
) -> None:
    """Store a chat message with its embedding in the database"""
    try:
        # Generate embedding for the message
        embedding = generate_embedding(content)
        
        # Create message object
        message = ChatMessage(
            role=role,
            contents=content,
            timestamp=datetime.utcnow()
        )
        
        # Check if session already exists
        existing_session = chat_history_collection.find_one({
            "user_id": user_id,
            "session_id": session_id
        })
        
        if existing_session:
            # Append to existing session
            chat_history_collection.update_one(
                {"user_id": user_id, "session_id": session_id},
                {
                    "$push": {
                        "messages": message.dict(),
                        "embeddings": embedding
                    },
                    "$set": {"timestamp": datetime.utcnow()}
                }
            )
        else:
            # Create new session
            chat_history = ChatHistoryModel(
                user_id=user_id,
                session_id=session_id,
                messages=[message],
                embeddings=[embedding] if embedding else [],
                timestamp=datetime.utcnow()
            )
            chat_history_collection.insert_one(chat_history.dict(by_alias=True, exclude={"id"}))
        
        print(f"✓ Stored message for user {user_id} in session {session_id}")
    except Exception as e:
        print(f"Error storing chat message: {e}")


def retrieve_relevant_history(
    user_id: str,
    current_message: str,
    limit: int = 5,
    similarity_threshold: float = 0.7
) -> List[Dict]:
    """Retrieve relevant chat history using vector similarity search"""
    try:
        # Generate embedding for current message
        query_embedding = generate_embedding(current_message)
        
        if not query_embedding:
            return []
        
        # Get all chat history for user
        all_sessions = chat_history_collection.find({"user_id": user_id})
        
        relevant_messages = []
        
        for session in all_sessions:
            messages = session.get("messages", [])
            embeddings = session.get("embeddings", [])
            
            for i, (message, embedding) in enumerate(zip(messages, embeddings)):
                if not embedding:
                    continue
                
                # Calculate similarity
                similarity = cosine_similarity(query_embedding, embedding)
                
                if similarity >= similarity_threshold:
                    relevant_messages.append({
                        "message": message,
                        "similarity": similarity,
                        "session_id": session.get("session_id"),
                        "timestamp": message.get("timestamp")
                    })
        
        # Sort by similarity and return top results
        relevant_messages.sort(key=lambda x: x["similarity"], reverse=True)
        # Debug: print(f"Found {len(relevant_messages)} relevant messages")
        return relevant_messages[:limit]
    
    except Exception as e:
        print(f"Error retrieving relevant history: {e}")
        return []


def get_session_history(user_id: str, session_id: str) -> Optional[Dict]:
    """Get all messages from a specific session"""
    try:
        session = chat_history_collection.find_one({
            "user_id": user_id,
            "session_id": session_id
        })
        
        if session:
            session["_id"] = str(session["_id"])
        # Debug: session retrieved
        
        return session
    except Exception as e:
        print(f"Error getting session history: {e}")
        return None


def create_session_summary(
    user_id: str,
    session_id: str,
    summary_text: str
) -> None:
    """Create and store a session summary with its embedding"""
    try:
        # Get session to count messages
        session = get_session_history(user_id, session_id)
        message_count = len(session.get("messages", [])) if session else 0
        
        # Generate embedding for summary
        summary_embedding = generate_embedding(summary_text)
        
        # Create summary object
        summary = SessionSummaryModel(
            user_id=user_id,
            session_id=session_id,
            summary=summary_text,
            summary_embedding=summary_embedding,
            session_date=datetime.utcnow(),
            message_count=message_count
        )
        
        # Store in database
        session_summary_collection.insert_one(summary.dict(by_alias=True, exclude={"id"}))
        print(f"✓ Created session summary for user {user_id}")
    
    except Exception as e:
        print(f"Error creating session summary: {e}")


def get_recent_summaries(user_id: str, limit: int = 3) -> List[Dict]:
    """Get recent session summaries for a user"""
    try:
        summaries = session_summary_collection.find(
            {"user_id": user_id}
        ).sort("session_date", -1).limit(limit)
        
        result = []
        for summary in summaries:
            summary["_id"] = str(summary["_id"])
            result.append(summary)
        
        return result
    except Exception as e:
        print(f"Error getting recent summaries: {e}")
        return []


def generate_summary_from_messages(messages: List[Dict]) -> str:
    """Generate a summary of the conversation using Gemini"""
    try:
        # Prepare conversation text with backward compatibility
        conversation_lines = []
        for msg in messages:
            role = msg.get('role', 'unknown').title()
            content = msg.get('contents') or msg.get('content', '')
            if content:  # Only include messages with actual content
                conversation_lines.append(f"{role}: {content}")
        
        conversation = "\n".join(conversation_lines)
        
        # Validate we have actual content to summarize
        if not conversation or len(conversation.strip()) < 10:
            print("⚠️  Not enough content to generate meaningful summary")
            return "Brief conversation session completed."
        
        print(f"\n{'='*60}")
        print("GENERATING SUMMARY FROM CONVERSATION:")
        print(f"{'='*60}")
        print(f"Message count: {len(conversation_lines)}")
        print(f"Conversation preview: {conversation[:200]}...")
        print(f"{'='*60}\n")
        
        # Create summary prompt - simplified to reduce token usage
        prompt = f"""Summarize this mental health counseling conversation in 3-4 sentences. Include: the main issue, people involved (with names), emotions expressed, and any advice given.

Conversation:
{conversation}

Summary:"""
        
        # Generate summary using Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.5,
                "max_output_tokens": 1024,
            }
        )
        print("response",response)
        
        if response and hasattr(response, 'text') and response.text:
            summary = response.text.strip()
            print(f"✓ Generated summary: {summary}\n")
            return summary
        else:
            return "Session completed with discussion of mental health concerns."
    
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Session completed."

