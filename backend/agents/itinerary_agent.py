import os
import re
import requests
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import time
from requests.exceptions import HTTPError
import logging
import traceback

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_location_id(destination):
    """Get location ID for TripAdvisor using a search API."""
    destination = destination.lower()
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchLocation"
    querystring = {"query": destination}
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring, timeout=5)
    response.raise_for_status()
    data = response.json()
    if not data.get("data") or len(data["data"]) == 0:
        raise Exception(f"No location data found for {destination} on TripAdvisor")
    return data["data"][0]["locationId"]

class ItineraryAgent:
    def __init__(self, db_path="travel_data.db"):
        self.db_path = db_path
        try:
            self.create_cache_table()
        except Exception as e:
            logger.error(f"Failed to create cache table: {str(e)}\n{traceback.format_exc()}")
            raise

    def create_cache_table(self):
        """Create a table to cache API responses."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS api_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT,
            data_type TEXT,
            data TEXT,
            last_updated TEXT
        )''')
        conn.commit()
        conn.close()

    def get_cached_data(self, destination: str, data_type: str) -> Optional[List]:
        """Retrieve cached data if it's still valid (less than 24 hours old)."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT data, last_updated FROM api_cache WHERE destination = ? AND data_type = ?",
                      (destination.lower(), data_type))
            result = c.fetchone()
            conn.close()

            if result:
                data, last_updated = result
                last_updated_date = datetime.fromisoformat(last_updated)
                if (datetime.now() - last_updated_date).total_seconds() < 24 * 60 * 60:  # 24 hours
                    return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached data for {destination}/{data_type}: {str(e)}\n{traceback.format_exc()}")
            return None

    def cache_data(self, destination: str, data_type: str, data: List):
        """Cache the API response data."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            timestamp = datetime.now().isoformat()
            c.execute("INSERT OR REPLACE INTO api_cache (destination, data_type, data, last_updated) VALUES (?, ?, ?, ?)",
                      (destination.lower(), data_type, json.dumps(data), timestamp))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error caching data for {destination}/{data_type}: {str(e)}\n{traceback.format_exc()}")

    def get_hotels(self, destination, start_date, budget, retries=3, backoff_factor=5):
        cached_hotels = self.get_cached_data(destination, "hotels")
        if cached_hotels:
            logger.info(f"Using cached hotel data for {destination}")
            return cached_hotels

        url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
        headers = {"X-RapidAPI-Key": RAPIDAPI_KEY}
        querystring = {"query": destination}

        for attempt in range(retries):
            try:
                resp = requests.get(url, headers=headers, params=querystring, timeout=5)
                remaining = resp.headers.get("X-RateLimit-Remaining")
                if remaining and int(remaining) < 5:
                    logger.warning(f"Only {remaining} requests remaining before hitting Booking.com rate limit.")
                resp.raise_for_status()
                break
            except HTTPError as e:
                if resp.status_code == 429:
                    if attempt == retries - 1:
                        raise
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Rate limit hit for searchDestination. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

        dest_id = resp.json()["data"][0]["dest_id"]
        price_range = {"low": (0, 50), "medium": (50, 150), "high": (150, 500)}.get(budget, (50, 150))
        hotel_url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
        querystring = {
            "dest_id": dest_id,
            "search_type": "CITY",
            "price_min": price_range[0] * 83,
            "price_max": price_range[1] * 83,
            "checkin_date": start_date,
            "checkout_date": (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
            "adults": 1,
            "rooms": 1,
            "currency_code": "INR"
        }

        for attempt in range(retries):
            try:
                hotel_resp = requests.get(hotel_url, headers=headers, params=querystring, timeout=5)
                remaining = hotel_resp.headers.get("X-RateLimit-Remaining")
                if remaining and int(remaining) < 5:
                    logger.warning(f"Only {remaining} requests remaining before hitting Booking.com rate limit.")
                hotel_resp.raise_for_status()
                break
            except HTTPError as e:
                if hotel_resp.status_code == 429:
                    if attempt == retries - 1:
                        raise
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Rate limit hit for searchHotels. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

        hotels = hotel_resp.json().get("data", {}).get("hotels", [])
        hotels_data = [{"name": h["property"]["name"], "price": h["property"]["priceBreakdown"]["grossPrice"]["value"]} for h in hotels[:3]]
        self.cache_data(destination, "hotels", hotels_data)
        return hotels_data

    def get_meals(self, destination, retries=3, backoff_factor=5):
        cached_meals = self.get_cached_data(destination, "meals")
        if cached_meals:
            logger.info(f"Using cached meal data for {destination}")
            return cached_meals

        location_id = get_location_id(destination)
        headers = {"X-RapidAPI-Key": RAPIDAPI_KEY}
        url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchRestaurants"
        querystring = {"locationId": location_id}

        for attempt in range(retries):
            try:
                resp = requests.get(url, headers=headers, params=querystring, timeout=5)
                remaining = resp.headers.get("X-RateLimit-Remaining")
                if remaining and int(remaining) < 5:
                    logger.warning(f"Only {remaining} requests remaining before hitting TripAdvisor rate limit.")
                resp.raise_for_status()
                break
            except HTTPError as e:
                if resp.status_code == 429:
                    if attempt == retries - 1:
                        raise
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Rate limit hit for searchRestaurants. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

        meals = resp.json().get("data", {}).get("data", [])
        meals_data = [{"name": m.get("name", "Local Restaurant"), "cuisine": m.get("cuisine", "Local Cuisine")} for m in meals[:3]]
        self.cache_data(destination, "meals", meals_data)
        return meals_data

    def get_activities(self, destination, retries=3, backoff_factor=5):
        cached_activities = self.get_cached_data(destination, "activities")
        if cached_activities:
            logger.info(f"Using cached activity data for {destination}")
            return cached_activities

        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        querystring = {"query": f"things to do in {destination}", "key": GOOGLE_PLACES_KEY}

        for attempt in range(retries):
            try:
                resp = requests.get(url, params=querystring, timeout=5)
                resp.raise_for_status()
                break
            except HTTPError as e:
                if resp.status_code == 429:
                    if attempt == retries - 1:
                        raise
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Rate limit hit for Google Places API. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise

        activities = resp.json().get("results", [])[:5]
        activities_data = [{"name": a.get("name", "Activity")} for a in activities]
        self.cache_data(destination, "activities", activities_data)
        return activities_data

    def parse_itinerary_to_dict(self, itinerary_text: str) -> Dict:
        """Parse the itinerary string into a structured dictionary, handling various formats."""
        itinerary_dict = {}
        current_day = None
        current_section = None
        lines = itinerary_text.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Handle day headings
            # Gemini format: "**Day X – YYYY-MM-DD: Description**"
            gemini_day_match = re.match(r"\*\*Day (\d+) – (\d{4}-\d{2}-\d{2}): (.+?)\*\*", line)
            # Simpler format: "Day X – YYYY-MM-DD" or "Day X – YYYY-MM-DD: Description"
            simple_day_match = re.match(r"Day (\d+) – (\d{4}-\d{2}-\d{2})(?:: (.+))?", line)
            
            if gemini_day_match:
                day_num, date, _ = gemini_day_match.groups()
                current_day = f"Day {day_num} – {date}"
                itinerary_dict[current_day] = {
                    "Transportation": [],
                    "Accommodation": [],
                    "Planned Activities": [],
                    "Meals": [],
                    "Total Cost": None
                }
                current_section = None
                continue
            elif simple_day_match:
                day_num, date, _ = simple_day_match.groups()
                current_day = f"Day {day_num} – {date}"
                itinerary_dict[current_day] = {
                    "Transportation": [],
                    "Accommodation": [],
                    "Planned Activities": [],
                    "Meals": [],
                    "Total Cost": None
                }
                current_section = None
                continue

            if not current_day:
                continue

            # Handle section headers
            # Gemini format: "**Transportation:**" or "* **Transportation:**"
            # Simpler format: "Transportation:"
            if re.match(r"(\* )?\*\*Transportation:\*\*", line) or line.startswith("Transportation:"):
                current_section = "Transportation"
                line = re.sub(r"(\* )?\*\*Transportation:\*\*", "Transportation:", line).replace("Transportation:", "").strip()
                if line:
                    itinerary_dict[current_day][current_section].append(f"Transportation: {line}")
            elif re.match(r"(\* )?\*\*Accommodation:\*\*", line) or line.startswith("Accommodation:"):
                current_section = "Accommodation"
                line = re.sub(r"(\* )?\*\*Accommodation:\*\*", "Accommodation:", line).replace("Accommodation:", "").strip()
                if line:
                    itinerary_dict[current_day][current_section].append(f"Accommodation: {line}")
            elif re.match(r"(\* )?\*\*Planned Activities:\*\*", line) or line.startswith("Planned Activities:"):
                current_section = "Planned Activities"
            elif re.match(r"(\* )?\*\*Meals for the Day:\*\*", line) or line.startswith("Meals for the Day:"):
                current_section = "Meals"
            elif re.match(r"(\* )?\*\*Total Estimated Cost for the Day:\*\*", line) or line.startswith("Total Estimated Cost for the Day:"):
                current_section = None
                cost = re.sub(r"(\* )?\*\*Total Estimated Cost for the Day:\*\*", "", line).replace("Total Estimated Cost for the Day:", "").strip()
                itinerary_dict[current_day]["Total Cost"] = f"Total Estimated Cost for the Day: {cost}"
            # Handle items under sections
            elif current_section:
                # Gemini format: "* **Morning (9:00 AM):** ..." or "* Morning: ..."
                # Simpler format: "**Morning (9:00 AM):** ..." or "Breakfast: ..."
                if re.match(r"\* \*\*(Morning|Afternoon|Evening)\b", line) or re.match(r"\* (Breakfast|Lunch|Dinner)\b", line):
                    cleaned_line = re.sub(r"^\* \*\*|\*\*$", "", line).strip()
                    itinerary_dict[current_day][current_section].append(cleaned_line)
                elif line.startswith("* ") or line.startswith("    * "):
                    cleaned_line = re.sub(r"^\*+\s*|\s*\*+$", "", line).strip()
                    if cleaned_line:
                        itinerary_dict[current_day][current_section].append(cleaned_line)
                elif re.match(r"\*\*(Morning|Afternoon|Evening)\b", line) or line.startswith("Breakfast:") or line.startswith("Lunch:") or line.startswith("Dinner:"):
                    cleaned_line = re.sub(r"^\*\*|\*\*$", "", line).strip()
                    itinerary_dict[current_day][current_section].append(cleaned_line)
        
        return itinerary_dict

    def generate_itinerary(self, destination, start_date, duration, trip_type, food_preference, num_members, budget):
        try:
            logger.info(f"Generating itinerary for destination: {destination}, trip_type: {trip_type}")
            # Try to get cached data first
            hotel_data = self.get_hotels(destination, start_date, budget)
            meals_data = self.get_meals(destination)
            activities = self.get_activities(destination)

            itinerary_text = "Your Trip Itinerary\n"
            itinerary_text += f"Vibe: A memorable {trip_type.lower()} trip in {destination}\n\n"

            total_budget = 0
            for i in range(duration):
                day_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=i)).strftime('%B %d, %Y')
                hotel = hotel_data[i % len(hotel_data)]
                meal = meals_data[i % len(meals_data)]
                activity_list = activities[i % len(activities):i % len(activities) + 3]

                daily_cost = hotel["price"] + 1500 + 2500 + 5000  # Meal costs
                total_budget += daily_cost

                itinerary_text += f"Day {i + 1} – {day_date}\n"
                itinerary_text += f"Transportation: Local transport in {destination}\n"
                itinerary_text += f"Accommodation: {hotel['name']} (Luxury 5-star), ₹{hotel['price']}\n"
                itinerary_text += f"Planned Activities:\n"
                for activity in activity_list:
                    itinerary_text += f"- {activity['name']}\n"
                itinerary_text += f"Meals for the Day:\n"
                itinerary_text += f"- Breakfast at {meal['name']}: {meal['cuisine']}, ₹1500\n"
                itinerary_text += f"- Lunch at Local Eatery: {food_preference} options, ₹2500\n"
                itinerary_text += f"- Dinner at Local Restaurant: {food_preference} options, ₹5000\n"
                itinerary_text += f"Total Estimated Cost for the Day: ₹{daily_cost}\n\n"

            itinerary_dict = self.parse_itinerary_to_dict(itinerary_text)
            logger.info(f"Generated itinerary: {itinerary_dict}")
            return {
                "itinerary": itinerary_dict,
                "vibe": f"A memorable {trip_type.lower()} trip in {destination}",
                "total_budget": total_budget
            }

        except Exception as api_error:
            logger.warning(f"Falling back to Gemini due to API failure: {str(api_error)}\n{traceback.format_exc()}")
            return self.generate_with_gemini(destination, start_date, duration, trip_type, food_preference, num_members, budget)

    def generate_with_gemini(
        self,
        destination: str,
        start_date: str,
        duration: int,
        trip_type: str,
        food_preference: str,
        num_members: int,
        budget: str,
        retry: bool = True
    ) -> Dict:
        logger.info(f"Generating itinerary with Gemini for destination: {destination}, trip_type: {trip_type}")
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Add an example for Maldives with relaxation trip type to guide Gemini
        example_section = ""
        if destination.lower() == "maldives" and trip_type.lower() == "relaxation":
            example_section = """
