import json
from typing import List
from tavily import TavilyClient
from openai import OpenAI
from config import settings
from models import RetreatRequirements, VendorItem, ItemType, AgentResponse

class DiscoveryAgent:
    def __init__(self):
        self.tavily = TavilyClient(api_key=settings.tavily_api_key)
        self.openai = OpenAI(api_key=settings.openai_api_key)
    
    def discover_vendors(self, requirements: RetreatRequirements) -> AgentResponse:
        print(f"\n🔎 [Discovery] Searching vendors...")
        items = []
        
        for itype in [ItemType.HOTEL, ItemType.CONFERENCE_ROOM, ItemType.CATERING, ItemType.TRANSPORTATION]:
            results = self.tavily.search(f"{itype.value} {requirements.location}", max_results=2)
            parsed = self._extract_with_llm(results.get('results', []), itype, requirements)
            items.extend(parsed)
            print(f"   ✓ Found {len(parsed)} {itype.value} options")
        
        print(f"✅ Total: {len(items)} items")
        return AgentResponse(success=True, data=items, message="OK")
    
    def _extract_with_llm(self, results: List[dict], itype: ItemType, req: RetreatRequirements) -> List[VendorItem]:
        if not results:
            return []
        
        prompt = f"""Extract {itype.value} vendor info from search results for {req.location}.

Results: {json.dumps(results[:2], indent=2)}

Return JSON array with REALISTIC prices:
[
  {{
    "vendor_name": "string",
    "description": "string (max 150 chars)",
    "price": number (realistic market price - Hotels: per room/night, Conference: per day, Catering: per person, Transport: per person),
    "capacity": {req.num_participants + 20},
    "rating": number (0-5)
  }}
]

Price guidelines for {req.location}:
- Hotels: $80-300 per room/night
- Conference: $500-2000 per day
- Catering: $30-100 per person
- Transport: $50-150 per person

Return ONLY valid JSON array, no markdown."""

        try:
            response = self.openai.chat.completions.create(
                model=settings.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            data = json.loads(content)
            
            vendors = []
            for idx, item in enumerate(data):
                vendors.append(VendorItem(
                    item_id=f"{itype.value}_{idx}",
                    item_type=itype,
                    vendor_name=item['vendor_name'],
                    description=item['description'],
                    price=float(item['price']),
                    capacity=int(item['capacity']),
                    rating=float(item.get('rating', 4.0)),
                    distance_km=5.0,
                    url=results[min(idx, len(results)-1)].get('url', '')
                ))
            return vendors
            
        except Exception as e:
            print(f"   ⚠️  LLM extraction failed: {e}")
            return []
