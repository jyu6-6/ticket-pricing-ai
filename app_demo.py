"""
Demo version of AI Ticket Pricing Dashboard
Uses mock data instead of live scraping for safe public deployment
"""

import streamlit as st
import os
import json
import random
from datetime import datetime
from dotenv import load_dotenv

# Only import analyzer - no Kafka or scraper
from analyzer import GeminiAnalyzer

load_dotenv()

# Tier options
TIERS = ["Lounge", "Floor", "Premium_Lower", "Lower_Bowl", "Upper_Bowl"]

# Mock market data (simulates real StubHub prices)
MOCK_PRICES = {
    "Upper_Bowl": 385.88,
    "Lounge": 415.30,
    "Lower_Bowl": 558.33,
    "Floor": 877.41,
    "Premium_Lower": 887.69
}

# Initialize Gemini analyzer
@st.cache_resource
def get_analyzer():
    return GeminiAnalyzer()

# Streamlit UI
st.set_page_config(page_title="AI Ticket Pricing Demo", page_icon="🎟️", layout="wide")

st.title("🎟️ AI-Dynamic Ticket Pricing Engine (Demo)")
st.markdown("**Real-time arbitrage recommendations powered by Gemini AI**")

# Demo banner
st.info("🎭 **Demo Mode** - Using sample market data. This is a portfolio demonstration of AI-powered pricing strategy.")

# Sidebar - User inputs
with st.sidebar:
    st.header("Your Listing")
    
    selected_tier = st.selectbox("Ticket Tier", TIERS)
    listing_price = st.number_input("My Listing Price ($)", min_value=0.0, value=100.0, step=5.0)
    
    st.divider()
    
    # Simulate market volatility button
    if st.button("🎲 Simulate Market Change", use_container_width=True):
        # Add some random variation to mock prices
        for tier in MOCK_PRICES:
            variation = random.uniform(-0.05, 0.05)  # ±5% variation
            MOCK_PRICES[tier] = round(MOCK_PRICES[tier] * (1 + variation), 2)
        st.success("Market prices updated!")
        st.rerun()
    
    st.caption("💡 Click to see how AI adapts to market changes")

# Main content
col1, col2 = st.columns([1, 1])

# Get current price for selected tier
current_price = MOCK_PRICES.get(selected_tier)

try:
    with col1:
        st.subheader("📊 Market Data")
        
        if current_price:
            # Calculate delta from session state
            if f'prev_price_{selected_tier}' not in st.session_state:
                st.session_state[f'prev_price_{selected_tier}'] = current_price
            
            prev_price = st.session_state[f'prev_price_{selected_tier}']
            delta = current_price - prev_price
            
            st.metric(
                label=f"{selected_tier} Floor",
                value=f"${current_price:.2f}",
                delta=f"${delta:.2f}" if delta != 0 else None
            )
            
            # Update previous price
            st.session_state[f'prev_price_{selected_tier}'] = current_price
        else:
            st.info("No market data available.")
    
    with col2:
        st.subheader("🧠 AI Recommendation")
        
        # Use container to ensure only one recommendation is shown
        recommendation_container = st.empty()
        
        if current_price:
            # Get AI recommendation
            analyzer = get_analyzer()
            
            with st.spinner("Analyzing..."):
                recommendation = analyzer.analyze(selected_tier, current_price, listing_price)
            
            action = recommendation['action']
            target = recommendation['target']
            logic = recommendation['logic']
            
            # Color-coded card
            if action in ['RAISE', 'HOLD']:
                color = "🟢"
                bg_color = "#d4edda"
            elif action == 'ADJUST':
                color = "🟡"
                bg_color = "#fff3cd"
            else:  # LIQUIDATE
                color = "🔴"
                bg_color = "#f8d7da"
            
            # Display in container (replaces previous content)
            with recommendation_container:
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 25px; border-radius: 12px; border: 2px solid #ddd;">
                    <h3 style="color: #222; margin-top: 0; font-weight: 600;">{color} {action}</h3>
                    <h2 style="color: #000; margin: 10px 0; font-size: 2.5rem; font-weight: 700;">${target:.2f}</h2>
                    <p style="color: #333; margin-bottom: 0; font-size: 1.05rem; line-height: 1.5;">{logic}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            with recommendation_container:
                st.warning("Waiting for market data...")

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Make sure Google Cloud credentials are configured.")

# Display all latest prices
st.divider()
st.subheader("💰 All Market Floors (Sample Data)")

cols = st.columns(len(TIERS))
for idx, tier in enumerate(TIERS):
    with cols[idx]:
        price = MOCK_PRICES.get(tier, 0)
        st.metric(tier, f"${price:.2f}")

# Footer
st.divider()
st.caption("🎓 **Educational Demo** - This is a portfolio project demonstrating AI-powered price analysis. Market data is simulated.")
st.caption("📊 Real version uses live StubHub data via Confluent Kafka streaming.")