**Example for Maldives (Relaxation Trip):**
Your Trip Itinerary  
Vibe: A relaxation trip in Maldives  

Day 1 – 23 June 2025: Arrival and Beach Relaxation  
Transportation: Arrival at Velana International Airport (MLE). Ferry to Hulhumalé (approx. 15 minutes).  
Accommodation: Hulhumalé Hotel (Budget-friendly guesthouse, clean rooms). Price: ₹3000 per night.  
Planned Activities:  
Morning – Airport Transfer & Check-in: Transfer to Hulhumalé by ferry. Check in to the hotel. Cost: ₹200 (ferry)  
Afternoon – Hulhumalé Beach Relaxation: Relax on the pristine beach, enjoy the turquoise waters. Cost: ₹0  
Evening – Sunset Stroll: Walk along the beach and enjoy the sunset. Cost: ₹0  
Meals for the Day:  
Breakfast – Hotel: Basic breakfast provided. Cost: Included  
Lunch – Local Eatery near beach: Vegetarian snacks and fresh juices. Cost: ₹300  
Dinner – Local Restaurant: Vegetarian curry and rice. Cost: ₹500  
Total Estimated Cost for the Day: ₹3500
"""

        prompt = f"""
You are a professional travel assistant. Generate a rich, engaging, clearly structured itinerary for **{destination}**. The itinerary must explicitly focus on {destination} and match the specified trip type and preferences.

