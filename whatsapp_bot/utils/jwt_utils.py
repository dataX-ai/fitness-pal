import jwt
import os
from typing import Dict, Any

JWT_SECRET = os.getenv('JWT_SECRET')

def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify JWT token and return decoded payload
    """
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token") 