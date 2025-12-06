import os
import json
from openai import OpenAI

# 1. SETUP GROQ (Using Llama 3 via Groq API)
print("Initializing AI...")

# Make sure you added GROQ_API_KEY to your Replit Secrets!
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ['GROQ_API_KEY']
)

CURRENT_SPOT = 58.50 

# 2. FAKE REDDIT POSTS (To test logic)
mock_posts = [
    {
        "author": "jmcsys",
        "flair": "S: 229 | B: 8",
        "title": "[WTS] Silver below melt! 35%, 40%, and 90%.",
        "body": """
        40% ( way below melt! ) melt = 8.60 ea, selling @ $7.75 ea
        Up to 7 40% silver Kennedy halves
        35% ( below melt! ) melt = 3.25 ea, selling @ $3.10 ea
        Up to 300 35% silver war nickels
        Shipping is $7 tracked for up to 12 oz.
        """
    },
    {
        "author": "Fermooto",
        "flair": "S: 14 | B: 2",
        "title": "[WTS] Stack Audit! Premium and generic 1oz silver",
        "body": """
        1oz US Flag Button - $55.5 (SPOT - 3)
        1oz Second Amendment Round - $55.5 (SPOT - 3)
        Shipping: $7 Ground, $12 Priority
        """
    },
    {
        "author": "ScammerGuy",
        "flair": None,
        "title": "[WTS] Gold chain",
        "body": "Just a gold chain $500."
    }
]

# 3. THE AI ANALYZER
def analyze_post(title, body):
    print(f"  -> Analyzing deal logic for: {title[:25]}...")
    
    prompt = f"""
    You are a precious metals scraper.
    Current Silver Spot Price is ${CURRENT_SPOT}.
    
    Analyze this post.
    1. Extract SHIPPING COST (default $6 if variable).
    2. Find items listed BELOW ${CURRENT_SPOT}/oz.
    
    Return JSON ONLY:
    {{
      "shipping_cost": number,
      "deals": [
        {{
          "item_name": "string",
          "listed_price": number,
          "estimated_weight_oz": number,
          "all_in_price_oz": number
        }}
      ]
    }}
    If no deals, return "deals": [].
    
    TITLE: {title}
    BODY: {body}
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"  [AI ERROR]: {e}")
        return None

# 4. RUN MOCK SCAN
print(f"\n--- RUNNING MOCK SCAN (Waiting for Reddit Unban) ---")

for post in mock_posts:
    print(f"\n🔎 Checking User: u/{post['author']}")
    
    # Test Flair Filter Logic
    if not post['flair']:
        print("   [SKIP] No seller flair (Risk Filter working).")
        continue
    
    # Test AI Logic
    data = analyze_post(post['title'], post['body'])
    
    if data and data.get('deals'):
        print(f"   ✅ SUCCESS! AI Found Deals:")
        print(f"      Shipping Calc: ${data['shipping_cost']}")
        for deal in data['deals']:
            print(f"      - {deal['item_name']} @ ${deal['listed_price']} (All-in: ${deal['all_in_price_oz']:.2f}/oz)")
    else:
        print("   [PASS] No deals found.")

print("\n--- MOCK SCAN COMPLETE ---")
