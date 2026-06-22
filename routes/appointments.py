import json
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from models import Appointment
from services.supabase import insert_appointment, get_appointments
from services.whatsapp import send_whatsapp_confirmation

router = APIRouter()

def extract_vapi_arguments(payload: dict) -> dict:
    keys = ["patient_name", "doctor_name", "appointment_time", "phone_number"]
    
    if all(k in payload for k in keys):
        return {k: payload[k] for k in keys}
        
    message = payload.get("message", {})
    tool_calls = message.get("toolCalls") or message.get("tool_calls")
    if tool_calls and isinstance(tool_calls, list):
        for tool_call in tool_calls:
            func = tool_call.get("function")
            if func:
                args = func.get("arguments")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        pass
                if isinstance(args, dict):
                    extracted = {k: args.get(k) for k in keys if args.get(k) is not None}
                    if len(extracted) == len(keys):
                        return extracted

    extracted = {}
    def recursive_search(d):
        for k, v in d.items():
            if k in keys and v is not None:
                extracted[k] = v
            elif isinstance(v, dict):
                recursive_search(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        recursive_search(item)

    recursive_search(payload)
    return {k: extracted.get(k) for k in keys if extracted.get(k) is not None}


# ✅ This endpoint accepts Pydantic model (for direct API calls and /docs testing)
@router.post("/book-appointment")
async def book_appointment(appointment: Appointment):
    try:
        try:
            appointment_data = appointment.model_dump()
        except AttributeError:
            appointment_data = appointment.dict()

        db_result = await insert_appointment(appointment_data)

        send_whatsapp_confirmation(
            to=appointment.phone_number,
            patient=appointment.patient_name,
            doctor=appointment.doctor_name,
            time=appointment.appointment_time
        )

        return {"success": True, "message": "Appointment booked", "data": db_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")


# ✅ This endpoint accepts raw Vapi webhook (flexible format)
@router.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    try:
        raw = await request.body()
        print("VAPI RAW BODY:", raw)
        body = json.loads(raw)
        print("VAPI PARSED BODY:", body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    extracted = extract_vapi_arguments(body)
    print("EXTRACTED:", extracted)

    required_keys = ["patient_name", "doctor_name", "appointment_time", "phone_number"]
    missing = [k for k in required_keys if k not in extracted]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing fields: {missing}. Full body: {body}"
        )

    try:
        db_result = await insert_appointment(extracted)

        send_whatsapp_confirmation(
            to=extracted["phone_number"],
            patient=extracted["patient_name"],
            doctor=extracted["doctor_name"],
            time=extracted["appointment_time"]
        )

        return {"result": "Appointment booked successfully", "data": db_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")


@router.get("/appointments")
async def fetch_appointments():
    try:
        return await get_appointments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch appointments: {str(e)}")


@router.post("/debug-vapi")
async def debug_vapi(request: Request):
    raw = await request.body()
    print("DEBUG RAW:", raw)
    try:
        body = json.loads(raw)
    except Exception:
        body = {"raw": str(raw)}
    print("DEBUG PARSED:", body)
    return {"received": body}