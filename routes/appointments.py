import json
from fastapi import APIRouter, HTTPException, Request
from models import Appointment
from services.supabase import insert_appointment, get_appointments
from services.whatsapp import send_whatsapp_confirmation

router = APIRouter()

def extract_vapi_arguments(payload: dict) -> dict:
    """
    Recursively extracts patient_name, doctor_name, appointment_time, phone_number
    from the Vapi webhook payload.
    Supports tool-calls format, function_call format, or direct root keys.
    """
    keys = ["patient_name", "doctor_name", "appointment_time", "phone_number"]
    
    # 1. Check direct root-level keys
    if all(k in payload for k in keys):
        return {k: payload[k] for k in keys}
        
    # 2. Check message -> toolCalls
    message = payload.get("message", {})
    tool_calls = message.get("toolCalls") or message.get("tool_calls")
    if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
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

    # 3. Check message -> functionCall
    func_call = message.get("functionCall") or message.get("function_call")
    if func_call:
        args = func_call.get("arguments")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                pass
        if isinstance(args, dict):
            extracted = {k: args.get(k) for k in keys if args.get(k) is not None}
            if len(extracted) == len(keys):
                return extracted

    # 4. Check root-level toolCalls or functionCall
    tool_calls = payload.get("toolCalls") or payload.get("tool_calls")
    if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
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

    # 5. Recursive fallback search
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


@router.post("/book-appointment")
async def book_appointment(request: Request):
    try:
        body = await request.json()
        
        # Handle both direct format and Vapi nested format
        # Direct: { patient_name, doctor_name, ... }
        # Vapi may send: { message: { toolCalls: [...] } }
        
        # Try to extract from nested Vapi format first
        extracted = extract_vapi_arguments(body)
        
        # If not found, try direct format
        if not all(k in extracted for k in ["patient_name", "doctor_name", "appointment_time"]):
            extracted = {
                "patient_name": body.get("patient_name"),
                "doctor_name": body.get("doctor_name"),
                "appointment_time": body.get("appointment_time"),
                "phone_number": body.get("phone_number", "not provided")
            }

        # Validate we have minimum required fields
        if not extracted.get("patient_name") or not extracted.get("doctor_name"):
            raise HTTPException(status_code=422, detail="Missing required fields")

        # Insert to Supabase
        db_result = await insert_appointment(extracted)

        # Send WhatsApp
        send_whatsapp_confirmation(
            to=extracted.get("phone_number", "not provided"),
            patient=extracted["patient_name"],
            doctor=extracted["doctor_name"],
            time=extracted.get("appointment_time", "TBD")
        )

        return {"success": True, "message": "Appointment booked", "data": db_result}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Booking failed: {str(e)}")


@router.get("/appointments")
async def fetch_appointments():
    try:
        return await get_appointments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch appointments: {str(e)}")


@router.post("/vapi-webhook")
async def vapi_webhook(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    extracted = extract_vapi_arguments(payload)
    
    # Check if we successfully extracted all necessary details
    required_keys = ["patient_name", "doctor_name", "appointment_time", "phone_number"]
    missing = [k for k in required_keys if k not in extracted]
    if missing:
        raise HTTPException(
            status_code=400, 
            detail=f"Missing appointment fields from webhook arguments: {', '.join(missing)}"
        )
        
    try:
        # Call booking logic to insert into Supabase
        db_result = await insert_appointment(extracted)
        
        # Trigger Twilio WhatsApp notification
        send_whatsapp_confirmation(
            to=extracted["phone_number"],
            patient=extracted["patient_name"],
            doctor=extracted["doctor_name"],
            time=extracted["appointment_time"]
        )
        
        return { "result": "Appointment booked successfully", "data": db_result }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vapi webhook booking failed: {str(e)}")


@router.post("/debug-vapi")
async def debug_vapi(request: Request):
    body = await request.json()
    print("VAPI SENT:", body)
    return {"received": body}
