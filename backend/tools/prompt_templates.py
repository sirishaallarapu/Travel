import os
import re
from tavily import TavilyClient
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def get_itinerary_prompt(data, vibe, effective_trip_type, valid, accommodations, activities, meals, budget, rooms_needed, extracted_data):
    destination = data.get("destination", "Unknown").capitalize()
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    num_members = data.get("num_members", 1)
    food_preference = data.get("food_preference", "non_veg").lower()
    budget_level = data.get("budget", "medium").lower()
    
    try:
        start = datetime.fromisoformat(start_date.replace("Z", ""))
        end = datetime.fromisoformat(end_date.replace("Z", ""))
        duration = (end - start).days + 1
        date_list = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(duration)]
    except Exception as e:
        logger.error(f"Date parsing error: {e}")
        duration = 4
        date_list = ["2025-06-11", "2025-06-12", "2025-06-13", "2025-06-14"]

    default_budget_ranges = {
        "low": {"acc_min": 20000, "acc_max": 50000, "act_min": 1000, "act_max": 5000, "meal_min": 500, "meal_max": 2000, "trans_min": 1000, "trans_max": 5000},
        "medium": {"acc_min": 50000, "acc_max": 100000, "act_min": 3000, "act_max": 10000, "meal_min": 1000, "meal_max": 3000, "trans_min": 2000, "trans_max": 8000},
        "high": {"acc_min": 80000, "acc_max": 200000, "act_min": 5000, "act_max": 20000, "meal_min": 2000, "meal_max": 5000, "trans_min": 4000, "trans_max": 10000}
    }

    budget_ranges = default_budget_ranges[budget_level]
    try:
        budget_query = f"cost estimates for a {budget_level}-budget {effective_trip_type} trip to {destination} in 2025 for accommodation, activities, meals, transport per day site:*.com"
        budget_response = tavily_client.search(query=budget_query, max_results=7)
        budget_data = budget_response.get("results", [])

        for result in budget_data:
            content = result.get("content", "").lower()
            if destination.lower() in content:
                acc_match = re.search(r'accommodation.*?₹\s*([\d,]+(?:\.?\d+)?)\s*[-–]?\s*₹?\s*([\d,]+(?:\.?\d+)?)?', content, re.IGNORECASE)
                if acc_match:
                    acc_min = float(acc_match.group(1).replace(",", ""))
                    acc_max = float(acc_match.group(2).replace(",", "")) if acc_match.group(2) else acc_min * 1.5
                    budget_ranges["acc_min"] = min(max(acc_min, budget_ranges["acc_min"]), budget_ranges["acc_max"])
                    budget_ranges["acc_max"] = max(min(acc_max, default_budget_ranges["high"]["acc_max"]), budget_ranges["acc_min"])

                act_match = re.search(r'(?:activity|activities).*?₹\s*([\d,]+(?:\.?\d+)?)\s*[-–]?\s*₹?\s*([\d,]+(?:\.?\d+)?)?', content, re.IGNORECASE)
                if act_match:
                    act_min = float(act_match.group(1).replace(",", ""))
                    act_max = float(act_match.group(2).replace(",", "")) if act_match.group(2) else act_min * 1.5
                    budget_ranges["act_min"] = min(max(act_min, budget_ranges["act_min"]), budget_ranges["act_max"])
                    budget_ranges["act_max"] = max(min(act_max, default_budget_ranges["high"]["act_max"]), budget_ranges["act_min"])

                meal_match = re.search(r'(?:meal|food|dining).*?₹\s*([\d,]+(?:\.?\d+)?)\s*[-–]?\s*₹?\s*([\d,]+(?:\.?\d+)?)?', content, re.IGNORECASE)
                if meal_match:
                    meal_min = float(meal_match.group(1).replace(",", ""))
                    meal_max = float(meal_match.group(2).replace(",", "")) if meal_match.group(2) else meal_min * 1.5
                    budget_ranges["meal_min"] = min(max(meal_min, budget_ranges["meal_min"]), budget_ranges["meal_max"])
                    budget_ranges["meal_max"] = max(min(meal_max, default_budget_ranges["high"]["meal_max"]), budget_ranges["meal_min"])

                trans_match = re.search(r'(?:transport|travel).*?₹\s*([\d,]+(?:\.?\d+)?)\s*[-–]?\s*₹?\s*([\d,]+(?:\.?\d+)?)?', content, re.IGNORECASE)
                if trans_match:
                    trans_min = float(trans_match.group(1).replace(",", ""))
                    trans_max = float(trans_match.group(2).replace(",", "")) if trans_match.group(2) else trans_min * 1.5
                    budget_ranges["trans_min"] = min(max(trans_min, budget_ranges["trans_min"]), budget_ranges["trans_max"])
                    budget_ranges["trans_max"] = max(min(trans_max, default_budget_ranges["high"]["trans_max"]), budget_ranges["trans_min"])
    except Exception as e:
        logger.error(f"Error fetching budget ranges: {e}")

    acc_min = budget_ranges["acc_min"]
    acc_max = budget_ranges["acc_max"]
    act_min = budget_ranges["act_min"]
    act_max = budget_ranges["act_max"]
    meal_min = budget_ranges["meal_min"]
    meal_max = budget_ranges["meal_max"]
    trans_min = budget_ranges["trans_min"]
    trans_max = budget_ranges["trans_max"]

    accommodation_str = "\n".join([
        f"- {acc.get('name', 'Unknown Resort')}: ₹{acc.get('price_per_night', acc_min):,}/night, Book: {acc.get('url', '[No URL]')}"
        for acc in accommodations
    ]) or f"- Suggest luxury resorts in {destination} (₹{acc_min:,}–₹{acc_max:,}/night)."
    activity_str = "\n".join([
        f"- {act.get('name', 'Unknown Activity')}: ₹{act.get('cost_per_person', act_min):,}/person"
        for act in activities
    ]) or f"- Suggest beach activities in {destination} (₹{act_min:,}–₹{act_max:,}/person)."
    meal_str = "\n".join([
        f"- {meal.get('name', 'Unknown Meal')}: ₹{meal.get('cost_per_person', meal_min):,}/person"
        for meal in meals
    ]) or f"- Suggest {food_preference} meals in {destination} (₹{meal_min:,}–₹{meal_max:,}/person)."

    prompt = f"""
Generate a {duration}-day itinerary for a {effective_trip_type} trip to {destination} from {start_date} to {end_date} for {num_members} traveler(s) with a {budget_level} budget and {food_preference} food preference. Vibe: '{vibe}'.

**Requirements**:
1. **Structure**:
   - Title: "Itinerary for {destination}"
   - Vibe: Include the provided vibe.
   - For each day (Day {{n}} - YYYY-MM-DD: [Theme]):
     - Transport: Mode (e.g., water taxi), route (e.g., Airport to Resort A, 8 km), cost (₹{trans_min:,}–₹{trans_max:,}).
     - Accommodation: Name, cost (₹{acc_min:,}–₹{acc_max:,}/night), booking link (e.g., [Resort Name](URL)). None on departure day.
     - Activities: For Morning, Afternoon, Evening, Night, provide a specific activity (e.g., Snorkeling at Coral Gardens) with location, distance (km), cost (₹{act_min:,}–₹{act_max:,}/person), and a 1-sentence description. No 'None' entries.
     - Meals: Meal type (e.g., Dinner), non-vegetarian dish (e.g., Grilled Lobster), restaurant, cost (₹{meal_min:,}–₹{meal_max:,}/person).
     - Daily Budget: Sum of transport, accommodation (ceil(num_members/2) rooms), activities, meals (all * num_members). Format: "Daily Budget: ₹X,XXX"
2. **Data**:
   - Accommodations: {accommodation_str}
   - Activities: {activity_str}
   - Meals: {meal_str}
3. **Constraints**:
   - Dates: Strictly {', '.join(date_list)}.
   - Activities: Detailed, specific (e.g., Jet Ski Tour around Lagoon, not 'Water Sports').
   - Meals: Non-vegetarian only.
   - Transport: Clear routes (e.g., 'Resort A to Vaitape, 5 km').
   - Booking Links: Valid URLs (e.g., https://www.booking.com/...).
   - Costs: INR, realistic for 2025, derived from provided data or market rates.
4. **Output**:
   - Plain text, no markdown.
   - End with: "Total Estimated Budget: ₹X,XXX\nDownload PDF at: [itinerary_{destination.lower().replace(' ', '_')}_{start.strftime('%Y%m%d')}.pdf]"

Example:
Itinerary for Maldives
Vibe: Tropical serenity awaits!
Day 1 - 2025-06-01: Arrival
Transport: Speedboat from Airport to Resort A (10 km), Cost: ₹5000
Accommodation: Resort A, Cost: ₹80000/night, Book: [Resort A](https://www.booking.com/hotel/mv/a)
Activities:
- Morning: Lagoon Swim at Resort Beach (0 km), Cost: ₹0/person - Swim in crystal waters.
- Afternoon: Beach Yoga (0 km), Cost: ₹2000/person - Relax with guided yoga.
- Evening: Sunset Cruise (0 km), Cost: ₹6000/person - Sail with cocktails.
- Night: Stargazing (0 km), Cost: ₹1000/person - View constellations.
Meals:
- Dinner: Grilled Tuna at Beach Shack, Cost: ₹3000/person
Daily Budget: ₹86000
...
Total Estimated Budget: ₹250000
Download PDF at: [itinerary_maldives_20250601.pdf]
"""
    return prompt