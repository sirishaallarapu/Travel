import re
import os
import logging
import traceback
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import google.generativeai as genai
from dotenv import load_dotenv
import random
import math

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ItineraryAgent:
    BUDGET_TIERS = {
        "budget-friendly": {
            "flight": Decimal("10000"),
            "hotel_per_night": Decimal("8000"),
            "daily_activity": Decimal("2000"),
            "meal": Decimal("1500"),
        },
        "mid-range": {
            "flight": Decimal("15000"),
            "hotel_per_night": Decimal("12000"),
            "daily_activity": Decimal("3000"),
            "meal": Decimal("2000"),
        },
        "premium": {
            "flight": Decimal("25000"),
            "hotel_per_night": Decimal("25000"),
            "daily_activity": Decimal("8000"),
            "meal": Decimal("5000"),
        }
    }

    def generate_with_gemini(self, destination: str, start_date: str, duration: int, trip_type: str,
                             food_preference: str, num_members: int, budget_preference: str,
                             flight_included=False, hotel_stars=['5'], from_location: str = "Hyderabad, India",
                             retry: bool = True, include_last_day_activities=False) -> dict:
        logger.info(f"Starting generation with: destination={destination}, start_date={start_date}, duration={duration}, trip_type={trip_type}, "
                    f"food_preference={food_preference}, num_members={num_members}, budget_preference={budget_preference}, "
                    f"flight_included={flight_included}, hotel_stars={hotel_stars}, from_location={from_location}, "
                    f"include_last_day_activities={include_last_day_activities}")

        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-2.0-flash")

        if budget_preference not in self.BUDGET_TIERS:
            logger.warning(f"Invalid budget preference '{budget_preference}'. Defaulting to 'mid-range'.")
            budget_preference = "mid-range"
        tier = self.BUDGET_TIERS[budget_preference]

        logger.info(f"Base daily budget guidance for {budget_preference}: {tier}")

        flight_prompt = "Include flights and transfers" if flight_included else "Do not include flights or airport transfers. Explicitly exclude any mention of flights or airport-related transfers in the itinerary."
        luxury_instruction = "Enhance with 5-star hotels, private transfers, spa experiences, and exclusive activities." if budget_preference == "premium" else ""
        mid_range_instruction = "Use 4-star hotels and moderate activities." if budget_preference == "mid-range" else ""
        budget_friendly_instruction = f"Use {', '.join(hotel_stars)}-star hotels and economical activities." if budget_preference == "budget-friendly" else ""

        # Enforce food preference in meals
        food_instruction = f"All meals (breakfast, lunch, dinner) must be {food_preference} options only, with appropriate dishes reflecting this preference (e.g., non-veg includes meat/fish, veg excludes them)."

        prompt = f"""
You are a highly skilled travel planner crafting a detailed {duration}-night itinerary for **{destination}**, tailored for a **{trip_type.lower()}** trip, with rich, narrative-style descriptions.

✈️ {flight_prompt}. If flights are included, include a flight from {from_location} to {destination} on Day 1 and a return flight on Day {duration + 1}. Use correct airport codes and realistic durations. Include an estimated flight cost range prefixed with '~₹' (e.g., ~₹2500 - ~₹4500 per person) in the Flights & Transfers section for Day 1 and Day {duration + 1}, but do not include it in the daily budget. Include appropriate transfers with costs prefixed with '~₹' listed separately in the 'Flights & Transfers' section for each day. If flights are not included, ensure no flight or airport transfer details are mentioned.

💰 IMPORTANT:
- Prefix all costs (activities, meals, hotel, transfers, flights) with '~₹' to indicate estimates.
- The 'Total Estimated Cost for the Day' should include only the costs of activities and meals (prefixed with '~₹'), excluding transfer costs.
- Ensure every meal (breakfast, lunch, dinner) includes a cost in the format 'Cost: ~₹<amount> per person', even with narrative descriptions, and strictly adheres to the {food_preference} preference. On Day {duration + 1} if include_last_day_activities is true and flights are not included, include non-zero costs for activities and meals; if flights are included, exclude activities and meals on Day {duration + 1}.
- Include four activities per day (morning, afternoon, evening, night) for Days 1 to {duration}, each with a 2–3 sentence narrative and "Cost: ~₹<amount> per person" based on the budget tier.
- Include three meals per day (breakfast, lunch, dinner) for Days 1 to {duration} with similar narratives and costs.
- Day {duration + 1} should include departure details (flight and transfer) if flights are included, with no activities or meals. If flights are not included and include_last_day_activities is true, include four activities and three meals with non-zero costs based on the budget tier; otherwise, exclude activities, meals, and hotel costs on Day {duration + 1}.
- DO NOT write “Total Estimated Cost for the Day” manually; it will be calculated automatically.
- In the Hotel section, list 2-3 hotel options with their names, star ratings (strictly matching the provided hotel_stars preference), brief descriptions (1-2 sentences), and costs per night prefixed with '~₹'.

Hotel preference: {', '.join(hotel_stars)} stars.
Travelers: {num_members}
From: {from_location} to {destination}
Start date: {start_date}, Duration: {duration + 1 if flight_included else duration} days
Food preference: {food_preference}

Structure each day like this:
---
Day X – YYYY-MM-DD (Day):
Day Plan: [A short, engaging overview]

Flights & Transfers:
- [Narrative description of flight or transfer, including cost range if applicable]

Hotel:
- [Hotel 1 Name] ([star]-star): [Brief description]. Cost: ~₹[amount] per night.
- [Hotel 2 Name] ([star]-star): [Brief description]. Cost: ~₹[amount] per night.
- [Hotel 3 Name] ([star]-star): [Brief description]. Cost: ~₹[amount] per night. (optional, include only if available)

Activity:
- Morning: [2–3 sentence narrative] Cost: ~₹[amount] per person (exclude on Day {duration + 1} unless flights are not included and include_last_day_activities is true, then use non-zero cost)
- Afternoon: [2–3 sentence narrative] Cost: ~₹[amount] per person (exclude on Day {duration + 1} unless flights are not included and include_last_day_activities is true, then use non-zero cost)
- Evening: [2–3 sentence narrative] Cost: ~₹[amount] per person (exclude on Day {duration + 1} unless flights are not included and include_last_day_activities is true, then use non-zero cost)
- Night: [2–3 sentence narrative] Cost: ~₹[amount] per person (exclude on Day {duration + 1} unless flights are not included and include_last_day_activities is true, then use non-zero cost)

Meals:
- Breakfast: [2–3 sentence narrative] Cost: ~₹[amount] per person (exclude on Day {duration + 1} unless flights are not included and include_last_day_activities is true, then use non-zero cost)
- Lunch: [2–3 sentence narrative] Cost: ~₹[amount] per person (exclude on Day {duration + 1} unless flights are not included and include_last_day_activities is true, then use non-zero cost)
- Dinner: [2–3 sentence narrative] Cost: ~₹[amount] per person (exclude on Day {duration + 1} unless flights are not included and include_last_day_activities is true, then use non-zero cost)

Total Estimated Cost for the Day: ~₹[amount] per person (excludes flights, transfers, and hotels) (exclude on Day {duration + 1}, includes only activities and meals)
---
"""

        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            dates = [(start_date_obj + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(duration + (1 if flight_included else 0))]
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            logger.info(f"Full Gemini response: {raw_text}")

            days_found = re.findall(r"Day\s+\d+\s*–\s*(\d{4}-\d{2}-\d{2})", raw_text)
            if not raw_text or len(days_found) < duration + (1 if flight_included else 0):
                if retry:
                    logger.warning("Gemini returned invalid or incomplete response. Retrying...")
                    return self.generate_with_gemini(destination, start_date, duration, trip_type, food_preference,
                                                    num_members, budget_preference, flight_included,
                                                    hotel_stars, from_location, retry=False, include_last_day_activities=include_last_day_activities)
                return self._fallback_itinerary(destination, start_date, duration, trip_type, num_members, budget_preference, num_members, hotel_stars)

            days = re.findall(r"Day\s+(\d+)\s*–\s*(\d{4}-\d{2}-\d{2})\s*\(.*\)", raw_text)
            itinerary_dict = {}
            total_cost = Decimal('0')  # Activities and meals only
            total_transfer_cost = Decimal('0')  # Separate transfer costs
            flight_cost = Decimal('0')
            hotel_cost = Decimal('0')

            all_hotels = []
            all_flights = []
            all_transfers = []
            all_activities = []
            all_meals = []

            for day_num, day_date in days[:duration + (1 if flight_included else 0)]:
                transfer_cost = Decimal('0')
                activity_costs = []
                meal_costs = []
                day_num = int(day_num)

                block = re.search(
                    rf"Day\s+{day_num}\s*–\s*{day_date}\s*\(.*\)[\s\S]*?(?=(?:Day\s+\d+\s*–\s*\d{{4}}-\d{{2}}-\d{{2}}\s*\(|$))",
                    raw_text, re.DOTALL
                )
                if not block:
                    continue

                block_text = block.group(0)

                day_plan_text = self._extract_section(
                    block_text,
                    r"Day Plan:\s*(.*?)(?=\n(?:Flights & Transfers|Hotel|Activity|Meals|\Z))"
                )

                flights_and_transfers = self._extract_lines(
                    block_text, r"Flights & Transfers:\s*((?:.|\n)*?)(?=\n(?:Hotel|Activity|Meals|\Z))"
                )

                # Filter out flight-related lines if flight_included is False
                if not flight_included:
                    flights_and_transfers = [line for line in flights_and_transfers if "Flight" not in line and "Airport" not in line]

                hotels = [h for h in self._extract_lines(
                    block_text,
                    r"Hotel:\s*((?:.|\n)*?)(?=\n(?:Activity|Meals|\Z))",
                    strip_stars=True
                ) if "Cost:" in h and (day_num <= duration or (day_num == duration + 1 and not flight_included)) and any(f"{star}-star" in h for star in hotel_stars)]

                activities = self._extract_lines(
                    block_text, r"Activity:\s*((?:.|\n)*?)(?=\n(?:Meals|Total|\Z))", strip_stars=True
                )

                meals = self._extract_lines(
                    block_text, r"Meals:\s*((?:.|\n)*?)(?=\n(?:Total|\Z))", strip_stars=True
                )

                cost_pattern = re.compile(r"Cost[:\s]*~₹([\d,]+)(?:\s*per\s*person)?", re.IGNORECASE)

                for item in flights_and_transfers:
                    if 'Transfer' in item and not flight_included:  # Only process transfers, skip flights
                        match = cost_pattern.search(item)
                        if match:
                            cost = Decimal(match.group(1).replace(",", ""))
                            transfer_cost += cost
                            total_transfer_cost += cost
                    elif 'Flight' in item and flight_included and day_num in [1, duration + 1]:
                        match = re.search(r"Estimated Flight Cost: ~₹(\d+)-~₹(\d+)", item)
                        if match:
                            flight_cost += Decimal((int(match.group(1)) + int(match.group(2))) / 2) * num_members
                        else:
                            logger.warning(f"No flight cost parsed for day {day_num}: {item}")
                            flight_cost += tier["flight"] * num_members  # Fallback to tier if not parsed

                activity_slots = {'Morning': None, 'Afternoon': None, 'Evening': None, 'Night': None}
                for act in activities:
                    for slot in activity_slots.keys():
                        if slot.lower() in act.lower() and activity_slots[slot] is None and (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities)):
                            activity_slots[slot] = act
                            break

                filtered_activities = [act if act else f"{slot}: A relaxing activity is planned. Cost: ~₹{tier['daily_activity'] / 4} per person" for slot, act in activity_slots.items() if (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities))]
                # Ensure non-zero costs on last day if include_last_day_activities is true and no flights
                if day_num == duration + 1 and not flight_included and include_last_day_activities:
                    for i in range(len(filtered_activities)):
                        if "Cost: ~₹0" in filtered_activities[i]:
                            filtered_activities[i] = filtered_activities[i].replace("Cost: ~₹0", f"Cost: ~₹{tier['daily_activity'] / 4}")

                for i in range(len(filtered_activities)):
                    if len(filtered_activities[i].split("Cost:")[0].strip().split()) < 10 and (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities)):
                        refine_prompt = f"Rewrite this activity as a 2-3 sentence narrative with vivid descriptions: {filtered_activities[i]}"
                        refine_response = model.generate_content(refine_prompt)
                        refined_text = refine_response.text.strip()
                        if "Cost:" not in refined_text and (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities)):
                            refined_text += f" Cost: ~₹{tier['daily_activity'] / 4}"
                        filtered_activities[i] = refined_text

                meal_slots = {'Breakfast': None, 'Lunch': None, 'Dinner': None}
                for meal in meals:
                    for slot in meal_slots.keys():
                        if slot.lower() in meal.lower() and meal_slots[slot] is None and (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities)):
                            meal_slots[slot] = meal
                            break

                filtered_meals = [meal if meal else f"{slot}: A light meal is planned. Cost: ~₹{tier['meal'] / 3} per person" for slot, meal in meal_slots.items() if (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities))]
                for i in range(len(filtered_meals)):
                    if len(filtered_meals[i].split("Cost:")[0].strip().split()) < 10 and (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities)):
                        refine_prompt = f"Rewrite this meal as a 2-3 sentence narrative with vivid descriptions: {filtered_meals[i]}"
                        refine_response = model.generate_content(refine_prompt)
                        refined_text = refine_response.text.strip() + f" Cost: ~₹{tier['meal'] / 3}" if "Cost:" not in refine_response.text.strip() and (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities)) else refine_response.text.strip()
                        filtered_meals[i] = refined_text

                for act in filtered_activities:
                    match = cost_pattern.search(act)
                    if match:
                        activity_costs.append(Decimal(match.group(1).replace(",", "")))
                    elif day_num == duration + 1 and not flight_included and include_last_day_activities:
                        activity_costs.append(tier["daily_activity"] / 4)  # Fallback cost

                for meal in filtered_meals:
                    match = cost_pattern.search(meal)
                    if match:
                        meal_costs.append(Decimal(match.group(1).replace(",", "")))
                    elif day_num == duration + 1 and not flight_included and include_last_day_activities:
                        meal_costs.append(tier["meal"] / 3)  # Fallback cost

                total_day_cost = sum(activity_costs) + sum(meal_costs)

                itinerary_dict[f"Day {day_num} – {day_date}"] = {
                    "Day Plan": [day_plan_text.strip()] if day_plan_text else [],
                    "Flights & Transfers": flights_and_transfers,
                    "Hotel": hotels,
                    "Activity": filtered_activities if (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities)) else [],
                    "Meals": filtered_meals if (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities)) else [],
                    "Total Cost": [f"Total Estimated Cost for the Day: ~₹{total_day_cost} per person (excludes flights, transfers, and hotels)"] if (day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities)) else []
                }

                if day_num <= duration or (day_num == duration + 1 and not flight_included and include_last_day_activities):
                    total_cost += total_day_cost

                    # Append collected details
                    all_hotels.extend(hotels)
                    for line in flights_and_transfers:
                        if 'Flight' not in line and 'Airport' not in line:  # Exclude flight lines
                            if 'Transfer' in line:
                                all_transfers.append(line)
                        elif 'Flight' in line and flight_included:
                            all_flights.append(line)
                    all_activities.extend(filtered_activities)
                    all_meals.extend(filtered_meals)

            # Only calculate flight_cost if flight_included is True
            if flight_included and flight_cost == Decimal('0'):
                logger.warning("No flight cost detected, using tier fallback.")
                flight_cost = tier["flight"] * num_members * 2  # Round trip

            try:
                hotel_price_str = [h for h in all_hotels if 'Cost:' in h][0].split('Cost: ~₹')[1].split(' per night')[0].replace(",", "").strip()
                hotel_price = Decimal(hotel_price_str)
                if hotel_price < tier["hotel_per_night"] - 5000 or hotel_price > tier["hotel_per_night"] + 5000:
                    logger.warning(f"Hotel price ~₹{hotel_price} outside {budget_preference} range ~₹{tier['hotel_per_night']-5000}–~₹{tier['hotel_per_night']+5000}, adjusting to tier default.")
                    hotel_price = tier["hotel_per_night"]
            except (IndexError, ValueError, InvalidOperation) as e:
                logger.warning(f"Hotel price parsing failed: {e}")
                hotel_price = tier["hotel_per_night"]

            hotel_cost = hotel_price * duration * math.ceil(num_members / 2)
            logger.info(f"Hotel cost: ~₹{hotel_cost}, Hotel price: ~₹{hotel_price}")

            logger.info(f"Total transfer cost: ~₹{total_transfer_cost}")

            daily_total = total_cost  # Per person (activities and meals only)
            grand_total = flight_cost + hotel_cost + (daily_total * num_members) + total_transfer_cost
            logger.info(f"Debug values - flight_cost: {flight_cost}, hotel_cost: {hotel_cost}, daily_total: {daily_total}, total_transfer_cost: {total_transfer_cost}, grand_total: {grand_total}")

            return {
                "itinerary": itinerary_dict,
                "vibe": f"{trip_type.title()} Vibe in {destination}",
                "total_budget": grand_total,
                "num_members": num_members,
                "duration": duration,
                "flights_and_transfers": {
                    "flights": all_flights if flight_included else [],
                    "transfers": all_transfers
                },
                "hotel": {
                    "name": ', '.join(h.split('(')[0].strip() for h in all_hotels) if all_hotels else f"Generic {hotel_stars[0]}-Star Hotel",
                    "nights": duration,
                    "rating": f"{hotel_stars[0]}.0/5",
                    "price": f"~₹{hotel_price} per night"
                },
                "activities": all_activities,
                "meals": all_meals,
                "meta": {
                    "destination": destination,
                    "flight_included": flight_included,
                    "budget_preference": budget_preference,
                    "summary": f"This is a {budget_preference} {trip_type} trip to {destination} for {num_members} {'person' if num_members == 1 else 'people'}, with an estimated total cost of ~₹{int(grand_total):,}."
                }
            }

        except Exception as e:
            logger.error(f"Gemini generation error: {str(e)}\n{traceback.format_exc()}")
            return self._fallback_itinerary(destination, start_date, duration, trip_type, num_members, budget_preference, num_members, hotel_stars)

    def _extract_lines(self, text, pattern, strip_stars=False):
        section = re.search(pattern, text, re.DOTALL)
        if not section:
            return []
        lines = [line.strip("- ").strip() for line in section.group(1).split("\n") if line.strip()]
        return [line.replace("**", "").strip() for line in lines] if strip_stars else lines

    def _extract_cost(self, cost_lines):
        for line in cost_lines:
            match = re.search(r"~₹([\d,]+)", line)
            if match:
                return Decimal(match.group(1).replace(",", ""))
        return Decimal('0')

    def _extract_section(self, text, pattern):
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _fallback_itinerary(self, destination, start_date, duration, trip_type, num_members, budget_preference="mid-range", requested_num_members=1, hotel_stars=['5'], reason=""):
        tier = self.BUDGET_TIERS.get(budget_preference, self.BUDGET_TIERS["mid-range"])
        flight_cost = Decimal('0')  # No flight cost in fallback unless specified
        hotel_cost = tier["hotel_per_night"] * duration * math.ceil(requested_num_members / 2)
        daily_total = (tier["daily_activity"] + tier["meal"]) * duration * requested_num_members
        grand_total = flight_cost + hotel_cost + daily_total

        return {
            "itinerary": {
                f"Day 1 – {start_date}": {
                    "Day Plan": [reason or f"Default itinerary for {destination} due to generation failure."],
                    "Flights & Transfers": [],
                    "Hotel": [f"Name: Generic {hotel_stars[0]}-Star Hotel Cost: ~₹{tier['hotel_per_night']} per night"],
                    "Activity": [
                        f"Morning: Guided tour. Cost: ~₹{tier['daily_activity'] * Decimal('0.5') / requested_num_members} per person",
                        f"Afternoon: Local experience. Cost: ~₹{tier['daily_activity'] * Decimal('0.3') / requested_num_members} per person",
                        f"Evening: Dining. Cost: ~₹{tier['meal'] / requested_num_members} per person",
                        f"Night: Relaxation. Cost: ~₹0 per person"
                    ],
                    "Meals": [
                        f"Breakfast: Buffet meal. Cost: ~₹{tier['meal'] * Decimal('0.4') / requested_num_members} per person",
                        f"Lunch: Local cuisine. Cost: ~₹{tier['meal'] * Decimal('0.4') / requested_num_members} per person",
                        f"Dinner: Special meal. Cost: ~₹{tier['meal'] * Decimal('0.6') / requested_num_members} per person"
                    ],
                    "Total Cost": [f"Total Estimated Cost for the Day: ~₹{(tier['daily_activity'] + tier['meal']) / requested_num_members} per person (excludes flights, transfers, and hotels)"]
                }
            },
            "vibe": f"{trip_type.title()} Vibe in {destination}",
            "total_budget": grand_total,
            "duration": duration,
            "num_members": requested_num_members,
            "flights_and_transfers": {"flights": [], "transfers": []},
            "hotel": {"name": f"Generic {hotel_stars[0]}-Star Hotel", "nights": duration, "rating": f"{hotel_stars[0]}/5", "price": f"~₹{tier['hotel_per_night']} per night"},
            "activities": [],
            "meals": [],
            "meta": {"destination": destination, "flight_included": False, "budget_preference": budget_preference, "summary": f"This is a {budget_preference} {trip_type} trip to {destination} for {requested_num_members} {'person' if requested_num_members == 1 else 'people'}, with an estimated total cost of ~₹{int(grand_total):,}."}
        }