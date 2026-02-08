"""
Main Orchestrator - Coordinates all 5 agents in the Corporate Retreat Agent System
"""
import json
from typing import Dict, Any
from datetime import datetime

from agent_requirements import RequirementsAnalystAgent
from agent_discovery import DiscoveryAgent
from agent_ranking import RankingAgent
from agent_cart import CartAgent
from agent_checkout import CheckoutAgent
from models import AgentResponse


class CorporateRetreatOrchestrator:
    """
    Main orchestrator that coordinates all 5 agents:
    1. Requirements Analyst - Parse user input
    2. Discovery Agent - Search for vendors
    3. Ranking Agent - Score and rank options
    4. Cart Agent - Build optimized cart
    5. Checkout Agent - Orchestrate payment
    """
    
    def __init__(self):
        self.req_agent = RequirementsAnalystAgent()
        self.disc_agent = DiscoveryAgent()
        self.rank_agent = RankingAgent()
        self.cart_agent = CartAgent()
        self.checkout_agent = CheckoutAgent()
        
        self.session_data = {
            "start_time": None,
            "requirements": None,
            "discovered_items": None,
            "ranked_items": None,
            "cart": None,
            "checkout_plan": None
        }
    
    def process_request(self, user_input: str, auto_checkout: bool = False) -> Dict[str, Any]:
        """
        Process a complete corporate retreat request through all agents
        
        Args:
            user_input: Natural language description of retreat requirements
            auto_checkout: If True, automatically proceed to checkout simulation
            
        Returns:
            Dictionary with results from all agents
        """
        print("=" * 80)
        print("🚀 CORPORATE RETREAT AGENT SYSTEM")
        print("=" * 80)
        print(f"Processing request...")
        print("=" * 80)
        
        self.session_data["start_time"] = datetime.now()
        results = {
            "success": False,
            "agents": {},
            "summary": {},
            "errors": []
        }
        
        try:
            # AGENT 1: Requirements Analyst
            print("\n" + "=" * 80)
            print("STEP 1/5: REQUIREMENTS ANALYSIS")
            print("=" * 80)
            
            req_result = self.req_agent.parse_requirements(user_input)
            results["agents"]["requirements"] = self._format_agent_result(req_result)
            
            if not req_result.success:
                results["errors"].append("Requirements analysis failed")
                return results
            
            self.session_data["requirements"] = req_result.data
            
            # AGENT 2: Discovery Agent
            print("\n" + "=" * 80)
            print("STEP 2/5: VENDOR DISCOVERY")
            print("=" * 80)
            
            disc_result = self.disc_agent.discover_vendors(req_result.data)
            results["agents"]["discovery"] = self._format_agent_result(disc_result)
            
            if not disc_result.success or not disc_result.data:
                results["errors"].append("Vendor discovery failed or no vendors found")
                return results
            
            self.session_data["discovered_items"] = disc_result.data
            
            # AGENT 3: Ranking Agent
            print("\n" + "=" * 80)
            print("STEP 3/5: VENDOR RANKING")
            print("=" * 80)
            
            rank_result = self.rank_agent.rank_items(disc_result.data, req_result.data)
            results["agents"]["ranking"] = self._format_agent_result(rank_result)
            
            if not rank_result.success:
                results["errors"].append("Vendor ranking failed")
                return results
            
            self.session_data["ranked_items"] = rank_result.data
            
            # AGENT 4: Cart Agent
            print("\n" + "=" * 80)
            print("STEP 4/5: CART BUILDING")
            print("=" * 80)
            
            cart_result = self.cart_agent.build_cart(rank_result.data, req_result.data)
            results["agents"]["cart"] = self._format_agent_result(cart_result)
            
            if not cart_result.success:
                results["errors"].append("Cart building failed")
                return results
            
            self.session_data["cart"] = cart_result.data
            
            # AGENT 5: Checkout Agent
            print("\n" + "=" * 80)
            print("STEP 5/5: CHECKOUT ORCHESTRATION")
            print("=" * 80)
            
            checkout_result = self.checkout_agent.orchestrate_checkout(cart_result.data)
            results["agents"]["checkout"] = self._format_agent_result(checkout_result)
            
            if not checkout_result.success:
                results["errors"].append("Checkout orchestration failed")
                return results
            
            self.session_data["checkout_plan"] = checkout_result.data
            
            # Optional: Simulate checkout
            if auto_checkout:
                print("\n" + "=" * 80)
                print("BONUS: CHECKOUT SIMULATION")
                print("=" * 80)
                
                sim_result = self.checkout_agent.simulate_checkout(checkout_result.data)
                results["agents"]["simulation"] = self._format_agent_result(sim_result)
            
            # Generate summary
            results["success"] = True
            results["summary"] = self._generate_summary()
            
            # Print final summary
            self._print_summary(results["summary"])
            
            return results
            
        except Exception as e:
            results["errors"].append(f"Orchestration error: {str(e)}")
            print(f"\n❌ FATAL ERROR: {str(e)}")
            return results
    
    def _format_agent_result(self, result: AgentResponse) -> Dict[str, Any]:
        """Format agent result for JSON serialization"""
        return {
            "success": result.success,
            "message": result.message,
            "errors": result.errors,
            "data_available": result.data is not None
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of the entire process"""
        requirements = self.session_data["requirements"]
        cart = self.session_data["cart"]
        checkout_plan = self.session_data["checkout_plan"]
        
        duration = (datetime.now() - self.session_data["start_time"]).total_seconds()
        
        return {
            "processing_time_seconds": round(duration, 2),
            "requirements": {
                "participants": requirements.num_participants,
                "location": requirements.location,
                "dates": f"{requirements.start_date} to {requirements.end_date}",
                "budget": requirements.budget
            },
            "discovery": {
                "vendors_found": len(self.session_data["discovered_items"])
            },
            "cart": {
                "items_selected": len(cart.items),
                "total_cost": cart.total_cost,
                "under_budget": requirements.budget - cart.total_cost,
                "meets_requirements": cart.meets_requirements,
                "vendors": list(set(
                    item.scored_item.item.vendor_name for item in cart.items
                ))
            },
            "checkout": {
                "payment_steps": len(checkout_plan.steps),
                "total_amount": checkout_plan.total_amount,
                "estimated_time": checkout_plan.estimated_completion_time
            }
        }
    
    def _print_summary(self, summary: Dict[str, Any]):
        """Print a formatted summary"""
        print("\n" + "=" * 80)
        print("📊 FINAL SUMMARY")
        print("=" * 80)
        
        print(f"\n⏱️  Processing Time: {summary['processing_time_seconds']} seconds")
        
        print(f"\n📋 Requirements:")
        for key, value in summary['requirements'].items():
            print(f"   {key}: {value}")
        
        print(f"\n🔍 Discovery:")
        print(f"   Vendors found: {summary['discovery']['vendors_found']}")
        
        print(f"\n🛒 Cart:")
        print(f"   Items selected: {summary['cart']['items_selected']}")
        print(f"   Total cost: ${summary['cart']['total_cost']:,.2f}")
        print(f"   Under budget: ${summary['cart']['under_budget']:,.2f}")
        print(f"   Requirements met: {summary['cart']['meets_requirements']}")
        print(f"   Vendors: {', '.join(summary['cart']['vendors'])}")
        
        print(f"\n💳 Checkout:")
        print(f"   Payment steps: {summary['checkout']['payment_steps']}")
        print(f"   Total amount: ${summary['checkout']['total_amount']:,.2f}")
        print(f"   Estimated time: {summary['checkout']['estimated_time']}")
        
        print("\n" + "=" * 80)
        print("✅ PROCESS COMPLETE")
        print("=" * 80)


# Main execution
if __name__ == "__main__":
    orchestrator = CorporateRetreatOrchestrator()
    
    user_request = """
    I am planning a business retreat for 50 senior managers in my company.
    Location: Las Vegas, Nevada
    Dates: March 15-17, 2025
    Budget: $100,000
    
    We need:
    - Hotel rooms for all participants
    - A conference room with AV setup for 50 people
    - Catering for lunch and dinner
    - Airport transfers
    """
    
    # Run the full pipeline
    results = orchestrator.process_request(user_request, auto_checkout=True)
    
    if results["success"]:
        print("\n🎉 All agents completed successfully!")
    else:
        print(f"\n❌ Process failed with errors: {results['errors']}")
