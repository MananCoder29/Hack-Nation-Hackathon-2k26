"""
Agent 4: Cart Agent
Builds and optimizes shopping carts from ranked items
"""
from typing import List, Dict
from openai import OpenAI
from config import settings
from models import (
    ScoredItem, Cart, CartItem, RetreatRequirements, 
    ItemType, AgentResponse
)


class CartAgent:
    """
    Builds a shopping cart by selecting the best items for each category.
    Ensures all requirements are met and provides optimization suggestions.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def build_cart(self, scored_items: List[ScoredItem], 
                   requirements: RetreatRequirements) -> AgentResponse:
        """
        Build an optimized cart from scored items
        
        Args:
            scored_items: List of scored vendor items
            requirements: Retreat requirements
            
        Returns:
            AgentResponse with Cart object
        """
        try:
            print(f"\n🛒 [Cart Agent] Building cart from {len(scored_items)} items...")
            
            # Group items by type
            items_by_type = self._group_by_type(scored_items)
            
            # Select best item from each category
            cart_items = []
            for item_type, items in items_by_type.items():
                if items:
                    best_item = items[0]  # Already sorted by score
                    quantity = self._calculate_quantity(best_item, requirements)
                    subtotal = best_item.item.price * quantity
                    
                    cart_item = CartItem(
                        scored_item=best_item,
                        quantity=quantity,
                        subtotal=subtotal
                    )
                    cart_items.append(cart_item)
                    
                    print(f"   ✓ Added: {best_item.item.vendor_name} ({item_type.value})")
                    print(f"     Quantity: {quantity} | Subtotal: ${subtotal:,.2f}")
            
            # Calculate totals
            total_cost = sum(item.subtotal for item in cart_items)
            
            # Check if requirements are met
            meets_requirements = self._check_requirements(cart_items, requirements)
            
            # Generate optimization suggestions
            suggestions = self._generate_suggestions(
                cart_items, requirements, total_cost, items_by_type
            )
            
            cart = Cart(
                items=cart_items,
                total_cost=total_cost,
                meets_requirements=meets_requirements,
                optimization_suggestions=suggestions
            )
            
            print(f"\n✅ [Cart Agent] Cart built successfully")
            print(f"   Total Cost: ${total_cost:,.2f}")
            print(f"   Budget: {'No limit specified' if requirements.budget >= 999999 else f'${requirements.budget:,.2f}'}")
            print(f"   Under Budget: ${requirements.budget - total_cost:,.2f}")
            print(f"   Requirements Met: {meets_requirements}")
            
            if suggestions:
                print(f"\n   💡 Optimization Suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"      {i}. {suggestion}")
            
            return AgentResponse(
                success=True,
                data=cart,
                message=f"Cart created with {len(cart_items)} items"
            )
            
        except Exception as e:
            error_msg = f"Cart building failed: {str(e)}"
            print(f"❌ [Cart Agent] {error_msg}")
            return AgentResponse(
                success=False,
                data=None,
                message="Failed to build cart",
                errors=[error_msg]
            )
    
    def _group_by_type(self, scored_items: List[ScoredItem]) -> Dict[ItemType, List[ScoredItem]]:
        """Group scored items by their type, maintaining sort order"""
        groups = {}
        for item in scored_items:
            item_type = item.item.item_type
            if item_type not in groups:
                groups[item_type] = []
            groups[item_type].append(item)
        return groups
    
    def _calculate_quantity(self, scored_item: ScoredItem, 
                          requirements: RetreatRequirements) -> int:
        """
        Calculate required quantity based on item type and participants
        """
        item_type = scored_item.item.item_type
        num_participants = requirements.num_participants
        
        if item_type == ItemType.HOTEL:
            # Assume 2 people per room
            return (num_participants + 1) // 2
        elif item_type == ItemType.CONFERENCE_ROOM:
            # One room for the whole group
            return 1
        elif item_type == ItemType.CATERING:
            # Per person, per day
            from datetime import datetime
            start = datetime.strptime(requirements.start_date, "%Y-%m-%d")
            end = datetime.strptime(requirements.end_date, "%Y-%m-%d")
            days = (end - start).days + 1
            meals_per_day = 2  # Lunch and dinner
            return num_participants * days * meals_per_day
        elif item_type == ItemType.TRANSPORTATION:
            # Per person, round trip
            return num_participants
        else:
            return 1
    
    def _check_requirements(self, cart_items: List[CartItem], 
                           requirements: RetreatRequirements) -> bool:
        """
        Check if cart meets all must-have requirements
        """
        # Check essential item types are present
        essential_types = {ItemType.HOTEL, ItemType.CONFERENCE_ROOM}
        present_types = {item.scored_item.item.item_type for item in cart_items}
        
        has_essentials = essential_types.issubset(present_types)
        
        # Check capacity
        has_capacity = all(
            item.scored_item.item.capacity >= requirements.num_participants
            for item in cart_items
        )
        
        # Check budget
        total_cost = sum(item.subtotal for item in cart_items)
        within_budget = total_cost <= requirements.budget
        
        return has_essentials and has_capacity and within_budget
    
    def _generate_suggestions(self, cart_items: List[CartItem], 
                             requirements: RetreatRequirements,
                             total_cost: float,
                             items_by_type: Dict[ItemType, List[ScoredItem]]) -> List[str]:
        """
        Generate optimization suggestions
        """
        suggestions = []
        
        # Budget optimization
        budget_remaining = requirements.budget - total_cost if requirements.budget < 999999 else 0
        if requirements.budget >= 999999:
            suggestions.append(
                f"💰 Total cost calculated: ${total_cost:,.2f} (no budget limit specified)"
            )
        elif budget_remaining < 0:
            suggestions.append(
                f"⚠️ Over budget by ${abs(budget_remaining):,.2f}. "
                "Consider selecting lower-cost alternatives."
            )
        elif budget_remaining > requirements.budget * 0.2:
            suggestions.append(
                f"💰 ${budget_remaining:,.2f} remaining. "
                "Consider upgrading services or adding team activities."
            )
        
        # Alternative options
        for cart_item in cart_items:
            item_type = cart_item.scored_item.item.item_type
            alternatives = items_by_type.get(item_type, [])
            
            if len(alternatives) > 1:
                current = cart_item.scored_item
                next_best = alternatives[1]
                
                price_diff = (next_best.item.price - current.item.price) * cart_item.quantity
                score_diff = current.total_score - next_best.total_score
                
                if price_diff < 0:  # Cheaper alternative
                    suggestions.append(
                        f"💡 {next_best.item.vendor_name} ({item_type.value}) "
                        f"could save ${abs(price_diff):,.2f} "
                        f"(score: {next_best.total_score:.2f} vs {current.total_score:.2f})"
                    )
        
        # Missing categories
        all_types = {ItemType.HOTEL, ItemType.CONFERENCE_ROOM, ItemType.CATERING, 
                     ItemType.TRANSPORTATION}
        present_types = {item.scored_item.item.item_type for item in cart_items}
        missing = all_types - present_types
        
        if missing:
            missing_names = [t.value.replace('_', ' ') for t in missing]
            suggestions.append(
                f"ℹ️ Consider adding: {', '.join(missing_names)}"
            )
        
        return suggestions
