from fastapi import APIRouter
import requests

router = APIRouter()

OUTAGE_API = "https://api.example.com/outages"


@router.get("/outages")
def get_outages():
    response = requests.get(OUTAGE_API)
    data = response.json()

    return data