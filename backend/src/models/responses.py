"""Pydantic response models for the Retreat Planner API."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime


class TrustScore(BaseModel):
    """Trust/rating information for an item."""
    
    rating: float = Field(..., ge=0, le=5, description="Rating out of 5")
    source: str = Field(..., description="Source of the rating")
    review_count: Optional[int] = Field(default=None, description="Number of reviews")


class ItemMetadata(BaseModel):
    """Category-specific metadata for an item."""
    
    # Flight metadata
    departure: Optional[str] = None
    arrival: Optional[str] = None
    duration: Optional[str] = None
    stops: Optional[int] = None
    airline: Optional[str] = None
    
    # Hotel metadata
    star_rating: Optional[int] = None
    amenities: Optional[List[str]] = None
    
    # Meeting room metadata
    capacity: Optional[int] = None
    equipment: Optional[List[str]] = None
    
    # Catering metadata
    cuisine: Optional[str] = None
    dietary_options: Optional[List[str]] = None


class DiscoveredItem(BaseModel):
    """A discovered item from vendor search."""
    
    item_id: str = Field(..., description="Unique item identifier")
    category: str = Field(..., description="Category: flights, hotels, meeting_rooms, catering")
    vendor: str = Field(..., description="Vendor/provider name")
    source: str = Field(..., description="Source URL")
    title: str = Field(..., description="Item title")
    description: str = Field(..., description="Item description")
    price: float = Field(..., ge=0, description="Price in USD")
    currency: str = Field(default="USD", description="Currency code")
    availability: bool = Field(default=True, description="Availability status")
    metadata: Optional[ItemMetadata] = Field(default=None, description="Category-specific metadata")
    trust_score: Optional[TrustScore] = Field(default=None, description="Trust/rating info")


class ParsedRequirements(BaseModel):
    """Structured retreat requirements."""
    
    attendees: int = Field(..., ge=1, description="Number of attendees")
    duration: str = Field(..., description="Duration (e.g., '2 days')")
    location: str = Field(..., description="Destination location")
    origin: Optional[str] = Field(default=None, description="Origin/departure city")
    budget: float = Field(..., ge=0, description="Total budget in USD")
    deadline: Optional[str] = Field(default=None, description="Event date (ISO format)")
    must_haves: List[str] = Field(default_factory=list, description="Required features")
    nice_to_haves: List[str] = Field(default_factory=list, description="Optional features")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="Additional preferences")


class CategoryScoreBreakdown(BaseModel):
    """Score breakdown for a category."""
    
    score: float = Field(..., ge=0, le=100)
    weight: int = Field(..., ge=0, le=100)


class PackageExplanation(BaseModel):
    """Human-readable explanation for package ranking."""
    
    why_ranked: str = Field(..., description="Summary of why package is ranked this way")
    category_breakdowns: Dict[str, Dict[str, CategoryScoreBreakdown]] = Field(
        default_factory=dict,
        description="Detailed score breakdowns per category"
    )


class RankedPackage(BaseModel):
    """A scored and ranked package."""
    
    package_id: str = Field(..., description="Unique package identifier")
    rank: int = Field(..., ge=1, description="Rank position")
    final_score: float = Field(..., ge=0, le=100, description="Final composite score")
    category_scores: Dict[str, float] = Field(..., description="Scores per category")
    items: Dict[str, DiscoveredItem] = Field(..., description="Items in the package")
    total_cost: float = Field(..., ge=0, description="Total package cost")
    explanation: PackageExplanation = Field(..., description="Ranking explanation")


class CartItem(BaseModel):
    """An item in the cart."""
    
    item: DiscoveredItem = Field(..., description="The item")
    quantity: int = Field(default=1, ge=1, description="Quantity")
    subtotal: float = Field(..., ge=0, description="Item subtotal")


class Cart(BaseModel):
    """Shopping cart state."""
    
    cart_id: str = Field(..., description="Unique cart identifier")
    items: Dict[str, CartItem] = Field(..., description="Cart items by category")
    subtotal: float = Field(..., ge=0, description="Cart subtotal")
    taxes: float = Field(default=0, ge=0, description="Estimated taxes")
    fees: float = Field(default=0, ge=0, description="Service fees")
    total: float = Field(..., ge=0, description="Cart total")
    savings: Optional[float] = Field(default=None, description="Savings vs alternatives")


class RetailerConfirmation(BaseModel):
    """Confirmation from a single retailer."""
    
    vendor: str = Field(..., description="Vendor name")
    category: str = Field(..., description="Item category")
    confirmation_number: str = Field(..., description="Booking confirmation number")
    status: str = Field(..., description="Booking status")
    item_total: float = Field(..., ge=0, description="Item total cost")


# API Response Models

class RequirementsResponse(BaseModel):
    """Response from requirements analysis endpoint."""
    
    session_id: str = Field(..., description="Session ID for subsequent calls")
    requirements: ParsedRequirements = Field(..., description="Parsed requirements")
    status: str = Field(default="success", description="Response status")
    message: Optional[str] = Field(default=None, description="Optional message")


class DiscoveryResponse(BaseModel):
    """Response from discovery endpoint."""
    
    session_id: str = Field(..., description="Session ID")
    items: List[DiscoveredItem] = Field(..., description="Discovered items")
    categories_searched: List[str] = Field(
        default_factory=list,
        description="Categories that were searched"
    )
    status: str = Field(default="success", description="Response status")
    message: Optional[str] = Field(default=None, description="Optional message")


class RankingResponse(BaseModel):
    """Response from ranking endpoint."""
    
    session_id: str = Field(..., description="Session ID")
    packages: List[RankedPackage] = Field(..., description="Ranked packages")
    weights_used: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Weights used for ranking"
    )
    status: str = Field(default="success", description="Response status")
    message: Optional[str] = Field(default=None, description="Optional message")


class CartResponse(BaseModel):
    """Response from cart endpoints."""
    
    session_id: str = Field(..., description="Session ID")
    cart: Cart = Field(..., description="Cart state")
    alternatives: Optional[List[DiscoveredItem]] = Field(
        default=None,
        description="Alternative items for swapping"
    )
    status: str = Field(default="success", description="Response status")
    message: Optional[str] = Field(default=None, description="Optional message")


class CheckoutResponse(BaseModel):
    """Response from checkout endpoint."""
    
    master_booking_id: str = Field(..., description="Master booking reference")
    confirmations: List[RetailerConfirmation] = Field(
        ...,
        description="Confirmations from each retailer"
    )
    total_cost: float = Field(..., ge=0, description="Total cost charged")
    status: str = Field(default="success", description="Response status")
    message: Optional[str] = Field(default=None, description="Optional message")
    receipt_url: Optional[str] = Field(default=None, description="Receipt download URL")
