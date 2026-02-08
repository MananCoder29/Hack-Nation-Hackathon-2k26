"""Agent 5: Checkout Agent - Process multi-retailer checkout."""

from typing import Dict, Any, List
import uuid
from datetime import datetime
import os

try:
    import stripe
except ImportError:
    stripe = None


class CheckoutAgent:
    """Agent that orchestrates checkout across multiple retailers."""
    
    def __init__(self):
        if stripe:
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
    
    async def process_checkout(
        self,
        cart: Dict[str, Any],
        checkout_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process checkout for all items in cart.
        
        Args:
            cart: Cart with all items
            checkout_data: Checkout request data (contact, payment info)
            
        Returns:
            Master booking confirmation with retailer confirmations
        """
        master_booking_id = f"RTR-{str(uuid.uuid4())[:8].upper()}"
        
        # Validate checkout data
        self._validate_checkout_data(checkout_data)
        
        # Process payment (simulated)
        payment_result = await self._process_payment(
            cart.get("total", 0),
            checkout_data.get("payment", {})
        )
        
        if not payment_result.get("success"):
            raise ValueError(f"Payment failed: {payment_result.get('error')}")
        
        # Generate confirmations for each retailer
        confirmations = []
        for category, cart_item in cart.get("items", {}).items():
            item = cart_item.get("item", {})
            confirmation = await self._book_with_retailer(
                category,
                item,
                cart_item,
                checkout_data
            )
            confirmations.append(confirmation)
        
        return {
            "master_booking_id": master_booking_id,
            "retailer_confirmations": confirmations,
            "total_cost": cart.get("total", 0),
            "payment_reference": payment_result.get("transaction_id"),
            "booking_date": datetime.now().isoformat(),
            "contact": checkout_data.get("contact", {}),
            "status": "confirmed"
        }
    
    def _validate_checkout_data(self, checkout_data: Dict[str, Any]) -> None:
        """Validate checkout data before processing.
        
        Args:
            checkout_data: Checkout request data
            
        Raises:
            ValueError: If validation fails
        """
        contact = checkout_data.get("contact", {})
        
        if not contact.get("name"):
            raise ValueError("Contact name is required")
        
        if not contact.get("email"):
            raise ValueError("Contact email is required")
        
        # Validate email format
        email = contact.get("email", "")
        if "@" not in email or "." not in email:
            raise ValueError("Invalid email format")
        
        if not checkout_data.get("terms_accepted", False):
            raise ValueError("Terms and conditions must be accepted")
    
    async def _process_payment(
        self,
        amount: float,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payment (simulated for demo).
        
        Args:
            amount: Payment amount
            payment_data: Payment details
            
        Returns:
            Payment result dictionary
        """
        method = payment_data.get("method", "stripe")
        
        if method == "stripe":
            # In production, this would use Stripe API
            # For demo, we simulate a successful payment
            return {
                "success": True,
                "transaction_id": f"ch_{str(uuid.uuid4())[:16]}",
                "method": "stripe",
                "amount": amount,
                "timestamp": datetime.now().isoformat()
            }
        
        elif method == "invoice":
            # Invoice payment - no immediate charge
            return {
                "success": True,
                "transaction_id": f"inv_{str(uuid.uuid4())[:8].upper()}",
                "method": "invoice",
                "amount": amount,
                "due_date": "Net 30",
                "timestamp": datetime.now().isoformat()
            }
        
        elif method == "po":
            # Purchase order
            po_number = payment_data.get("po_number")
            if not po_number:
                return {
                    "success": False,
                    "error": "PO number required for purchase order payment"
                }
            
            return {
                "success": True,
                "transaction_id": f"po_{po_number}",
                "method": "purchase_order",
                "amount": amount,
                "po_number": po_number,
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            return {
                "success": False,
                "error": f"Unsupported payment method: {method}"
            }
    
    async def _book_with_retailer(
        self,
        category: str,
        item: Dict[str, Any],
        cart_item: Dict[str, Any],
        checkout_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Book with individual retailer (simulated).
        
        Args:
            category: Item category
            item: Item details
            cart_item: Cart item with quantity
            checkout_data: Checkout data
            
        Returns:
            Retailer confirmation
        """
        # Generate retailer-specific confirmation number
        vendor = item.get("vendor", "Unknown")
        conf_prefix = {
            "flights": "FLT",
            "hotels": "HTL",
            "meeting_rooms": "MTG",
            "catering": "CTR"
        }.get(category, "BKG")
        
        confirmation_number = f"{conf_prefix}-{str(uuid.uuid4())[:6].upper()}"
        
        return {
            "vendor": vendor,
            "category": category,
            "confirmation_number": confirmation_number,
            "status": "confirmed",
            "item_title": item.get("title", ""),
            "quantity": cart_item.get("quantity", 1),
            "item_total": cart_item.get("subtotal", 0),
            "booking_details": self._generate_booking_details(category, item, cart_item),
            "cancellation_policy": self._get_cancellation_policy(category),
            "contact_info": self._get_vendor_contact(vendor)
        }
    
    def _generate_booking_details(
        self,
        category: str,
        item: Dict[str, Any],
        cart_item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate category-specific booking details.
        
        Args:
            category: Item category
            item: Item details
            cart_item: Cart item
            
        Returns:
            Booking details dictionary
        """
        metadata = item.get("metadata", {})
        
        if category == "flights":
            return {
                "departure": metadata.get("departure", ""),
                "arrival": metadata.get("arrival", ""),
                "passengers": cart_item.get("quantity", 1),
                "class": "Economy/Business Mix",
                "baggage": "1 checked bag included"
            }
        
        elif category == "hotels":
            return {
                "check_in": "TBD",
                "check_out": "TBD",
                "room_nights": cart_item.get("quantity", 1),
                "room_type": "Standard Double",
                "amenities": metadata.get("amenities", [])
            }
        
        elif category == "meeting_rooms":
            return {
                "capacity": metadata.get("capacity", 50),
                "equipment": metadata.get("equipment", []),
                "setup_style": "Theater/Classroom",
                "duration": f"{cart_item.get('quantity', 1)} day(s)"
            }
        
        else:  # catering
            return {
                "meals": cart_item.get("quantity", 1),
                "cuisine": metadata.get("cuisine", ""),
                "dietary_options": metadata.get("dietary_options", []),
                "service_style": metadata.get("service_style", "Buffet")
            }
    
    def _get_cancellation_policy(self, category: str) -> str:
        """Get cancellation policy for category.
        
        Args:
            category: Item category
            
        Returns:
            Cancellation policy string
        """
        policies = {
            "flights": "Free cancellation up to 24 hours before departure",
            "hotels": "Free cancellation up to 48 hours before check-in",
            "meeting_rooms": "Full refund up to 7 days before event",
            "catering": "Full refund up to 5 days before event, 50% up to 48 hours"
        }
        return policies.get(category, "Contact vendor for cancellation policy")
    
    def _get_vendor_contact(self, vendor: str) -> Dict[str, str]:
        """Get vendor contact information.
        
        Args:
            vendor: Vendor name
            
        Returns:
            Contact information dictionary
        """
        return {
            "email": f"support@{vendor.lower().replace(' ', '')}.com",
            "phone": "1-800-555-0123",
            "support_hours": "24/7"
        }
