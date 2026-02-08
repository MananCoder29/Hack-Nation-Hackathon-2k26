import asyncio
import sys
import os
from typing import Dict, Any

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..'))

from src.crew.retreat_crew import RetreatPlannerCrew
from dotenv import load_dotenv

async def run_real_e2e_test():
    """Run a real end-to-end test of all 5 agents."""
    # Load .env explicitly
    load_dotenv(os.path.join(current_dir, '..', '.env'))
    
    print("\n🚀 Starting Real End-to-End Agent Test...")
    print("=" * 60)
    
    crew = RetreatPlannerCrew()
    
    # 1. Agent 1: Requirements Analyst
    print("\nStep 1: Running Requirements Analyst (Live OpenAI)...")
    user_input = "Plan a 3-day executive retreat in Miami for 40 people with a $60,000 budget. We need 4-star hotels and flights from Seattle."
    try:
        requirements = await crew.run_requirements_analyst(user_input)
        print(f"✅ Requirements parsed: {requirements['location']}, {requirements['attendees']} people, ${requirements['budget']}")
    except Exception as e:
        print(f"❌ Requirements Error: {e}")
        return

    # 2. Agent 2: Discovery Agent
    print("\nStep 2: Running Discovery Agent (Live Tavily)...")
    try:
        items = await crew.run_discovery_agent()
        print(f"✅ Discovered {len(items)} options across multiple categories.")
        
        # Verify we have items in key categories
        categories = set(item['category'] for item in items)
        print(f"   Categories found: {', '.join(categories)}")
    except Exception as e:
        print(f"❌ Discovery Error: {e}")
        return

    # 3. Agent 3: Ranking Agent
    print("\nStep 3: Running Ranking Agent...")
    try:
        packages = await crew.run_ranking_agent()
        print(f"✅ Generated and ranked {len(packages)} package combinations.")
        top_pkg = packages[0]
        print(f"   Top Package Score: {top_pkg['final_score']} (Total Cost: ${top_pkg['total_cost']})")
        print(f"   Top Package Explanation: {top_pkg['explanation']['why_ranked']}")
    except Exception as e:
        print(f"❌ Ranking Error: {e}")
        return

    # 4. Agent 4: Cart Agent
    print("\nStep 4: Running Cart Agent...")
    try:
        package_id = packages[0]['package_id']
        cart = await crew.run_cart_agent(package_id)
        print(f"✅ Cart built successfully. Total: ${cart['total']}")
        print(f"   Items in cart: {list(cart['items'].keys())}")
        
        # Test Cart Modification (Remove)
        category_to_remove = list(cart['items'].keys())[0]
        item_id_to_remove = cart['items'][category_to_remove]['item']['item_id']
        print(f"   Testing Modification: Removing {category_to_remove}...")
        
        modification = {
            "action": "remove",
            "item_id": item_id_to_remove
        }
        updated_cart = await crew.modify_cart(modification)
        print(f"✅ Item removed. New Total: ${updated_cart['total']}")
    except Exception as e:
        print(f"❌ Cart Error: {e}")
        return

    # 5. Agent 5: Checkout Agent
    print("\nStep 5: Running Checkout Agent (Simulated Payment)...")
    try:
        checkout_data = {
            "contact": {
                "name": "Manan Shah",
                "email": "manan@example.com"
            },
            "terms_accepted": True,
            "payment": {
                "method": "stripe"
            }
        }
        result = await crew.run_checkout_agent(checkout_data)
        print(f"✅ Checkout Complete! Master Booking ID: {result['master_booking_id']}")
        print(f"   Retailer Confirmations: {len(result['retailer_confirmations'])}")
    except Exception as e:
        print(f"❌ Checkout Error: {e}")
        return

    print("\n" + "=" * 60)
    print("🎯 REAL E2E TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_real_e2e_test())
