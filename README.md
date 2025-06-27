# 🚀 Full Stack Project Setup (FastAPI + Frontend)

This guide walks you through setting up both the **backend (FastAPI)** and the **frontend (React/Vite/Next/etc.)**.

---

## 🔧 Backend Setup (FastAPI)

### 1. Create a Virtual Environment

```bash
python -m venv venv
# Activate the environment
source venv/bin/activate       # On macOS/Linux
venv\Scripts\activate          # On Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the `backend/` directory with the following content:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

> ✅ **Replace the placeholders with your actual API keys.**


### 4. Run the FastAPI Server

```bash
cd backend
uvicorn main:app --reload
```

---

## 🌐 Frontend: Required Node.js & React Setup

Make sure you have the following installed:

- **Node.js**: v18+ (recommended)
- **npm**: comes with Node.js

If not installed, download from: https://nodejs.org

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Run the Frontend Development Server

```bash
npm run dev
```

---

## 📌 Notes

- Ensure your FastAPI entrypoint is defined in `main.py` as:

```python
from fastapi import FastAPI

app = FastAPI()
```

- If you're using CORS or environment variables:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

✅ You're all set! Happy developing! 🚀
