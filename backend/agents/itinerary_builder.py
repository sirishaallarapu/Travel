import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
TRIPADVISOR_KEY = os.getenv("TRIPADVISOR_API_KEY")
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)

class ItineraryBuilder:
    def __init__(self, destination, start_date, days, budget="medium"):
        self.destination = destination
        self.start_date = datetime.strptime(start_date[:10], "%Y-%m-%d")
        self.days = days
        self.budget = budget

    def get_location_id_booking(self):
        url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
        headers = {"X-RapidAPI-Key": RAPIDAPI_KEY}
        params = {"query": self.destination}
        response = requests.get(url, headers=headers, params=params)
        response_json = response.json()
        if "data" not in response_json or not response_json["data"]:
            raise Exception(f"No destination ID found for {self.destination}")
        return response_json['data'][0]['dest_id']

    def fetch_hotels(self, location_id):
        url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
        headers = {"X-RapidAPI-Key": RAPIDAPI_KEY}
        price_filter = {"low": (0, 50), "medium": (50, 150), "high": (150, 500)}[self.budget]

        params = {
            "dest_id": location_id,
            "search_type": "CITY",
            "price_min": price_filter[0],
            "price_max": price_filter[1],
            "order_by": "popularity",
            "currency_code": "INR",
            "adults": 1,
            "checkin_date": self.start_date.strftime("%Y-%m-%d"),
            "checkout_date": (self.start_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "rooms": 1
        }

        response = requests.get(url, headers=headers, params=params)
        response_json = response.json()
        hotels = response_json.get("data", {}).get("hotels", [])
        if not hotels:
            raise Exception("Hotel data not found in Booking API response")
        return hotels[:3]

    def fetch_meals(self):
        url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchRestaurants"
        headers = {"X-RapidAPI-Key": RAPIDAPI_KEY}
        location_id = "304554"  # Static for now
        params = {"locationId": location_id}
        response = requests.get(url, headers=headers, params=params)
        response_json = response.json()
        meals = response_json.get("data", {}).get("data", [])
        if not meals:
            raise Exception("Meal data not found in TripAdvisor API response")
        return meals[:3]

    def fetch_activities(self):
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        query = f"things to do in {self.destination}"
        params = {"query": query, "key": GOOGLE_PLACES_KEY}
        response = requests.get(url, params=params)
        activities = response.json().get('results', [])
        if not activities:
            raise Exception("Activity data not found from Google Places API")
        return activities[:3]

    def format_day(self, date_str, hotel, activities, meals):
        hotel_str = f"🏨 Stay: {hotel['property']['name']} – ₹{hotel['property']['priceBreakdown']['grossPrice']['value']} per night\nBooking: {hotel['property'].get('url', 'N/A')}"
        act_str = "\n".join([f"- {a.get('name', a.get('formatted_address', 'No description'))}" for a in activities])
        meal_str = "\n".join([f"- {m.get('name', 'No description')}" for m in meals])
        return f"""Day – {date_str}
--------------------------------------------------

{hotel_str}

🎯 Activities:
{act_str}

🍽️ Meals:
{meal_str}
"""

    def format_with_gemini(self, text):
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(f"""
            Format this trip itinerary in clean markdown. Organize it by day.
            Include:
            - 🏨 Stay with hotel name and price
            - 🎯 Activities in bullet points
            - 🍽️ Meals in bullet points
            Maintain formatting and emojis.

            Text:
            {text}
            """)
            return response.text
        except Exception as e:
            print(f"⚠️ Gemini Flash failed: {e}, falling back to gemini-pro")
            model = genai.GenerativeModel("gemini-pro")
            response = model.generate_content(f"""
            Format this trip itinerary in markdown with:
            - 🏨 Stay with hotel name and price
            - 🎯 Activities
            - 🍽️ Meals

            Text:
            {text}
            """)
            return response.text

    def build_itinerary(self):
        try:
            location_id = self.get_location_id_booking()
            hotels = self.fetch_hotels(location_id)
            meals = self.fetch_meals()
            activities = self.fetch_activities()

            full_text = ""
            for i in range(self.days):
                date = (self.start_date + timedelta(days=i)).strftime("%B %d, %Y")
                hotel = hotels[i % len(hotels)]
                acts = activities[i % len(activities):] + activities[:i % len(activities)]
                food = meals[i % len(meals):] + meals[:i % len(meals)]
                full_text += self.format_day(date, hotel, acts[:3], food[:3]) + "\n\n"

            markdown = self.format_with_gemini(full_text)

            # Convert markdown into a structured dictionary
            itinerary_dict = {}
            current_day = ""
            for line in markdown.splitlines():
                line = line.strip()
                if line.lower().startswith("day"):
                    current_day = line
                    itinerary_dict[current_day] = []
                elif line.startswith("-") or line.startswith("🏨") or line.startswith("🎯") or line.startswith("🍽️") or line.startswith("Booking"):
                    if current_day:
                        itinerary_dict[current_day].append(line)

            return itinerary_dict

        except Exception as e:
            raise Exception(f"Failed to generate itinerary: {str(e)}")
