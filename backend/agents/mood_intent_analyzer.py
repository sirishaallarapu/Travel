# agents/mood_intent_analyzer.py

import logging
import json
from database.db_utils import call_gemini  # Custom Gemini wrapper you already use

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def analyze_mood_intent(trip_type: str) -> tuple:
    """
    Analyzes the mood and intent of a trip based on the given trip_type.
    Returns:
        mood: str – One of ['romantic', 'lively', 'adventurous', 'relaxing', 'cultural']
        intent: str – One of ['romantic trip', 'beach trip', 'adventure trip', 'cultural exploration', 'city exploration']
    """

    logger.info(f"Detecting mood and intent for trip_type: {trip_type}")

    prompt = f"""
You are a travel expert helping match a user's trip type to their mood and intent.

Trip Type: {trip_type}

Respond with a valid JSON object with the following keys:
- mood: One of ['romantic', 'lively', 'adventurous', 'relaxing', 'cultural']
- intent: One of ['romantic trip', 'beach trip', 'adventure trip', 'cultural exploration', 'city exploration']

Only respond with JSON. No explanations.
"""

    try:
        response = call_gemini(prompt, temperature=0.2, max_tokens=150)
        result = json.loads(response)

        mood = result.get("mood", "relaxing")
        intent = result.get("intent", "beach trip")

        logger.info(f"Detected mood: {mood}, intent: {intent}")
        return mood, intent

    except Exception as e:
        logger.error(f"Failed to detect mood and intent: {e}")
        return "relaxing", "beach trip"  # fallback
