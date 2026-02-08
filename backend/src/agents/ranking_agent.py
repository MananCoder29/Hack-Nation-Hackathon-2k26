"""Agent 3: Ranking Agent - Score and rank packages with dynamic weights."""

from typing import Dict, Any, List, Optional
import itertools
import uuid


class RankingAgent:
    """Agent that scores and ranks packages using transparent, adjustable weights."""
    
    def __init__(self):
        # Default weights per category (must sum to 100 within each category)
        self.default_category_weights = {
            "flights": {
                "price_weight": 50,
                "timing_weight": 25,
                "trust_weight": 15,
                "comfort_weight": 10
            },
            "hotels": {
                "price_weight": 20,
                "trust_weight": 40,
                "location_weight": 25,
                "amenities_weight": 15
            },
            "meeting_rooms": {
                "price_weight": 25,
                "capacity_weight": 35,
                "equipment_weight": 25,
                "trust_weight": 15
            },
            "catering": {
                "price_weight": 30,
                "trust_weight": 30,
                "dietary_weight": 25,
                "service_weight": 15
            }
        }
        
        # Default category importance weights (must sum to 100)
        self.default_category_importance = {
            "flights": 30,
            "hotels": 40,
            "meeting_rooms": 15,
            "catering": 15
        }
    
    async def rank(
        self,
        items: List[Dict[str, Any]],
        requirements: Dict[str, Any],
        custom_weights: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rank packages using transparent, adjustable scoring.
        
        Args:
            items: List of discovered items from Agent 2
            requirements: Structured requirements from Agent 1
            custom_weights: Optional custom weights to override defaults
            
        Returns:
            List of ranked packages with scores and explanations
        """
        # Group items by category
        grouped_items = self._group_by_category(items)
        
        # Ensure all categories have at least one item (for package generation)
        for category in ["flights", "hotels", "meeting_rooms", "catering"]:
            if category not in grouped_items or not grouped_items[category]:
                grouped_items[category] = [self._create_placeholder_item(category, requirements)]
        
        # Generate all possible packages (one item per category)
        packages = self._generate_packages(grouped_items)
        
        # Score each package
        scored_packages = []
        for pkg in packages:
            score_data = self._score_package(pkg, requirements, custom_weights)
            scored_packages.append(score_data)
        
        # Sort by final score (descending)
        scored_packages.sort(key=lambda x: x["final_score"], reverse=True)
        
        # Add rank position
        for rank, pkg in enumerate(scored_packages, 1):
            pkg["rank"] = rank
        
        return scored_packages
    
    def _group_by_category(
        self, 
        items: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group items by their category.
        
        Args:
            items: List of all discovered items
            
        Returns:
            Dict mapping category names to lists of items
        """
        grouped = {}
        for item in items:
            category = item.get("category", "unknown")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(item)
        return grouped
    
    def _generate_packages(
        self, 
        grouped: Dict[str, List[Dict[str, Any]]]
    ) -> List[Dict[str, Dict[str, Any]]]:
        """Generate all combinations of packages (one item per category).
        
        Args:
            grouped: Items grouped by category
            
        Returns:
            List of package dictionaries (category -> item mapping)
        """
        categories = ["flights", "hotels", "meeting_rooms", "catering"]
        
        # Get items for each category (use empty list if category missing)
        items_by_category = [grouped.get(cat, []) for cat in categories]
        
        # Filter out empty categories
        valid_categories = []
        valid_items = []
        for cat, items in zip(categories, items_by_category):
            if items:
                valid_categories.append(cat)
                valid_items.append(items)
        
        if not valid_items:
            return []
        
        packages = []
        for combo in itertools.product(*valid_items):
            pkg = {cat: item for cat, item in zip(valid_categories, combo)}
            packages.append(pkg)
        
        # Limit to top 50 packages for performance
        return packages[:50]
    
    def _score_package(
        self,
        package: Dict[str, Dict[str, Any]],
        requirements: Dict[str, Any],
        custom_weights: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate final package score with transparent breakdown.
        
        Args:
            package: Dict mapping category to selected item
            requirements: User requirements
            custom_weights: Optional custom scoring weights
            
        Returns:
            Dict with package details, scores, and explanation
        """
        category_scores = {}
        category_breakdowns = {}
        
        for category, item in package.items():
            score, breakdown = self._score_item(
                item,
                category,
                requirements,
                custom_weights
            )
            category_scores[category] = score
            category_breakdowns[category] = breakdown
        
        # Get category importance weights
        importance = self.default_category_importance.copy()
        if custom_weights and custom_weights.get("category_importance"):
            importance.update(custom_weights["category_importance"])
        
        # Normalize importance weights if they don't sum to 100
        total_importance = sum(importance.get(cat, 0) for cat in category_scores)
        if total_importance == 0:
            total_importance = 100
        
        # Calculate weighted final score
        final_score = sum(
            category_scores.get(cat, 0) * (importance.get(cat, 25) / total_importance)
            for cat in category_scores
        )
        
        # Calculate total cost
        total_cost = sum(item.get("price", 0) for item in package.values())
        
        return {
            "package_id": f"pkg_{str(uuid.uuid4())[:8]}",
            "final_score": round(final_score, 2),
            "category_scores": {cat: round(score, 2) for cat, score in category_scores.items()},
            "items": package,
            "total_cost": round(total_cost, 2),
            "explanation": self._generate_explanation(
                category_scores,
                category_breakdowns,
                requirements,
                total_cost,
                importance
            )
        }
    
    def _score_item(
        self,
        item: Dict[str, Any],
        category: str,
        requirements: Dict[str, Any],
        custom_weights: Optional[Dict[str, Any]]
    ) -> tuple:
        """Score an individual item based on category-specific criteria.
        
        Args:
            item: Item to score
            category: Item category
            requirements: User requirements
            custom_weights: Optional custom weights
            
        Returns:
            Tuple of (final_score, breakdown_dict)
        """
        # Get weights for this category
        default_weights = self.default_category_weights.get(category, {})
        weights = default_weights.copy()
        
        if custom_weights and custom_weights.get(category):
            weights.update(custom_weights[category])
        
        # Calculate base scores
        price_score = self._calculate_price_score(
            item.get("price", 0),
            requirements.get("budget", 100000)
        )
        
        trust_rating = item.get("trust_score", {})
        if isinstance(trust_rating, dict):
            trust_score = trust_rating.get("rating", 3) * 20  # Convert 5-star to 100
        else:
            trust_score = 60  # Default
        
        breakdown = {}
        final_score = 0
        total_weight = 0
        
        if category == "flights":
            timing_score = 75  # Could be calculated from departure times
            comfort_score = 70  # Could be based on class, stops, etc.
            
            components = [
                ("price", price_score, weights.get("price_weight", 50)),
                ("timing", timing_score, weights.get("timing_weight", 25)),
                ("trust", trust_score, weights.get("trust_weight", 15)),
                ("comfort", comfort_score, weights.get("comfort_weight", 10)),
            ]
        
        elif category == "hotels":
            location_score = 85  # Could be based on proximity to venue
            amenities = item.get("metadata", {}).get("amenities", [])
            amenities_score = min(100, len(amenities) * 12)  # More amenities = higher score
            
            components = [
                ("price", price_score, weights.get("price_weight", 20)),
                ("trust", trust_score, weights.get("trust_weight", 40)),
                ("location", location_score, weights.get("location_weight", 25)),
                ("amenities", amenities_score, weights.get("amenities_weight", 15)),
            ]
        
        elif category == "meeting_rooms":
            capacity = item.get("metadata", {}).get("capacity", 50)
            required_capacity = requirements.get("attendees", 50)
            capacity_score = 100 if capacity >= required_capacity else (capacity / required_capacity) * 100
            
            equipment = item.get("metadata", {}).get("equipment", [])
            equipment_score = min(100, len(equipment) * 25)
            
            components = [
                ("price", price_score, weights.get("price_weight", 25)),
                ("capacity", capacity_score, weights.get("capacity_weight", 35)),
                ("equipment", equipment_score, weights.get("equipment_weight", 25)),
                ("trust", trust_score, weights.get("trust_weight", 15)),
            ]
        
        elif category == "catering":
            dietary_options = item.get("metadata", {}).get("dietary_options", [])
            dietary_score = min(100, len(dietary_options) * 20)
            service_score = 80  # Could be based on service style
            
            components = [
                ("price", price_score, weights.get("price_weight", 30)),
                ("trust", trust_score, weights.get("trust_weight", 30)),
                ("dietary", dietary_score, weights.get("dietary_weight", 25)),
                ("service", service_score, weights.get("service_weight", 15)),
            ]
        
        else:
            # Default scoring for unknown categories
            components = [
                ("price", price_score, 50),
                ("trust", trust_score, 50),
            ]
        
        # Calculate weighted score
        for name, score, weight in components:
            final_score += score * weight
            total_weight += weight
            breakdown[name] = {"score": round(score, 1), "weight": weight}
        
        if total_weight > 0:
            final_score = final_score / total_weight
        
        return round(final_score, 2), breakdown
    
    def _calculate_price_score(self, price: float, budget: float) -> float:
        """Calculate price score (lower price = higher score, within budget).
        
        Args:
            price: Item price
            budget: Total budget
            
        Returns:
            Score from 0-100
        """
        if budget <= 0:
            return 50
        
        # Price as percentage of total budget
        price_ratio = price / budget
        
        if price_ratio > 0.5:  # More than 50% of budget for single category
            return max(0, 100 - (price_ratio * 150))
        elif price_ratio > 0.3:
            return 100 - (price_ratio * 100)
        else:
            return 100 - (price_ratio * 50)
    
    def _generate_explanation(
        self,
        category_scores: Dict[str, float],
        breakdowns: Dict[str, Dict],
        requirements: Dict[str, Any],
        total_cost: float,
        importance: Dict[str, int]
    ) -> Dict[str, Any]:
        """Generate human-readable explanation for package ranking.
        
        Args:
            category_scores: Scores per category
            breakdowns: Detailed breakdowns per category
            requirements: User requirements
            total_cost: Total package cost
            importance: Category importance weights
            
        Returns:
            Dict with explanation and detailed breakdowns
        """
        budget = requirements.get("budget", 100000)
        budget_pct = (total_cost / budget * 100) if budget > 0 else 0
        
        # Find strongest and weakest categories
        sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        strengths = [cat for cat, score in sorted_cats if score >= 70]
        
        # Generate summary
        if budget_pct <= 80:
            cost_assessment = f"Under budget at ${total_cost:,.0f} ({budget_pct:.0f}% of ${budget:,.0f})"
        elif budget_pct <= 100:
            cost_assessment = f"Within budget at ${total_cost:,.0f} ({budget_pct:.0f}% of ${budget:,.0f})"
        else:
            cost_assessment = f"Over budget at ${total_cost:,.0f} ({budget_pct:.0f}% of ${budget:,.0f})"
        
        strengths_str = ", ".join(strengths) if strengths else "balanced options"
        
        return {
            "why_ranked": f"{cost_assessment}. Strong scores in: {strengths_str}.",
            "category_breakdowns": breakdowns,
            "budget_analysis": {
                "total_cost": total_cost,
                "budget": budget,
                "percentage_used": round(budget_pct, 1)
            },
            "weights_applied": importance
        }
    
    def _create_placeholder_item(
        self,
        category: str,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a placeholder item when category has no results.
        
        Args:
            category: Category name
            requirements: User requirements
            
        Returns:
            Placeholder item dictionary
        """
        return {
            "item_id": f"{category}_placeholder",
            "category": category,
            "vendor": "To Be Determined",
            "source": "",
            "title": f"{category.replace('_', ' ').title()} - TBD",
            "description": f"Placeholder for {category}",
            "price": 0,
            "currency": "USD",
            "availability": False,
            "metadata": {},
            "trust_score": {"rating": 0, "source": "N/A"}
        }
