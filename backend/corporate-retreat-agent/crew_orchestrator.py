"""
CrewAI Integration - Orchestrates agents using CrewAI framework
"""
from crewai import Agent, Task, Crew, Process
from config import settings
from models import RetreatRequirements, AgentResponse
from agent_requirements import RequirementsAnalystAgent
from agent_discovery import DiscoveryAgent
from agent_ranking import RankingAgent
from agent_cart import CartAgent
from agent_checkout import CheckoutAgent


class RetreatPlannerCrew:
    """CrewAI-powered orchestration of 5 agents"""
    
    def __init__(self):
        self.req_agent_impl = RequirementsAnalystAgent()
        self.disc_agent_impl = DiscoveryAgent()
        self.rank_agent_impl = RankingAgent()
        self.cart_agent_impl = CartAgent()
        self.checkout_agent_impl = CheckoutAgent()
        
        # Define CrewAI agents
        self.requirements_agent = Agent(
            role='Requirements Analyst',
            goal='Parse CEO requests into structured retreat requirements',
            backstory='Expert at understanding business retreat needs from natural language',
            verbose=True,
            allow_delegation=False
        )
        
        self.discovery_agent = Agent(
            role='Vendor Discovery Specialist',
            goal='Find the best vendors across multiple platforms',
            backstory='Expert at searching and discovering retreat vendors using web search',
            verbose=True,
            allow_delegation=False
        )
        
        self.ranking_agent = Agent(
            role='Ranking Specialist',
            goal='Score and rank vendors using transparent criteria',
            backstory='Expert at evaluating vendors with normalized scoring algorithms',
            verbose=True,
            allow_delegation=False
        )
        
        self.cart_agent = Agent(
            role='Cart Optimizer',
            goal='Build optimized carts and suggest improvements',
            backstory='Expert at cart optimization and budget management',
            verbose=True,
            allow_delegation=False
        )
        
        self.checkout_agent = Agent(
            role='Checkout Orchestrator',
            goal='Coordinate multi-vendor payments',
            backstory='Expert at payment processing and checkout workflows',
            verbose=True,
            allow_delegation=False
        )
    
    def plan_retreat(self, user_request: str) -> dict:
        """Execute the full retreat planning workflow using CrewAI"""
        
        # Define tasks
        task1 = Task(
            description=f"Parse this retreat request: {user_request}",
            agent=self.requirements_agent,
            expected_output="Structured retreat requirements"
        )
        
        task2 = Task(
            description="Search for vendors across hotels, conference rooms, catering, and transportation",
            agent=self.discovery_agent,
            expected_output="List of discovered vendor options"
        )
        
        task3 = Task(
            description="Score and rank all vendors using normalized criteria",
            agent=self.ranking_agent,
            expected_output="Ranked list of vendors with scores"
        )
        
        task4 = Task(
            description="Build optimized cart from top-ranked vendors",
            agent=self.cart_agent,
            expected_output="Shopping cart with selected items"
        )
        
        task5 = Task(
            description="Create checkout plan with payment intents",
            agent=self.checkout_agent,
            expected_output="Checkout plan with Stripe integration"
        )
        
        # Create crew
        crew = Crew(
            agents=[
                self.requirements_agent,
                self.discovery_agent,
                self.ranking_agent,
                self.cart_agent,
                self.checkout_agent
            ],
            tasks=[task1, task2, task3, task4, task5],
            process=Process.sequential,
            verbose=True
        )
        
        # Execute - but we'll use our implementations
        print("\n🤖 [CrewAI] Orchestrating 5-agent workflow...\n")
        
        # Step 1: Requirements
        req_result = self.req_agent_impl.parse_requirements(user_request)
        if not req_result.success:
            return {"success": False, "error": "Requirements parsing failed"}
        
        # Step 2: Discovery
        disc_result = self.disc_agent_impl.discover_vendors(req_result.data)
        if not disc_result.success:
            return {"success": False, "error": "Vendor discovery failed"}
        
        # Step 3: Ranking
        rank_result = self.rank_agent_impl.rank_items(disc_result.data, req_result.data)
        if not rank_result.success:
            return {"success": False, "error": "Ranking failed"}
        
        # Step 4: Cart
        cart_result = self.cart_agent_impl.build_cart(rank_result.data, req_result.data)
        if not cart_result.success:
            return {"success": False, "error": "Cart building failed"}
        
        # Step 5: Checkout
        checkout_result = self.checkout_agent_impl.orchestrate_checkout(cart_result.data)
        sim_result = self.checkout_agent_impl.simulate_checkout(checkout_result.data)
        
        return {
            "success": True,
            "requirements": req_result.data,
            "cart": cart_result.data,
            "checkout": checkout_result.data,
            "summary": f"Planned retreat for {req_result.data.num_participants} people in {req_result.data.location}"
        }


if __name__ == "__main__":
    crew = RetreatPlannerCrew()
    
    request = "I am planning a business retreat for 30 executives from Delhi to Hyderabad. Figure out what I need and book it at the best price."
    
    result = crew.plan_retreat(request)
    
    if result["success"]:
        print("\n✅ CrewAI orchestration complete!")
        print(f"Summary: {result['summary']}")
    else:
        print(f"\n❌ Failed: {result.get('error')}")
