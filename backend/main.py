from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from routes.trip_routes import router as trip_router
import logging
import traceback

app = FastAPI()
from dotenv import load_dotenv
import os  # You likely already have this somewhere

load_dotenv()  # 👈 Load variables from .env at startup


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mount trip routes
app.include_router(trip_router, prefix="/api")

# Validation exception handler (✅ only on app)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation failed: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Root
@app.get("/")
def read_root():
    return {"message": "🚀 Welcome to the Trip Generator App running on localhost!"}
