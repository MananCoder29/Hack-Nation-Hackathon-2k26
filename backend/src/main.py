"""FastAPI main application for Retreat Planner API."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

from src.config import settings
from src.crew.retreat_crew import RetreatPlannerCrew
from src.models.requests import (
    RetreatRequirementsRequest,
    WeightAdjustmentRequest,
    CartModificationRequest,
    CheckoutRequest,
)
from src.models.responses import (
    RequirementsResponse,
    DiscoveryResponse,
    RankingResponse,
    CartResponse,
    CheckoutResponse,
    ParsedRequirements,
    DiscoveredItem,
    RankedPackage,
    Cart,
    CartItem,
    RetailerConfirmation,
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Retreat Planner API",
    description="Multi-agent retreat planning system powered by CrewAI and Tavily",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session storage (use Redis/database in production)
crew_instances: Dict[str, RetreatPlannerCrew] = {}


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """API root - returns service information."""
    return {
        "message": "Retreat Planner API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health", tags=["Info"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "active_sessions": len(crew_instances)
    }


# ============================================================================
# Agent Endpoints
# ============================================================================

@app.post("/api/v1/analyze-requirements", response_model=RequirementsResponse, tags=["Agents"])
async def analyze_requirements(request: RetreatRequirementsRequest):
    """Agent 1: Parse and structure retreat requirements from natural language.
    
    This is the first step in the planning flow. It creates a new session
    and returns a session_id for subsequent API calls.
    """
    try:
        # Create new crew instance
        crew = RetreatPlannerCrew()
        session_id = crew.session_id
        crew_instances[session_id] = crew
        
        # Run requirements analysis
        result = await crew.run_requirements_analyst(request.user_input)
        
        # Convert to response model
        requirements = ParsedRequirements(
            attendees=result.get("attendees", 0),
            duration=result.get("duration", ""),
            location=result.get("location", ""),
            origin=result.get("origin"),
            budget=result.get("budget", 0),
            deadline=result.get("deadline"),
            must_haves=result.get("must_haves", []),
            nice_to_haves=result.get("nice_to_haves", []),
            preferences=result.get("preferences"),
        )
        
        return RequirementsResponse(
            session_id=session_id,
            requirements=requirements,
            status="success",
            message="Requirements analyzed successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/v1/discover-options", response_model=DiscoveryResponse, tags=["Agents"])
async def discover_options(session_id: str = Query(..., description="Session ID from analyze-requirements")):
    """Agent 2: Search and discover options using Tavily.
    
    Searches for flights, hotels, meeting rooms, and catering options
    based on the analyzed requirements.
    """
    try:
        crew = crew_instances.get(session_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Session not found. Please analyze requirements first.")
        
        # Run discovery
        result = await crew.run_discovery_agent()
        
        # Convert to response model
        items = [
            DiscoveredItem(**item) for item in result
        ]
        
        # Get unique categories
        categories = list(set(item.category for item in items))
        
        return DiscoveryResponse(
            session_id=session_id,
            items=items,
            categories_searched=categories,
            status="success",
            message=f"Discovered {len(items)} options across {len(categories)} categories"
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")


@app.post("/api/v1/rank-packages", response_model=RankingResponse, tags=["Agents"])
async def rank_packages(
    session_id: str = Query(..., description="Session ID"),
    weights: Optional[WeightAdjustmentRequest] = None
):
    """Agent 3: Rank packages with optional custom weights.
    
    Creates package combinations from discovered items and scores them
    based on configurable criteria weights.
    """
    try:
        crew = crew_instances.get(session_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Convert weights to dict if provided
        custom_weights = None
        if weights:
            custom_weights = {}
            if weights.category_importance:
                custom_weights["category_importance"] = weights.category_importance.model_dump()
            if weights.flights:
                custom_weights["flights"] = weights.flights.model_dump(exclude_none=True)
            if weights.hotels:
                custom_weights["hotels"] = weights.hotels.model_dump(exclude_none=True)
            if weights.meeting_rooms:
                custom_weights["meeting_rooms"] = weights.meeting_rooms.model_dump(exclude_none=True)
            if weights.catering:
                custom_weights["catering"] = weights.catering.model_dump(exclude_none=True)
        
        # Run ranking
        result = await crew.run_ranking_agent(custom_weights)
        
        # Convert to response model (simplified for now)
        packages = []
        for pkg in result[:10]:  # Limit to top 10
            packages.append(RankedPackage(
                package_id=pkg["package_id"],
                rank=pkg["rank"],
                final_score=pkg["final_score"],
                category_scores=pkg["category_scores"],
                items={cat: DiscoveredItem(**item) for cat, item in pkg["items"].items()},
                total_cost=pkg["total_cost"],
                explanation={
                    "why_ranked": pkg["explanation"]["why_ranked"],
                    "category_breakdowns": pkg["explanation"].get("category_breakdowns", {})
                }
            ))
        
        return RankingResponse(
            session_id=session_id,
            packages=packages,
            weights_used=custom_weights,
            status="success",
            message=f"Ranked {len(packages)} packages"
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")


@app.post("/api/v1/cart/build", response_model=CartResponse, tags=["Cart"])
async def build_cart(
    session_id: str = Query(..., description="Session ID"),
    package_id: str = Query(..., description="ID of package to add to cart")
):
    """Agent 4: Build cart from selected package.
    
    Creates a shopping cart from the selected ranked package,
    calculating quantities, taxes, and fees.
    """
    try:
        crew = crew_instances.get(session_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Build cart
        result = await crew.run_cart_agent(package_id)
        
        # Convert to response model
        cart_items = {}
        for category, cart_item in result.get("items", {}).items():
            cart_items[category] = CartItem(
                item=DiscoveredItem(**cart_item["item"]),
                quantity=cart_item["quantity"],
                subtotal=cart_item["subtotal"]
            )
        
        cart = Cart(
            cart_id=result["cart_id"],
            items=cart_items,
            subtotal=result["subtotal"],
            taxes=result["taxes"],
            fees=result["fees"],
            total=result["total"],
            savings=result.get("savings")
        )
        
        return CartResponse(
            session_id=session_id,
            cart=cart,
            status="success",
            message="Cart built successfully"
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cart build failed: {str(e)}")


@app.post("/api/v1/cart/modify", response_model=CartResponse, tags=["Cart"])
async def modify_cart(
    session_id: str = Query(..., description="Session ID"),
    modification: CartModificationRequest = None
):
    """Modify cart items or optimize.
    
    Supports actions: swap, remove, adjust_weights, optimize
    """
    try:
        crew = crew_instances.get(session_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not modification:
            raise HTTPException(status_code=400, detail="Modification request required")
        
        # Modify cart
        result = await crew.modify_cart(modification.model_dump())
        
        # Convert to response model
        cart_items = {}
        for category, cart_item in result.get("items", {}).items():
            cart_items[category] = CartItem(
                item=DiscoveredItem(**cart_item["item"]),
                quantity=cart_item["quantity"],
                subtotal=cart_item["subtotal"]
            )
        
        cart = Cart(
            cart_id=result["cart_id"],
            items=cart_items,
            subtotal=result["subtotal"],
            taxes=result["taxes"],
            fees=result["fees"],
            total=result["total"],
            savings=result.get("savings")
        )
        
        return CartResponse(
            session_id=session_id,
            cart=cart,
            status="success",
            message=f"Cart modified ({modification.action})"
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cart modification failed: {str(e)}")


@app.post("/api/v1/checkout", response_model=CheckoutResponse, tags=["Checkout"])
async def checkout(
    session_id: str = Query(..., description="Session ID"),
    checkout_data: CheckoutRequest = None
):
    """Agent 5: Process checkout.
    
    Processes payment and creates bookings with all retailers.
    Returns a master booking ID and individual confirmations.
    """
    try:
        crew = crew_instances.get(session_id)
        if not crew:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if not checkout_data:
            raise HTTPException(status_code=400, detail="Checkout data required")
        
        # Process checkout
        result = await crew.run_checkout_agent(checkout_data.model_dump())
        
        # Convert to response model
        confirmations = [
            RetailerConfirmation(
                vendor=conf["vendor"],
                category=conf["category"],
                confirmation_number=conf["confirmation_number"],
                status=conf["status"],
                item_total=conf["item_total"]
            )
            for conf in result.get("retailer_confirmations", [])
        ]
        
        # Clean up session after successful checkout
        del crew_instances[session_id]
        
        return CheckoutResponse(
            master_booking_id=result["master_booking_id"],
            confirmations=confirmations,
            total_cost=result["total_cost"],
            status="success",
            message="Booking confirmed successfully"
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout failed: {str(e)}")


# ============================================================================
# Full Flow Endpoint (for testing)
# ============================================================================

@app.post("/api/v1/full-flow", tags=["Testing"])
async def run_full_flow(request: RetreatRequirementsRequest):
    """Run all agents in sequence (for testing/demo).
    
    Executes the complete flow: requirements -> discovery -> ranking
    Returns a summary of results.
    """
    try:
        crew = RetreatPlannerCrew()
        session_id = crew.session_id
        
        # Agent 1: Requirements
        requirements = await crew.run_requirements_analyst(request.user_input)
        
        # Agent 2: Discovery
        items = await crew.run_discovery_agent()
        
        # Agent 3: Ranking
        packages = await crew.run_ranking_agent()
        
        # Store crew for potential follow-up
        crew_instances[session_id] = crew
        
        return {
            "session_id": session_id,
            "requirements": requirements,
            "items_count": len(items),
            "items_by_category": {
                cat: len([i for i in items if i["category"] == cat])
                for cat in set(i["category"] for i in items)
            },
            "top_packages": [
                {
                    "package_id": p["package_id"],
                    "rank": p["rank"],
                    "score": p["final_score"],
                    "total_cost": p["total_cost"]
                }
                for p in packages[:3]
            ],
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Full flow failed: {str(e)}")


# ============================================================================
# Session Management
# ============================================================================

@app.get("/api/v1/session/{session_id}", tags=["Session"])
async def get_session_state(session_id: str):
    """Get current session state for debugging."""
    crew = crew_instances.get(session_id)
    if not crew:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return crew.get_session_state()


@app.delete("/api/v1/session/{session_id}", tags=["Session"])
async def delete_session(session_id: str):
    """Delete a session to free resources."""
    if session_id in crew_instances:
        del crew_instances[session_id]
        return {"status": "deleted", "session_id": session_id}
    
    raise HTTPException(status_code=404, detail="Session not found")


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
