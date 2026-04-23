def success(data, message="ok", status=200):
    return {"success": True, "message": message, "data": data}, status


def error(message, status=400, details=None):
    payload = {"success": False, "message": message}
    if details is not None:
        payload["details"] = details
    return payload, status
