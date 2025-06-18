from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from ..models.itinerary import TripRequest
from ..agents.itinerary_builder import ItineraryBuilder
from ..agents.vibe_matcher import get_trip_vibe  # Optional if you want to add vibe
import os

router = APIRouter()

@router.post("/api/trip")
async def generate_itinerary(trip: TripRequest):
    try:
        builder = ItineraryBuilder(
            destination=trip.destination,
            start_date=str(trip.start_date),
            days=trip.duration,
            budget=trip.budget
        )
        itinerary_dict = builder.build_itinerary()

        vibe = get_trip_vibe({  # Optional vibe logic
            "destination": trip.destination,
            "trip_type": trip.trip_type
        })

        pdf_path = f"itinerary_{trip.destination.lower().replace(' ', '_')}_{trip.start_date.strftime('%Y%m%d')}.pdf"

        return {
            "itinerary": itinerary_dict,
            "vibe": vibe,
            "pdf_path": pdf_path if os.path.exists(pdf_path) else "",
            "error": None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating itinerary: {str(e)}")
