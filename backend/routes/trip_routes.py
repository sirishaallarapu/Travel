from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, validator, Field
from datetime import datetime
from typing import Dict, Optional, List
import logging
import traceback

from agents.itinerary_agent import ItineraryAgent

itinerary_agent = ItineraryAgent()

from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env at startup

router = APIRouter()
logger = logging.getLogger(__name__)
agent = ItineraryAgent()

class TripRequest(BaseModel):
    from_location: str
    destination: str
    trip_type: str
    food_preference: str
    num_members: int
    budget_preference: str  # Changed from budget_per_person to budget_preference
    start_date: str
    duration: int
    flight_included: bool = False
    hotel_stars: List[str] = Field(default=["4"], description="List of hotel star ratings (e.g., '3', '4', '5')")

    @validator('start_date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('start_date must be in YYYY-MM-DD format')

    @validator('budget_preference')
    def validate_budget_preference(cls, v):
        valid_preferences = {'budget-friendly', 'mid-range', 'premium'}
        if v.lower() not in valid_preferences:
            raise ValueError('budget_preference must be one of: budget-friendly, mid-range, premium')
        return v.lower()

    @validator('hotel_stars')
    def validate_hotel_stars(cls, v):
        valid_stars = {'3', '4', '5'}  # Acceptable star ratings
        if not all(star in valid_stars for star in v):
            raise ValueError('hotel_stars must contain only valid star ratings (3, 4, or 5)')
        return v

class TripResponse(BaseModel):
    itinerary: Dict
    vibe: str
    total_budget: Optional[float]
    num_members: int
    duration: int
    hotel: Dict
    meta: Dict

@router.post("/trip")
async def trip_handler(trip: TripRequest):
    logger.info(f"Processing trip request: from_location={trip.from_location}, destination={trip.destination}, trip_type={trip.trip_type}, "
                f"food_preference={trip.food_preference}, num_members={trip.num_members}, budget_preference={trip.budget_preference}, "
                f"start_date={trip.start_date}, duration={trip.duration}, flight_included={trip.flight_included}, hotel_stars={trip.hotel_stars}")
    try:
        itinerary_data = itinerary_agent.generate_with_gemini(
            destination=trip.destination,
            start_date=trip.start_date,
            duration=trip.duration,
            trip_type=trip.trip_type,
            food_preference=trip.food_preference,
            num_members=trip.num_members,
            budget_preference=trip.budget_preference,
            flight_included=trip.flight_included,
            hotel_stars=trip.hotel_stars,
            from_location=trip.from_location,
            include_last_day_activities=trip.flight_included  # Set to true if flights are included
        )
        logger.info(f"Generated itinerary data: {itinerary_data}")
        return {
            "itinerary": itinerary_data["itinerary"],
            "vibe": itinerary_data["vibe"],
            "total_budget": itinerary_data["total_budget"],
            "num_members": itinerary_data["num_members"],
            "duration": itinerary_data["duration"],
            "flights_and_transfers": itinerary_data["flights_and_transfers"],
            "hotel": itinerary_data["hotel"],
            "activities": itinerary_data["activities"],
            "meals": itinerary_data["meals"],
            "meta": itinerary_data["meta"],
        }
    except Exception as e:
        logger.error(f"Trip generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
