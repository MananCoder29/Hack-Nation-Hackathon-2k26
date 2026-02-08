"""
Interactive Retreat Planner with User Conversation
"""
from main import CorporateRetreatOrchestrator
from openai import OpenAI
from config import settings
import json

class InteractiveRetreatPlanner:
    def __init__(self):
        self.orchestrator = CorporateRetreatOrchestrator()
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.conversation = []
        self.gathered_info = {
            "participants": None,
            "location": None,
            "start_date": None,
            "end_date": None,
            "budget": None,
            "trip_type": "round-trip",  # Default
            "must_haves": []
        }
    
    def ask_user(self, question: str) -> str:
        """Ask user a question and get response"""
        print(f"\n🤖 Agent: {question}")
        response = input("You: ")
        self.conversation.append({"agent": question, "user": response})
        return response
    
    def gather_requirements(self):
        """Interactively gather all requirements"""
        print("=" * 80)
        print("🎯 INTERACTIVE RETREAT PLANNER")
        print("=" * 80)
        
        # Initial request
        initial = self.ask_user("What retreat are you planning? (Be as detailed or brief as you like)")
        
        # Use LLM to determine what's missing
        missing = self._check_missing_info(initial)
        
        # Ask for missing info
        if "participants" in missing:
            response = self.ask_user("How many people will attend?")
            self.gathered_info["participants"] = int(response)
        
        if "location" in missing:
            response = self.ask_user("Where is the retreat location?")
            self.gathered_info["location"] = response
        
        if "dates" in missing:
            response = self.ask_user("What dates? (e.g., March 15-17, 2025)")
            self.gathered_info["start_date"], self.gathered_info["end_date"] = self._parse_dates(response)
            
            # Ask about trip type if it's a travel retreat
            if any(word in initial.lower() for word in ["from", "to", "travel", "flight"]):
                trip_type = self.ask_user("Is this a round-trip or one-way? (round/one-way)")
                self.gathered_info["trip_type"] = "round-trip" if "round" in trip_type.lower() else "one-way"
        
        if "budget" in missing:
            response = self.ask_user("What's your budget? (or say 'flexible' for best price)")
            if "flex" in response.lower() or "best" in response.lower():
                self.gathered_info["budget"] = None
            else:
                self.gathered_info["budget"] = float(response.replace("$", "").replace(",", ""))
        
        # Confirm
        print("\n" + "=" * 80)
        print("📋 CONFIRMED REQUIREMENTS:")
        print("=" * 80)
        for key, value in self.gathered_info.items():
            if value:
                print(f"   {key}: {value}")
        
        confirm = self.ask_user("Does this look correct? (yes/no)")
        
        if "yes" in confirm.lower():
            return self._build_request_string()
        else:
            print("\nLet's start over...")
            return self.gather_requirements()
    
    def _check_missing_info(self, text: str) -> list:
        """Use LLM to check what info is missing"""
        prompt = f"""Analyze this retreat request and list what's MISSING:

Request: "{text}"

Check for:
- participants (number of people)
- location (city/destination)
- dates (start and end dates)
- budget (dollar amount)

Return ONLY a JSON array of missing items, e.g.: ["participants", "dates"]
If nothing is missing, return: []"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
        
        return json.loads(content)
    
    def _parse_dates(self, date_str: str):
        """Parse date string into start and end dates"""
        from datetime import datetime, timedelta
        
        if not date_str or date_str.strip() == "":
            # Default to 30 days from now
            start = datetime(2025, 3, 8)
            end = start + timedelta(days=2)
            return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        
        # Try to parse user input
        try:
            # Handle formats like "feb 15-17", "15-17 march", etc.
            import re
            
            # Extract month
            months = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                     "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
            
            month_match = re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', date_str.lower())
            month = months.get(month_match.group(1)) if month_match else 3
            
            # Extract day range like "15-17"
            day_match = re.search(r'(\d{1,2})-(\d{1,2})', date_str)
            if day_match:
                start_day = int(day_match.group(1))
                end_day = int(day_match.group(2))
            else:
                # Single date or fallback
                start_day = 15
                end_day = 17
            
            # Extract year
            year_match = re.search(r'20(\d{2})', date_str)
            year = int(f"20{year_match.group(1)}") if year_match else 2025
            
            start_date = f"{year}-{month:02d}-{start_day:02d}"
            end_date = f"{year}-{month:02d}-{end_day:02d}"
            
            return start_date, end_date
            
        except:
            # Fallback to defaults
            return "2025-03-15", "2025-03-17"
    
    def _build_request_string(self) -> str:
        """Build complete request string from gathered info"""
        parts = []
        
        # Get info from conversation
        full_text = " ".join([msg["user"] for msg in self.conversation])
        
        # Add trip type info
        if self.gathered_info.get("trip_type"):
            full_text += f" Trip type: {self.gathered_info['trip_type']}."
        
        # Just return the full conversation - LLM will parse it
        return full_text
    
    def run(self):
        """Run the interactive planner"""
        # Gather requirements
        final_request = self.gather_requirements()
        
        print("\n" + "=" * 80)
        print("🚀 PROCESSING YOUR REQUEST...")
        print("=" * 80)
        
        # Run the orchestrator
        results = self.orchestrator.process_request(final_request, auto_checkout=True)
        
        if results["success"]:
            print("\n✅ Your retreat is planned!")
        else:
            print(f"\n❌ Planning failed: {results['errors']}")


if __name__ == "__main__":
    planner = InteractiveRetreatPlanner()
    planner.run()
