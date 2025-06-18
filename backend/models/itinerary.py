from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TripRequest(BaseModel):
    destination: str
    trip_type: str
    duration: int
    food_preference: str
    num_members: int
    budget: float
    start_date: datetime
    end_date: datetime
    source: Optional[str] = None

class TripResponse(BaseModel):
    itinerary: str
    vibe: Optional[str] = None