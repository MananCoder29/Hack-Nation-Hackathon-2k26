"""Scoring service with utilities for package ranking."""

from typing import Dict, Any, List, Optional


class ScoringService:
    """Service for scoring and ranking utilities."""
    
    @staticmethod
    def normalize_weights(weights: Dict[str, int]) -> Dict[str, float]:
        """Normalize weights to sum to 1.0.
        
        Args:
            weights: Dict of weights (may not sum to 100)
            
        Returns:
            Dict of normalized weights summing to 1.0
        """
        total = sum(weights.values())
        if total == 0:
            return {k: 0 for k in weights}
        return {k: v / total for k, v in weights.items()}
    
    @staticmethod
    def calculate_weighted_score(
        scores: Dict[str, float],
        weights: Dict[str, int]
    ) -> float:
        """Calculate weighted average score.
        
        Args:
            scores: Dict of component scores (0-100)
            weights: Dict of weights for each component
            
        Returns:
            Weighted average score
        """
        normalized = ScoringService.normalize_weights(weights)
        
        total = sum(
            scores.get(key, 0) * weight
            for key, weight in normalized.items()
        )
        
        return round(total, 2)
    
    @staticmethod
    def price_to_score(price: float, budget: float, category_ratio: float = 0.25) -> float:
        """Convert price to score based on budget allocation.
        
        Args:
            price: Item price
            budget: Total budget
            category_ratio: Expected ratio of budget for this category
            
        Returns:
            Score from 0-100
        """
        expected_price = budget * category_ratio
        
        if price <= 0:
            return 50  # Neutral score for unknown price
        
        if price <= expected_price * 0.5:
            return 100  # Great value
        elif price <= expected_price:
            return 100 - ((price / expected_price) * 30)  # Good value
        elif price <= expected_price * 1.5:
            return 70 - ((price - expected_price) / expected_price * 40)  # Acceptable
        else:
            return max(0, 30 - ((price - expected_price * 1.5) / expected_price * 30))  # Poor value
    
    @staticmethod
    def rating_to_score(rating: float, max_rating: float = 5.0) -> float:
        """Convert rating to score.
        
        Args:
            rating: Rating value
            max_rating: Maximum possible rating
            
        Returns:
            Score from 0-100
        """
        if rating <= 0:
            return 50  # Neutral for unknown
        return min(100, (rating / max_rating) * 100)
    
    @staticmethod
    def capacity_to_score(capacity: int, required: int) -> float:
        """Score capacity based on requirement.
        
        Args:
            capacity: Available capacity
            required: Required capacity
            
        Returns:
            Score from 0-100
        """
        if capacity >= required:
            # Slight penalty for too much excess (waste)
            excess_ratio = capacity / required
            if excess_ratio <= 1.2:
                return 100
            elif excess_ratio <= 1.5:
                return 90
            else:
                return 80
        else:
            # Strong penalty for insufficient capacity
            return (capacity / required) * 70
    
    @staticmethod
    def generate_score_explanation(
        final_score: float,
        category_scores: Dict[str, float],
        total_cost: float,
        budget: float
    ) -> str:
        """Generate human-readable score explanation.
        
        Args:
            final_score: Final calculated score
            category_scores: Scores per category
            total_cost: Total package cost
            budget: User budget
            
        Returns:
            Explanation string
        """
        budget_pct = (total_cost / budget * 100) if budget > 0 else 0
        
        # Determine overall quality tier
        if final_score >= 85:
            tier = "Excellent"
        elif final_score >= 70:
            tier = "Good"
        elif final_score >= 55:
            tier = "Fair"
        else:
            tier = "Below Average"
        
        # Find strengths
        strengths = [cat for cat, score in category_scores.items() if score >= 75]
        weaknesses = [cat for cat, score in category_scores.items() if score < 60]
        
        parts = [f"{tier} overall package (score: {final_score:.0f}/100)."]
        
        if budget_pct <= 100:
            parts.append(f"Within budget at {budget_pct:.0f}%.")
        else:
            parts.append(f"Over budget at {budget_pct:.0f}%.")
        
        if strengths:
            parts.append(f"Strong in: {', '.join(strengths)}.")
        
        if weaknesses:
            parts.append(f"Could improve: {', '.join(weaknesses)}.")
        
        return " ".join(parts)
