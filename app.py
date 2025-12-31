"""
Streamlit Dashboard for AI Ticket Pricing
"""

import os
import json
import time
import subprocess
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from confluent_kafka import Consumer
from analyzer import GeminiAnalyzer

load_dotenv()

# Tier options
TIERS = ["Lounge", "Floor", "Premium_Lower", "Lower_Bowl", "Upper_Bowl"]

# Initialize Gemini analyzer
@st.cache_resource
def get_analyzer():
    return GeminiAnalyzer()

# Initialize Kafka consumer
@st.cache_resource
def get_kafka_consumer():
    config = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVER'),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'PLAIN',
        'sasl.username': os.getenv('CONFLUENT_KEY'),
        'sasl.password': os.getenv('CONFLUENT_SECRET'),
        'group.id': 'streamlit-dashboard',
        'auto.offset.reset': 'latest'
    }
    consumer = Consumer(config)
    consumer.subscribe(['ticket-market-updates'])
    return consumer

# Get latest prices from Kafka
def get_latest_prices(consumer, timeout=2.0):
    """Poll Kafka for latest prices"""
    prices = {}
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        msg = consumer.poll(0.1)
        if msg is None:
            continue
        if msg.error():
            continue
        
        try:
            data = json.loads(msg.value().decode('utf-8'))
            prices[data['tier']] = data['price']
        except:
            pass
    
    return prices

# Streamlit UI
st.set_page_config(page_title="AI Ticket Pricing", page_icon="🎟️", layout="wide")

st.title("🎟️ AI-Dynamic Ticket Pricing Engine")
st.markdown("**Real-time arbitrage recommendations powered by Gemini 3.0 Flash**")

# Sidebar - User inputs
with st.sidebar:
    st.header("Your Listing")
    
    selected_tier = st.selectbox("Ticket Tier", TIERS)
    listing_price = st.number_input("My Listing Price ($)", min_value=0.0, value=100.0, step=5.0)
    
    st.divider()
    
    if st.button("🔄 Force Scrape", use_container_width=True):
        with st.spinner("Scraping StubHub..."):
            try:
                subprocess.run(["python", "scraper.py", "--once"], check=True, timeout=30)
                st.success("Scrape complete!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Scrape failed: {e}")

# Main content
col1, col2 = st.columns([1, 1])

# Get latest market data
try:
    consumer = get_kafka_consumer()
    latest_prices = get_latest_prices(consumer)
    
    # Get current price for selected tier
    current_price = latest_prices.get(selected_tier, None)
    
    with col1:
        st.subheader("📊 Market Floor")
        
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
            st.info("No market data yet. Click 'Force Scrape' to get latest prices.")
    
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
    st.info("Make sure Kafka credentials are configured in .env")

# Display all latest prices
st.divider()
st.subheader("💰 All Market Floors")

if latest_prices:
    cols = st.columns(len(TIERS))
    for idx, tier in enumerate(TIERS):
        with cols[idx]:
            price = latest_prices.get(tier, "—")
            if isinstance(price, float):
                st.metric(tier, f"${price:.2f}")
            else:
                st.metric(tier, price)
else:
    st.info("No market data available yet.")

