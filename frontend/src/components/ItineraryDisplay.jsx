import React, { useState, useEffect } from 'react';
import {
  Card, CardContent, Typography, Box, Button
} from '@mui/material';
import EventIcon from '@mui/icons-material/Event';
import FlightIcon from '@mui/icons-material/Flight';
import HotelIcon from '@mui/icons-material/Hotel';
import LocalActivityIcon from '@mui/icons-material/LocalActivity';
import RestaurantIcon from '@mui/icons-material/Restaurant';
import CurrencyRupeeIcon from '@mui/icons-material/CurrencyRupee';

const ItineraryDisplay = ({
  itinerary,
  vibe,
  destination,
  total_budget,
  num_members,
  meta,
  flights_and_transfers,
  hotel,
}) => {
  const safeKeys = obj =>
    obj && typeof obj === 'object' && !Array.isArray(obj)
      ? Object.keys(obj)
      : [];

  const days = safeKeys(itinerary);
  const [activeDay, setActiveDay] = useState('');

  useEffect(() => {
    if (days.length && !activeDay) {
      setActiveDay(days[0]);
    }
    console.log("Summary prop:", meta?.summary);  // Debug log
  }, [days, activeDay, meta?.summary]);

  const formatDate = dateStr =>
    new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });

  const handleDayChange = day => setActiveDay(day);

  const renderDayPlan = () => {
    if (!activeDay || !itinerary?.[activeDay]) return null;

    const data = itinerary[activeDay];
    const dateMatch = activeDay.match(/Day \d+ – (\d{4}-\d{2}-\d{2})/);
    const dateStr = dateMatch ? dateMatch[1] : '';

    const costLine = data['Total Cost']?.[0] || '';
    const costMatch = costLine.match(/~₹([\d,]+)/);
    const cost = costMatch ? costMatch[1] : '0';
    if (!costMatch) {
      console.warn(`Failed to parse cost from "${costLine}" for ${activeDay}`);
    }

    return (
      <Card>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>
            {formatDate(dateStr)}
          </Typography>

          <Box mt={2}>
            <Typography variant="h6" display="flex" alignItems="center" gutterBottom>
              <EventIcon sx={{ mr: 1 }} /> Day Plan:
            </Typography>
            <Typography variant="body2" mb={2}>
              {data['Day Plan']?.[0] || 'Not specified'}
            </Typography>
          </Box>

          {data['Flights & Transfers']?.length > 0 && (
            <Box mt={2}>
              <Typography variant="h6" display="flex" alignItems="center" gutterBottom>
                <FlightIcon sx={{ mr: 1 }} /> Flights & Transfers:
              </Typography>
              <ul style={{ paddingLeft: 20 }}>
                {data['Flights & Transfers'].map((item, i) => (
                  <li key={i}><Typography variant="body2">{item}</Typography></li>
                ))}
              </ul>
            </Box>
          )}

          {data['Hotel']?.length > 0 && (
            <Box mt={2}>
              <Typography variant="h6" display="flex" alignItems="center" gutterBottom>
                <HotelIcon sx={{ mr: 1 }} /> Hotel:
              </Typography>
              <ul style={{ paddingLeft: 20 }}>
                {data['Hotel'].map((h, i) => (
                  <li key={i}><Typography variant="body2">{h}</Typography></li>
                ))}
              </ul>
            </Box>
          )}

          {data['Activity']?.length > 0 && (
            <Box mt={2}>
              <Typography variant="h6" display="flex" alignItems="center" gutterBottom>
                <LocalActivityIcon sx={{ mr: 1 }} /> Activity:
              </Typography>
              <ul style={{ paddingLeft: 20 }}>
                {data['Activity'].map((act, i) => (
                  <li key={i}><Typography variant="body2">{act}</Typography></li>
                ))}
              </ul>
            </Box>
          )}

          {data['Meals']?.length > 0 && (
            <Box mt={2}>
              <Typography variant="h6" display="flex" alignItems="center" gutterBottom>
                <RestaurantIcon sx={{ mr: 1 }} /> Meals:
              </Typography>
              <ul style={{ paddingLeft: 20 }}>
                {data['Meals'].map((meal, i) => (
                  <li key={i}><Typography variant="body2">{meal}</Typography></li>
                ))}
              </ul>
            </Box>
          )}

          {data['Total Cost']?.[0] && (
            <Box mt={2}>
              <Typography variant="h6" display="flex" alignItems="center" gutterBottom>
                <CurrencyRupeeIcon sx={{ mr: 1 }} /> {data['Total Cost'][0]}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Box sx={{ p: 2, backgroundColor: '#f9fbff' }}>
      {meta?.note && (
        <Typography variant="body2" color="error" gutterBottom sx={{ mb: 1 }}>
          {meta.note}
        </Typography>
      )}
      <Typography variant="caption" color="textSecondary" gutterBottom>
        Today's date and time is 2:22 AM IST on Thursday, June 26, 2025.
      </Typography>
      {days.length > 0 && (
        <>
          <Typography
            variant="h4"
            gutterBottom
            sx={{ fontWeight: 'bold', fontSize: '2rem', mb: 2 }}
          >
            <em style={{ fontSize: '1.1rem' }}>{vibe} trip in {destination} – Destination</em>
          </Typography>

          <Box mb={2}>
            {days.map(day => (
              <Button
                key={day}
                variant={day === activeDay ? 'contained' : 'outlined'}
                onClick={() => handleDayChange(day)}
                sx={{ mr: 1, mb: 1 }}
              >
                {day}
              </Button>
            ))}
          </Box>

          {renderDayPlan()}

          <Box sx={{ mt: 3, p: 2, backgroundColor: '#e3f2fd', borderRadius: 1 }}>
            <Typography variant="body2">Description:</Typography>
            <Typography variant="body2" sx={{ mb: 2 }}>
              {meta?.summary || "This is a test description. The plan includes hotel stays, daily activities, meals, and flights. The estimated total cost for this 4-day journey is approximately ₹77,500."}
            </Typography>
          </Box>
        </>
      )}
    </Box>
  );
};

export default ItineraryDisplay;