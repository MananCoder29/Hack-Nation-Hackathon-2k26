"""
Run the Corporate Retreat Agent with custom input
"""
from main import CorporateRetreatOrchestrator

if __name__ == "__main__":
    orchestrator = CorporateRetreatOrchestrator()
    
    print("=" * 80)
    print("🎯 CORPORATE RETREAT PLANNER - CUSTOM INPUT")
    print("=" * 80)
    print("\nEnter your retreat planning request (CEO-style):")
    print("Example: 'I am planning a business retreat for 50 senior managers.'")
    print("         'Figure out what I need and book it at the best price.'\n")
    
    # Get user input
    user_input = input("Your request: ")
    
    # Run the agent system
    results = orchestrator.process_request(user_input, auto_checkout=True)
    
    if results["success"]:
        print("\n🎉 Planning complete! All agents succeeded.")
    else:
        print(f"\n❌ Planning failed: {results['errors']}")
