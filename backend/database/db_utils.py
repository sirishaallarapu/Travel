import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")


def call_gemini(prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
    """
    Call Gemini API to generate text from a prompt.
    """
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        params = {"key": GEMINI_API_KEY}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "temperature": temperature
            }
        }
        response = requests.post(url, params=params, json=payload)
        response.raise_for_status()
        result = response.json()
        generated_text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        return generated_text if generated_text else prompt
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return prompt


def enhance_description_with_gemini(
    description: str,
    data_type: str,
    destination: str,
    name: str,
    additional_info: dict = None
) -> str:
    """
    Enhance short descriptions for travel data types using Gemini.
    """
    try:
        rating = additional_info.get("rating", "N/A") if additional_info else "N/A"
        reviews = additional_info.get("reviews", "N/A") if additional_info else "N/A"
        price = additional_info.get("price", "N/A") if additional_info else "N/A"

        if data_type == "hotel":
            prompt = (
                f"Enhance the following hotel description to make it vivid and appealing "
                f"for travelers to {destination}. Include the rating ({rating}) and reviews ({reviews}). "
                f"Limit to 100 words:\n\n{description}"
            )
        elif data_type == "activity":
            prompt = (
                f"Enhance this activity description for a cultural trip in {destination}. "
                f"Include the activity name ({name}). Make it exciting and tourist-friendly. "
                f"Limit to 100 words:\n\n{description}"
            )
        elif data_type == "meal":
            prompt = (
                f"Enhance this restaurant description for a rich dining experience in {destination}. "
                f"Include name ({name}), rating ({rating}), and reviews ({reviews}). "
                f"Limit to 100 words:\n\n{description}"
            )
        elif data_type == "transport":
            prompt = (
                f"Enhance this transportation description to be practical and comforting for travelers to {destination}. "
                f"Mention price ({price}). Keep it under 100 words:\n\n{description}"
            )
        else:
            return description

        full_prompt = f"You are a travel copywriter. {prompt}"
        return call_gemini(prompt=full_prompt, max_tokens=150, temperature=0.7)

    except Exception as e:
        logger.error(f"Error enhancing {data_type} description with Gemini: {e}")
        return description
