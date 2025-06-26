import os
import logging
import requests

logger = logging.getLogger(__name__)

TAVILY_KEY = os.getenv("TAVILY_KEY")
TAVILY_URL = "https://api.tavily.com/search"

def tavily_search(query: str, max_results: int = 5):
    headers = {"Authorization": f"Bearer {TAVILY_KEY}"}
    body = {
        "query": query,
        "max_results": max_results,
        "include_images": False
    }
    resp = requests.post(TAVILY_URL, headers=headers, json=body)
    resp.raise_for_status()
    return resp.json().get("results", [])

def extract_item_fields(item):
    """Extract name, price, rating, content from Tavily result safely."""
    name = item.get("title") or item.get("name") or "Unnamed"
    content = item.get("content", "")

    # Simple price extraction pattern (₹ or INR followed by digits)
    price_match = (
        item.get("price") or
        _extract_price(content) or
        1000  # fallback
    )

    # Simple rating extraction pattern (e.g., 3.5/5 or 4 stars)
    rating_match = (
        item.get("rating") or
        _extract_rating(content) or
        "4.0"
    )

    return {
        "name": name,
        "price": price_match,
        "rating": rating_match,
        "content": content
    }

def _extract_price(text):
    import re
    match = re.search(r"(₹|INR)?\s?(\d{3,6})", text)
    return int(match.group(2)) if match else None

def _extract_rating(text):
    import re
    match = re.search(r"(\d\.\d)\s?(?:/5|stars?)", text, re.IGNORECASE)
    return match.group(1) if match else None

def fetch_recommendations(destination, trip_type, food_preference, num_members, budget_per_person, hotel_stars):
    logger.info(f"🌐 Searching Tavily for: {destination}, {trip_type}, food={food_preference}, budget=₹{budget_per_person}, stars={hotel_stars}")

    hotels_q = f"{destination} {trip_type} hotels {' '.join(hotel_stars)} star"
    acts_q = f"things to do in {destination} for {trip_type} travelers"
    meals_q = f"top {food_preference} restaurants in {destination}"
    trans_q = f"{destination} airport transfer options"

    # Tavily calls
    raw_hotels = tavily_search(hotels_q)
    raw_activities = tavily_search(acts_q)
    raw_meals = tavily_search(meals_q)
    raw_transport = tavily_search(trans_q)

    logger.info("✅ Tavily recommendations fetched.")

    return {
        "hotels": [extract_item_fields(h) for h in raw_hotels],
        "activities": [extract_item_fields(a) for a in raw_activities],
        "meals": [extract_item_fields(m) for m in raw_meals],
        "transport": [t.get("content", "") for t in raw_transport if t.get("content")]
    }
