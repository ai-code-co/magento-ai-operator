import os 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL= os.getenv("DATABASE_URL")
print("7 db url",DATABASE_URL)
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,       # Checks if connection is alive before using it
    pool_recycle=300,        # Closes connections older than 5 minutes
    connect_args={
        "connect_timeout": 10
    }
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base= declarative_base()