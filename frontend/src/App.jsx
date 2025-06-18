import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ItineraryDisplay from './components/ItineraryDisplay';
import './App.css';
import logo from './assets/info.webp'; // Ensure this path and file are correct

function App() {
  const [itinerary, setItinerary] = useState(null); // Initialize as null to indicate no itinerary yet
  const [vibe, setVibe] = useState('');
  const [destination, setDestination] = useState('');
  const [totalBudget, setTotalBudget] = useState(null); // Initialize as null to handle cases where budget is unavailable

  const handleItineraryUpdate = (newItinerary, tripVibe, dest, budget) => {
    setItinerary(newItinerary); // Expecting a dictionary
    setVibe(tripVibe);
    setDestination(dest);
    setTotalBudget(budget); // Could be a number or null
  };

  return (
    <div className="app">
      <Sidebar setItinerary={handleItineraryUpdate} />

      <div className="main-content">
        <div className="header-with-logo">
          <img src={logo} alt="Logo" className="logo-img" />
          <h1 className="main-heading">Story Trip Generator</h1>
        </div>

        <ItineraryDisplay
          itinerary={itinerary}
          vibe={vibe}
          destination={destination}
          totalBudget={totalBudget}
        />
      </div>
    </div>
  );
}

export default App;