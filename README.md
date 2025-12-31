# 🎟️ AI-Dynamic Ticket Pricing Engine

A real-time arbitrage tool that analyzes ticket prices and uses **Google Gemini AI** to recommend Hold/Sell/Liquidate strategies.

## ⚠️ Legal Disclaimer

**Educational purposes only.** This project demonstrates AI-powered price analysis and web scraping techniques. Web scraping may violate StubHub's Terms of Service. Use responsibly and at your own risk. The author is not responsible for any misuse or legal consequences.

**For learning and personal use only - not for commercial purposes.**

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run the App
```bash
streamlit run app.py
```

### 4. Run Scraper (Optional)
```bash
python scraper.py --once  # Single scrape
python scraper.py         # Continuous loop
```

## 📋 Setup

### Google Cloud Setup
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

## 📁 Files

- `app.py` - Streamlit UI
- `scraper.py` - StubHub scraper + Kafka publisher
- `analyzer.py` - Gemini AI recommendation engine
- `.env` - Your credentials (gitignored)
- `requirements.txt` - Python dependencies

## 🔒 Security

Never commit `.env` file - it contains sensitive credentials!


