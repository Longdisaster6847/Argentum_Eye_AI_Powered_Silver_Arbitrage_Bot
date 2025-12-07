import os
import json
from openai import OpenAI
import feedparser
from bs4 import BeautifulSoup
import time
import random
import logging
import yfinance as yf
from datetime import datetime

# --- CONFIGURATION ---
RSS_URL = "https://www.reddit.com/r/Pmsforsale/new/.rss"
GROQ_MODEL = "llama-3.3-70b-versatile"
LOG_FILE = "argentum_log.txt"

# --- SETUP LOGGING ---
logging.basicConfig(
    filename=LOG_FILE, 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 1. SETUP CLIENTS
if 'GROQ_API_KEY' not in os.environ:
    print("❌ ERROR: GROQ_API_KEY not found in Secrets!")
    exit()

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ['GROQ_API_KEY']
)

# 2. HELPER FUNCTIONS
def get_time():
    return datetime.now().strftime("%H:%M:%S")

def get_live_spot():
    try:
        ticker = yf.Ticker("SI=F")
        data = ticker.history(period="1d")
        if not data.empty:
            return round(data['Close'].iloc[-1], 2)
    except Exception as e:
        logging.error(f"Spot Price Error: {e}")
    return 58.50 # Fallback

def get_latest_posts():
    headers = {'User-Agent': 'Mozilla/5.0'} 
    try:
        feed = feedparser.parse(RSS_URL, request_headers=headers)
        clean_posts = []
        for entry in feed.entries[:10]:
            if "[WTB]" in entry.title or "[WTT]" in entry.title:
                continue

            soup = BeautifulSoup(entry.summary, "html.parser")
            for tag in soup.find_all(['del', 's', 'strike']):
                tag.decompose()
            clean_posts.append({
                "title": entry.title,
                "link": entry.link,
                "body": soup.get_text()
            })
        return clean_posts
    except Exception as e:
        logging.error(f"RSS Fetch Error: {e}")
        return []

def analyze_post(title, body, current_spot):
    # Define your tiers
    PRIMARY_MODEL = "llama-3.3-70b-versatile"
    FALLBACK_MODEL = "llama-3.1-8b-instant"
    
    prompt = f"""
    You are a precious metals analyzer.
    Current Silver Spot Price: ${current_spot}/oz.

    **MATH RULES:**
    - Kilo = 32.15 oz.
    - 10oz Bar = 10.0 oz.
    - 5oz Bar = 5.0 oz.
    - 90% Silver = 0.715 oz per $1 Face Value.
    - Peace/Morgan = 0.773 oz per coin.
    - Libertad/Eagle/Maple/Britannia = 1.0 oz per coin.
    - War Nickel = 0.056 oz.

    **YOUR TASK:**
    1. Identify items, Price, and **QUANTITY AVAILABLE** (default to 1 if unknown).
       - If price says "ea", it is Price Per Item.
    2. **CATEGORY:**
       - "Premium": Libertad, Eagle, Morgan, Peace, Engelhard, Vintage, Key Date.
       - "Bullion": Junk, 90%, 40%, War Nickel, Generic Round/Bar.
    3. Calculate Weight Per Item (oz). MUST BE A SINGLE NUMBER.

    If Price is for a LOT/ROLL/TUBE, treat 'Quantity' as 1 (1 Lot). If Price is 'each', 'Quantity' is the coin count

    Return JSON ONLY:
    {{
      "shipping_cost": number,
      "deals": [
        {{
          "item_name": "string",
          "category": "Premium" or "Bullion",
          "listed_price": number,
          "quantity_available": number,
          "weight_per_item_oz": number
        }}
      ]
    }}

    TITLE: {title}
    BODY: {body}
    """
    
    # --- NEW FALLBACK LOGIC ---
    try:
        # Attempt 1: Primary Model (70B)
        response = client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        # Check if it's a Rate Limit error (usually contains 429 or 'rate_limit')
        error_msg = str(e).lower()
        if "429" in error_msg or "rate limit" in error_msg:
            logging.warning(f"⚠️ Rate Limit hit on 70b. Switching to 8b Fallback...")
            print(f"   ⚠️ Rate Limit! Fallback to 8b model...")
            
            try:
                # Attempt 2: Fallback Model (8B)
                response = client.chat.completions.create(
                    model=FALLBACK_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e2:
                logging.error(f"❌ Fallback Failed: {e2}")
                return None
        else:
            # Real error (not rate limit)
            logging.error(f"AI Error: {e}")
            return None

# --- MAIN INFINITE LOOP ---
current_spot = get_live_spot()
print(f"\n--- STARTING ARGENTUM EYE (Spot: ${current_spot}) ---")
logging.info(f"Bot Started. Spot: ${current_spot}")

seen_links = set()
last_spot_update = time.time()
deals_found_session = 0

while True:
    try:
        # 1. Update Spot Price (Every 15 mins)
        if time.time() - last_spot_update > 900:
            new_spot = get_live_spot()
            if new_spot > 0:
                current_spot = new_spot
                print(f"[{get_time()}] 💰 Updated Spot: ${current_spot}")
            last_spot_update = time.time()

        # 2. Fetch & Analyze Posts
        posts = get_latest_posts()

        for post in posts:
            if post['link'] in seen_links:
                continue
            seen_links.add(post['link'])

            print(f"\n[{get_time()}] 🔎 Checking: {post['title']}") 

            data = analyze_post(post['title'], post['body'], current_spot)

            if data and data.get('deals'):
                ship_cost = data.get('shipping_cost', 6.00)

                for deal in data['deals']:
                    # --- RESTORED MATH BLOCK ---
                    qty = deal.get('quantity_available', 1)
                    price = deal.get('listed_price', 0) # Use .get() for safety
                    weight = deal.get('weight_per_item_oz', 0) # Use .get() for safety

                    # SAFETY CHECK: If AI returned None or 0, skip
                    if not weight or not price: 
                        continue

                    # Ensure they are numbers (sometimes AI returns strings "1.0")
                    try:
                        qty = float(qty)
                        price = float(price)
                        weight = float(weight)
                    except ValueError:
                        continue # Skip if AI returned text instead of numbers

                    total_oz = weight * qty

                    total_oz = weight * qty
                    final_price_per_oz = ((price * qty) + ship_cost) / total_oz

                    threshold = current_spot
                    if deal['category'] == 'Premium':
                        threshold = current_spot + 10.00

                    # --- END RESTORED MATH BLOCK ---

                    # Sanity floor: if price/oz is unrealistically low, assume AI math error
                    min_floor = current_spot * 0.5  # e.g. 50% of spot; adjust if you like

                    if final_price_per_oz < min_floor:
                        print(f"   [{get_time()}] [Auto-Reject] {deal['item_name']} @ ${final_price_per_oz:.2f}/oz                                         (suspiciously low, likely AI math error)")
                        continue
        # HUMANIZED SLEEP
        sleep_time = random.randint(60, 90)
        print(f"[{get_time()}] 💤 Sleeping {sleep_time}s...", end="\r")
        time.sleep(sleep_time)

    except KeyboardInterrupt:
        print(f"\n🛑 Stopping. Total Deals Found: {deals_found_session}")
        logging.info("Bot Stopped by User.")
        break
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        logging.critical(f"Loop Crash: {e}")
        time.sleep(60)
