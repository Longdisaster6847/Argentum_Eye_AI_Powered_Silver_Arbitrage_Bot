import os
import json
from openai import OpenAI
import feedparser
from bs4 import BeautifulSoup
import time
import yfinance as yf
from datetime import datetime

# --- CONFIGURATION ---
RSS_URL = "https://www.reddit.com/r/Pmsforsale/new/.rss"
GROQ_MODEL = "llama-3.3-70b-versatile"

# 1. SETUP GROQ CLIENT
print("Initializing AI Client...")
if 'GROQ_API_KEY' not in os.environ:
    print("❌ ERROR: GROQ_API_KEY not found in Secrets!")
    exit()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ['GROQ_API_KEY']
)

# 2. LIVE SPOT PRICE FUNCTION
def get_live_spot():
    try:
        ticker = yf.Ticker("XAGUSD=X")
        data = ticker.history(period="1d")
        if not data.empty:
            price = data['Close'].iloc[-1]
            return round(price, 2)
    except Exception as e:
        print(f"  [Spot Check Fail]: {e}")

    return 58.50 

# 3. RSS FETCHING
def get_latest_posts():
    print("  -> Fetching RSS...")
    headers = {'User-Agent': 'Mozilla/5.0'} 
    feed = feedparser.parse(RSS_URL, request_headers=headers)

    clean_posts = []

    for entry in feed.entries[:10]:
        soup = BeautifulSoup(entry.summary, "html.parser")

        for tag in soup.find_all(['del', 's', 'strike']):
            tag.decompose()

        text_body = soup.get_text()

        clean_posts.append({
            "title": entry.title,
            "link": entry.link,
            "body": text_body
        })
    return clean_posts

# 4. AI ANALYSIS (With Dynamic Math)
def analyze_post(title, body, current_spot):
    print(f"  -> Sending to AI: {title[:30]}...")

    melt_90_fv = current_spot * 0.715
    melt_40_coin = current_spot * 0.1479 
    melt_35_coin = current_spot * 0.0563 

    prompt = f"""
    You are a math-focused precious metals analyzer.
    Current Silver Spot Price: ${current_spot}/oz.

    **CRITICAL MATH RULES:**
    - 90% Silver = 0.715 oz per $1 Face Value (e.g. $10FV = 7.15oz).
    - 40% Silver Half = 0.148 oz per coin.
    - 35% War Nickel = 0.056 oz per coin.
    - .999 Fine = 1.0 oz per coin.

    **YOUR TASK:**
    1. Identify items.
    2. Extract Price and Quantity. 
       - If price says "ea" or "each", do NOT divide by quantity.
    3. Calculate Total Pure Silver Weight in Ounces.
    4. Calculate Price Per Ounce = (Price + Shipping) / Total Weight.
       - **MUST BE A FINAL NUMBER (e.g. 25.50), NOT AN EQUATION.**
    5. **FILTER:** ONLY return items where Price Per Ounce is LESS THAN ${current_spot}.

    Return JSON ONLY:
    {{
      "shipping_cost": number,
      "deals": [
        {{
          "item_name": "string",
          "listed_price": number,
          "all_in_price_per_oz": number
        }}
      ]
    }}

    TITLE: {title}
    BODY: {body}
    """

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)

        verified_deals = []
        if data and data.get('deals'):
            for deal in data['deals']:
                if deal['all_in_price_per_oz'] < current_spot:
                    verified_deals.append(deal)
                else:
                    print(f"   [Auto-Reject] AI flagged {deal['item_name']} at ${deal['all_in_price_per_oz']}/oz (Above Spot)")
            data['deals'] = verified_deals

        return data
    except Exception as e:
        print(f"  [AI ERROR]: {e}")
        return None

# --- MAIN LOOP ---
current_spot = get_live_spot()
print(f"\n--- STARTING INFINITE MONITOR (Spot: ${current_spot}) ---")
seen_links = set()
last_spot_update = time.time()

while True:
    try:
        if time.time() - last_spot_update > 900:
            new_spot = get_live_spot()
            if new_spot > 0:
                current_spot = new_spot
                print(f"\n💰 UPDATED SPOT PRICE: ${current_spot}")
            last_spot_update = time.time()

        posts = get_latest_posts()

        for post in posts:
            if post['link'] in seen_links:
                continue

            seen_links.add(post['link'])
            print(f"\n🔎 New Post: {post['title']}")

            data = analyze_post(post['title'], post['body'], current_spot)

            if data and data.get('deals'):
                msg = f"🚨 DEAL: {data['deals'][0]['item_name']} @ ${data['deals'][0]['all_in_price_per_oz']:.2f}/oz"
                print(msg)
            else:
                print("   [PASS] No deals.")

        print(".", end="", flush=True)
        time.sleep(60)

    except KeyboardInterrupt:
        print("\nStopping...")
        break
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(60)
