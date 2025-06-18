 Project Setup Instructions
Clone the repository

bash
Copy
Edit
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
Create and activate a virtual environment

bash
Copy
Edit
python -m venv venv
source venv/bin/activate     # On Windows: venv\Scripts\activate
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
Set up environment variables

Create a .env file in the root directory.

Add your Gemini API key:

ini
Copy
Edit
GOOGLE_API_KEY=your_gemini_api_key_here
Run the application

For FastAPI backend:

bash
Copy
Edit
uvicorn main:app --reload
For Streamlit interface:

bash
Copy
Edit
streamlit run app.py
