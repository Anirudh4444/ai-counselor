from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserModel(BaseModel):
    """User model for database storage"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    username: str
    email: EmailStr
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str  # "user" or "counselor"
    contents: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatHistoryModel(BaseModel):
    """Chat history model with vector embeddings"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    session_id: str
    messages: List[ChatMessage]
    embeddings: Optional[List[List[float]]] = None  # Vector embeddings for each message
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class SessionSummaryModel(BaseModel):
    """Session summary model with vector embedding"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    session_id: str
    summary: str
    summary_embedding: Optional[List[float]] = None  # Vector embedding of summary
    session_date: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class TokenData(BaseModel):
    """JWT token data"""
    username: Optional[str] = None
    user_id: Optional[str] = None
