# agents/vibe_matcher.py

import logging
from typing import Dict
from database.db_utils import call_gemini

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_trip_vibe(data: Dict[str, str]) -> str:
    """
    Generate a short vibe statement like 'Vibe: adventurous' based on trip type and destination.
    
    Args:
        data: Dictionary with 'trip_type' and 'destination' keys.
    
    Returns:
        A string representing the trip vibe.
    """
    trip_type = data.get('trip_type', 'generic').strip().lower()
    destination = data.get('destination', 'unknown').strip().lower()

    logger.info(f"Generating vibe for trip_type='{trip_type}', destination='{destination}'")

    prompt = f"""
You are a travel expert who crafts concise vibe labels.
Generate a short vibe statement in the format: Vibe: [vibe]
The vibe should reflect a {trip_type} trip to {destination}.
Keep it under 10 words.
Example: Vibe: adventurous
"""

    try:
        response = call_gemini(prompt=prompt, max_tokens=20, temperature=0.8).strip()
        if not response.lower().startswith("vibe:"):
            response = f"Vibe: {trip_type}"
        logger.info(f"Generated vibe: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to generate vibe: {str(e)}")
        return f"Vibe: {trip_type}"
