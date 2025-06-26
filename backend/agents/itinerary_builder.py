import os
import re
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

from agents.mood_intent_analyzer import analyze_mood_intent
from agents.vibe_matcher import get_trip_vibe
from agents.stay_activity_recommender import fetch_recommendations
from agents.gemini_utils import generate_with_gemini  # 👈 You must have this helper

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ItineraryBuilder:
    def __init__(
        self,
        destination: str,
        start_date: str,
        days: int,
        trip_type: str,
        food_preference: str,
        num_members: int,
        budget_per_person: int,
        hotel_stars: list,
        from_location: str = "Hyderabad, India",
        flight_included: bool = False
    ):
        self.destination = destination
        self.start_date = datetime.strptime(start_date[:10], "%Y-%m-%d")
        self.days = days
        self.trip_type = trip_type
        self.food_preference = food_preference
        self.num_members = num_members
        self.budget_per_person = budget_per_person
        self.hotel_stars = hotel_stars
        self.from_location = from_location
        self.flight_included = flight_included

        # Step 1: Mood + Intent
        self.mood, self.intent = analyze_mood_intent(trip_type)

        # Step 2: Vibe
        self.vibe = get_trip_vibe({"trip_type": trip_type, "destination": destination})

        # Step 3: Fetch Recommendations
        self.recommendations = fetch_recommendations(
            destination=self.destination,
            trip_type=self.trip_type,
            food_preference=self.food_preference,
            num_members=self.num_members,
            budget_per_person=self.budget_per_person,
            hotel_stars=self.hotel_stars
        )

        # Gemini fallback if any field is missing
        if not self.recommendations.get("activities"):
            logger.warning("⚠️ No activities from Tavily. Using Gemini.")
            self.recommendations["activities"] = generate_with_gemini(
                f"Suggest 5 {self.trip_type} activities to do in {self.destination}. "
                "Return JSON list with 'name', 'description', 'price (INR)'."
            )

        if not self.recommendations.get("meals"):
            logger.warning("⚠️ No meals from Tavily. Using Gemini.")
            self.recommendations["meals"] = generate_with_gemini(
                f"List 5 {self.food_preference} dishes popular in {self.destination}. "
                "Return JSON list with 'name', 'description', 'price (INR)'."
            )

        if self.flight_included and not self.recommendations.get("flights"):
            self.recommendations["flights"] = [generate_with_gemini(
                f"Create a sample flight detail from {self.from_location} to {self.destination} on {self.start_date.strftime('%Y-%m-%d')}. "
                "Return JSON with 'departure', 'arrival', 'date', 'departureTime', 'arrivalTime', 'flightNumber'."
            )]

    def extract_price(self, text: str) -> int:
        match = re.search(r"₹\s?(\d{3,6})", text or "")
        return int(match.group(1)) if match else 3000

    def extract_rating(self, text: str) -> str:
        match = re.search(r"(\d\.\d)\s?(?:/5|stars?)", text or "", re.IGNORECASE)
        return match.group(1) if match else "4.0"

    def format_day(self, day_num: int, date_str: str) -> dict:
        hotel = self.recommendations["hotels"][day_num % len(self.recommendations["hotels"])]
        activities = self.recommendations["activities"][day_num % len(self.recommendations["activities"]):][:3]
        meals = self.recommendations["meals"][day_num % len(self.recommendations["meals"]):][:3]

        hotel_name = hotel.get("title") or hotel.get("name", "Unnamed Hotel")
        hotel_content = hotel.get("content", "")
        hotel_price = hotel.get("price") or self.extract_price(hotel_content)
        hotel_rating = hotel.get("rating") or self.extract_rating(hotel_content)

        total_cost = (
            hotel_price +
            sum(act.get("price", 1000) for act in activities) +
            sum(meal.get("price", 500) for meal in meals)
        ) * self.num_members

        return {
            "Day Plan": [
                f"Day {day_num + 1} in {self.destination} includes exciting activities, delicious meals, and a relaxing stay at {hotel_name}."
            ] if hotel_name else [""],
            "Hotel": [
                f"{hotel_name} (₹{hotel_price}/night, Rating: {hotel_rating})"
            ] if hotel_name else [""],
            "Activity": [
                f"{act.get('name', 'Unnamed Activity')} ({act.get('price', 1000)} INR)" for act in activities
            ] if activities else [],
            "Meals": [
                f"{meal.get('name', 'Unnamed Meal')} ({meal.get('price', 500)} INR)" for meal in meals
            ] if meals else [],
            "Total Cost": [f"Total Estimated Cost for the Day: ₹{total_cost}"]
        }

    def build_itinerary(self) -> dict:
        try:
            itinerary = {}
            total_budget = 0

            for i in range(self.days):
                date = (self.start_date + timedelta(days=i)).strftime("%Y-%m-%d")
                day_key = f"Day {i + 1} – {date}"
                formatted_day = self.format_day(i, date)
                itinerary[day_key] = formatted_day

                cost_match = re.search(r"₹([\d,]+)", formatted_day["Total Cost"][0])
                if cost_match:
                    total_budget += int(cost_match.group(1).replace(",", ""))

            hotel_info = self.recommendations["hotels"][0]
            hotel_title = hotel_info.get("title") or hotel_info.get("name", "Unnamed Hotel")
            hotel_content = hotel_info.get("content", "")
            hotel_rating = hotel_info.get("rating") or self.extract_rating(hotel_content)
            hotel_price = hotel_info.get("price") or self.extract_price(hotel_content)

            return {
                "itinerary": itinerary,
                "meta": {
                    "destination": self.destination,
                    "vibe": self.vibe,
                    "mood": self.mood,
                    "intent": self.intent,
                    "vibe_description": f"{self.vibe} experience in {self.destination}",
                    "total_budget": total_budget,
                    "num_members": self.num_members,
                    "flight_included": self.flight_included,
                    "flights_and_transfers": {
                        "flights": [
                            {
                                "departure": self.from_location,
                                "arrival": f"{self.destination} Airport",
                                "departureTime": "10:00",
                                "arrivalTime": "12:30",
                                "date": self.start_date.strftime("%Y-%m-%d"),
                                "flightNumber": "AI-101"
                            }
                        ] if self.flight_included else [],
                        "transfers": self.recommendations.get("transport") or []
                    },

                    "hotel": {
                        "name": hotel_title,
                        "rating": hotel_rating,
                        "price": hotel_price,
                        "nights": self.days
                    },
                    "activities": [a.get("title") or a.get("name", "Unnamed Activity") for a in self.recommendations["activities"]],
                    "meals": [m.get("title") or m.get("name", "Unnamed Meal") for m in self.recommendations["meals"]]
                }
            }
        except Exception as e:
            logger.error(f"❌ Failed to build itinerary: {str(e)}")
            raise
