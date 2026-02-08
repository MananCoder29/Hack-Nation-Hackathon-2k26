import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set dummy API keys for initialization checks
os.environ["OPENAI_API_KEY"] = "sk-dummy"
os.environ["TAVILY_API_KEY"] = "tvly-dummy"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_dummy"

from src.agents.requirements_analyst import RequirementsAnalystAgent
from src.agents.discovery_agent import DiscoveryAgent
from src.agents.ranking_agent import RankingAgent
from src.agents.cart_agent import CartAgent
from src.agents.checkout_agent import CheckoutAgent
from src.crew.retreat_crew import RetreatPlannerCrew

@pytest.fixture
def mock_requirements():
    return {
        "attendees": 50,
        "duration": "3 days",
        "location": "Miami",
        "budget": 50000,
        "must_haves": ["4-star hotel", "flights"],
        "origin": "New York"
    }

@pytest.fixture
def mock_discovered_items():
    return [
        {
            "item_id": "flights_001",
            "category": "flights",
            "vendor": "Delta",
            "price": 15000,
            "title": "Delta Group Flight",
            "trust_score": {"rating": 4.5}
        },
        {
            "item_id": "hotels_001",
            "category": "hotels",
            "vendor": "Marriott",
            "price": 20000,
            "title": "Marriott Miami",
            "trust_score": {"rating": 4.8},
            "metadata": {"amenities": ["WiFi", "Pool"]}
        },
        {
            "item_id": "meeting_rooms_001",
            "category": "meeting_rooms",
            "vendor": "Miami Regency",
            "price": 5000,
            "title": "Grand Ballroom",
            "trust_score": {"rating": 4.2},
            "metadata": {"capacity": 100, "equipment": ["Projector"]}
        },
        {
            "item_id": "catering_001",
            "category": "catering",
            "vendor": "Miami Eats",
            "price": 7000,
            "title": "Full Catering Package",
            "trust_score": {"rating": 4.0},
            "metadata": {"dietary_options": ["Vegan"]}
        }
    ]

@pytest.mark.asyncio
async def test_full_workflow_e2e(mock_requirements, mock_discovered_items):
    """Test the full 5-agent workflow with mocks where necessary."""
    
    with patch('src.agents.requirements_analyst.Agent'), \
         patch('src.agents.requirements_analyst.Crew'), \
         patch('src.agents.discovery_agent.TavilyClient'):
        
        # 1. Setup Crew
        crew = RetreatPlannerCrew()
        
        # 2. Mock Agent 1 (Requirements)
        with patch.object(RequirementsAnalystAgent, 'analyze', return_value=mock_requirements):
            requirements = await crew.run_requirements_analyst("Planning a retreat for 50 people in Miami for 3 days with a 50k budget")
            assert requirements["attendees"] == 50
            assert requirements["location"] == "Miami"
        
        # 3. Mock Agent 2 (Discovery)
        with patch.object(DiscoveryAgent, 'discover', return_value=mock_discovered_items):
            items = await crew.run_discovery_agent()
            assert len(items) == 4
            assert items[0]["category"] == "flights"
    
    # 4. Test Agent 3 (Ranking) - Real logic
    packages = await crew.run_ranking_agent()
    assert len(packages) > 0
    top_package = packages[0]
    assert "package_id" in top_package
    assert "final_score" in top_package
    
    package_id = top_package["package_id"]
    
    # 5. Test Agent 4 (Cart) - Real logic
    cart = await crew.run_cart_agent(package_id)
    assert cart["total"] > 0
    assert "flights" in cart["items"]
    
    # Test Modify Cart (Swap)
    new_flight = {
        "item_id": "flights_002",
        "category": "flights",
        "vendor": "United",
        "price": 12000,
        "title": "United Group Flight",
        "trust_score": {"rating": 4.2}
    }
    
    modification = {
        "action": "swap",
        "item_id": "flights_001",
        "new_item": new_flight
    }
    
    updated_cart = await crew.modify_cart(modification)
    assert updated_cart["items"]["flights"]["item"]["vendor"] == "United"
    assert updated_cart["items"]["flights"]["subtotal"] == 12000 * 50 # 50 attendees
    
    # 6. Test Agent 5 (Checkout) - Real logic (mocking external payment if any)
    checkout_data = {
        "contact": {
            "name": "John Doe",
            "email": "john@example.com"
        },
        "terms_accepted": True,
        "payment": {
            "method": "stripe"
        }
    }
    
    with patch('src.agents.checkout_agent.datetime') as mock_date:
        # Mocking time for consistent output
        mock_date.now.return_value.isoformat.return_value = "2026-02-08T04:15:03"
        
        result = await crew.run_checkout_agent(checkout_data)
        assert result["status"] == "confirmed"
        assert "master_booking_id" in result
        assert len(result["retailer_confirmations"]) == 4

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_full_workflow_e2e())
