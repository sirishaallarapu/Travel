import os
import re
from tavily import TavilyClient
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_KEY"))

def get_itinerary_prompt(data, vibe, effective_trip_type, valid, accommodations, activities, meals, budget, rooms_needed, extracted_data):
    destination = data.get("destination", "Unknown").capitalize()
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    num_members = data.get("num_members", 1)
    food_preference = data.get("food_preference", "non_veg").lower()
    budget_level = data.get("budget", "medium").lower()
    hotel_stars = data.get("hotel_stars", ['3', '4', '5'])
    flight_included = data.get("flight_included", True)

    try:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        duration = (end - start).days + 1
        date_list = [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(duration)]
    except Exception as e:
        logger.error(f"Date parsing error: {e}")
        duration = 4
        date_list = ["2025-06-11", "2025-06-12", "2025-06-13", "2025-06-14"]

    default_budget_ranges = {
        "low": {"acc_min": 2000, "acc_max": 5000, "act_min": 500, "act_max": 1500, "meal_min": 300, "meal_max": 800, "trans_min": 500, "trans_max": 2000},
        "medium": {"acc_min": 5000, "acc_max": 10000, "act_min": 1000, "act_max": 3000, "meal_min": 600, "meal_max": 1500, "trans_min": 800, "trans_max": 3000},
        "high": {"acc_min": 10000, "acc_max": 20000, "act_min": 2000, "act_max": 6000, "meal_min": 1200, "meal_max": 3000, "trans_min": 1500, "trans_max": 5000},
    }
    budget_ranges = default_budget_ranges.get(budget_level, default_budget_ranges["medium"])

    # Optional Tavily Web Search enhancement skipped for now (based on your instruction)

    acc_min = budget_ranges["acc_min"]
    acc_max = budget_ranges["acc_max"]
    act_min = budget_ranges["act_min"]
    act_max = budget_ranges["act_max"]
    meal_min = budget_ranges["meal_min"]
    meal_max = budget_ranges["meal_max"]
    trans_min = budget_ranges["trans_min"]
    trans_max = budget_ranges["trans_max"]

    # Filter accommodations by hotel stars
    accommodations = [
        acc for acc in accommodations if str(acc.get("star_rating", "3")) in hotel_stars
    ]

    accommodation_str = "\n".join([
        f"- {acc.get('name', 'Hotel')}: ₹{acc.get('price_per_night', acc_min):,}/night, Book: {acc.get('url', '[No URL]')}"
        for acc in accommodations
    ]) or f"- Suggest hotels in {destination} (₹{acc_min:,}–₹{acc_max:,}/night)."

    activity_str = "\n".join([
        f"- {act.get('name', 'Activity')}: ₹{act.get('cost_per_person', act_min):,}/person"
        for act in activities
    ]) or f"- Suggest activities for {effective_trip_type} in {destination} (₹{act_min:,}–₹{act_max:,}/person)."

    meal_str = "\n".join([
        f"- {meal.get('name', 'Meal')}: ₹{meal.get('cost_per_person', meal_min):,}/person"
        for meal in meals if food_preference in meal.get("type", "non_veg")
    ]) or f"- Suggest {food_preference} meals in {destination} (₹{meal_min:,}–₹{meal_max:,}/person)."

    prompt = f"""
Generate a {duration}-day itinerary for a {effective_trip_type} trip to {destination} from {start_date} to {end_date} for {num_members} traveler(s) with a {budget_level} budget and {food_preference} food preference. Vibe: '{vibe}'.

**Requirements**:
1. **Structure**:
   - Title: "Itinerary for {destination}"
   - Vibe: {vibe}
   - For each day (Day {{n}} – YYYY-MM-DD):
     - Transport:
       {"Include flight details for Day 1 and last day, and local transfers only for intermediate days." if flight_included else "Only include local transfers for each day."}
     - Accommodation:
       - Mention only on Day 1 and only again if hotel is changed.
     - Activities:
       - Morning, Afternoon, Evening, Night – include activity name, location, distance, cost (₹/person), and 1-line summary.
     - Meals:
       - List {food_preference} dishes only with restaurant name and cost/person.
     - Daily Budget:
       - Include a breakdown and total daily cost: ₹XX/person, ₹YY/total

2. **Content Data**:
   - **Hotels**:
     {accommodation_str}
   - **Activities**:
     {activity_str}
   - **Meals**:
     {meal_str}

3. **Constraints**:
   - Use these dates strictly: {', '.join(date_list)}
   - Mention prices realistically in INR (2025 estimated).
   - Don't repeat flights on middle days.
   - Highlight hotel booking links inline.
   - Meals should match user’s food preference.
   - Match budget_per_person × num_members in final cost.

4. **Output Format**:
   - Plain text only.
   - End with:
     Total Estimated Budget: ₹XXXXX
     Download PDF at: [itinerary_{destination.lower().replace(" ", "_")}_{start.strftime('%Y%m%d')}.pdf]
"""
    return prompt
