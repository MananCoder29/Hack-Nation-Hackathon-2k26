"""Retreat Planner Crew - Orchestrates all agents for retreat planning."""

from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

from src.agents.requirements_analyst import RequirementsAnalystAgent
from src.agents.discovery_agent import DiscoveryAgent
from src.agents.ranking_agent import RankingAgent
from src.agents.cart_agent import CartAgent
from src.agents.checkout_agent import CheckoutAgent


class RetreatPlannerCrew:
    """Orchestrates the 5-agent retreat planning workflow.
    
    This crew manages the state and flow between:
    1. Requirements Analyst - Parse natural language requirements
    2. Discovery Agent - Search vendors using Tavily
    3. Ranking Agent - Score and rank packages
    4. Cart Agent - Build and optimize cart
    5. Checkout Agent - Process multi-retailer checkout
    """
    
    def __init__(self):
        """Initialize a new crew session."""
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.now().isoformat()
        
        # Workflow state
        self.requirements: Optional[Dict[str, Any]] = None
        self.discovered_items: Optional[List[Dict[str, Any]]] = None
        self.ranked_packages: Optional[List[Dict[str, Any]]] = None
        self.cart: Optional[Dict[str, Any]] = None
        
        # Initialize agents (lazy loading for some)
        self._requirements_agent: Optional[RequirementsAnalystAgent] = None
        self._discovery_agent: Optional[DiscoveryAgent] = None
        self._ranking_agent: Optional[RankingAgent] = None
        self._cart_agent: Optional[CartAgent] = None
        self._checkout_agent: Optional[CheckoutAgent] = None
    
    @property
    def requirements_agent(self) -> RequirementsAnalystAgent:
        """Lazy-load requirements analyst agent."""
        if self._requirements_agent is None:
            self._requirements_agent = RequirementsAnalystAgent()
        return self._requirements_agent
    
    @property
    def discovery_agent(self) -> DiscoveryAgent:
        """Lazy-load discovery agent."""
        if self._discovery_agent is None:
            self._discovery_agent = DiscoveryAgent()
        return self._discovery_agent
    
    @property
    def ranking_agent(self) -> RankingAgent:
        """Lazy-load ranking agent."""
        if self._ranking_agent is None:
            self._ranking_agent = RankingAgent()
        return self._ranking_agent
    
    @property
    def cart_agent(self) -> CartAgent:
        """Lazy-load cart agent."""
        if self._cart_agent is None:
            self._cart_agent = CartAgent()
        return self._cart_agent
    
    @property
    def checkout_agent(self) -> CheckoutAgent:
        """Lazy-load checkout agent."""
        if self._checkout_agent is None:
            self._checkout_agent = CheckoutAgent()
        return self._checkout_agent
    
    async def run_requirements_analyst(self, user_input: str) -> Dict[str, Any]:
        """Execute Agent 1: Requirements Analysis.
        
        Args:
            user_input: Natural language retreat requirements
            
        Returns:
            Structured requirements dictionary
        """
        self.requirements = await self.requirements_agent.analyze(user_input)
        return self.requirements
    
    async def run_discovery_agent(self) -> List[Dict[str, Any]]:
        """Execute Agent 2: Multi-Source Discovery.
        
        Returns:
            List of discovered items across all categories
            
        Raises:
            ValueError: If requirements not analyzed yet
        """
        if not self.requirements:
            raise ValueError("Requirements not analyzed yet. Run requirements analyst first.")
        
        self.discovered_items = await self.discovery_agent.discover(self.requirements)
        return self.discovered_items
    
    async def run_ranking_agent(
        self, 
        custom_weights: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute Agent 3: Intelligent Ranking.
        
        Args:
            custom_weights: Optional custom weights for scoring
            
        Returns:
            List of ranked packages with scores and explanations
            
        Raises:
            ValueError: If items not discovered yet
        """
        if not self.discovered_items:
            raise ValueError("Items not discovered yet. Run discovery agent first.")
        
        self.ranked_packages = await self.ranking_agent.rank(
            self.discovered_items,
            self.requirements,
            custom_weights
        )
        return self.ranked_packages
    
    async def run_cart_agent(self, package_id: str) -> Dict[str, Any]:
        """Execute Agent 4: Cart Building.
        
        Args:
            package_id: ID of the selected package
            
        Returns:
            Cart dictionary with items and totals
            
        Raises:
            ValueError: If packages not ranked yet or package not found
        """
        if not self.ranked_packages:
            raise ValueError("Packages not ranked yet. Run ranking agent first.")
        
        # Find the selected package
        selected_package = next(
            (p for p in self.ranked_packages if p.get("package_id") == package_id),
            None
        )
        
        if not selected_package:
            raise ValueError(f"Package {package_id} not found in ranked packages")
        
        self.cart = await self.cart_agent.build_cart(
            selected_package,
            self.requirements
        )
        return self.cart
    
    async def modify_cart(self, modification: Dict[str, Any]) -> Dict[str, Any]:
        """Modify cart and potentially re-rank.
        
        Args:
            modification: Modification request (swap, remove, adjust_weights, optimize)
            
        Returns:
            Updated cart dictionary
            
        Raises:
            ValueError: If cart not built yet
        """
        if not self.cart:
            raise ValueError("Cart not built yet. Run cart agent first.")
        
        action = modification.get("action", "")
        
        # If weights changed, re-rank and rebuild cart
        if action == "adjust_weights":
            weights = modification.get("weights")
            self.ranked_packages = await self.ranking_agent.rank(
                self.discovered_items,
                self.requirements,
                weights
            )
            # Rebuild cart with top package
            if self.ranked_packages:
                top_package = self.ranked_packages[0]
                self.cart = await self.cart_agent.build_cart(
                    top_package,
                    self.requirements
                )
        else:
            # Handle swap, remove, or optimize
            self.cart = await self.cart_agent.modify(self.cart, modification)
        
        return self.cart
    
    async def run_checkout_agent(
        self, 
        checkout_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute Agent 5: Checkout Orchestration.
        
        Args:
            checkout_data: Checkout request with contact and payment info
            
        Returns:
            Master booking confirmation with retailer confirmations
            
        Raises:
            ValueError: If cart not built yet
        """
        if not self.cart:
            raise ValueError("Cart not built yet. Run cart agent first.")
        
        confirmation = await self.checkout_agent.process_checkout(
            self.cart,
            checkout_data
        )
        return confirmation
    
    def get_session_state(self) -> Dict[str, Any]:
        """Get current session state for debugging/monitoring.
        
        Returns:
            Dictionary with session state information
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "has_requirements": self.requirements is not None,
            "discovered_items_count": len(self.discovered_items) if self.discovered_items else 0,
            "ranked_packages_count": len(self.ranked_packages) if self.ranked_packages else 0,
            "has_cart": self.cart is not None,
            "cart_total": self.cart.get("total") if self.cart else None
        }
