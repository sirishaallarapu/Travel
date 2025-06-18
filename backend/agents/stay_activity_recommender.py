# agents/stay_activity_recommender.py

import sqlite3
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def fetch_recommendations(
    db_path: str,
    destination: str,
    trip_type: str,
    food_preference: str,
    num_members: int,
    budget: str
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch hotel, activity, meal, and transport recommendations from the SQLite DB.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Fetch data with filters
        cursor.execute(
            "SELECT * FROM hotels WHERE destination = ? AND budget = ? LIMIT 5",
            (destination, budget)
        )
        hotels = cursor.fetchall()

        cursor.execute(
            "SELECT * FROM activities WHERE destination = ? AND type = ? LIMIT 6",
            (destination, trip_type)
        )
        activities = cursor.fetchall()

        cursor.execute(
            "SELECT * FROM meals WHERE destination = ? AND food_preference = ? LIMIT 6",
            (destination, food_preference)
        )
        meals = cursor.fetchall()

        cursor.execute(
            "SELECT * FROM transport WHERE destination = ? AND budget = ? LIMIT 3",
            (destination, budget)
        )
        transport = cursor.fetchall()

        if not hotels or not activities or not meals or not transport:
            raise ValueError("Insufficient data in the database. Please scrape data first.")

        recommendations = {
            "hotels": [
                {"name": h[1], "price": h[2], "rating": h[3], "num_reviews": h[4], "budget": h[5]} for h in hotels
            ],
            "activities": [
                {"name": a[1], "description": a[2], "price": a[3], "type": a[4]} for a in activities
            ],
            "meals": [
                {"name": m[1], "description": m[2], "price": m[3], "rating": m[4], "num_reviews": m[5], "food_preference": m[6]} for m in meals
            ],
            "transport": [
                {"name": t[1], "description": t[2], "price": t[3], "budget": t[4]} for t in transport
            ]
        }

        return recommendations

    except Exception as e:
        logger.error(f"❌ Error fetching recommendations: {e}")
        raise

    finally:
        if conn:
            conn.close()
