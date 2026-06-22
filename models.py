from pydantic import BaseModel

class Appointment(BaseModel):
    patient_name: str
    doctor_name: str
    appointment_time: str
    phone_number: str
