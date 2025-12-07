# Argentum Eye 👁️🪙
**Real-time AI Silver Deal Scanner**

Argentum Eye is an automated bot that monitors Reddit (r/Pmsforsale) for under-spot silver deals in real-time. Unlike standard keyword scrapers, it uses an LLM (Llama 3 via Groq) to "read" the post, understand context (e.g., "below melt," "shipped"), and mathematically verify if a listing is below spot price.

## Features
*   🚀 **Live Scanning:** Monitors RSS feeds for new listings instantly (No Reddit API Key required).
*   🧠 **AI Logic:** Identifies "War Nickels," "90% Junk," and "Premium" items automatically using Groq Llama 3.
*   🧮 **Math Safety:** Python layer double-checks AI calculations against live Spot Price (Yahoo Finance).
*   🛡️ **Smart Filters:** Ignores "Sold" items, "WTB" posts, and overpriced numismatics.
*   🤖 **Bot Stealth:** Uses randomized sleep intervals to behave like a human user.

## How it Works
1.  **Fetch:** Grabs the latest 10 posts from the subreddit RSS feed.
2.  **Clean:** Removes strikethrough text (sold items) and parses HTML.
3.  **Analyze:** Sends the text to Llama 3 with a strict prompt to extract items, prices, and quantities.
4.  **Verify:** Python calculates the "All-In Price Per Ounce" (Price + Shipping / Weight).
5.  **Alert:** If the price is below Spot (or Spot + Premium for specific items), it logs the deal.

## Requirements
*   Python 3.x
*   Groq API Key
*   Libraries: `openai`, `feedparser`, `beautifulsoup4`, `yfinance`

---
*Built with Python and AI Assistance.*
