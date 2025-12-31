"""
StubHub Ticket Scraper with Kafka Publishing
Scrapes ticket price floors and publishes to Confluent Kafka
"""

import os
import json
import time
import random
import argparse
import requests
from dotenv import load_dotenv
from confluent_kafka import Producer

# Load environment variables
load_dotenv()

# Tier mapping from master spec
TIER_MAPPING = {
    "9067": "Lounge",
    "1724": "Floor",
    "682": "Premium_Lower",
    "478": "Lower_Bowl",
    "306": "Upper_Bowl"
}


def create_kafka_producer():
    """Create Confluent Kafka producer"""
    config = {
        'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVER'),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'PLAIN',
        'sasl.username': os.getenv('CONFLUENT_KEY'),
        'sasl.password': os.getenv('CONFLUENT_SECRET'),
    }
    return Producer(config)


def fetch_ticket_data():
    """Fetch ticket data from StubHub API"""
    url = os.getenv('SCRAPE_URL')
    headers = json.loads(os.getenv('SCRAPE_HEADERS'))
    cookies = json.loads(os.getenv('SCRAPE_COOKIES'))
    params = json.loads(os.getenv('SCRAPE_PARAMS'))
    json_data = json.loads(os.getenv('SCRAPE_JSON_DATA'))
    
    response = requests.post(url, headers=headers, cookies=cookies, params=params, json=json_data)
    response.raise_for_status()
    return response.json()


def clean_and_categorize(raw_json):
    """Extract minimum prices for each tier"""
    section_data = raw_json.get('sectionPopupData', {})
    tier_prices = {}
    
    # Group by tier prefix and find minimum price
    for key, value in section_data.items():
        prefix = key.split('_')[0]  # Get prefix before first underscore
        if prefix in TIER_MAPPING:
            tier_name = TIER_MAPPING[prefix]
            raw_price = value.get('rawMinPrice', float('inf'))
            
            if tier_name not in tier_prices or raw_price < tier_prices[tier_name]:
                tier_prices[tier_name] = raw_price
    
    return tier_prices


def publish_to_kafka(producer, tier_prices):
    """Publish each tier's price to Kafka"""
    topic = 'ticket-market-updates'
    
    for tier, price in tier_prices.items():
        message = {
            'tier': tier,
            'price': price,
            'timestamp': time.time()
        }
        
        producer.produce(topic, value=json.dumps(message))
        print(f"Published: {tier} = ${price:.2f}")
    
    producer.flush()


def run_once():
    """Run scraper once"""
    print("Fetching ticket data...")
    raw_data = fetch_ticket_data()
    
    print("Categorizing by tier...")
    tier_prices = clean_and_categorize(raw_data)
    
    print("Publishing to Kafka...")
    producer = create_kafka_producer()
    publish_to_kafka(producer, tier_prices)
    
    print("✓ Scrape complete!")


def run_loop():
    """Run scraper in continuous loop with random delays"""
    while True:
        try:
            run_once()
            
            # Random delay between 10-60 minutes (600-3600 seconds)
            delay = random.randint(600, 3600)
            print(f"\nSleeping for {delay // 60} minutes...")
            time.sleep(delay)
            
        except Exception as e:
            print(f"Error: {e}")
            print("Retrying in 5 minutes...")
            time.sleep(300)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='StubHub Ticket Scraper')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    args = parser.parse_args()
    
    if args.once:
        run_once()
    else:
        print("Starting continuous scraping loop...")
        run_loop()
