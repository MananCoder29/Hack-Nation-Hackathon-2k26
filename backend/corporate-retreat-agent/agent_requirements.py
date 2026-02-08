"""
Agent 1: Requirements Analyst
Parses natural language requirements into structured data
"""
import json
from typing import Dict, Any
from openai import OpenAI
from config import settings
from models import RetreatRequirements, AgentResponse


class RequirementsAnalystAgent:
    """
    Parses user's natural language requirements and extracts:
    - Number of participants
    - Location
    - Dates
    - Budget
    - Must-haves vs nice-to-haves
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.system_prompt = """You are a Requirements Analyst Agent for corporate retreat planning.

Your task is to parse natural language requirements and extract structured information.

Extract the following:
1. num_participants: number of people attending
2. location: target city/location (destination city)
3. start_date: in YYYY-MM-DD format (if not mentioned, use 30 days from today: 2025-03-08)
4. end_date: in YYYY-MM-DD format (if not mentioned, use start_date + 2 days)
5. budget: total budget in dollars (if not mentioned, use 999999 - system will calculate from actual vendor prices later)
6. must_haves: list of required features (always include: hotels, conference room, flights if international, catering, transportation)
7. nice_to_haves: list of optional features
8. special_requirements: any special needs mentioned

IMPORTANT: 
- If dates not mentioned, use defaults
- If budget not mentioned, use 999999 (unlimited - find best prices)
- For international trips (different countries), must_haves should include "flights"
- Always fill all required fields
- Return ONLY valid JSON with these exact fields. No markdown, no explanations.

Example output:
{
    "num_participants": 50,
    "location": "Las Vegas",
    "start_date": "2025-03-15",
    "end_date": "2025-03-17",
    "budget": 999999,
    "must_haves": ["conference room for 50", "hotel rooms", "airport transfers"],
    "nice_to_haves": ["team building activities", "welcome dinner"],
    "special_requirements": "Need AV setup and dietary accommodations"
}"""
    
    def parse_requirements(self, user_input: str) -> AgentResponse:
        """
        Parse natural language requirements into structured format
        
        Args:
            user_input: Natural language description of retreat requirements
            
        Returns:
            AgentResponse with RetreatRequirements data
        """
        try:
            print(f"\n🔍 [Requirements Analyst] Analyzing input...")
            
            response = self.client.chat.completions.create(
                model=settings.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            # Parse JSON response
            requirements_dict = json.loads(content)
            
            # Validate and create RetreatRequirements object
            requirements = RetreatRequirements(**requirements_dict)
            
            print(f"✅ [Requirements Analyst] Successfully parsed requirements:")
            print(f"   - Participants: {requirements.num_participants}")
            print(f"   - Location: {requirements.location}")
            print(f"   - Dates: {requirements.start_date} to {requirements.end_date}")
            print(f"   - Budget: {'No limit - will optimize for best price' if requirements.budget >= 999999 else f'${requirements.budget:,.2f}'}")
            print(f"   - Must-haves: {len(requirements.must_haves)} items")
            
            return AgentResponse(
                success=True,
                data=requirements,
                message="Requirements successfully analyzed"
            )
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response: {str(e)}"
            print(f"❌ [Requirements Analyst] {error_msg}")
            return AgentResponse(
                success=False,
                data=None,
                message="Failed to parse requirements",
                errors=[error_msg]
            )
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ [Requirements Analyst] {error_msg}")
            return AgentResponse(
                success=False,
                data=None,
                message="Failed to analyze requirements",
                errors=[error_msg]
            )


# Test function
if __name__ == "__main__":
    agent = RequirementsAnalystAgent()
    
    test_input = """
    I am planning a business retreat for 50 senior managers in my company. 
    We need it in Las Vegas from March 15-17, 2025. 
    Budget is around $100,000. 
    Must have: hotel rooms, conference room with AV setup, airport transfers, catering.
    Nice to have: team building activities, welcome dinner.
    """
    
    result = agent.parse_requirements(test_input)
    if result.success:
        print(f"\n✅ Test passed!")
        print(f"Requirements: {result.data}")
    else:
        print(f"\n❌ Test failed: {result.errors}")
