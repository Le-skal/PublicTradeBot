# 🤖 TradeBot - Automated Trading System

An AI-powered trading bot that analyzes financial news and trades cryptocurrencies and stocks based on machine learning predictions.

## 🎯 What It Does

- **Fetches 250+ articles** daily from L'Agefi RSS feed (French financial news)
- **Analyzes sentiment** using transformer models (CamemBERT)
- **Generates trading signals** for 10 assets (BTC, ETH, French stocks)
- **Executes trades** automatically based on ML predictions
- **Tracks performance** with live dashboard
- **Stores everything** in Google Sheets (no database needed!)

## 🏗️ Architecture

```
GitHub Actions (Daily 12pm CET)
         ↓
    8_daily_runner.py
    ├─ Fetch RSS articles
    ├─ Fetch market prices
    ├─ ML predictions
    ├─ Execute trades
         ↓
  Google Sheets (Data storage)
         ↓
  Vercel Dashboard (Public results)
```

## 📊 Trading Universe

- **Crypto**: BTC, ETH (Bitcoin, Ethereum)
- **French Stocks**: LVMH, Hermès, TotalEnergies, Engie, BNP, SocGen, Capgemini, Schneider

## 🎮 Strategy

- **Signals**: ML model (XGBoost) + sentiment analysis + keyword detection
- **Position sizing**: 25% per trade, max 3 open positions
- **Risk management**: -8% stop loss, +20% take profit
- **Frequency**: Max 1 trade per day (very selective)
- **Confidence threshold**: 0.520 (top 10% signals only)

## 📈 Performance

Backtested on 2024-2025 data with strong results on selective trades.

## 🔧 Project Files

**Production (Daily Bot):**
- `8_daily_runner.py` - Main automated bot
- `google_sheets_client.py` - Google Sheets integration
- `models/trading_model.pkl` - Trained ML model

**Training Pipeline (Optional):**
- `2_fetch_all_data.py` - Fetch historical data
- `3_sentiment_analysis.py` - Analyze sentiment
- `4_technical_indicators.py` - Calculate indicators
- `5_feature_engineering.py` - Create ML features
- `6_train_model.py` - Train model
- `7_backtest.py` - Backtest strategy

**Configuration:**
- `.github/workflows/` - GitHub Actions (runs daily)
- `requirements.txt` - Dependencies
- `.env` - Environment variables (GitHub Secrets)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- GitHub account (for GitHub Actions)
- Google Sheets + Service Account credentials
- Vercel account (optional, for dashboard)

### Setup

1. **Clone & Install**
```bash
git clone <repo>
cd tradebot
pip install -r requirements.txt
```

2. **Create Google Sheets Credentials**
- Go to https://console.cloud.google.com
- Create a service account
- Get the JSON credentials

3. **Set Environment Variables**
```bash
export GOOGLE_SHEETS_ID="your_sheet_id"
export GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account"...}'
```

4. **Test Locally**
```bash
python 8_daily_runner.py
```

5. **Set Up GitHub Actions**
- Push to GitHub
- Go to Settings → Secrets and variables → Actions
- Add the two environment variables above
- The bot will run daily automatically!

## 📊 Dashboard

View live results at your Vercel deployment URL (public read-only).

## 🧪 Retraining

To retrain with new data:

```bash
# Update historical data
python 2_fetch_all_data.py

# Run entire pipeline
python 3_sentiment_analysis.py
python 4_technical_indicators.py
python 5_feature_engineering.py
python 6_train_model.py
python 7_backtest.py
```

## ⚙️ Configuration

Edit `8_daily_runner.py` to adjust trading parameters:

```python
PORTFOLIO_CONFIG = {
    "initial_capital": 1000.0,      # Starting capital
    "max_positions": 3,               # Max open positions
    "position_size": 0.25,            # 25% per trade
    "min_confidence": 0.520,          # Confidence threshold
    "stop_loss": -0.08,               # -8% stop loss
    "take_profit": 0.20,              # +20% take profit
}
```

## 🔐 Security

- Credentials stored in GitHub Secrets (never in code)
- Dashboard is public read-only
- No sensitive data exposed
- API keys restricted to specific endpoints

## 💼 What's Included

- ✅ Full ML pipeline (data → features → model → trades)
- ✅ Automated daily execution
- ✅ Google Sheets integration
- ✅ Real-time portfolio tracking
- ✅ Trade history & analysis
- ✅ News article tracking
- ✅ Sentiment analysis
- ✅ Technical indicators
- ✅ Risk management

## 📝 License

MIT - Feel free to fork and customize!

## ⚠️ Disclaimer

**Educational project only. Not financial advice. Trade at your own risk!**

Past performance does not guarantee future results. All trading carries risk.

## 🤝 Contributing

This is a personal trading bot. You're welcome to:
- Fork and customize
- Improve the strategy
- Add new assets
- Enhance the dashboard

---

**Questions?** Check the logs in GitHub Actions or your local `.env` setup.
