import uuid
import time

def get_response(request_message:str) -> tuple[str, str]:
    time.sleep(5)
    return str(uuid.uuid4()), f"Reply for: {request_message}"

def record_feedback(message_id:str, is_positive:bool) -> str:
    if is_positive:
        return "Glad it helped"
    else:
        return "Noted, we will work on it"