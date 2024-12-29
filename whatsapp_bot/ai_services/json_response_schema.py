import typing

class Measurement(typing.TypedDict):
    value: typing.Optional[float]
    unit: typing.Optional[str]

class Measurements(typing.TypedDict):
    height: Measurement
    weight: Measurement

GEMINI_EXERCISE_RESPONSE_SCHEMA = {
    "properties": {
        "exercises": {
            "items": {
                "properties": {
                    "exercise_name": {
                        "description": "Name of the exercise performed",
                        "type": "string"
                    },
                    "sets": {
                        "description": "Number of sets performed",
                        "type": "integer"
                    },
                    "reps": {
                        "description": "Number of reps per set",
                        "type": "string"
                    },
                    "weight": {
                        "properties": {
                            "value": {
                                "description": "Numerical weight value",
                                "type": "number"
                            },
                            "unit": {
                                "description": "Unit of weight measurement",
                                "enum": ["lbs", "kg", "body weight", "not specified"],
                                "type": "string"
                            },
                            "type": {
                                "description": "Type of weight used",
                                "enum": ["barbell", "dumbbell", "machine", "body weight", "not specified"],
                                "type": "string"
                            }
                        },
                        "required": ["value", "unit"],
                        "type": "object"
                    }
                },
                "required": ["exercise_name", "sets", "reps", "weight"],
                "type": "object"
            },
            "type": "array"
        },
        "parsed_from": {
            "description": "Original input text",
            "type": "string"
        },
        "confidence": {
            "description": "Confidence score of the parsing",
            "maximum": 1,
            "minimum": 0,
            "type": "number"
        }
    },
    "required": ["exercises", "parsed_from"],
    "type": "object"
}

GEMINI_NAME_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "description": "Name of the person",
            "type": "string"
        }
    },
    "required": ["name"]
}