---
Your Trip Itinerary  
Vibe: A {trip_type.lower()} trip in {destination}

Day 1 – <Formatted Date>: Arrival and Initial Exploration  
Transportation: <Arrival/movement info specific to {destination}>  
Accommodation: <Hotel name, type, quality, price>  
Planned Activities:  
Morning – <Activity>: <desc specific to {destination}>. Cost: ₹____  
Afternoon – <Activity>: <desc specific to {destination}>. Cost: ₹____  
Evening – <Activity>: <desc specific to {destination}>. Cost: ₹____  
Meals for the Day:  
Breakfast – <Where>: <desc>. Cost: ₹____  
Lunch – <Where>: <desc>. Cost: ₹____  
Dinner – <Where>: <desc>. Cost: ₹____  
Total Estimated Cost for the Day: ₹____
---

{example_section}

**Instructions:**
- This itinerary MUST be for "{destination}" only. Do not mention any other destinations (e.g., do not mention Goa unless destination is Goa).
- Ensure all activities, accommodations, and meals are specific to {destination}.
- Match the trip type: {trip_type.lower()}.
- Consider food preference: {food_preference.lower()}.
- Strictly adhere to the budget: {budget.lower()}. For 'low' budget, keep daily costs under ₹10,000 per person; for 'high' budget, costs can be higher but should be reasonable for a luxury experience.
- Generate the itinerary for exactly {num_members} traveler(s). Do not assume a different number of travelers.
- Generate for {duration} days starting from {start_date}.
- Include realistic costs in INR (₹).
- If you cannot generate a valid itinerary for {destination}, return a message indicating the failure.

