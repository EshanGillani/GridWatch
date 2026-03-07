from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base


base = declarative_base()

class User(base):
    tableName = "users"

    id = Column(Integer, primary_key = True)
    username = Column(String)
    email = Column(String)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    
    
