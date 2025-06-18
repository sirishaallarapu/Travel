import React, { useState } from 'react';
import axios from 'axios';
import './sidebar.css';

const Sidebar = ({ setItinerary }) => {
    const [destination, setDestination] = useState('');
    const [tripType, setTripType] = useState('');
    const [foodPreference, setFoodPreference] = useState('');
    const [numMembers, setNumMembers] = useState(1);
    const [budget, setBudget] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        // Validate dates
        const start = new Date(startDate);
        const end = new Date(endDate);
        const duration = Math.ceil((end - start) / (1000 * 60 * 60 * 24));

        if (start >= end) {
            setError('End date must be after start date.');
            setLoading(false);
            return;
        }

        if (duration < 1) {
            setError('Trip duration must be at least 1 day.');
            setLoading(false);
            return;
        }

        const tripRequest = {
            destination,
            trip_type: tripType,
            food_preference: foodPreference,
            num_members: parseInt(numMembers),
            budget,
            start_date: start.toISOString().split('T')[0], // Format as YYYY-MM-DD
            duration,
        };

        try {
            const response = await axios.post('http://localhost:8000/api/trip', tripRequest);
            console.log('API Response:', response.data);

            const { itinerary, vibe, total_budget } = response.data;

            if (itinerary && typeof itinerary === 'object') {
                // Pass the itinerary dictionary directly, along with vibe and total_budget
                setItinerary(itinerary, vibe, destination, total_budget);
            } else {
                console.error("Unexpected response format:", response.data);
                setItinerary(
                    { "Error": ["Itinerary data is missing or invalid."] },
                    vibe || tripType,
                    destination,
                    total_budget || 0
                );
            }
        } catch (error) {
            console.error('Error generating itinerary:', error);
            setError('Failed to generate itinerary. Please try again.');
            setItinerary(
                { "Error": ["Failed to generate itinerary. Please try again."] },
                tripType,
                destination,
                0
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="sidebar">
            <h2 className="sidebar-title">Plan Your Trip</h2>
            {error && <div className="error-message">{error}</div>}
            <form className="trip-form" onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="destination">Destination</label>
                    <input
                        type="text"
                        id="destination"
                        className="form-input"
                        value={destination}
                        onChange={(e) => setDestination(e.target.value)}
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="tripType">Trip Type</label>
                    <select
                        id="tripType"
                        className="form-input"
                        value={tripType}
                        onChange={(e) => setTripType(e.target.value)}
                        required
                    >
                        <option value="">Select Trip Type</option>
                        <option value="cultural">Cultural</option>
                        <option value="adventure">Adventure</option>
                        <option value="relaxation">Relaxation</option>
                    </select>
                </div>
                <div className="form-group">
                    <label htmlFor="foodPreference">Food Preference</label>
                    <select
                        id="foodPreference"
                        className="form-input"
                        value={foodPreference}
                        onChange={(e) => setFoodPreference(e.target.value)}
                        required
                    >
                        <option value="">Select Food Preference</option>
                        <option value="veg">Vegetarian</option>
                        <option value="non-veg">Non-Vegetarian</option>
                    </select>
                </div>
                <div className="form-group">
                    <label htmlFor="numMembers">Number of Members</label>
                    <input
                        type="number"
                        id="numMembers"
                        className="form-input"
                        value={numMembers}
                        onChange={(e) => setNumMembers(e.target.value)}
                        min="1"
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="budget">Budget</label>
                    <select
                        id="budget"
                        className="form-input"
                        value={budget}
                        onChange={(e) => setBudget(e.target.value)}
                        required
                    >
                        <option value="">Select Budget</option>
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                    </select>
                </div>
                <div className="form-group">
                    <label htmlFor="startDate">Start Date</label>
                    <input
                        type="date"
                        id="startDate"
                        className="form-input"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        min={new Date().toISOString().split('T')[0]} // Prevent past dates
                        required
                    />
                </div>
                <div className="form-group">
                    <label htmlFor="endDate">End Date</label>
                    <input
                        type="date"
                        id="endDate"
                        className="form-input"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        min={startDate || new Date().toISOString().split('T')[0]}
                        required
                    />
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