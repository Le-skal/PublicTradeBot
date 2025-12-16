"""
Script pour récupérer toutes les données nécessaires au Trading Simulator
- L'Agefi RSS (sentiment)
- Prix crypto (Yahoo Finance)
- Prix actions FR (Yahoo Finance)
- Google Trends

Usage:
    python fetch_all_data.py --start-date 2024-01-01 --end-date 2025-11-19
"""

import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from pytrends.request import TrendReq
import time
import os
from pathlib import Path
import json
import random

# ============================================================================
# CONFIGURATION
# ============================================================================

UNIVERSE = {
    "crypto": ["BTC", "ETH"],  # Symboles pour Yahoo Finance
    "actions_fr": {
        "MC.PA": "LVMH",
        "RMS.PA": "Hermès",
        "TTE.PA": "TotalEnergies",
        "ENGI.PA": "Engie",
        "BNP.PA": "BNP Paribas",
        "GLE.PA": "Société Générale",
        "CAP.PA": "Capgemini",
        "SU.PA": "Schneider Electric",
    },
}

# Keywords pour Google Trends
TRENDS_KEYWORDS = {
    "BTC": ["bitcoin", "btc"],
    "ETH": ["ethereum", "eth"],
    "MC.PA": ["lvmh", "louis vuitton"],
    "RMS.PA": ["hermès", "hermes"],
    "TTE.PA": ["totalenergies", "total energie"],
    "ENGI.PA": ["engie"],
    "BNP.PA": ["bnp paribas", "bnp"],
    "GLE.PA": ["société générale", "socgen"],
    "CAP.PA": ["capgemini"],
    "SU.PA": ["schneider electric"],
    "macro": ["bourse", "cac40", "inflation", "bce"],
}

# Paths
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Créer les dossiers
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 1. FETCH CRYPTO PRICES (Yahoo Finance)
# ============================================================================


def fetch_crypto_prices(start_date, end_date, save_path=None):
    """
    Récupère les prix historiques des cryptos via Yahoo Finance

    Args:
        start_date: str format 'YYYY-MM-DD'
        end_date: str format 'YYYY-MM-DD'

    Returns:
        pd.DataFrame: Prix avec colonnes [date, asset, open, high, low, close, volume]
    """
    print("\n₿ Fetching crypto prices from Yahoo Finance...")

    # Mapping des symboles crypto pour Yahoo Finance
    crypto_tickers = {
        "BTC": "BTC-EUR",  # Bitcoin en EUR
        "ETH": "ETH-EUR",  # Ethereum en EUR
    }

    all_data = []

    for symbol, ticker in crypto_tickers.items():
        try:
            print(f"  Fetching {symbol} ({ticker})...")

            crypto = yf.Ticker(ticker)
            df = crypto.history(start=start_date, end=end_date)

            if df.empty:
                print(f"  ⚠️  No data for {ticker}")
                continue

            df = df.reset_index()
            df["asset"] = symbol
            df = df.rename(columns={"Date": "date"})

            # Garder les colonnes importantes
            df = df[["date", "asset", "Open", "High", "Low", "Close", "Volume"]]
            df.columns = ["date", "asset", "open", "high", "low", "close", "volume"]

            all_data.append(df)

            print(f"  ✅ {symbol}: {len(df)} data points")

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ Error fetching {ticker}: {e}")

    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        df_combined["date"] = pd.to_datetime(df_combined["date"]).dt.tz_localize(None)
        df_combined = df_combined.sort_values("date").reset_index(drop=True)

        print(f"\n✅ Total crypto data points: {len(df_combined)}")

        if save_path:
            df_combined.to_csv(save_path, index=False)
            print(f"💾 Saved to {save_path}")

        return df_combined

    return pd.DataFrame()


# ============================================================================
# 2. FETCH STOCK PRICES (Yahoo Finance)
# ============================================================================


def fetch_stock_prices(start_date, end_date, save_path=None):
    """
    Récupère les prix historiques des actions via Yahoo Finance

    Args:
        start_date: str format 'YYYY-MM-DD'
        end_date: str format 'YYYY-MM-DD'

    Returns:
        pd.DataFrame: Prix avec colonnes [date, asset, open, high, low, close, volume]
    """
    print("\n📈 Fetching stock prices from Yahoo Finance...")

    all_data = []

    for ticker, name in UNIVERSE["actions_fr"].items():
        try:
            print(f"  Fetching {name} ({ticker})...")

            stock = yf.Ticker(ticker)
            df = stock.history(start=start_date, end=end_date)

            if df.empty:
                print(f"  ⚠️  No data for {ticker}")
                continue

            df = df.reset_index()
            df["asset"] = ticker
            df["name"] = name
            df = df.rename(columns={"Date": "date"})

            # Garder les colonnes importantes
            df = df[["date", "asset", "name", "Open", "High", "Low", "Close", "Volume"]]
            df.columns = [
                "date",
                "asset",
                "name",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ]

            all_data.append(df)

            print(f"  ✅ {name}: {len(df)} data points")

            # Rate limiting
            time.sleep(0.5)

        except Exception as e:
            print(f"  ❌ Error fetching {ticker}: {e}")

    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        df_combined["date"] = pd.to_datetime(df_combined["date"]).dt.tz_localize(None)
        df_combined = df_combined.sort_values("date").reset_index(drop=True)

        print(f"\n✅ Total stock data points: {len(df_combined)}")

        if save_path:
            df_combined.to_csv(save_path, index=False)
            print(f"💾 Saved to {save_path}")

        return df_combined

    return pd.DataFrame()


