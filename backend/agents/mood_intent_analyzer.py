# agents/mood_intent_analyzer.py

import logging
import json
from database.db_utils import call_gemini  # Reusable Gemini wrapper

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def analyze_mood_intent(trip_type: str, intent: str) -> dict:
    """
    Use Gemini API to analyze and generate mood and intent based on the trip type and user input.

    Returns a dict like:
    {
        "vibe_description": "...",
        "mood": "romantic",
        "intent": "romantic trip"
    }
    """
    logger.info(f"Analyzing mood and intent for trip_type: '{trip_type}', intent: '{intent}'")

    prompt = f"""
You are a travel expert analyzing user input to determine the mood and intent of a trip.
Trip Type: {trip_type}
Intent: {intent}

Generate a valid JSON object with the following fields:
- vibe_description: A detailed, engaging description of the trip's vibe (50-100 words).
- mood: One of ['romantic', 'lively', 'adventurous', 'relaxing', 'cultural'].
- intent: One of ['romantic trip', 'beach trip', 'adventure trip', 'cultural exploration', 'city exploration'].

Respond ONLY with valid JSON.
"""

    try:
        response = call_gemini(
            prompt=f"Respond ONLY with valid JSON.\n{prompt}",
            max_tokens=200,
            temperature=0.3
        )
        result = json.loads(response)
        logger.info(f"Mood and intent analysis result: {result}")
        return result

    except Exception as e:
        logger.error(f"Failed to analyze mood and intent: {str(e)}")

        # Fallback response
        return {
            "vibe_description": f"A memorable {trip_type} trip tailored to your preferences.",
            "mood": "cultural",
            "intent": "city exploration"
        }
