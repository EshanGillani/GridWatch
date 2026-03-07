from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

database_url = "postgresql://postgres:MozzSticks2023!@localhost:5432/gridwatch"

engine = create_engine(database_url)

SessionLocal = sessionmaker(
    autocommit = False,
    autoflush = False,
    bind = engine
)

# creates the database connection and session system for interaction with the PostgreSQL database.
