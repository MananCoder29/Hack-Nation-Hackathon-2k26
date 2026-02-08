"""
Agent 3: Ranking Agent
Scores and ranks vendors using transparent, weighted scoring logic
"""
from typing import List, Dict
from openai import OpenAI
from config import settings
from models import VendorItem, ScoredItem, RetreatRequirements, AgentResponse


class RankingAgent:
    """
    Ranks vendor items using normalized scoring across multiple criteria:
    - Price (30%): Lower is better
    - Availability (20%): Can handle required participants
    - Quality (20%): Based on ratings and reputation
    - Time/Efficiency (10%): Service speed
    - Operational Risk (10%): Reliability
    - Distance (10%): Proximity to city center
    
    All scores are normalized to 0-1 scale before weighting.
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.weights = {
            'price': settings.weight_price,
            'availability': settings.weight_availability,
            'quality': settings.weight_quality,
            'time': settings.weight_time,
            'risk': settings.weight_risk,
            'distance': settings.weight_distance
        }
    
    def rank_items(self, items: List[VendorItem], requirements: RetreatRequirements) -> AgentResponse:
        """
        Score and rank all vendor items
        
        Args:
            items: List of discovered vendor items
            requirements: Retreat requirements for context
            
        Returns:
            AgentResponse with list of ScoredItem objects sorted by score
        """
        try:
            print(f"\n📊 [Ranking Agent] Scoring {len(items)} items...")
            
            if not items:
                return AgentResponse(
                    success=True,
                    data=[],
                    message="No items to rank"
                )
            
            # Group items by type for normalization
            items_by_type = {}
            for item in items:
                if item.item_type not in items_by_type:
                    items_by_type[item.item_type] = []
                items_by_type[item.item_type].append(item)
            
            # Score items within their type groups
            all_scored_items = []
            for item_type, type_items in items_by_type.items():
                scored = self._score_item_group(type_items, requirements)
                all_scored_items.extend(scored)
            
            # Sort by total score descending
            all_scored_items.sort(key=lambda x: x.total_score, reverse=True)
            
            print(f"✅ [Ranking Agent] Ranked {len(all_scored_items)} items")
            print(f"\n   Top 3 items:")
            for i, scored in enumerate(all_scored_items[:3], 1):
                print(f"   {i}. {scored.item.vendor_name} ({scored.item.item_type.value})")
                print(f"      Score: {scored.total_score:.3f} | Price: ${scored.item.price}")
            
            return AgentResponse(
                success=True,
                data=all_scored_items,
                message=f"Successfully ranked {len(all_scored_items)} items"
            )
            
        except Exception as e:
            error_msg = f"Ranking failed: {str(e)}"
            print(f"❌ [Ranking Agent] {error_msg}")
            return AgentResponse(
                success=False,
                data=[],
                message="Failed to rank items",
                errors=[error_msg]
            )
    
    def _score_item_group(self, items: List[VendorItem], requirements: RetreatRequirements) -> List[ScoredItem]:
        """Score a group of items of the same type"""
        if not items:
            return []
        
        prices = [item.price for item in items]
        ratings = [item.rating for item in items]
        distances = [item.distance_km if item.distance_km else 5.0 for item in items]
        
        min_price, max_price = min(prices), max(prices)
        min_rating, max_rating = min(ratings), max(ratings)
        min_distance, max_distance = min(distances), max(distances)
        
        scored_items = []
        
        for item in items:
            normalized = {}
            
            if max_price > min_price:
                normalized['price'] = 1 - ((item.price - min_price) / (max_price - min_price))
            else:
                normalized['price'] = 1.0
            
            normalized['availability'] = 1.0 if item.capacity >= requirements.num_participants else 0.5
            
            if max_rating > min_rating:
                normalized['quality'] = (item.rating - min_rating) / (max_rating - min_rating)
            else:
                normalized['quality'] = 1.0
            
            normalized['time'] = item.rating / 5.0
            normalized['risk'] = item.rating / 5.0
            
            distance = item.distance_km if item.distance_km else 5.0
            if max_distance > min_distance:
                normalized['distance'] = 1 - ((distance - min_distance) / (max_distance - min_distance))
            else:
                normalized['distance'] = 1.0
            
            weighted_score = sum(
                normalized[criterion] * self.weights[criterion]
                for criterion in self.weights.keys()
            )
            
            scored_item = ScoredItem(
                item=item,
                normalized_scores=normalized,
                weighted_score=weighted_score,
                total_score=weighted_score,
                reasoning=f"Score: {weighted_score:.2f}"
            )
            scored_items.append(scored_item)
        
        return scored_items
