from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.appointments import router as appointments_router
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = FastAPI(
    title="CliniCall Backend",
    description="AI Voice Receptionist Backend for Clinics in India - MVP",
    version="1.0.0"
)

# Add CORS Middleware to allow all origins, methods, and headers for the demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register appointments router
app.include_router(appointments_router)

@app.get("/")
async def health_check():
    return { "status": "CliniCall backend running" }
