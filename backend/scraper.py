import os
import requests
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
from requests.exceptions import HTTPError

load_dotenv()  # Load API keys from .env

# Destination mapping for ambiguous locations
DESTINATION_MAPPING = {
    "maldives": "Malé, Maldives",
    # Add other mappings as needed
}

# Country code mapping for destinations
COUNTRY_CODE_MAPPING = {
    "maldives": "MV",
    "malé, maldives": "MV",
    "bangkok, thailand": "TH",
    # Add other mappings as needed
}

def create_tables(db_path):
    """Create database tables if they don’t exist."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hotels 
                 (id INTEGER PRIMARY KEY, destination TEXT, name TEXT, price REAL, rating REAL, num_reviews INTEGER, budget TEXT, last_updated TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS activities 
                 (id INTEGER PRIMARY KEY, destination TEXT, name TEXT, description TEXT, price REAL, type TEXT, last_updated TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS meals 
                 (id INTEGER PRIMARY KEY, destination TEXT, name TEXT, description TEXT, price REAL, rating REAL, num_reviews INTEGER, food_preference TEXT, last_updated TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transport 
                 (id INTEGER PRIMARY KEY, destination TEXT, name TEXT, description TEXT, price REAL, budget TEXT, last_updated TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS destination_cache 
                 (destination TEXT PRIMARY KEY, dest_id TEXT, last_updated TEXT)''')
    conn.commit()
    conn.close()

def get_cached_dest_id(db_path, destination):
    """Check if dest_id is cached in the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT dest_id, last_updated FROM destination_cache WHERE destination = ?", (destination,))
    result = c.fetchone()
    conn.close()
    if result:
        dest_id, last_updated = result
        # Check if cache is still valid (e.g., less than 7 days old)
        last_updated_date = datetime.fromisoformat(last_updated)
        if (datetime.now() - last_updated_date).days < 7:
            print(f"Using cached dest_id for {destination}: {dest_id}")
            return dest_id
    return None

