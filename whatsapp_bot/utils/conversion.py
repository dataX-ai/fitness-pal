import pandas as pd
from typing import Optional
from ..utils.config import BMI_TARGETS

def calculate_goal_weight(height_cm: float, body_type: str) -> Optional[float]:
    """
    Calculate goal weight based on height and desired body type using BMI formula
    Args:
        height_cm: Height in centimeters
        body_type: 'lean', 'athletic', or 'bulk'
    Returns:
        Goal weight in kg or None if inputs are invalid
    """
    if not height_cm or pd.isna(height_cm) or not body_type or pd.isna(body_type):
        return None
        
    # Convert height to meters
    height_m = height_cm / 100
    
    # Get target BMI for body type (default to athletic if unknown type)
    target_bmi = BMI_TARGETS.get(body_type.lower(), BMI_TARGETS['athletic'])
    
    # BMI formula: weight = BMI * height^2
    goal_weight = target_bmi * (height_m ** 2)
    
    return round(goal_weight, 1)

def kg_to_lbs(kg: float) -> float:
    """Convert kilograms to pounds"""
    return kg * 2.20462

def lbs_to_kg(lbs: float) -> float:
    """Convert pounds to kilograms"""
    return lbs / 2.20462

def cm_to_inches(cm: float) -> float:
    """Convert centimeters to inches"""
    return cm / 2.54

def inches_to_cm(inches: float) -> float:
    """Convert inches to centimeters"""
    return inches * 2.54
