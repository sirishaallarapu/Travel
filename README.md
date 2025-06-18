## 🚀 Project Setup Guide

Follow these steps to set up and run the Travel Itinerary Generator project locally.
Create and activate a virtual environment

python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
Install dependencies

pip install -r requirements.txt
Set up environment variables

Create a .env file in the root directory.

Add your Gemini API key:

Run the application

For FastAPI backend:
cd backend
uvicorn main:app --reload


For React interface:
npm install
npm run dev
