"""
Agent 5: Checkout Agent
Orchestrates checkout process across multiple vendors using Stripe
"""
import stripe
from typing import List
from config import settings
from models import Cart, CheckoutPlan, CheckoutStep, AgentResponse


class CheckoutAgent:
    """
    Orchestrates the checkout process across multiple vendors.
    Uses Stripe for payment processing (test mode).
    """
    
    def __init__(self):
        stripe.api_key = settings.stripe_secret_key
    
    def orchestrate_checkout(self, cart: Cart) -> AgentResponse:
        """
        Create a checkout plan for all items in the cart
        
        Args:
            cart: Shopping cart with selected items
            
        Returns:
            AgentResponse with CheckoutPlan object
        """
        try:
            print(f"\n💳 [Checkout Agent] Orchestrating checkout for {len(cart.items)} vendors...")
            
            # Group items by vendor
            vendor_groups = self._group_by_vendor(cart)
            
            # Create checkout steps
            steps = []
            total_amount = 0.0
            
            for vendor_name, items in vendor_groups.items():
                vendor_total = sum(item.subtotal for item in items)
                total_amount += vendor_total
                
                # Create Stripe payment intent (test mode)
                try:
                    payment_intent = self._create_payment_intent(
                        vendor_name,
                        vendor_total
                    )
                    
                    step = CheckoutStep(
                        vendor_name=vendor_name,
                        items=[f"{item.scored_item.item.description[:50]}..." for item in items],
                        total_amount=vendor_total,
                        status="ready",
                        payment_intent_id=payment_intent.id
                    )
                    
                    print(f"   ✓ {vendor_name}: ${vendor_total:,.2f}")
                    print(f"     Payment Intent: {payment_intent.id}")
                    print(f"     Status: {payment_intent.status}")
                    
                except Exception as e:
                    print(f"   ⚠️ {vendor_name}: Failed to create payment intent - {str(e)}")
                    step = CheckoutStep(
                        vendor_name=vendor_name,
                        items=[f"{item.scored_item.item.description[:50]}..." for item in items],
                        total_amount=vendor_total,
                        status="error"
                    )
                
                steps.append(step)
            
            # Create checkout plan
            plan = CheckoutPlan(
                steps=steps,
                total_amount=total_amount,
                estimated_completion_time="5-10 minutes"
            )
            
            print(f"\n✅ [Checkout Agent] Checkout plan created")
            print(f"   Total Vendors: {len(steps)}")
            print(f"   Total Amount: ${total_amount:,.2f}")
            print(f"   Estimated Time: {plan.estimated_completion_time}")
            
            return AgentResponse(
                success=True,
                data=plan,
                message=f"Checkout plan created for {len(steps)} vendors"
            )
            
        except Exception as e:
            error_msg = f"Checkout orchestration failed: {str(e)}"
            print(f"❌ [Checkout Agent] {error_msg}")
            return AgentResponse(
                success=False,
                data=None,
                message="Failed to create checkout plan",
                errors=[error_msg]
            )
    
    def _group_by_vendor(self, cart: Cart) -> dict:
        """Group cart items by vendor name"""
        groups = {}
        for item in cart.items:
            vendor = item.scored_item.item.vendor_name
            if vendor not in groups:
                groups[vendor] = []
            groups[vendor].append(item)
        return groups
    
    def _create_payment_intent(self, vendor_name: str, amount: float):
        """
        Create a Stripe payment intent for a vendor
        
        Args:
            vendor_name: Name of the vendor
            amount: Payment amount in dollars
            
        Returns:
            Stripe PaymentIntent object
        """
        # Convert to cents for Stripe
        amount_cents = int(amount * 100)
        
        payment_intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            description=f"Corporate Retreat - {vendor_name}",
            metadata={
                "vendor": vendor_name,
                "integration": "Corporate Retreat Agent"
            },
            # Automatic payment methods
            automatic_payment_methods={
                "enabled": True,
            }
        )
        
        return payment_intent
    
    def simulate_checkout(self, plan):
        """Simulate checkout execution"""
        print(f"\n🎬 [Checkout Agent] Simulating checkout...")
        for step in plan.steps:
            if step.payment_intent_id:
                step.status = "completed"
                print(f"   ✓ {step.vendor_name}: Completed")
        print(f"\n✅ Checkout simulation complete")
        return AgentResponse(success=True, data={"plan": plan}, message="Simulation OK")
