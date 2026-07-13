def write_trace(trace_message:str, is_warning:bool = False):
    message = trace_message if not is_warning else f"WARNING: {trace_message}"
    print(message)