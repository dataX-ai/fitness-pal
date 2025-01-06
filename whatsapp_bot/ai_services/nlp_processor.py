from typing import Dict, List, Optional, Tuple,Any
import typing
from ..models import WhatsAppUser
from .prompts import LLAMA_SYSTEM_PROMPT, GEMINI_EXERCISE_SYSTEM_PROMPT, GEMINI_NAME_SYSTEM_PROMPT, GEMINI_MEASUREMENTS_SYSTEM_PROMPT, GEMINI_MATCH_EXERCISE_SYSTEM_PROMPT
from .json_response_schema import GEMINI_EXERCISE_RESPONSE_SCHEMA,GEMINI_NAME_RESPONSE_SCHEMA,Measurements
import os
from litellm import completion,JSONSchemaValidationError
from dotenv import load_dotenv
from ..services import logger_service
import json
from llama_cpp import Llama
from llama_cpp.llama_speculative import LlamaPromptLookupDecoding
from enum import Enum
from ollama import chat
from ollama import ChatResponse
import google.generativeai as genai
from ollama import Client
from typing_extensions import TypedDict

load_dotenv()

logger = logger_service.get_logger()
os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

ollama_host = os.getenv('OLLAMA_HOST', 'localhost')
ollama_port = os.getenv('OLLAMA_PORT', '11434')
client = Client(host=f"http://{ollama_host}:{ollama_port}")

class MessageIntent(Enum):
    NAME = 'name'
    EXERCISE = 'exercise'
    HEIGHT_WEIGHT = 'height_weight'
    UNKNOWN = 'unknown'

class ExerciseMatch(TypedDict, total=True):  # total=True makes all fields required
    matched_exercise: str
    confidence: typing.Literal["HIGH", "MEDIUM", "LOW"]

class ExerciseMatchResponse(TypedDict, total=True):
    matched_exercises: list[ExerciseMatch]

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

        json_response = match_exercise_name(json.loads(response.choices[0].message.content))
    except JSONSchemaValidationError as e:
        logger.error(f"Schema validation error in Gemini response: {e}")
        raise ValueError("Failed to parse workout details - invalid response format")
    except Exception as e:
        logger.error(f"Error in parsing Gemini response: {e}")
        raise RuntimeError(f"Failed to process workout details: {str(e)}")
    
    return json_response


def classify_message_intent(message:str)->str:
    try:
        response: ChatResponse = client.chat(
            model='hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:Q4_K_L',
            messages=[
                {
                    'role': 'system',
                    'content': LLAMA_SYSTEM_PROMPT
                },
                {
                    'role': 'user',
                    'content': message,
                },
            ]
        )
        classification = response['message']['content']
        logger.info(f"Classification Response: {response}")
        logger.info(f"Predicted message intent {classification}")
        if 'name' in classification:
            return MessageIntent.NAME
        elif 'exercise' in classification:
            return MessageIntent.EXERCISE
        elif 'height_weight' in classification:
            return MessageIntent.HEIGHT_WEIGHT
        else:
            return MessageIntent.UNKNOWN
    except Exception as e:
        logger.error(f"Error in classify_message_intent: {str(e)}")
        return MessageIntent.UNKNOWN


def extract_height_weight(message: str) -> Dict[str,Any]:
    model = genai.GenerativeModel("gemini-2.0-flash-exp",
                                  system_instruction=GEMINI_MEASUREMENTS_SYSTEM_PROMPT)
    try:
        result = model.generate_content(
            message,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=Measurements
            ),
        )
        json_response = json.loads(result.text)
        
        # Return in the format expected by the handler
        return json_response
        
    except JSONSchemaValidationError as e:
        logger.error(f"Schema validation error in Gemini response: {e}")
        raise ValueError("Failed to parse workout details - invalid response format")
    except Exception as e:
        logger.error(f"Error in parsing Gemini response: {e}")
        raise RuntimeError(f"Failed to process workout details: {str(e)}")

    return None

def extract_name_response(message: str) -> str:
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

def match_exercise_name(exercise_dict:Dict) -> Dict[str,Any]:
    model = genai.GenerativeModel("gemini-2.0-flash-exp",
                                  system_instruction=GEMINI_MATCH_EXERCISE_SYSTEM_PROMPT)
    try:
        result = model.generate_content(
            json.dumps(exercise_dict),
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ExerciseMatchResponse
            ),
        )
        matched_exercise_json = json.loads(result.text)
        
        # Update the original exercise names in-place
        for i, matched in enumerate(matched_exercise_json["matched_exercises"]):
            exercise_dict["exercises"][i]["exercise_name"] = matched["matched_exercise"]
        
        return exercise_dict
        
    except JSONSchemaValidationError as e:
        logger.error(f"Schema validation error in Gemini response: {e}")
        raise ValueError("Failed to parse workout details - invalid response format")
    except Exception as e:
        logger.error(f"Error in parsing Gemini response: {e}")
        raise RuntimeError(f"Failed to process workout details: {str(e)}")

