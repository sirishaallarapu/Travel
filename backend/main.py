from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import logging
import traceback
from agents.itinerary_agent import ItineraryAgent
from pdf_generator import generate_pdf
from fastapi.responses import Response

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TripRequest(BaseModel):
    destination: str
    trip_type: str
    food_preference: str
    num_members: int
    budget: str
    start_date: str
    duration: int

class TripResponse(BaseModel):
    itinerary: Dict
    vibe: str
    total_budget: Optional[float]

agent = ItineraryAgent()

@app.post("/api/trip")
async def trip_handler(request: TripRequest):
    try:
        logger.info(f"Received trip request: {request.dict()}")
        itinerary_data = agent.generate_itinerary(
            destination=request.destination,
            start_date=request.start_date,
            duration=request.duration,
            trip_type=request.trip_type,
            food_preference=request.food_preference,
            num_members=request.num_members,
            budget=request.budget,
        )
        logger.info(f"Generated itinerary data: {itinerary_data}")
        response = TripResponse(
            itinerary=itinerary_data["itinerary"],
            vibe=itinerary_data["vibe"],
            total_budget=itinerary_data["total_budget"],
        )
        logger.info(f"Returning response: {response.dict()}")
        return response
    except Exception as e:
        logger.error(f"Trip generation error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to generate itinerary: {str(e)}")

@app.post("/api/generate-pdf")
async def generate_pdf_endpoint(data: Dict):
    try:
        pdf_buffer = generate_pdf(data)
        return Response(
            content=pdf_buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=itinerary.pdf"},
        )
    except Exception as e:
        logger.error(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")