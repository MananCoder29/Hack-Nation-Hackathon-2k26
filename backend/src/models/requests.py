"""Pydantic request models for the Retreat Planner API."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any


class RetreatRequirementsRequest(BaseModel):
    """Request model for analyzing retreat requirements."""
    
    user_input: str = Field(
        ...,
        description="Natural language description of retreat requirements",
        min_length=10,
        examples=[
            "Plan a 2-day retreat in Las Vegas for 50 managers. Budget $60,000. "
            "Need 4-star hotel, flights from SF, meeting room, catering."
        ]
    )


class CategoryWeights(BaseModel):
    """Weights for scoring within a category."""
    
    price_weight: int = Field(default=50, ge=0, le=100)
    trust_weight: int = Field(default=25, ge=0, le=100)
    timing_weight: Optional[int] = Field(default=None, ge=0, le=100)
    comfort_weight: Optional[int] = Field(default=None, ge=0, le=100)
    location_weight: Optional[int] = Field(default=None, ge=0, le=100)
    amenities_weight: Optional[int] = Field(default=None, ge=0, le=100)
    capacity_weight: Optional[int] = Field(default=None, ge=0, le=100)
    equipment_weight: Optional[int] = Field(default=None, ge=0, le=100)
    dietary_weight: Optional[int] = Field(default=None, ge=0, le=100)
    service_weight: Optional[int] = Field(default=None, ge=0, le=100)


class CategoryImportance(BaseModel):
    """Importance weights for each category (must sum to 100)."""
    
    flights: int = Field(default=30, ge=0, le=100)
    hotels: int = Field(default=40, ge=0, le=100)
    meeting_rooms: int = Field(default=15, ge=0, le=100)
    catering: int = Field(default=15, ge=0, le=100)


class WeightAdjustmentRequest(BaseModel):
    """Request model for adjusting ranking weights."""
    
    category_importance: Optional[CategoryImportance] = Field(
        default=None,
        description="Importance weights for each category"
    )
    flights: Optional[CategoryWeights] = Field(
        default=None,
        description="Scoring weights for flights"
    )
    hotels: Optional[CategoryWeights] = Field(
        default=None,
        description="Scoring weights for hotels"
    )
    meeting_rooms: Optional[CategoryWeights] = Field(
        default=None,
        description="Scoring weights for meeting rooms"
    )
    catering: Optional[CategoryWeights] = Field(
        default=None,
        description="Scoring weights for catering"
    )


class CartModificationRequest(BaseModel):
    """Request model for modifying cart items."""
    
    action: str = Field(
        ...,
        description="Action to perform: 'swap', 'remove', 'adjust_weights', 'optimize'",
        pattern="^(swap|remove|adjust_weights|optimize)$"
    )
    item_id: Optional[str] = Field(
        default=None,
        description="Item ID to modify (for swap/remove)"
    )
    new_item_id: Optional[str] = Field(
        default=None,
        description="New item ID to swap with (for swap)"
    )
    weights: Optional[WeightAdjustmentRequest] = Field(
        default=None,
        description="New weights (for adjust_weights)"
    )
    optimization_goal: Optional[str] = Field(
        default=None,
        description="Optimization goal: 'cost', 'quality', 'balanced'",
        pattern="^(cost|quality|balanced)$"
    )


class PaymentDetails(BaseModel):
    """Payment information for checkout."""
    
    method: str = Field(
        default="stripe",
        description="Payment method: 'stripe', 'invoice', 'po'"
    )
    stripe_token: Optional[str] = Field(
        default=None,
        description="Stripe payment token (if using Stripe)"
    )
    po_number: Optional[str] = Field(
        default=None,
        description="Purchase order number (if using PO)"
    )


class ContactDetails(BaseModel):
    """Contact information for booking."""
    
    name: str = Field(..., description="Primary contact name")
    email: str = Field(..., description="Contact email")
    phone: Optional[str] = Field(default=None, description="Contact phone")
    company: Optional[str] = Field(default=None, description="Company name")


class CheckoutRequest(BaseModel):
    """Request model for checkout."""
    
    contact: ContactDetails = Field(..., description="Contact information")
    payment: PaymentDetails = Field(
        default_factory=PaymentDetails,
        description="Payment details"
    )
    special_requests: Optional[str] = Field(
        default=None,
        description="Special requests or notes"
    )
    terms_accepted: bool = Field(
        default=False,
        description="User accepted terms and conditions"
    )
