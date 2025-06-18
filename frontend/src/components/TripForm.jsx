import React from 'react';
import './ItineraryDisplay.css'; // Adjust path if needed

const ItineraryDisplay = ({ itinerary, vibe }) => {
  if (!itinerary) {
    return <div className="itinerary-empty">No itinerary to display.</div>;
  }

  const { destination, description, days, total_cost } = itinerary;

  return (
    <div className="itinerary-container">
      <h2>{destination} Itinerary</h2>
      {description && <p className="itinerary-description">{description}</p>}
      {days && days.length > 0 ? (
        days.map((day, index) => (
          <div key={index} className="day-container">
            <h3>Day {index + 1}: {day.date}</h3>
            <p><strong>Activities:</strong> {day.activities?.join(', ') || 'None'}</p>
            <p><strong>Meals:</strong> {day.meals?.join(', ') || 'None'}</p>
            <p><strong>Accommodation:</strong> {day.accommodation || 'None'}</p>
            <p><strong>Transport:</strong> {day.transport || 'None'}</p>
            <p><strong>Daily Cost:</strong> INR {day.daily_cost || 0}</p>
          </div>
        ))
      ) : (
        <p>No days planned.</p>
      )}
      <h3>Total Cost: INR {total_cost || 0}</h3>
      {vibe && <p className="vibe">Trip Vibe: {vibe}</p>}
    </div>
  );
};

export default ItineraryDisplay;