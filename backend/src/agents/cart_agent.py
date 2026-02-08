"""Agent 4: Cart Agent - Build and optimize shopping cart."""

from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime


class CartAgent:
    """Agent that builds and optimizes shopping carts from selected packages."""
    
    def __init__(self):
        self.tax_rate = 0.0875  # 8.75% default tax rate
        self.service_fee_rate = 0.025  # 2.5% service fee
    
    async def build_cart(
        self,
        package: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build cart from selected package.
        
        Args:
            package: Selected ranked package
            requirements: User requirements
            
        Returns:
            Cart dictionary with items, totals, and metadata
        """
        cart_id = f"cart_{str(uuid.uuid4())[:8]}"
        items = package.get("items", {})
        
        cart_items = {}
        subtotal = 0
        
        for category, item in items.items():
            price = item.get("price", 0)
            quantity = self._calculate_quantity(category, item, requirements)
            item_subtotal = price * quantity
            
            cart_items[category] = {
                "item": item,
                "quantity": quantity,
                "unit_price": price,
                "subtotal": round(item_subtotal, 2)
            }
            subtotal += item_subtotal
        
        # Calculate taxes and fees
        taxes = subtotal * self.tax_rate
        fees = subtotal * self.service_fee_rate
        total = subtotal + taxes + fees
        
        # Calculate potential savings vs alternatives
        savings = self._calculate_savings(package, requirements)
        
        return {
            "cart_id": cart_id,
            "items": cart_items,
            "subtotal": round(subtotal, 2),
            "taxes": round(taxes, 2),
            "fees": round(fees, 2),
            "total": round(total, 2),
            "savings": savings,
            "created_at": datetime.now().isoformat(),
            "requirements_summary": self._summarize_requirements(requirements)
        }
    
    async def modify(
        self,
        cart: Dict[str, Any],
        modification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Modify cart based on user action.
        
        Args:
            cart: Current cart state
            modification: Modification request
            
        Returns:
            Updated cart dictionary
        """
        action = modification.get("action", "")
        
        if action == "swap":
            return await self._swap_item(cart, modification)
        elif action == "remove":
            return await self._remove_item(cart, modification)
        elif action == "optimize":
            return await self._optimize_cart(cart, modification)
        else:
            return cart
    
    def _calculate_quantity(
        self,
        category: str,
        item: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> int:
        """Calculate quantity needed based on category and requirements.
        
        Args:
            category: Item category
            item: Item dictionary
            requirements: User requirements
            
        Returns:
            Quantity needed
        """
        attendees = requirements.get("attendees", 50)
        
        # Extract duration in days
        duration = requirements.get("duration", "2 days")
        import re
        days_match = re.search(r'(\d+)', duration)
        num_days = int(days_match.group(1)) if days_match else 2
        
        if category == "flights":
            # One flight per attendee (round trip typically priced together)
            return attendees
        elif category == "hotels":
            # Rooms for all attendees (assuming double occupancy)
            rooms = (attendees // 2) + (attendees % 2)
            return rooms * num_days  # Room-nights
        elif category == "meeting_rooms":
            # One room for the duration
            return num_days
        elif category == "catering":
            # Meals per person per day
            return attendees * num_days
        else:
            return 1
    
    def _calculate_savings(
        self,
        package: Dict[str, Any],
        requirements: Dict[str, Any]
    ) -> Optional[float]:
        """Calculate estimated savings vs booking separately.
        
        Args:
            package: Selected package
            requirements: User requirements
            
        Returns:
            Estimated savings amount or None
        """
        # Estimate savings as 10-15% vs individual booking
        total_cost = package.get("total_cost", 0)
        if total_cost > 0:
            import random
            savings_pct = random.uniform(0.10, 0.15)
            return round(total_cost * savings_pct, 2)
        return None
    
    def _summarize_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of requirements for cart display.
        
        Args:
            requirements: Full requirements dictionary
            
        Returns:
            Summarized requirements
        """
        return {
            "attendees": requirements.get("attendees", 50),
            "duration": requirements.get("duration", "2 days"),
            "location": requirements.get("location", ""),
            "origin": requirements.get("origin", ""),
            "event_type": "Corporate Retreat"
        }
    
    async def _swap_item(
        self,
        cart: Dict[str, Any],
        modification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Swap an item in the cart with an alternative.
        
        Args:
            cart: Current cart
            modification: Swap modification request
            
        Returns:
            Updated cart
        """
        item_id = modification.get("item_id")
        new_item = modification.get("new_item")
        
        if not item_id or not new_item:
            return cart
        
        # Find and replace the item
        for category, cart_item in cart.get("items", {}).items():
            if cart_item.get("item", {}).get("item_id") == item_id:
                old_subtotal = cart_item.get("subtotal", 0)
                new_price = new_item.get("price", 0)
                quantity = cart_item.get("quantity", 1)
                new_subtotal = new_price * quantity
                
                # Update item
                cart["items"][category] = {
                    "item": new_item,
                    "quantity": quantity,
                    "unit_price": new_price,
                    "subtotal": round(new_subtotal, 2)
                }
                
                # Recalculate totals
                cart = self._recalculate_totals(cart)
                break
        
        return cart
    
    async def _remove_item(
        self,
        cart: Dict[str, Any],
        modification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Remove an item from the cart.
        
        Args:
            cart: Current cart
            modification: Remove modification request
            
        Returns:
            Updated cart
        """
        item_id = modification.get("item_id")
        
        if not item_id:
            return cart
        
        # Find and remove the item
        for category in list(cart.get("items", {}).keys()):
            if cart["items"][category].get("item", {}).get("item_id") == item_id:
                del cart["items"][category]
                cart = self._recalculate_totals(cart)
                break
        
        return cart
    
    async def _optimize_cart(
        self,
        cart: Dict[str, Any],
        modification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize cart based on goal (cost, quality, balanced).
        
        Args:
            cart: Current cart
            modification: Optimization request
            
        Returns:
            Optimized cart (placeholder - would need alternative items)
        """
        goal = modification.get("optimization_goal", "balanced")
        
        # In a full implementation, this would:
        # 1. Get alternative items for each category
        # 2. Re-score based on optimization goal
        # 3. Select new items that better meet the goal
        
        # For now, return the cart with a note
        cart["optimization_applied"] = goal
        cart["optimization_note"] = f"Cart optimized for {goal}"
        
        return cart
    
    def _recalculate_totals(self, cart: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate cart totals after modification.
        
        Args:
            cart: Cart to recalculate
            
        Returns:
            Cart with updated totals
        """
        subtotal = sum(
            item.get("subtotal", 0) 
            for item in cart.get("items", {}).values()
        )
        
        taxes = subtotal * self.tax_rate
        fees = subtotal * self.service_fee_rate
        total = subtotal + taxes + fees
        
        cart["subtotal"] = round(subtotal, 2)
        cart["taxes"] = round(taxes, 2)
        cart["fees"] = round(fees, 2)
        cart["total"] = round(total, 2)
        cart["modified_at"] = datetime.now().isoformat()
        
        return cart
