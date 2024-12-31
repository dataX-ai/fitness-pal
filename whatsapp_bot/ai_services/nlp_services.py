from ..services import logger_service
from .nlp_processor import extract_height_weight, classify_message_intent, MessageIntent, extract_name_response

logger = logger_service.get_logger()

def is_name_response(message: str) -> tuple[bool, str]:
    """
    Check if message is a name response
    Args:
        message: The message text
    Returns:
        True/False, name
    """
    if classify_message_intent(message) == MessageIntent.NAME:
        try:
            name = extract_name_response(message)
            if name and name not in ['', 'null', 'None', 'none', 'NULL', 'NONE']:
                return True, name
            else:
                return False, None
        except Exception as e:
            logger.error(f"Error in extracting name: {e}")
    return False, None


def is_measurement_response(message: str) -> tuple[bool, float, float]:
    """
    Check if message is a measurement response and extract measurement
    Args:
        message: The message text
    Returns:
        True or False
    """
    classification = classify_message_intent(message)
    if classification == MessageIntent.HEIGHT_WEIGHT:
        try:
            extracted_data = get_converted_height_weight(message)
            logger.info(f"Extracted data: {extracted_data}")
            if not extracted_data['height'] and not extracted_data['weight']:
                return False, None, None
            return True, extracted_data['height'], extracted_data['weight']
        except Exception as e:
            logger.error(f"Error in extracting height/weight: {e}")
        return False, None, None


def is_gym_log(message: str) -> bool:
    """
    Determine if the message is a gym log.
    Args:
        message: The user's message text
    Returns:
        True or False
    """
    if classify_message_intent(message) == MessageIntent.EXERCISE:
        return True
    else:
        return False

def get_converted_height_weight(message: str) -> tuple[float, float]:
    """
    Get height and weight from message and convert to cm and kg respectively
    Args:
        message: The message text
    Returns:
        dict with 'height' in cm and 'weight' in kg, None for missing/invalid values
    Raises:
        ValueError: If both height and weight are missing or if units are missing
    """
    extracted_data = extract_height_weight(message)
    height_data = extracted_data.get('height', {})
    weight_data = extracted_data.get('weight', {})
    
    # Validate presence of required fields
    height_value = height_data.get('value')
    height_unit = height_data.get('unit', '').lower() if height_data.get('unit') else None
    weight_value = weight_data.get('value')
    weight_unit = weight_data.get('unit', '').lower() if weight_data.get('unit') else None
    
    # Check if at least one measurement is present
    if height_value is None and weight_value is None:
        raise ValueError("No height or weight measurements found in the message")
    
    # Convert height to cm if present
    converted_height = None
    if height_value is not None:
        if height_unit is None:
            logger.warning("Height value present but unit is missing")
        else:
            # Handle combined feet and inches format (e.g., "5'11" or "5ft11in" or "5'6" or 5.5 or "5'10''")
            if "'" in height_unit or ("ft" in height_unit and "in" in height_unit):
                try:
                    # Check if the value contains a quote (e.g., "5'6" or "5'10''")
                    if isinstance(height_value, str) and "'" in height_value:
                        # Handle format with double quotes (5'10'')
                        height_value = height_value.replace("''", "").replace('"', "")
                        feet_str, inches_str = height_value.split("'")
                        feet = float(feet_str.strip())
                        inches = float(inches_str.strip())
                    # Check if the value is a decimal number (e.g., 5.5 ft'in)
                    elif isinstance(height_value, (int, float)):
                        feet = int(height_value)  # Get the whole number part
                        inches = (height_value - feet) * 12  # Convert decimal to inches
                    # Handle "ft" format (e.g., "5ft6in")
                    elif isinstance(height_value, str) and "ft" in height_value:
                        feet_str, inches_str = height_value.split("ft")
                        inches_str = inches_str.replace("in", "")
                        feet = float(feet_str.strip())
                        inches = float(inches_str.strip())
                    else:
                        raise ValueError(f"Unsupported height format: {height_value}")
                        
                    converted_height = (feet * 30.48) + (inches * 2.54)
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse combined feet-inches format: {e}, data: {extracted_data}")
            elif height_unit in ['ft', 'feet', 'foot', 'feets']:
                converted_height = height_value * 30.48
            elif height_unit in ['in', 'inch', 'inches']:
                converted_height = height_value * 2.54
            elif height_unit in ['m', 'meter', 'meters', 'metre', 'metres', 'mtrs', 'mtr']:
                converted_height = height_value * 100
            elif height_unit in ['cm', 'centimeter', 'centimeters', 'centimetre', 'centimetres']:
                converted_height = height_value
            else:
                logger.warning(f"Unrecognized height unit: {height_unit}, data: {extracted_data}")
            
    # Convert weight to kg if present
    converted_weight = None
    if weight_value is not None:
        if weight_unit is None:
            logger.warning("Weight value present but unit is missing")
        else:
            if weight_unit in ['lb', 'lbs', 'pound', 'pounds']:
                converted_weight = weight_value * 0.453592
            elif weight_unit in ['kg', 'kgs', 'kilogram', 'kilograms']:
                converted_weight = weight_value
            elif weight_unit in ['g', 'gram', 'grams', 'gm', 'gms']:
                converted_weight = weight_value / 1000  # Convert grams to kg
            else:
                logger.warning(f"Unrecognized weight unit: {weight_unit}, data: {extracted_data}")
            
    return {'height': converted_height, 'weight': converted_weight}