# ============================================================================
# 3. FETCH GOOGLE TRENDS
# ============================================================================


def fetch_google_trends(start_date, end_date, save_path=None):
    """
    Récupère les données Google Trends pour tous les assets

    Args:
        start_date: str format 'YYYY-MM-DD'
        end_date: str format 'YYYY-MM-DD'

    Returns:
        pd.DataFrame: Trends avec colonnes [date, keyword, interest]
    """
    print("\n🔍 Fetching Google Trends data...")
    print("  💡 Tip: If you get 429 errors, try using a proxy or VPN")

    # Add custom headers to mimic a real browser with session
    import requests

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
    )

    pytrends = TrendReq(hl="fr-FR", tz=60, timeout=(10, 25))
    # Replace pytrends session with our custom session
    pytrends.session = session

    all_data = []

    # Timeframe pour pytrends
    timeframe = f"{start_date} {end_date}"

    for asset, keywords in TRENDS_KEYWORDS.items():
        # Limiter à 5 keywords max par requête (limite Google)
        keyword_list = keywords[:5] if len(keywords) > 5 else keywords

        try:
            print(f"  Fetching trends for {asset}: {keyword_list}")

            pytrends.build_payload(
                keyword_list, cat=0, timeframe=timeframe, geo="FR", gprop=""
            )

            # Récupérer interest over time
            df = pytrends.interest_over_time()

            if df.empty:
                print(f"  ⚠️  No trends data for {asset}")
                continue

            # Reformater
            df = df.reset_index()
            df = df.drop(columns=["isPartial"], errors="ignore")

            # Moyenne des keywords pour cet asset
            df["interest"] = df[keyword_list].mean(axis=1)
            df["asset"] = asset
            df = df[["date", "asset", "interest"]]

            all_data.append(df)

            print(f"  ✅ {asset}: {len(df)} data points")

            # Rate limiting important pour Google - random delay to mimic human behavior
            delay = random.uniform(2, 3)
            print(f"  ⏳ Waiting {delay:.1f} seconds before next request...")
            time.sleep(delay)

        except Exception as e:
            print(f"  ❌ Error fetching trends for {asset}: {e}")

    if all_data:
        df_combined = pd.concat(all_data, ignore_index=True)
        df_combined["date"] = pd.to_datetime(df_combined["date"])
        df_combined = df_combined.sort_values("date").reset_index(drop=True)

        print(f"\n✅ Total trends data points: {len(df_combined)}")

        if save_path:
            df_combined.to_csv(save_path, index=False)
            print(f"💾 Saved to {save_path}")

        return df_combined

    return pd.DataFrame()


# ============================================================================
# 5. MAIN FUNCTION
# ============================================================================


def main(start_date="2024-01-01", end_date="2025-11-19"):
    """
    Fonction principale pour fetcher toutes les données
    """
    print("=" * 80)
    print("🚀 TRADING SIMULATOR - DATA FETCHING")
    print("=" * 80)
    print(f"Period: {start_date} to {end_date}")
    print(
        f"Universe: {len(UNIVERSE['crypto'])} cryptos + {len(UNIVERSE['actions_fr'])} stocks"
    )
    print("=" * 80)

    # 1. Crypto prices
    df_crypto = fetch_crypto_prices(
        start_date=start_date,
        end_date=end_date,
        save_path=RAW_DIR / "prices_crypto.csv",
    )

    # 2. Stock prices
    df_stocks = fetch_stock_prices(
        start_date=start_date,
        end_date=end_date,
        save_path=RAW_DIR / "prices_stocks.csv",
    )

    # 3. Google Trends
    df_trends = fetch_google_trends(
        start_date=start_date,
        end_date=end_date,
        save_path=RAW_DIR / "google_trends.csv",
    )

    # Summary
    print("\n" + "=" * 80)
    print("📊 DATA FETCHING SUMMARY")
    print("=" * 80)
    print(f"Crypto prices:      {len(df_crypto):>6} rows")
    print(f"Stock prices:       {len(df_stocks):>6} rows")
    print(f"Google Trends:      {len(df_trends):>6} rows")
    print("=" * 80)

    # Save metadata
    metadata = {
        "fetch_date": datetime.now().isoformat(),
        "period": {"start": start_date, "end": end_date},
        "universe": UNIVERSE,
        "data_counts": {
            "crypto_prices": len(df_crypto),
            "stock_prices": len(df_stocks),
            "google_trends": len(df_trends),
        },
    }

    with open(RAW_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n✅ All data fetched successfully!")
    print(f"📁 Data saved in: {RAW_DIR}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch all data for Trading Simulator")
    parser.add_argument(
        "--start-date", type=str, default="2024-01-01", help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date", type=str, default="2025-11-19", help="End date (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    main(start_date=args.start_date, end_date=args.end_date)
