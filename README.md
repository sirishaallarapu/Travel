# Trip Itinerary Generator Project Setup and Instructions

## Overview
This project is a web-based trip itinerary generator using FastAPI for the backend, React with Material-UI (MUI) for the frontend, and ReportLab for PDF generation. The application allows users to input trip details (destination, dates, preferences, etc.) and generates an itinerary with an optional PDF download.

## Project Setup

### Prerequisites
- **Python 3.9+**: For the FastAPI backend.
- **Node.js and npm**: For the React frontend.
- **pip**: For installing Python dependencies.
- **TexLive-full and TexLive-fonts-extra**: For potential LaTeX-based PDF generation (not used here).
- **Git** (optional): For version control.

### Backend Setup (FastAPI)
1. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

### Install dependencies
pip install -r requirements.txt

### Configure .env in the backend
GOOGLE_API_KEY=your_gemini_api_key_here

### Run the fastAPI serevr
cd backend
uvicorn main:app --reload

### Run the frontend erever
cd frontend
npm install
npm run dev