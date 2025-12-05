# Reddit Deal Scanner Bot

## Overview
A Python bot that scans r/pmsforsale subreddit posts to identify good deals on precious metals. Uses OpenAI to analyze listings and find items priced below spot.

## Current State
- Mock mode: Using test data while waiting for Reddit API access
- AI analysis: Working with OpenAI GPT-4o-mini

## Features
- Analyzes post titles and bodies for pricing
- Calculates all-in price per oz including shipping
- Filters out users without seller flair (risk mitigation)
- Finds items listed below current spot price ($58.50/oz)

## Files
- `main.py` - Main bot script with mock data and AI analyzer

## Required Secrets
- `OPENAI_API_KEY` - OpenAI API key for deal analysis

## Future Enhancements
- Reddit API integration (PRAW) once access is restored
- Real-time scanning of new posts
- Notifications for good deals
