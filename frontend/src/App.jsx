import React, { useState } from 'react';
import { ThemeProvider, createTheme, Box } from '@mui/material';
import Sidebar from './components/Sidebar';
import ItineraryDisplay from './components/ItineraryDisplay';
import ErrorBoundary from './components/ErrorBoundary';
import './App.css';
import logo from './assets/info.webp';

const theme = createTheme({
  palette: {
    primary: { main: '#3b82f6' },
    secondary: { main: '#f97316' },
  },
});

function App() {
  const [itinerary, setItinerary] = useState(null);
  const [vibe, setVibe] = useState('');
  const [destination, setDestination] = useState('');
  const [totalBudget, setTotalBudget] = useState(null);
  const [hotel, setHotel] = useState(null);
  const [num_members, setNumMembers] = useState(1);
  const [flight_included, setFlightIncluded] = useState(false);
  const [meta, setMeta] = useState({}); // Add meta state to hold note

  const handleItineraryUpdate = (data) => {
    console.log('Received data in App.jsx:', data);
    setItinerary(data.itinerary || null);
    setVibe(data.vibe || '');
    setDestination(data.meta?.destination || data.destination || '');
    setTotalBudget(data.total_budget || null);
    setNumMembers(data.num_members || 1);
    setFlightIncluded(data.meta?.flight_included || false);
    setMeta(data.meta || {}); // Store full meta object, including note

    const duration = data.duration || Object.keys(data.itinerary || {}).length || 1;
    const allHotels = data.itinerary
      ? [...new Set(Object.values(data.itinerary).flatMap(day => day['Hotel'] || []).filter(h => !h.includes('No hotel stay required')))]
      : [];
    setHotel({
      name: allHotels.length > 0 ? allHotels.join(', ') : 'Not specified',
      nights: duration,
      rating: '4.0/5',
      price: '12000' // Adjust based on max_hotel_cost or response
    });
  };

  return (
    <ThemeProvider theme={theme}>
      <div className="app-container" style={{ display: 'flex', height: '100vh', margin: 0, padding: 0 }}>
        <Sidebar setItinerary={handleItineraryUpdate} />
        <div className="main-content" style={{ flex: 1, overflowY: 'auto', backgroundColor: '#e0f7fa', padding: '20px', height: '100vh' }}>
          <Box className="header-with-logo" sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <img src={logo} alt="Logo" className="logo-img" style={{ width: '50px', marginRight: '10px' }} />
              <h1 className="main-heading">Story Trip Generator</h1>
            </Box>
            {!itinerary && (
              <Box sx={{
                backgroundColor: '#f8f9fa',
                width: '100%',
                textAlign: 'center',
                padding: '12px',
                fontSize: '1.1rem',
                borderRadius: '8px',
                color: '#333',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
              }}>
                Enter your details for your dream trip itinerary
              </Box>
            )}
          </Box>

          <ErrorBoundary>
            <ItineraryDisplay
              itinerary={itinerary}
              vibe={vibe}
              destination={destination}
              totalBudget={totalBudget}
              hotel={hotel}
              num_members={num_members}
              meta={meta} // Pass meta to ItineraryDisplay
            />
          </ErrorBoundary>
        </div>
      </div>
    </ThemeProvider>
  );
}

export default App;