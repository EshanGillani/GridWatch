from models import base
from database.py import engine
import models

base.metadata.create_all(bind=engine)

