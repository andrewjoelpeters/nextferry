from fastapi import FastAPI
from .next_sailings import get_next_sailings
from .serializers import RouteSchedule
from typing import List

app = FastAPI()

@app.get("/")
def fetch_next_sailings() -> List[RouteSchedule]:
    return get_next_sailings()
