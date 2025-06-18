import React from 'react';
import './ItineraryDisplay.css';

function ItineraryDisplay({ itinerary, vibe, destination = "Your Destination", totalBudget }) {
  // Convert the itinerary dictionary to a string format for rendering
  let itineraryString = '';
  if (itinerary && typeof itinerary === 'object' && !Array.isArray(itinerary)) {
    Object.entries(itinerary).forEach(([day, sections]) => {
      if (sections.Error) {
        itineraryString += `${day}\n${sections.Error.join('\n')}\n\n`;
        return;
      }

      itineraryString += `${day}\n`;
      if (sections["Transportation"]?.length > 0) {
        itineraryString += `${sections["Transportation"].join('\n')}\n`;
      }
      if (sections["Accommodation"]?.length > 0) {
        itineraryString += `${sections["Accommodation"].join('\n')}\n`;
      }
      if (sections["Planned Activities"]?.length > 0) {
        itineraryString += "Planned Activities:\n";
        itineraryString += sections["Planned Activities"].map(item => `${item}`).join('\n') + '\n';
      }
      if (sections["Meals"]?.length > 0) {
        itineraryString += "Meals for the Day:\n";
        itineraryString += sections["Meals"].map(item => `${item}`).join('\n') + '\n';
      }
      if (sections["Total Cost"]) {
        itineraryString += `${sections["Total Cost"]}\n`;
      }
      itineraryString += '\n';
    });
  }

  if (!itineraryString) {
    return <p className="no-itinerary">Enter your details for your dream trip itinerary</p>;
  }

  const lines = itineraryString.split('\n');
  const elements = [];
  let finalTotal = totalBudget !== null ? `Total Trip Budget: ₹${totalBudget}` : 'Total Trip Budget: Not available due to itinerary generation failure.';
  const urlRegex = /(https?:\/\/[^\s]+)/;

  lines.forEach((line, idx) => {
    const trimmed = line.trim().toLowerCase();

    // Skip repeated heading lines
    if (trimmed.startsWith('your trip itinerary') || trimmed.startsWith('vibe:') || trimmed.startsWith('destination:')) {
      return;
    }

    // Handle total cost at the end (already handled via totalBudget prop)
    if (trimmed.startsWith('total trip budget')) {
      return; // Skip since we're using the totalBudget prop
    }

    // Handle links
    const match = line.match(urlRegex);
    if (match) {
      const url = match[0];
      const textBefore = line.replace(url, '').trim();
      elements.push(
        <p key={idx} className="item">
          {textBefore}{' '}
          <a href={url} target="_blank" rel="noopener noreferrer" className="book-link">
            Book Now
          </a>
        </p>
      );
      return;
    }

    // Day headings
    if (line.startsWith('Day')) {
      elements.push(<h3 key={idx} className="day-heading">{line}</h3>);
    }
    // Section headers
    else if (line.startsWith('Transportation:') || line.startsWith('Accommodation:')) {
      elements.push(<p key={idx} className="section">{line}</p>);
    }
    else if (line.startsWith('Planned Activities:') || line.startsWith('Meals for the Day:')) {
      elements.push(<p key={idx} className="section-title">{line}</p>);
    }
    else if (line.startsWith('Total Estimated Cost for the Day')) {
      elements.push(<p key={idx} className="day-total">{line}</p>);
    }
    // List items or normal text
    else {
      elements.push(<p key={idx} className="item">{line}</p>);
    }
  });

  async function handleDownloadPDF() {
    try {
      const response = await fetch('http://localhost:8000/api/generate-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ itinerary }),
      });

      if (!response.ok) {
        alert('Failed to generate PDF');
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `trip_itinerary.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      alert('Error occurred while downloading PDF');
    }
  }

  return (
    <div className="itinerary-container fade-in">
      <h2 className="itinerary-title">Your Trip Itinerary</h2>
      {vibe && <p className="vibe"><em>Vibe: {vibe}</em></p>}

      <div className="itinerary-body">{elements}</div>

      {finalTotal && (
        <p className="final-total">{finalTotal}</p>
      )}

      <div className="itinerary-footer">
        <button className="pdf-button" onClick={handleDownloadPDF}>
          📄 Download PDF
        </button>
      </div>
    </div>
  );
}

export default ItineraryDisplay;