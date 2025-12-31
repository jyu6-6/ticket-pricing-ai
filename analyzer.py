"""
Gemini AI Recommendation Engine
Analyzes ticket pricing and recommends strategies
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel

load_dotenv()

# System instructions from master spec
SYSTEM_INSTRUCTION = """You are an AI Ticket Arbitrage Specialist. Goal: Maximize reseller profit.

**Tier Rules:**
- **Floor/VIP (1724):** Inelastic. HOLD unless within 48 hours.
- **Lower Bowl (682, 478):** Competitive. ADJUST to stay in bottom 10% of floor.
- **Upper Bowl/Lounges (306, 9067):** Elastic. If floor drops >3%, LIQUIDATE.

**Phase Logic:**
- **Hype Phase (60+ days):** Strategy = HOLD/RAISE. Catch early-bird FOMO.
- **The Dip (14-30 days):** Strategy = ADJUST. Market is saturated; match the floor.
- **The Burn (<48 hours):** Strategy = LIQUIDATE. Price 5% below floor for instant exit.

**Output:** Return ONLY a JSON object: {"action": "RAISE|HOLD|ADJUST|LIQUIDATE", "target": float, "logic": "1-sentence"}.
"""


class GeminiAnalyzer:
    """Gemini-powered ticket pricing analyzer"""
    
    def __init__(self):
        project_id = os.getenv('GCP_PROJECT_ID')
        aiplatform.init(project=project_id, location='us-central1')
        self.model = GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=SYSTEM_INSTRUCTION
        )
        self.event_date = datetime.strptime(os.getenv('EVENT_DATE'), '%Y-%m-%d')
    
    def calculate_days_to_event(self):
        """Calculate days until event"""
        today = datetime.now()
        delta = self.event_date - today
        return delta.days
    
    def analyze(self, tier, market_floor, listing_price):
        """
        Analyze pricing strategy
        
        Args:
            tier: Ticket tier (e.g., "VIP_Floor")
            market_floor: Current market floor price
            listing_price: User's current listing price
        
        Returns:
            dict: {"action": str, "target": float, "logic": str}
        """
        days_to_event = self.calculate_days_to_event()
        
        prompt = f"""
Today's Date: {datetime.now().strftime('%Y-%m-%d')}
Event Date: {self.event_date.strftime('%Y-%m-%d')}
Days to Event: {days_to_event}
Seating Tier: {tier}
Market Floor Price: ${market_floor:.2f}
My Current Listing Price: ${listing_price:.2f}

Recommend a strategy.
"""
        
        from vertexai.generative_models import HarmCategory, HarmBlockThreshold
        
        response = self.model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': 2048,  # Increased to handle thinking tokens (957) + response
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Debug the response structure
        # print(f"DEBUG - Response object: {response}")
        # print(f"DEBUG - Has candidates: {hasattr(response, 'candidates')}")
        # if hasattr(response, 'candidates') and response.candidates:
        #     print(f"DEBUG - Finish reason: {response.candidates[0].finish_reason}")
        #     print(f"DEBUG - Safety ratings: {response.candidates[0].safety_ratings}")
        
        # Get the full response text
        try:
            text = response.candidates[0].content.parts[0].text.strip()
        except (IndexError, AttributeError):
            text = response.text.strip()
        
        # Debug: Print what we got
        # print(f"DEBUG - Raw response: '{text}'")
        # print(f"DEBUG - Response length: {len(text)}")
        
        if not text:
            raise ValueError("Gemini returned an empty response")
        
        # Remove markdown code blocks if present
        if text.startswith('```'):
            # Find the first newline and last newline to extract content
            lines = text.split('\n')
            # Remove first line (```json or ```) and last line (```)
            text = '\n'.join(lines[1:-1])
        
        # Sometimes Gemini wraps in ```json, remove that too
        if text.startswith('json'):
            text = text[4:].strip()
        
        # print(f"DEBUG - After cleaning: '{text}'")
        
        return json.loads(text)


if __name__ == "__main__":
    # Test the analyzer
    analyzer = GeminiAnalyzer()
    
    result = analyzer.analyze(
        tier="Lounge",
        market_floor=250.00,
        listing_price=275.00
    )
    
    print(json.dumps(result, indent=2))
