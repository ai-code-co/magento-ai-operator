from sqlalchemy.orm import Session
from app.models.models import Session as SessionModel
from app.models.models import Message
from typing import Optional

def create_session(db:Session,userid,title):
    new_session = SessionModel(
    userid=userid,
    title=title
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session.session_id

def save_message(db:Session,sessionid,role,content,intent: Optional[str] = None):
    new_message= Message(
        sessionref=sessionid,
        role=role,
        content=content,
        intent=intent
    )
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message  

def get_sessions(db:Session):
    return db.query(SessionModel).order_by(SessionModel.created_at.desc()).all()

def get_chats(db:Session,session_id: str):
    return db.query(Message).filter(Message.sessionref == session_id).all()

def delete_chat_session(db: Session, session_id: str):
    deleted_count = (
        db.query(SessionModel)
        .filter(SessionModel.session_id == session_id)
        .delete()
    )
    db.commit()
    return deleted_count
