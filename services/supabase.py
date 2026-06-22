import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def _get_headers():
    return {
        "apikey": SUPABASE_KEY or "",
        "Authorization": f"Bearer {SUPABASE_KEY or ''}",
        "Content-Type": "application/json"
    }

async def insert_appointment(data: dict) -> dict:
    """
    Inserts an appointment into the Supabase 'appointments' table.
    Expects data matching the Supabase table schema.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is not set in environment variables.")

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/appointments"
    headers = _get_headers()
    headers["Prefer"] = "return=representation"

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        response.raise_for_status()
        inserted = response.json()
        if isinstance(inserted, list) and len(inserted) > 0:
            return inserted[0]
        return inserted

async def get_appointments() -> list:
    """
    Fetches all appointments from the Supabase 'appointments' table.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_KEY is not set in environment variables.")

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/appointments"
    headers = _get_headers()

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{url}?select=*", headers=headers)
        response.raise_for_status()
        return response.json()
