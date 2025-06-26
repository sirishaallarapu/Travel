# agents/vibe_matcher.py

import logging
from typing import Dict
from database.db_utils import call_gemini

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_trip_vibe(data: Dict[str, str]) -> str:
    """
    Generate a concise trip vibe statement like 'Vibe: adventurous' 
    based on the trip type and destination provided.

    Args:
        data (dict): Dictionary with 'trip_type' and 'destination' keys.

    Returns:
        str: A formatted vibe string (e.g., 'Vibe: adventurous')
    """
    trip_type = data.get('trip_type', 'relaxing').strip().lower()
    destination = data.get('destination', 'somewhere').strip().title()

    logger.info(f"Generating vibe for trip_type='{trip_type}', destination='{destination}'")

    prompt = f"""
You are a travel expert who crafts concise vibe labels.
Create a short vibe sentence in the format: Vibe: [vibe_word]
It should match the mood of a {trip_type} trip to {destination}.
The vibe must be a single word like 'romantic', 'adventurous', 'relaxing', etc.
Length: under 10 words.
Example: Vibe: romantic
Only return the sentence starting with 'Vibe:'.
"""

    try:
        response = call_gemini(prompt=prompt, max_tokens=20, temperature=0.7).strip()

        # Clean and format response
        if not response.lower().startswith("vibe:"):
            response = f"Vibe: {trip_type}"
        else:
            response = response.splitlines()[0].strip()

        logger.info(f"Generated vibe: {response}")
        return response

    except Exception as e:
        logger.error(f"Vibe generation failed: {e}")
        return f"Vibe: {trip_type}"
