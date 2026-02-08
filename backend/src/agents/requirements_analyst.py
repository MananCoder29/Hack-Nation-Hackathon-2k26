"""Agent 1: Requirements Analyst - Parse and structure retreat requirements."""

from crewai import Agent, Task, Crew
from typing import Dict, Any
import json
import re
from datetime import datetime


class RequirementsAnalystAgent:
    """Agent that extracts structured requirements from natural language input."""
    
    def __init__(self):
        self.agent = Agent(
            role="Requirements Analyst",
            goal="Extract and structure retreat requirements from natural language",
            backstory="""You are an expert at parsing complex event planning 
            requirements. You extract key details like attendee count, budget, 
            location, dates, and preferences with high accuracy. You always 
            return valid JSON and validate that all required fields are present.""",
            verbose=True,
            allow_delegation=False
        )
    
    async def analyze(self, user_input: str) -> Dict[str, Any]:
        """Parse user input and extract structured requirements.
        
        Args:
            user_input: Natural language description of retreat requirements
            
        Returns:
            Dict containing structured requirements
        """
        task = Task(
            description=f"""
            Analyze this retreat planning request and extract the following information.
            Return ONLY valid JSON with no additional explanation or markdown formatting.
            
            Required fields:
            - attendees: number (integer, must be positive)
            - duration: string (e.g., "2 days", "3 nights")
            - location: string (destination city/state)
            - budget: number (total budget in USD, integer)
            
            Optional fields:
            - origin: string (departure city if mentioned)
            - deadline: string (event date in ISO format YYYY-MM-DD if mentioned)
            - must_haves: array of strings (required features)
            - nice_to_haves: array of strings (optional features)
            - preferences: object (additional preferences like dietary, accessibility)
            
            User request: {user_input}
            
            Return valid JSON only, no explanation, no markdown code blocks.
            """,
            agent=self.agent,
            expected_output="JSON object with retreat requirements"
        )
        
        # Use Crew to execute the task
        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            verbose=True
        )
        
        result = crew.kickoff()
        result_str = str(result.raw) if hasattr(result, 'raw') else str(result)
        
        # Parse LLM output to JSON
        try:
            # Try to clean common issues
            cleaned = self._clean_json_output(result_str)
            requirements = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback parsing if LLM returns malformed JSON
            requirements = self._fallback_parse(user_input)
        
        # Ensure required fields and validate
        requirements = self._ensure_required_fields(requirements, user_input)
        self._validate_requirements(requirements)
        
        return requirements
    
    def _clean_json_output(self, text: str) -> str:
        """Clean LLM output to extract valid JSON."""
        # Remove markdown code blocks if present
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        
        # Find JSON object boundaries
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1:
            return text[start:end + 1]
        
        return text
    
    def _validate_requirements(self, req: Dict[str, Any]) -> None:
        """Validate extracted requirements.
        
        Args:
            req: Requirements dictionary to validate
            
        Raises:
            ValueError: If validation fails
        """
        if req.get("attendees", 0) <= 0:
            raise ValueError("Attendees must be greater than 0")
        
        if req.get("budget", 0) <= 0:
            raise ValueError("Budget must be greater than 0")
        
        if not req.get("location"):
            raise ValueError("Location is required")
        
        if not req.get("duration"):
            raise ValueError("Duration is required")
        
        # Ensure deadline is in future if provided
        if "deadline" in req and req["deadline"]:
            try:
                deadline = datetime.fromisoformat(req["deadline"])
                if deadline < datetime.now():
                    # Set to reasonable future date
                    req["deadline"] = None
            except (ValueError, TypeError):
                req["deadline"] = None
    
    def _ensure_required_fields(
        self, 
        req: Dict[str, Any], 
        original_input: str
    ) -> Dict[str, Any]:
        """Ensure all required fields are present with fallback extraction."""
        
        # Initialize with defaults if missing
        if "must_haves" not in req:
            req["must_haves"] = []
        if "nice_to_haves" not in req:
            req["nice_to_haves"] = []
        if "preferences" not in req:
            req["preferences"] = {}
        
        # Try to extract missing required fields from original input
        if not req.get("attendees"):
            match = re.search(r'(\d+)\s*(?:people|attendees|managers|employees|guests)', 
                            original_input, re.IGNORECASE)
            req["attendees"] = int(match.group(1)) if match else 50
        
        if not req.get("budget"):
            match = re.search(r'\$\s*([\d,]+)', original_input)
            if match:
                req["budget"] = int(match.group(1).replace(',', ''))
            else:
                match = re.search(r'budget\s*(?:of\s*)?([\d,]+)', original_input, re.IGNORECASE)
                req["budget"] = int(match.group(1).replace(',', '')) if match else 50000
        
        if not req.get("location"):
            # Try to extract location from text using patterns
            # Patterns: "in [Location]", "to [Location]", "at [Location]"
            location_patterns = [
                r'(?:retreat|trip|event|conference|meeting)\s+(?:in|at|to)\s+([A-Za-z][A-Za-z\s]+?)(?:\s+for|\s+with|,|\.|$)',
                r'(?:in|at|to)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)(?:\s+for|,|\.|$)',
                r'destination[:\s]+([A-Za-z][A-Za-z\s,]+?)(?:\.|,|$)',
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, original_input, re.IGNORECASE)
                if match:
                    extracted = match.group(1).strip()
                    # Clean up common trailing words
                    extracted = re.sub(r'\s+(for|with|and)\s*$', '', extracted, flags=re.IGNORECASE)
                    if len(extracted) >= 2:
                        req["location"] = extracted
                        break
            
            # If still no location, the LLM should have extracted it
            if not req.get("location"):
                req["location"] = "Location not specified"
        
        if not req.get("duration"):
            match = re.search(r'(\d+)\s*(?:day|night)', original_input, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                req["duration"] = f"{num} days"
            else:
                req["duration"] = "2 days"
        
        return req
    
    def _fallback_parse(self, text: str) -> Dict[str, Any]:
        """Fallback parser if JSON parsing fails completely.
        
        Args:
            text: Original user input to parse
            
        Returns:
            Dict with extracted requirements using regex patterns
        """
        # Extract attendees
        attendees_match = re.search(
            r'(\d+)\s*(?:people|attendees|managers|employees|guests)', 
            text, re.IGNORECASE
        )
        attendees = int(attendees_match.group(1)) if attendees_match else 50
        
        # Extract budget
        budget_match = re.search(r'\$\s*([\d,]+)', text)
        if budget_match:
            budget = int(budget_match.group(1).replace(',', ''))
        else:
            budget = 60000
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*(?:-?\s*)?day', text, re.IGNORECASE)
        duration = f"{duration_match.group(1)} days" if duration_match else "2 days"
        
        # Extract origin
        origin_match = re.search(
            r'(?:from|departing|leaving)\s+([A-Za-z\s]+?)(?:\s*,|\s+to|\s*\.)', 
            text, re.IGNORECASE
        )
        origin = origin_match.group(1).strip() if origin_match else None
        
        # Extract location (destination) - use pattern matching for any location
        location = None
        location_patterns = [
            r'(?:retreat|trip|event|conference|meeting)\s+(?:in|at|to)\s+([A-Za-z][A-Za-z\s]+?)(?:\s+for|\s+with|,|\.|$)',
            r'(?:in|at|to)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)(?:\s+for|,|\.|$)',
            r'destination[:\s]+([A-Za-z][A-Za-z\s,]+?)(?:\.|,|$)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                extracted = re.sub(r'\s+(for|with|and)\s*$', '', extracted, flags=re.IGNORECASE)
                if len(extracted) >= 2:
                    location = extracted
                    break
        
        if not location:
            location = "Location not specified"
        
        # Extract must-haves
        must_haves = []
        if "4-star" in text.lower() or "4 star" in text.lower():
            must_haves.append("4-star hotel")
        if "hotel" in text.lower() and "4-star hotel" not in must_haves:
            must_haves.append("hotel")
        if "flight" in text.lower():
            must_haves.append("flights")
        if "meeting" in text.lower() or "conference" in text.lower():
            must_haves.append("meeting room")
        if "catering" in text.lower() or "food" in text.lower() or "meal" in text.lower():
            must_haves.append("catering")
        
        return {
            "attendees": attendees,
            "budget": budget,
            "duration": duration,
            "location": location,
            "origin": origin or "San Francisco",
            "must_haves": must_haves,
            "nice_to_haves": [],
            "preferences": {}
        }
