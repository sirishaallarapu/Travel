import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './sidebar.css';

const Sidebar = ({ setItinerary }) => {
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [tripType, setTripType] = useState('');
  const [foodPreference, setFoodPreference] = useState('');
  const [numMembers, setNumMembers] = useState(1);
  const [startDate, setStartDate] = useState('2025-06-28'); // Default to a future date
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [duration, setDuration] = useState(2);
  const [flightOption, setFlightOption] = useState('with');
  const [budgetPreference, setBudgetPreference] = useState('mid-range'); // Default to mid-range
  const [hotelStars, setHotelStars] = useState([]);
  const [suggestionsFrom, setSuggestionsFrom] = useState([]);
  const [suggestionsTo, setSuggestionsTo] = useState([]);
  const [showSuggestionsFrom, setShowSuggestionsFrom] = useState(false);
  const [showSuggestionsTo, setShowSuggestionsTo] = useState(false);

  // Comprehensive list of locations including all popular Indian cities
  const locations = [
    { name: 'New Delhi', country: 'India' },
    { name: 'Mumbai', country: 'India' },
    { name: 'Bangalore', country: 'India' },
    { name: 'Chennai', country: 'India' },
    { name: 'Kolkata', country: 'India' },
    { name: 'Hyderabad', country: 'India' },
    { name: 'Pune', country: 'India' },
    { name: 'Ahmedabad', country: 'India' },
    { name: 'Jaipur', country: 'India' },
    { name: 'Surat', country: 'India' },
    { name: 'Lucknow', country: 'India' },
    { name: 'Kanpur', country: 'India' },
    { name: 'Nagpur', country: 'India' },
    { name: 'Patna', country: 'India' },
    { name: 'Indore', country: 'India' },
    { name: 'Thane', country: 'India' },
    { name: 'Bhopal', country: 'India' },
    { name: 'Vadodara', country: 'India' },
    { name: 'Ludhiana', country: 'India' },
    { name: 'Agra', country: 'India' },
    { name: 'Nashik', country: 'India' },
    { name: 'Faridabad', country: 'India' },
    { name: 'Meerut', country: 'India' },
    { name: 'Rajkot', country: 'India' },
    { name: 'Varanasi', country: 'India' },
    { name: 'Srinagar', country: 'India' },
    { name: 'Aurangabad', country: 'India' },
    { name: 'Amritsar', country: 'India' },
    { name: 'Allahabad', country: 'India' },
    { name: 'Ranchi', country: 'India' },
    { name: 'Howrah', country: 'India' },
    { name: 'Coimbatore', country: 'India' },
    { name: 'Jabalpur', country: 'India' },
    { name: 'Gwalior', country: 'India' },
    { name: 'Vijayawada', country: 'India' },
    { name: 'Jodhpur', country: 'India' },
    { name: 'Madurai', country: 'India' },
    { name: 'Raipur', country: 'India' },
    { name: 'Kota', country: 'India' },
    { name: 'Guwahati', country: 'India' },
    { name: 'Chandigarh', country: 'India' },
    { name: 'Hubli-Dharwad', country: 'India' },
    { name: 'Shimla', country: 'India' },
    { name: 'Bhubaneswar', country: 'India' },
    { name: 'Visakhapatnam', country: 'India' },
    { name: 'Udaipur', country: 'India' },
    { name: 'Mangalore', country: 'India' },
    { name: 'Mysore', country: 'India' },
    { name: 'Tiruchirappalli', country: 'India' },
    { name: 'Bareilly', country: 'India' },
    { name: 'Aligarh', country: 'India' },
    { name: 'Moradabad', country: 'India' },
    { name: 'Bikaner', country: 'India' },
    { name: 'Saharanpur', country: 'India' },
    { name: 'Dehradun', country: 'India' },
    { name: 'Kolhapur', country: 'India' },
    { name: 'Ajmer', country: 'India' },
    { name: 'Akola', country: 'India' },
    { name: 'Durgapur', country: 'India' },
    { name: 'Guntur', country: 'India' },
    { name: 'Nanded', country: 'India' },
    { name: 'Tirupati', country: 'India' },
    { name: 'Kozhikode', country: 'India' },
    { name: 'Ooty', country: 'India' },
    { name: 'Darjeeling', country: 'India' },
    { name: 'Gangtok', country: 'India' },
    { name: 'Manali', country: 'India' },
    { name: 'Rishikesh', country: 'India' },
    { name: 'Haridwar', country: 'India' },
    { name: 'Puri', country: 'India' },
    { name: 'Bodhgaya', country: 'India' },
    { name: 'Kanyakumari', country: 'India' },
    { name: 'Daman', country: 'India' },
    { name: 'Diu', country: 'India' },
    { name: 'Siliguri', country: 'India' },
    { name: 'Jaisalmer', country: 'India' },
    { name: 'Pushkar', country: 'India' },
    { name: 'Leh', country: 'India' },
    { name: 'Kullu', country: 'India' },
    { name: 'Mount Abu', country: 'India' },
    { name: 'Shillong', country: 'India' },
    { name: 'Imphal', country: 'India' },
    { name: 'Aizawl', country: 'India' },
    { name: 'Goa', country: 'India' },
    { name: 'Goa', country: 'India', type: 'State' },
    { name: 'Kerala', country: 'India', type: 'State' },
    { name: 'Rajasthan', country: 'India', type: 'State' },
    { name: 'Uttarakhand', country: 'India', type: 'State' },
    { name: 'Himachal Pradesh', country: 'India', type: 'State' },
    { name: 'Andaman and Nicobar Islands', country: 'India', type: 'State' },
    { name: 'Ladakh', country: 'India', type: 'State' },
    { name: 'Malé', country: 'Maldives' },
    { name: 'Dubai', country: 'United Arab Emirates' },
    { name: 'Abu Dhabi', country: 'United Arab Emirates' },
    { name: 'Sharjah', country: 'United Arab Emirates' },
    { name: 'Bangkok', country: 'Thailand' },
    { name: 'Phuket', country: 'Thailand' },
    { name: 'Pattaya', country: 'Thailand' },
    { name: 'Singapore', country: 'Singapore' },
    { name: 'London', country: 'United Kingdom' },
    { name: 'Manchester', country: 'United Kingdom' },
    { name: 'Edinburgh', country: 'United Kingdom' },
    { name: 'Paris', country: 'France' },
    { name: 'Nice', country: 'France' },
    { name: 'Lyon', country: 'France' },
    { name: 'New York', country: 'United States' },
    { name: 'Los Angeles', country: 'United States' },
    { name: 'Chicago', country: 'United States' },
    { name: 'San Francisco', country: 'United States' },
    { name: 'Tokyo', country: 'Japan' },
    { name: 'Osaka', country: 'Japan' },
    { name: 'Kyoto', country: 'Japan' },
    { name: 'Sydney', country: 'Australia' },
    { name: 'Melbourne', country: 'Australia' },
    { name: 'Perth', country: 'Australia' },
    { name: 'Rome', country: 'Italy' },
    { name: 'Venice', country: 'Italy' },
    { name: 'Milan', country: 'Italy' },
    { name: 'Amsterdam', country: 'Netherlands' },
    { name: 'Berlin', country: 'Germany' },
    { name: 'Munich', country: 'Germany' },
    { name: 'Barcelona', country: 'Spain' },
    { name: 'Madrid', country: 'Spain' },
    { name: 'Istanbul', country: 'Turkey' },
    { name: 'Cape Town', country: 'South Africa' },
    { name: 'Johannesburg', country: 'South Africa' },
    { name: 'Rio de Janeiro', country: 'Brazil' },
    { name: 'Sao Paulo', country: 'Brazil' },
    { name: 'Hong Kong', country: 'Hong Kong' },
    { name: 'Seoul', country: 'South Korea' },
    { name: 'Kuala Lumpur', country: 'Malaysia' },
    { name: 'Hanoi', country: 'Vietnam' },
    { name: 'Ho Chi Minh City', country: 'Vietnam' },
    { name: 'Cairo', country: 'Egypt' },
    { name: 'Hurghada', country: 'Egypt' },
    { name: 'Moscow', country: 'Russia' },
    { name: 'St. Petersburg', country: 'Russia' },
    { name: 'Toronto', country: 'Canada' },
    { name: 'Vancouver', country: 'Canada' },
    { name: 'Mexico City', country: 'Mexico' },
    { name: 'Cancun', country: 'Mexico' },
    { name: 'Honeymoon', country: 'Category', type: 'Category' },
    { name: 'Family', country: 'Category', type: 'Category' },
    { name: 'Adventure', country: 'Category', type: 'Category' },
    { name: 'Beach', country: 'Category', type: 'Category' },
  ];

  const filterSuggestions = (input, type) => {
    const filtered = locations.filter((location) =>
      (location.name.toLowerCase().startsWith(input.toLowerCase()) ||
        location.country.toLowerCase().startsWith(input.toLowerCase())) &&
      (!type || location.type === type || !location.type)
    );
    return filtered
      .map((loc) => `${loc.name}, ${loc.country}${loc.type ? ` (${loc.type})` : ''}`)
      .slice(0, 5);
  };

  const handleFromChange = (e) => {
    const value = e.target.value;
    setFrom(value);
    setSuggestionsFrom(filterSuggestions(value, 'from'));
    setShowSuggestionsFrom(true);
  };

  const handleToChange = (e) => {
    const value = e.target.value;
    setTo(value);
    setSuggestionsTo(filterSuggestions(value, 'to'));
    setShowSuggestionsTo(true);
  };

  const handleSuggestionClick = (suggestion, field) => {
    if (field === 'from') {
      setFrom(suggestion);
      setShowSuggestionsFrom(false);
    } else {
      setTo(suggestion);
      setShowSuggestionsTo(false);
    }
  };

  const handleFlightChange = (e) => {
    setFlightOption(e.target.value);
  };

  const handleHotelStarChange = (e) => {
    const value = e.target.value;
    setHotelStars((prev) =>
      prev.includes(value) ? prev.filter((star) => star !== value) : [...prev, value]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const start = new Date(startDate);
    if (isNaN(start.getTime())) {
      setError('Invalid start date. Please select a valid date.');
      setLoading(false);
      return;
    }

    const end = new Date(start);
    end.setDate(start.getDate() + duration);
    const durationDays = duration;

    if (durationDays < 1) {
      setError('Trip duration must be at least 1 day.');
      setLoading(false);
      return;
    }

    if (from.trim() === to.trim()) {
      setError('Departure and destination cannot be the same.');
      setLoading(false);
      return;
    }

    const tripRequest = {
      from_location: from.trim(),
      destination: to.trim(),
      trip_type: tripType,
      food_preference: foodPreference,
      num_members: parseInt(numMembers),
      budget_preference: budgetPreference,
      start_date: start.toISOString().split('T')[0],
      duration: durationDays,
      flight_included: flightOption === 'with',
      hotel_stars: hotelStars.length > 0 ? hotelStars : ['3', '4', '5'], // Default to all if none selected
    };

    try {
      const response = await axios.post('http://localhost:8000/api/trip', tripRequest);
      const data = response.data;
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format from server');
      }
      setItinerary(data);
    } catch (error) {
      console.error('Error generating itinerary:', error.response ? error.response.data : error.message);
      setError('Failed to generate itinerary. Please try again.');
      setItinerary({
        itinerary: { Error: ['Failed to generate itinerary. Please try again.'] },
        vibe: tripType,
        destination: to,
        total_budget: 0,
        flights_and_transfers: null,
        hotel: null,
        activities: null,
        meals: null,
        num_members: parseInt(numMembers),
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const handleClickOutside = () => {
      setShowSuggestionsFrom(false);
      setShowSuggestionsTo(false);
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  return (
    <div className="sidebar">
      <h2 className="sidebar-title">Plan Your Trip</h2>
      {error && <div className="error-message">{error}</div>}
      <form className="trip-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label><em>From</em></label>
          <input type="text" className="form-input" value={from} onChange={handleFromChange} onFocus={() => setShowSuggestionsFrom(true)} autoComplete="off" required />
          {showSuggestionsFrom && suggestionsFrom.length > 0 && (
            <ul className="suggestions-list">
              {suggestionsFrom.map((s, i) => (
                <li key={i} onClick={() => handleSuggestionClick(s, 'from')} className="suggestion-item">{s}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="form-group">
          <label><em>To</em></label>
          <input type="text" className="form-input" value={to} onChange={handleToChange} onFocus={() => setShowSuggestionsTo(true)} autoComplete="off" required />
          {showSuggestionsTo && suggestionsTo.length > 0 && (
            <ul className="suggestions-list">
              {suggestionsTo.map((s, i) => (
                <li key={i} onClick={() => handleSuggestionClick(s, 'to')} className="suggestion-item">{s}</li>
              ))}
            </ul>
          )}
        </div>

        <div className="form-group">
          <label><em>Trip Type</em></label>
          <select className="form-input" value={tripType} onChange={(e) => setTripType(e.target.value)} required>
            <option value="cultural">Cultural</option>
            <option value="adventure">Adventure</option>
            <option value="relaxation">Relaxation</option>
          </select>
        </div>

        <div className="form-group">
          <label><em>Food Preference</em></label>
          <select className="form-input" value={foodPreference} onChange={(e) => setFoodPreference(e.target.value)} required>
            <option value="veg">Vegetarian</option>
            <option value="non-veg">Non-Vegetarian</option>
          </select>
        </div>

        <div className="form-group">
          <label><em>Number of Members</em></label>
          <input type="number" className="form-input" value={numMembers} onChange={(e) => setNumMembers(e.target.value)} min="1" required />
        </div>

        <div className="form-group">
          <label><em>Start Date</em></label>
          <input type="date" className="form-input" value={startDate} onChange={(e) => setStartDate(e.target.value)} min="2025-06-19" required />
        </div>

        <div className="form-group">
          <label><em>Duration (in Nights)</em></label>
          <input type="range" className="form-input range-input" min="2" max="7" value={duration} onChange={(e) => setDuration(parseInt(e.target.value))} />
          <span className="range-value">{duration}N</span>
        </div>

        <div className="form-group">
          <label><em>Flights</em></label>
          <div className="radio-group">
            <label><input type="radio" value="with" checked={flightOption === 'with'} onChange={handleFlightChange} /> With Flight</label>
            <label><input type="radio" value="without" checked={flightOption === 'without'} onChange={handleFlightChange} /> Without Flight</label>
          </div>
        </div>

        <div className="form-group">
          <label><em>Budget Preference</em></label>
          <select className="form-input" value={budgetPreference} onChange={(e) => setBudgetPreference(e.target.value)} required>
            <option value="budget-friendly">Budget-Friendly</option>
            <option value="mid-range">Mid-Range</option>
            <option value="premium">Premium</option>
          </select>
        </div>

        <div className="form-group">
          <label><em>Hotel Category</em></label>
          <div className="checkbox-group">
            {['3', '4', '5'].map((star) => (
              <label key={star}>
                <input type="checkbox" value={star} checked={hotelStars.includes(star)} onChange={handleHotelStarChange} /> {star}★
              </label>
            ))}
          </div>
        </div>

        <div className="form-group">
          <button type="submit" className="submit-button" disabled={loading}>
            {loading ? 'Generating...' : 'Generate Itinerary'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Sidebar;