def cache_dest_id(db_path, destination, dest_id):
    """Cache the dest_id in the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    c.execute("INSERT OR REPLACE INTO destination_cache (destination, dest_id, last_updated) VALUES (?, ?, ?)",
              (destination, dest_id, timestamp))
    conn.commit()
    conn.close()
    print(f"Cached dest_id for {destination}: {dest_id}")

def fetch_dest_id_hotelscom(destination, retries=3, backoff_factor=5):
    """Fetch destination ID from Hotels.com API as a fallback."""
    url = "https://hotels-com-provider.p.rapidapi.com/v2/regions"
    querystring = {"query": destination, "locale": "en_US"}
    headers = {
        "X-RapidAPI-Key": os.getenv("HOTELS_API_KEY"),
        "X-RapidAPI-Host": "hotels-com-provider.p.rapidapi.com"
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=5)
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining and int(remaining) < 5:
                print(f"Warning: Only {remaining} requests remaining before hitting Hotels.com API rate limit.")
            response.raise_for_status()
            break
        except HTTPError as e:
            if response.status_code == 429:
                if attempt == retries - 1:
                    raise Exception(f"Hotels.com API rate limit exceeded for regions: {str(e)}")
                wait_time = backoff_factor * (2 ** attempt)
                print(f"Rate limit hit for Hotels.com regions. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Hotels.com API error for regions: {str(e)}")
    
    data = response.json()
    print(f"Hotels.com API regions response for {destination}: {data}")
    regions = data.get("data", [])
    if not regions:
        raise Exception(f"No regions found for {destination} on Hotels.com API")
    return regions[0].get("regionId")  # Hotels.com returns 'regionId' as the destination ID

def fetch_hotels_hotelscom(destination, checkin, checkout, adults=1, rooms=1, retries=3, backoff_factor=5):
    """Fetch hotels from Hotels.com API as a fallback."""
    # First, get the destination ID
    dest_id = fetch_dest_id_hotelscom(destination, retries, backoff_factor)
    
    url = "https://hotels-com-provider.p.rapidapi.com/v2/hotels/search"
    querystring = {
        "region_id": dest_id,
        "check_in_date": checkin,
        "check_out_date": checkout,
        "adults_number": adults,
        "room_quantity": rooms,
        "currency": "USD",
        "locale": "en_US"
    }
    headers = {
        "X-RapidAPI-Key": os.getenv("HOTELS_API_KEY"),
        "X-RapidAPI-Host": "hotels-com-provider.p.rapidapi.com"
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=5)
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining and int(remaining) < 5:
                print(f"Warning: Only {remaining} requests remaining before hitting Hotels.com API rate limit.")
            response.raise_for_status()
            break
        except HTTPError as e:
            if response.status_code == 429:
                if attempt == retries - 1:
                    raise Exception(f"Hotels.com API rate limit exceeded for searchHotels: {str(e)}")
                wait_time = backoff_factor * (2 ** attempt)
                print(f"Rate limit hit for Hotels.com searchHotels. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Hotels.com API error for searchHotels: {str(e)}")
    
    data = response.json()
    print(f"Hotels.com API searchHotels response for {destination}: {data}")
    hotels = data.get("data", {}).get("hotels", [])
    if not hotels:
        raise Exception(f"No hotels found for {destination} on Hotels.com API for dates {checkin} to {checkout}")
    
    return [
        {
            "name": hotel.get("name", "Unknown Hotel"),
            "price": float(hotel.get("price", {}).get("lead", {}).get("amount", 0)),
            "rating": float(hotel.get("rating", {}).get("value", 0)),
            "num_reviews": int(hotel.get("rating", {}).get("count", 0))
        }
        for hotel in hotels[:5]
    ]

def fetch_hotels_booking_com(destination, checkin, checkout, adults=1, rooms=1, retries=3, backoff_factor=5, db_path="travel_data.db"):
    """Fetch hotels from Booking.com API with fallback to Hotels.com API."""
    use_hotelscom = False
    cached_dest_id = get_cached_dest_id(db_path, destination)
    if cached_dest_id:
        dest_id = cached_dest_id
    else:
        url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
        querystring = {"query": destination}
        headers = {
            "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
            "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
        }
        
        try:
            for attempt in range(retries):
                try:
                    response = requests.get(url, headers=headers, params=querystring, timeout=5)
                    remaining = response.headers.get("X-RateLimit-Remaining")
                    if remaining and int(remaining) < 5:
                        print(f"Warning: Only {remaining} requests remaining before hitting Booking.com rate limit.")
                    response.raise_for_status()
                    break
                except HTTPError as e:
                    if response.status_code == 429:
                        if attempt == retries - 1:
                            raise
                        wait_time = backoff_factor * (2 ** attempt)
                        print(f"Rate limit hit for searchDestination. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise
            data = response.json()
            print(f"Booking.com searchDestination response for {destination}: {data}")
            if not data.get("data"):
                raise Exception(f"No destination data found for {destination}")
            dest_id = data["data"][0]["dest_id"]
            cache_dest_id(db_path, destination, dest_id)
        except HTTPError as e:
            if e.response.status_code in [429, 503]:
                print(f"Booking.com searchDestination failed with {e.response.status_code}. Falling back to Hotels.com API...")
                dest_id = fetch_dest_id_hotelscom(destination, retries, backoff_factor)
                cache_dest_id(db_path, destination, dest_id)
                use_hotelscom = True
            else:
                raise

    if use_hotelscom:
        print("Using Hotels.com API for hotel search since searchDestination used Hotels.com.")
        return fetch_hotels_hotelscom(destination, checkin, checkout, adults, rooms, retries, backoff_factor)

    url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
    querystring = {
        "dest_id": dest_id,
        "arrival_date": checkin,
        "departure_date": checkout,
        "adults": adults,
        "room_qty": rooms,
        "currency_code": "USD"
    }
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
    }
    
    try:
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=headers, params=querystring, timeout=5)
                remaining = response.headers.get("X-RateLimit-Remaining")
                if remaining and int(remaining) < 5:
                    print(f"Warning: Only {remaining} requests remaining before hitting Booking.com rate limit.")
                response.raise_for_status()
                break
            except HTTPError as e:
                if response.status_code == 429:
                    if attempt == retries - 1:
                        raise
                    wait_time = backoff_factor * (2 ** attempt)
                    print(f"Rate limit hit for searchHotels. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise
        data = response.json()
        print(f"Booking.com searchHotels response for {destination}: {data}")
        hotels = data.get("data", {}).get("hotels", [])
        if not hotels:
            raise Exception(f"No hotels found for {destination} on Booking.com for dates {checkin} to {checkout}")
        return [
            {
                "name": hotel["property"]["name"],
                "price": hotel["priceBreakdown"]["grossPrice"]["value"],
                "rating": hotel["property"]["reviewScore"],
                "num_reviews": hotel["property"]["reviewCount"],
            }
            for hotel in hotels[:5]
        ]
    except HTTPError as e:
        if e.response.status_code in [429, 503]:
            print(f"Booking.com searchHotels failed with {e.response.status_code}. Falling back to Hotels.com API...")
            return fetch_hotels_hotelscom(destination, checkin, checkout, adults, rooms, retries, backoff_factor)
        raise

def get_location_id(destination):
    """Get location ID for TripAdvisor using a search API."""
    destination = DESTINATION_MAPPING.get(destination.lower(), destination)
    url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchLocation"
    querystring = {"query": destination}
    headers = {
        "X-RapidAPI-Key": os.getenv("TRIPADVISOR_API_KEY"),
        "X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
    }
    response = requests.get(url, headers=headers, params=querystring, timeout=5)
    response.raise_for_status()
    data = response.json()
    if not data.get("data") or len(data["data"]) == 0:
        raise Exception(f"No location data found for {destination} on TripAdvisor")
    location_id = data["data"][0]["locationId"]
    return location_id

def get_coordinates(destination):
    """Get latitude and longitude for a destination using Google Geocoding API."""
    destination = DESTINATION_MAPPING.get(destination.lower(), destination)
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={destination}&key={os.getenv('GOOGLE_API_KEY')}"
    response = requests.get(geocode_url, timeout=5)
    response.raise_for_status()
    data = response.json()
    if not data.get("results") or len(data["results"]) == 0:
        raise Exception(f"No geocoding results found for {destination}")
    lat = data["results"][0]["geometry"]["location"]["lat"]
    lng = data["results"][0]["geometry"]["location"]["lng"]
    return lat, lng

import os
import sqlite3
import requests
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from geopy.geocoders import Nominatim

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Country code mapping for car rentals
COUNTRY_CODE_MAPPING = {
    "maldives": "MV",
    "goa": "IN",
    "paris": "FR",
    "new york": "US",
    "tokyo": "JP",
}

# ----------- Helper Functions ------------

def get_coordinates(destination):
    geolocator = Nominatim(user_agent="trip_app")
    location = geolocator.geocode(destination)
    if location:
        return location.latitude, location.longitude
    raise ValueError(f"Could not get coordinates for {destination}")

def get_location_id(destination):
    mock_ids = {
        "maldives": "315247",
        "goa": "297604",
        "paris": "187147",
        "new york": "60763",
    }
    return mock_ids.get(destination.lower(), "315247")

def create_tables(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hotels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination TEXT, name TEXT, price REAL, rating REAL, num_reviews INTEGER, budget TEXT, last_updated TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination TEXT, name TEXT, description TEXT, price REAL, type TEXT, last_updated TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination TEXT, name TEXT, description TEXT, price REAL, rating REAL, num_reviews INTEGER, food_preference TEXT, last_updated TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS transport (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        destination TEXT, name TEXT, description TEXT, price REAL, budget TEXT, last_updated TEXT)''')

    conn.commit()
    conn.close()

# ------------ API Fetchers ----------------

def fetch_hotels_booking_com(destination, checkin, checkout, db_path):
    # Dummy hotels for testing
    return [
        {"name": "Ocean Breeze Resort", "price": 200, "rating": 4.5, "num_reviews": 321},
        {"name": "Seaside Villas", "price": 150, "rating": 4.2, "num_reviews": 198},
    ]

def fetch_activities_google_places(destination, trip_type):
    try:
        lat, lng = get_coordinates(destination)
        places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        querystring = {
            "location": f"{lat},{lng}",
            "radius": 5000,
            "type": "tourist_attraction",
            "key": os.getenv("GOOGLE_API_KEY")
        }
        response = requests.get(places_url, params=querystring, timeout=5)
        response.raise_for_status()
        places = response.json().get("results", [])
        return [
            {"name": p["name"], "description": p.get("vicinity", "No description"), "price": 0, "type": trip_type}
            for p in places[:5]
        ]
    except Exception as e:
        logger.error(f"Google Places API failed: {e}")
        return fetch_activities_tripadvisor(destination, trip_type)

def fetch_activities_tripadvisor(destination, trip_type):
    try:
        location_id = get_location_id(destination)
        url = "https://tripadvisor16.p.rapidapi.com/api/v1/hotels/searchAttractions"
        headers = {
            "X-RapidAPI-Key": os.getenv("TRIPADVISOR_API_KEY"),
            "X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params={"locationId": location_id}, timeout=10)
        response.raise_for_status()
        attractions = response.json().get("data", [])
        return [
            {"name": a["name"], "description": a.get("description", "No description"), "price": 0, "type": trip_type}
            for a in attractions[:5]
        ]
    except Exception as e:
        logger.error(f"TripAdvisor API failed for activities: {e}")
        return []

def fetch_meals_tripadvisor(destination, food_preference):
    try:
        location_id = get_location_id(destination)
        url = "https://tripadvisor16.p.rapidapi.com/api/v1/restaurant/searchRestaurants"
        headers = {
            "X-RapidAPI-Key": os.getenv("TRIPADVISOR_API_KEY"),
            "X-RapidAPI-Host": "tripadvisor16.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params={"locationId": location_id}, timeout=10)
        response.raise_for_status()
        restaurants = response.json().get("data", {}).get("data", [])
        return [
            {
                "name": r["name"],
                "description": r.get("location", {}).get("address", "No description"),
                "price": 0,
                "rating": float(r.get("averageRating", 0)),
                "num_reviews": int(r.get("reviewCount", 0)),
                "food_preference": food_preference,
            }
            for r in restaurants[:5]
        ]
    except Exception as e:
        logger.error(f"TripAdvisor API failed for meals: {e}")
        return fetch_meals_yelp(destination, food_preference)

def fetch_meals_yelp(destination, food_preference):
    try:
        lat, lng = get_coordinates(destination)
        url = "https://yelp-api3.p.rapidapi.com/api/search-businesses"
        headers = {
            "X-RapidAPI-Key": os.getenv("YELP_API_KEY"),
            "X-RapidAPI-Host": "yelp-api3.p.rapidapi.com"
        }
        querystring = {
            "latitude": lat,
            "longitude": lng,
            "term": "restaurants",
            "categories": food_preference.lower().replace(" ", ""),
            "limit": 5
        }
        response = requests.get(url, headers=headers, params=querystring, timeout=5)
        response.raise_for_status()
        businesses = response.json().get("businesses", [])
        return [
            {
                "name": b["name"],
                "description": b.get("location", {}).get("address1", "No description"),
                "price": 0,
                "rating": b.get("rating", 0),
                "num_reviews": b.get("review_count", 0),
                "food_preference": food_preference,
            }
            for b in businesses[:5]
        ]
    except Exception as e:
        logger.error(f"Yelp API failed for meals: {e}")
        return []

def fetch_transport_booking_com(destination, pick_up_date, drop_off_date):
    try:
        lat, lng = get_coordinates(destination)
    except Exception as e:
        logger.warning(f"Falling back to Maldives coords: {e}")
        lat, lng = 3.2028, 73.2207

    country_code = COUNTRY_CODE_MAPPING.get(destination.lower(), "IN")
    url = "https://booking-com15.p.rapidapi.com/api/v1/cars/searchCarRentals"
    headers = {
        "x-rapidapi-host": "booking-com15.p.rapidapi.com",
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY")
    }
    params = {
        "pick_up_latitude": lat,
        "pick_up_longitude": lng,
        "drop_off_latitude": lat,
        "drop_off_longitude": lng,
        "pick_up_time": "10:00",
        "drop_off_time": "10:00",
        "driver_age": "30",
        "currency_code": "USD",
        "location": country_code
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()
        cars = response.json().get("data", [])
        return [
            {
                "name": c.get("name", "Car Rental"),
                "description": c.get("description", "No description"),
                "price": c.get("price", 0),
            }
            for c in cars[:3]
        ]
    except Exception as e:
        logger.error(f"Booking.com transport API failed: {e}")
        return []

# ------------ Main Runner ----------------

def scrape_and_store_data(db_path, destination, budget, trip_type, food_preference, start_date, duration):
    create_tables(db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    timestamp = datetime.now().isoformat()

    # Clean old data
    for table in ["hotels", "activities", "meals", "transport"]:
        c.execute(f"DELETE FROM {table} WHERE destination = ?", (destination,))

    # Parse dates
    try:
        start_date_obj = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
    except ValueError:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    checkin = start_date_obj.strftime("%Y-%m-%d")
    checkout = (start_date_obj + timedelta(days=duration)).strftime("%Y-%m-%d")

    # Hotels
    hotels = fetch_hotels_booking_com(destination, checkin, checkout, db_path)
    for h in hotels:
        c.execute("""INSERT INTO hotels (destination, name, price, rating, num_reviews, budget, last_updated)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                  (destination, h["name"], h["price"], h["rating"], h["num_reviews"], budget, timestamp))

    # Activities
    activities = fetch_activities_google_places(destination, trip_type)
    for a in activities:
        c.execute("""INSERT INTO activities (destination, name, description, price, type, last_updated)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (destination, a["name"], a["description"], a["price"], a["type"], timestamp))

    # Meals
    meals = fetch_meals_tripadvisor(destination, food_preference)
    for m in meals:
        c.execute("""INSERT INTO meals (destination, name, description, price, rating, num_reviews, food_preference, last_updated)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (destination, m["name"], m["description"], m["price"], m["rating"], m["num_reviews"], m["food_preference"], timestamp))

    # Transport
    transport = fetch_transport_booking_com(destination, checkin, checkout)
    for t in transport:
        c.execute("""INSERT INTO transport (destination, name, description, price, budget, last_updated)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (destination, t["name"], t["description"], t["price"], budget, timestamp))

    conn.commit()
    conn.close()
    logger.info(f"Data scraped and stored for {destination} ✅")

