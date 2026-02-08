"""Data models"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class ItemType(str, Enum):
    HOTEL = "hotel"
    FLIGHT = "flight"
    CONFERENCE_ROOM = "conference_room"
    CATERING = "catering"
    TRANSPORTATION = "transportation"
    COORDINATION = "coordination"

class RetreatRequirements(BaseModel):
    num_participants: int
    location: str
    start_date: str
    end_date: str
    budget: float
    must_haves: List[str] = Field(default_factory=list)
    nice_to_haves: List[str] = Field(default_factory=list)
    special_requirements: Optional[str] = None

class VendorItem(BaseModel):
    item_id: str
    item_type: ItemType
    vendor_name: str
    description: str
    price: float
    capacity: int
    rating: float = 0.0
    distance_km: Optional[float] = None
    availability: bool = True
    delivery_time_days: Optional[int] = None
    url: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)

class ScoredItem(BaseModel):
    item: VendorItem
    normalized_scores: Dict[str, float] = Field(default_factory=dict)
    weighted_score: float = 0.0
    total_score: float = 0.0
    reasoning: str = ""

class CartItem(BaseModel):
    scored_item: ScoredItem
    quantity: int = 1
    subtotal: float = 0.0

class Cart(BaseModel):
    items: List[CartItem] = Field(default_factory=list)
    total_cost: float = 0.0
    meets_requirements: bool = False
    optimization_suggestions: List[str] = Field(default_factory=list)

class CheckoutStep(BaseModel):
    vendor_name: str
    items: List[str]
    total_amount: float
    status: str = "pending"
    payment_intent_id: Optional[str] = None

class CheckoutPlan(BaseModel):
    steps: List[CheckoutStep] = Field(default_factory=list)
    total_amount: float = 0.0
    estimated_completion_time: str = ""

class AgentResponse(BaseModel):
    success: bool
    data: Any
    message: str = ""
    errors: List[str] = Field(default_factory=list)
