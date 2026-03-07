
from fastapi import FastAPI
from app.models.models import Base
from app.database import engine
from app.routes import user_routes
from app.routes import report_routes
from app.routes import outage_routes


app = FastAPI()

app.include_router(report_routes.router)

app.include_router(outage_routes.router)

Base.metadata.create_all(bind=engine)

app.include_router(user_routes.router)

@app.get("/")
def root():
    return {"message": "GridWatch API is running"}