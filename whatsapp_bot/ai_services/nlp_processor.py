from typing import Dict, List, Optional, Tuple,Any
from ..models import WhatsAppUser
from .prompts import LLAMA_SYSTEM_PROMPT, GEMINI_EXERCISE_SYSTEM_PROMPT, GEMINI_NAME_SYSTEM_PROMPT
from .json_response_schema import GEMINI_EXERCISE_RESPONSE_SCHEMA,GEMINI_NAME_RESPONSE_SCHEMA,Measurements
import os
import litellm
from litellm import completion,JSONSchemaValidationError
from dotenv import load_dotenv
from ..services import logger_service
import json
from llama_cpp import Llama
from enum import Enum
import google.generativeai as genai


class MessageIntent(Enum):
    NAME = 'name'
    EXERCISE = 'exercise'
    HEIGHT_WEIGHT = 'height_weight'
    UNKNOWN = 'unknown'

load_dotenv()

logger = logger_service.get_logger
os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
genai.configure(os.getenv('GEMINI_API_KEY'))


def extract_workout_details(message: str) -> Dict[str, Any]:
    if os.getenv('DEBUG') is True:
        os.environ['LITELLM_LOG'] = 'DEBUG'
    os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
    try:
        response = completion(
            model="gemini/gemini-2.0-flash-exp", 
            messages=[{
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": GEMINI_EXERCISE_SYSTEM_PROMPT,
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": message,
                            }
                        ],
                    }
                    ],
            response_format={
                "type": "json_object", 
                "response_schema": GEMINI_EXERCISE_RESPONSE_SCHEMA,
                "enforce_validation": True 
            }
        )

        json_response = json.loads(response.choices[0].message.content)
    except JSONSchemaValidationError as e:
        logger.error(f"Schema validation error in Gemini response: {e}")
        raise ValueError("Failed to parse workout details - invalid response format")
    except Exception as e:
        logger.error(f"Error in parsing Gemini response: {e}")
        raise RuntimeError(f"Failed to process workout details: {str(e)}")
    
    return json_response


def classify_message_intent(message:str)->str:

    llm = Llama.from_pretrained(
        repo_id="bartowski/Llama-3.2-1B-Instruct-GGUF",
        filename="Llama-3.2-1B-Instruct-Q4_K_L.gguf",
    )
    response = llm.create_chat_completion(
	messages = [
        {
            "role": "system",
            "content": LLAMA_SYSTEM_PROMPT
		},
		{
			"role": "user",
			"content": message
		}
	    ]
    )
    classification = response['choices'][0]['message']['content']
    logger.info(f"Predicted message intent {classification}")
    if 'name' in classification:
        return MessageIntent.NAME
    elif 'exercise' in classification:
        return MessageIntent.EXERCISE
    elif 'height_weight' in classification:
        return MessageIntent.HEIGHT_WEIGHT
    else:
        return MessageIntent.UNKNOWN

def extract_height_weight(message: str) -> Dict[str,Any]:
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    try:
        result = model.generate_content(
            "I weighed myself today and I am 190 pounds. Yayy",
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=Measurements
            ),
        )
        json_response = json.loads(result.text)
        
    except JSONSchemaValidationError as e:
        logger.error(f"Schema validation error in Gemini response: {e}")
        raise ValueError("Failed to parse workout details - invalid response format")
    except Exception as e:
        logger.error(f"Error in parsing Gemini response: {e}")
        raise RuntimeError(f"Failed to process workout details: {str(e)}")

    return json_response

def extract_name_response(message: str, user: WhatsAppUser) -> str:
    """
    Extract Name from a message
    Args:
        message: The message text
        user: WhatsAppUser object
    """
    
    try:
        response = completion(
            model="gemini/gemini-2.0-flash-exp", 
            messages=[{
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": GEMINI_NAME_SYSTEM_PROMPT,
                            }
                        ],
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": message,
                            }
                        ],
                    }
                    ],
            response_format={
                "type": "json_object", 
                "response_schema": GEMINI_NAME_RESPONSE_SCHEMA,
                "enforce_validation": True 
            }
        )
        json_response = json.loads(response.choices[0].message.content)

    except JSONSchemaValidationError as e:
        logger.error(f"Schema validation error in Gemini response: {e}")
        raise ValueError("Failed to parse name details - invalid response format")
    except Exception as e:
        logger.error(f"Error in parsing Gemini response: {e}")
        raise RuntimeError(f"Failed to process name details: {str(e)}")
    
    return json_response['name']