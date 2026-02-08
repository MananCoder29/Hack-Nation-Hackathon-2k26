"""Validation utilities for retreat planning."""

from typing import Dict, Any, List, Tuple
import re
from datetime import datetime


def validate_requirements(requirements: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate structured requirements.
    
    Args:
        requirements: Requirements dictionary to validate
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Required fields
    required_fields = ["attendees", "budget", "location", "duration"]
    
    for field in required_fields:
        if field not in requirements or requirements[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Attendees validation
    attendees = requirements.get("attendees", 0)
    if not isinstance(attendees, int) or attendees <= 0:
        errors.append("Attendees must be a positive integer")
    elif attendees > 10000:
        errors.append("Attendees cannot exceed 10,000")
    
    # Budget validation
    budget = requirements.get("budget", 0)
    if not isinstance(budget, (int, float)) or budget <= 0:
        errors.append("Budget must be a positive number")
    elif budget > 10000000:
        errors.append("Budget cannot exceed $10,000,000")
    
    # Location validation
    location = requirements.get("location", "")
    if not location or len(location) < 2:
        errors.append("Location must be at least 2 characters")
    
    # Duration validation
    duration = requirements.get("duration", "")
    if duration and not re.match(r'^\d+\s*(day|days|night|nights|week|weeks)s?$', duration, re.IGNORECASE):
        errors.append("Duration must be in format like '2 days' or '3 nights'")
    
    # Deadline validation (optional)
    deadline = requirements.get("deadline")
    if deadline:
        try:
            deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
            if deadline_dt < datetime.now(deadline_dt.tzinfo if deadline_dt.tzinfo else None):
                errors.append("Deadline cannot be in the past")
        except (ValueError, TypeError):
            errors.append("Deadline must be in ISO format (YYYY-MM-DD)")
    
    return len(errors) == 0, errors


def validate_weights(weights: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate weight configuration.
    
    Args:
        weights: Weights dictionary to validate
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    valid_categories = ["flights", "hotels", "meeting_rooms", "catering"]
    
    # Validate category importance
    if "category_importance" in weights:
        importance = weights["category_importance"]
        
        if not isinstance(importance, dict):
            errors.append("category_importance must be a dictionary")
        else:
            total = 0
            for cat, weight in importance.items():
                if cat not in valid_categories:
                    errors.append(f"Unknown category in importance: {cat}")
                if not isinstance(weight, (int, float)):
                    errors.append(f"Weight for {cat} must be a number")
                elif weight < 0 or weight > 100:
                    errors.append(f"Weight for {cat} must be between 0 and 100")
                else:
                    total += weight
            
            if total > 0 and abs(total - 100) > 1:  # Allow 1% tolerance
                errors.append(f"Category importance weights should sum to 100 (got {total})")
    
    # Validate category-specific weights
    for category in valid_categories:
        if category in weights:
            cat_weights = weights[category]
            
            if not isinstance(cat_weights, dict):
                errors.append(f"{category} weights must be a dictionary")
                continue
            
            for key, value in cat_weights.items():
                if not key.endswith("_weight"):
                    continue
                    
                if not isinstance(value, (int, float)):
                    errors.append(f"{category}.{key} must be a number")
                elif value < 0 or value > 100:
                    errors.append(f"{category}.{key} must be between 0 and 100")
    
    return len(errors) == 0, errors


def validate_session_id(session_id: str) -> Tuple[bool, List[str]]:
    """Validate session ID format.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    if not session_id:
        errors.append("Session ID is required")
        return False, errors
    
    # Basic UUID format check
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, session_id.lower()):
        errors.append("Invalid session ID format (expected UUID)")
    
    return len(errors) == 0, errors


def validate_checkout_data(checkout_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate checkout request data.
    
    Args:
        checkout_data: Checkout data to validate
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Contact validation
    contact = checkout_data.get("contact", {})
    
    if not contact.get("name"):
        errors.append("Contact name is required")
    elif len(contact["name"]) < 2:
        errors.append("Contact name must be at least 2 characters")
    
    email = contact.get("email", "")
    if not email:
        errors.append("Contact email is required")
    elif not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        errors.append("Invalid email format")
    
    # Payment validation
    payment = checkout_data.get("payment", {})
    method = payment.get("method", "stripe")
    
    valid_methods = ["stripe", "invoice", "po"]
    if method not in valid_methods:
        errors.append(f"Invalid payment method. Must be one of: {', '.join(valid_methods)}")
    
    if method == "po" and not payment.get("po_number"):
        errors.append("PO number required for purchase order payment")
    
    # Terms acceptance
    if not checkout_data.get("terms_accepted", False):
        errors.append("Terms and conditions must be accepted")
    
    return len(errors) == 0, errors
