from app.core.database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Enum
)
from enum import Enum as PyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index= True)
    userid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False,index=True)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)
    
class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer,primary_key=True, index=True)
    
    userid = Column(
        UUID(as_uuid=True),
        ForeignKey("users.userid",ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True,nullable=False, index=True)
    title= Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    


# message role 
class MessageRole(PyEnum):
    ai = "ai"
    user = "user"
    
class Message(Base):
    __tablename__ = "messages"
    
    id=Column(Integer,primary_key=True,nullable=False, index=True)
    
    sessionref= Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.session_id",ondelete="CASCADE"),
        nullable=False,
        index=True
    )   
    
    role =Column(Enum(MessageRole),nullable=False)
    message_id = Column(UUID(as_uuid=True),default=uuid.uuid4,unique=True,nullable=False,index=True)
    
    content = Column(String,nullable=False)
    intent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True),server_default=func.now(),nullable=False)