Destination: {destination}  
Trip Type: {trip_type}  
Food Preference: {food_preference}  
Duration: {duration} days  
Start Date: {start_date}  
Budget: {budget}  
Travelers: {num_members}
"""

        try:
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            logger.info(f"Gemini response: {raw_text}")

            # Check if Gemini hallucinated the wrong destination
            if destination.lower() not in raw_text.lower():
                if retry:
                    logger.warning("Gemini hallucinated wrong destination. Retrying with strict prompt...")
                    return self.generate_with_gemini(destination, start_date, duration, trip_type, food_preference, num_members, budget, retry=False)

                logger.error("Gemini failed to produce destination-specific content.")
                return {
                    "itinerary": {f"Day 1 – {start_date}": {"Error": [f"Sorry, we couldn't generate a valid itinerary for {destination}."]}},
                    "vibe": f"{trip_type.title()} trip in {destination}",
                    "total_budget": None
                }

            # Extract the total trip cost from the "Total Estimated Cost for the Trip" line, if present
            total_trip_cost_match = re.search(r"Total Estimated Cost for the Trip.*₹\s*([\d,]+)\s*(?:-\s*₹([\d,]+))?", raw_text)
            if total_trip_cost_match:
                min_cost = int(total_trip_cost_match.group(1).replace(",", ""))
                max_cost = int(total_trip_cost_match.group(2).replace(",", "")) if total_trip_cost_match.group(2) else min_cost
                total_cost = (min_cost + max_cost) / 2  # Use the average of the range
            else:
                # Fallback: Sum the daily totals
                daily_cost_matches = re.findall(r"Total Estimated Cost for the Day: ₹\s*([\d,]+)\s*(?:-\s*₹([\d,]+))?", raw_text)
                total_cost = 0
                for min_cost, max_cost in daily_cost_matches:
                    min_cost = int(min_cost.replace(",", ""))
                    max_cost = int(max_cost.replace(",", "")) if max_cost else min_cost
                    total_cost += (min_cost + max_cost) / 2

            vibe_match = re.search(r"Vibe:\s*(.+)", raw_text)
            extracted_vibe = vibe_match.group(1).strip() if vibe_match else f"{trip_type.title()} Vibe"

            itinerary_dict = self.parse_itinerary_to_dict(raw_text)
            logger.info(f"Parsed Gemini itinerary: {itinerary_dict}")

            return {
                "itinerary": itinerary_dict,
                "vibe": extracted_vibe,
                "total_budget": total_cost if total_cost > 0 else None
            }

        except Exception as e:
            logger.error(f"Gemini generation error: {str(e)}\n{traceback.format_exc()}")
            return {
                "itinerary": {f"Day 1 – {start_date}": {"Error": ["Itinerary generation failed due to an internal error."]}},
                "vibe": "N/A",
                "total_budget": None
            }