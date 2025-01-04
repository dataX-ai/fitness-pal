import jwt
import os
from typing import Dict, Any
from django.conf import settings

# Get JWT secret from Django settings or environment variable
JWT_SECRET = getattr(settings, 'JWT_SECRET', os.getenv('JWT_SECRET'))

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token and return decoded payload
    """
    if not JWT_SECRET:
        raise ValueError("JWT_SECRET is not configured")
        
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token") 