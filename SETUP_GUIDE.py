#!/usr/bin/env python3
"""
PORTFOLIO SETUP GUIDE - Complete Installation Instructions
"""

# ============================================================================
# QUICK START CHECKLIST
# ============================================================================

SETUP_STEPS = """

✅ STEP 1: Prerequisites Check (5 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Python 3.9+ installed:  python --version
□ Git installed:          git --version
□ GitHub account:         github.com
□ Google Sheets:          Existing sheet created
□ Google credentials:     Service account JSON ready
□ Vercel account:         Optional, for dashboard


✅ STEP 2: Clone & Install (3 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Clone repo:
  git clone https://github.com/YOUR_USERNAME/tradebot.git
  cd tradebot

□ Create virtual environment:
  python -m venv venv
  source venv/bin/activate  # Linux/Mac
  venv\\Scripts\\activate    # Windows

□ Install dependencies:
  pip install -r requirements.txt


✅ STEP 3: Google Sheets Setup (5 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Get Google Service Account JSON:
  - Go to https://console.cloud.google.com
  - Create project: "TradeBot"
  - Enable APIs: Google Sheets API + Google Drive API
  - Create Service Account
  - Download JSON credentials (keep safe!)

□ Share your Google Sheet:
  - Open your sheet
  - Share → "Anyone with link" → Viewer
  - Copy sheet ID from URL

□ Create .env file locally:
  GOOGLE_SHEETS_ID=YOUR_SHEET_ID
  GOOGLE_SHEETS_CREDENTIALS_JSON={"type":"service_account",...}


✅ STEP 4: Test Locally (5 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Load environment:
  source .env  # Linux/Mac
  # Or set manually in Windows

□ Test the bot:
  python 8_daily_runner.py

□ Check Google Sheets:
  - New sheets created? (portfolio_history, trades, etc.)
  - Data populated?


✅ STEP 5: GitHub Setup (5 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Create GitHub repo:
  - Go to github.com/new
  - Name: "tradebot"
  - Make it public (optional)

□ Push code:
  git add .
  git commit -m "Initial commit: TradeBot"
  git branch -M main
  git remote add origin https://github.com/YOUR_USERNAME/tradebot.git
  git push -u origin main

□ Set GitHub Secrets:
  - Repo → Settings → Secrets and variables → Actions
  - Add Secret: GOOGLE_SHEETS_ID
  - Add Secret: GOOGLE_SHEETS_CREDENTIALS_JSON


✅ STEP 6: Enable GitHub Actions (2 min)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ Check workflow file:
  .github/workflows/daily_trading.yml exists?

□ Enable Actions:
  - Repo → Actions tab
  - Click "I understand..."
  - Ready to go!

□ Manual test:
  - Actions tab → Select workflow → Run workflow
  - Watch it execute!


✅ STEP 7: Monitor & Verify (Ongoing)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

□ GitHub Actions:
  - Watch runs in Actions tab
  - Check logs for errors
  - Should run daily at 12pm CET

□ Google Sheets:
  - New entries appear daily?
  - Check: portfolio_history, trades, rss_articles
  - Data looks reasonable?

□ Optional: Deploy Dashboard to Vercel
  - Create Vercel account
  - Deploy dashboard.html
  - Get live dashboard URL


✅ TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problem: "GOOGLE_SHEETS_ID not set"
→ Check .env file exists and is loaded
→ Verify environment variables are set correctly
→ Check GitHub Secrets are added correctly

Problem: "Failed to connect to Google Sheets"
→ Check service account has Sheet Editor access
→ Verify JSON credentials are valid
→ Make sure sheet is shared with service account email

Problem: "No trading signals generated"
→ Normal! Model is very selective
→ Check market conditions
→ Adjust min_confidence in 8_daily_runner.py

Problem: GitHub Actions fails
→ Check workflow logs (Actions tab)
→ Verify all secrets are set
→ Ensure requirements.txt has all dependencies


🎯 NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Monitor first few runs (1-2 days)
2. Adjust trading parameters if needed
3. Optional: Retrain model with latest data
4. Optional: Deploy dashboard to Vercel
5. Share dashboard with friends!


📚 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

- README.md          - Overview
- QUICKSTART.md      - 15-min setup
- FILE_ORGANIZATION  - Project structure
- DEPLOYMENT.md      - Detailed setup
- Models/            - Trained model
- Data/              - Training data

🎉 You're all set! The bot will now run automatically daily!

"""

if __name__ == "__main__":
    print(SETUP_STEPS)
