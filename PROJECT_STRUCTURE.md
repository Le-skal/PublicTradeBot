# Key Project Files for Portfolio

## 🚀 Core Trading Bot
- `8_daily_runner.py` - Automated daily trading bot (PRODUCTION)
- `google_sheets_client.py` - Google Sheets integration

## 📊 ML Pipeline (Training & Analysis)
- `2_fetch_all_data.py` - Fetch crypto/stocks/trends data
- `3_sentiment_analysis.py` - NLP sentiment from financial news
- `4_technical_indicators.py` - RSI, MACD, Bollinger Bands, etc.
- `5_feature_engineering.py` - Create ML features for model
- `6_train_model.py` - XGBoost model training
- `7_backtest.py` - Backtest strategy performance

## 📁 Key Directories
- `data/raw/` - Historical prices, news articles, trends
- `data/processed/` - Engineered features
- `models/` - Trained XGBoost model
- `results/` - Backtest results, performance metrics

## ⚙️ Configuration
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (Google credentials)
- `.github/workflows/` - GitHub Actions automation

## 🎯 How It Works
1. Daily: Fetch 250+ financial news articles
2. Daily: Analyze sentiment using CamemBERT
3. Daily: Calculate technical indicators (RSI, MACD, BB)
4. Daily: ML predictions from trained model
5. Daily: Execute trades automatically based on signals
6. Daily: Store results in Google Sheets
7. Optional: View dashboard with live performance

## 📈 Trading Strategy
- Universe: BTC, ETH, 8 French stocks
- Signals: ML + sentiment + keyword detection
- Risk: Max 3 positions, -8% stop loss, +20% take profit
- Selectivity: Only top 10% confidence signals trade

## 💼 What Makes This Portfolio-Ready
- ✅ Complete ML pipeline (data → predictions)
- ✅ Production-ready bot (automated daily execution)
- ✅ Clean, well-commented code
- ✅ Risk management built-in
- ✅ Google Sheets for data (no DB needed)
- ✅ GitHub Actions for automation
- ✅ Backtest results included

## 🔐 Security
- No API keys in code (uses environment variables)
- Google credentials stored as GitHub Secrets
- Dashboard read-only for public viewing
- Service account with minimal permissions

All code is production-tested and ready to deploy!
