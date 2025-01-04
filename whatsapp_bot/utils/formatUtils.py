def format_phone_number(phone: str) -> str:
    """
    Format phone number to standard format:
    - Removes hyphens
    - Ensures + prefix
    Examples:
        +91-9830546388 -> +919830546388
        919830546388 -> +919830546388
    """
    if not phone:
        return phone

    # Remove hyphen and any whitespace
    phone = phone.replace('-', '').strip()

    # Add + prefix if missing
    return f"+{phone}" if not phone.startswith('+') else phone 