import uuid

def get_response(request_message:str) -> tuple[str, str]:
    return str(uuid.uuid4()), f"Repsonse for {request_message}"

def record_feedback(message_id:str, is_positive:bool) -> str:
    if is_positive:
        return "Glad it helped"
    else:
        return "Noted, we will work on it"