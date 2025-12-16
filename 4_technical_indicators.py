"""
ÉTAPE 2.2 : TECHNICAL INDICATORS
Calcule les indicateurs techniques pour crypto et actions

Entrée :
    - data/raw/prices_crypto.csv
    - data/raw/prices_stocks.csv
Sortie :
    - data/processed/technical_features.csv

Usage:
    python technical_indicators.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Paramètres des indicateurs techniques
PARAMS = {
    "rsi_period": 14,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bollinger_period": 20,
    "bollinger_std": 2,
    "ma_short": 7,
    "ma_medium": 30,
    "ma_long": 90,
    "volume_ma": 20,
}


# ============================================================================
# 1. CHARGER LES DONNÉES
# ============================================================================


def load_price_data():
    """Charge les données de prix crypto et actions"""
    print("\n📂 Loading price data...")

    # Crypto
    crypto_file = RAW_DIR / "prices_crypto.csv"
    if not crypto_file.exists():
        raise FileNotFoundError(f"File not found: {crypto_file}")

    df_crypto = pd.read_csv(crypto_file)
    df_crypto["date"] = pd.to_datetime(df_crypto["date"])
    df_crypto["asset_type"] = "crypto"
    # Renommer pour uniformité
    df_crypto = df_crypto.rename(columns={"price": "close"})
    df_crypto["open"] = df_crypto["close"]  # Approximation
    df_crypto["high"] = df_crypto["close"]
    df_crypto["low"] = df_crypto["close"]

    print(f"   ✅ Crypto: {len(df_crypto)} rows, {df_crypto['asset'].nunique()} assets")

    # Actions
    stocks_file = RAW_DIR / "prices_stocks.csv"
    if not stocks_file.exists():
        raise FileNotFoundError(f"File not found: {stocks_file}")

    df_stocks = pd.read_csv(stocks_file)
    df_stocks["date"] = pd.to_datetime(df_stocks["date"])
    df_stocks["asset_type"] = "stock"

    print(f"   ✅ Stocks: {len(df_stocks)} rows, {df_stocks['asset'].nunique()} assets")

    # Combiner
    # Pour les actions, on a déjà open, high, low, close
    df_crypto_subset = df_crypto[
        ["date", "asset", "asset_type", "open", "high", "low", "close", "volume"]
    ]
    df_stocks_subset = df_stocks[
        ["date", "asset", "asset_type", "open", "high", "low", "close", "volume"]
    ]

    df_combined = pd.concat([df_crypto_subset, df_stocks_subset], ignore_index=True)
    df_combined = df_combined.sort_values(["asset", "date"]).reset_index(drop=True)

    print(f"\n   📊 Combined: {len(df_combined)} total rows")

    return df_combined


# ============================================================================
# 2. INDICATEURS TECHNIQUES
# ============================================================================


def calculate_rsi(series, period=14):
    """
    Calcule le Relative Strength Index (RSI)

    Returns:
        Series: RSI values (0-100)
    """
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_macd(series, fast=12, slow=26, signal=9):
    """
    Calcule le MACD (Moving Average Convergence Divergence)

    Returns:
        tuple: (macd, signal_line, histogram)
    """
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()

    macd = ema_fast - ema_slow
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line

    return macd, signal_line, histogram


def calculate_bollinger_bands(series, period=20, std_dev=2):
    """
    Calcule les Bollinger Bands

    Returns:
        tuple: (upper_band, middle_band, lower_band)
    """
    middle_band = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()

    upper_band = middle_band + (std * std_dev)
    lower_band = middle_band - (std * std_dev)

    return upper_band, middle_band, lower_band


def calculate_moving_averages(series, periods=[7, 30, 90]):
    """
    Calcule les Moving Averages

    Returns:
        dict: {period: ma_series}
    """
    mas = {}
    for period in periods:
        mas[f"ma_{period}"] = series.rolling(window=period).mean()
    return mas


def calculate_volatility(series, period=20):
    """
    Calcule la volatilité (rolling standard deviation des returns)

    Returns:
        Series: Volatility values
    """
    returns = series.pct_change()
    volatility = returns.rolling(window=period).std() * np.sqrt(252)  # Annualisé

    return volatility


def calculate_volume_indicators(volume, close, period=20):
    """
    Calcule les indicateurs de volume

    Returns:
        dict: Volume indicators
    """
    indicators = {}

    # Volume Moving Average
    indicators["volume_ma"] = volume.rolling(window=period).mean()

    # Volume ratio (current / MA)
    indicators["volume_ratio"] = volume / indicators["volume_ma"]

    # On-Balance Volume (OBV)
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    indicators["obv"] = obv

    return indicators


# ============================================================================
# 3. APPLIQUER LES INDICATEURS PAR ASSET
# ============================================================================


def calculate_technical_features(df):
    """
    Calcule tous les indicateurs techniques pour chaque asset

    Returns:
        DataFrame avec tous les indicateurs
    """
    print("\n📈 Calculating technical indicators...")

    all_features = []

    for asset in tqdm(df["asset"].unique(), desc="   Processing assets"):
        df_asset = df[df["asset"] == asset].copy().sort_values("date")

        if len(df_asset) < 100:  # Pas assez de données
            print(f"   ⚠️  Skipping {asset} (only {len(df_asset)} data points)")
            continue

        # Prix de clôture
        close = df_asset["close"]
        volume = df_asset["volume"]

        # 1. RSI
        df_asset["rsi"] = calculate_rsi(close, period=PARAMS["rsi_period"])

        # 2. MACD
        macd, signal, hist = calculate_macd(
            close,
            fast=PARAMS["macd_fast"],
            slow=PARAMS["macd_slow"],
            signal=PARAMS["macd_signal"],
        )
        df_asset["macd"] = macd
        df_asset["macd_signal"] = signal
        df_asset["macd_histogram"] = hist

        # 3. Bollinger Bands
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(
            close, period=PARAMS["bollinger_period"], std_dev=PARAMS["bollinger_std"]
        )
        df_asset["bb_upper"] = bb_upper
        df_asset["bb_middle"] = bb_middle
        df_asset["bb_lower"] = bb_lower
        df_asset["bb_width"] = (bb_upper - bb_lower) / bb_middle  # Normalized width
        df_asset["bb_position"] = (close - bb_lower) / (bb_upper - bb_lower)  # 0-1

        # 4. Moving Averages
        mas = calculate_moving_averages(
            close, periods=[PARAMS["ma_short"], PARAMS["ma_medium"], PARAMS["ma_long"]]
        )
        for ma_name, ma_values in mas.items():
            df_asset[ma_name] = ma_values

        # 5. MA Crossovers
        df_asset[f"ma_cross_short_medium"] = (
            df_asset[f'ma_{PARAMS["ma_short"]}'] > df_asset[f'ma_{PARAMS["ma_medium"]}']
        ).astype(int)

        # 6. Volatility
        df_asset["volatility"] = calculate_volatility(close, period=20)

        # 7. Returns
        df_asset["returns_1d"] = close.pct_change(1)
        df_asset["returns_7d"] = close.pct_change(7)
        df_asset["returns_30d"] = close.pct_change(30)

        # 8. Volume indicators
        vol_indicators = calculate_volume_indicators(
            volume, close, period=PARAMS["volume_ma"]
        )
        for vol_name, vol_values in vol_indicators.items():
            df_asset[vol_name] = vol_values

        # 9. Price momentum
        df_asset["momentum_7d"] = close - close.shift(7)
        df_asset["momentum_30d"] = close - close.shift(30)

        # 10. Distance from MAs (%)
        df_asset["dist_from_ma_short"] = (
            close / df_asset[f'ma_{PARAMS["ma_short"]}'] - 1
        ) * 100
        df_asset["dist_from_ma_medium"] = (
            close / df_asset[f'ma_{PARAMS["ma_medium"]}'] - 1
        ) * 100

        all_features.append(df_asset)

    df_features = pd.concat(all_features, ignore_index=True)

    print(
        f"   ✅ Technical indicators calculated for {len(df['asset'].unique())} assets"
    )

    return df_features


# ============================================================================
# 4. CRÉER DES FEATURES AGRÉGÉES
# ============================================================================


def create_aggregate_features(df):
    """
    Crée des features agrégées (ex: moyenne RSI de toutes les actions)

    Returns:
        DataFrame avec features agrégées
    """
    print("\n🔄 Creating aggregate features...")

    # Séparer crypto et stocks
    df_crypto = df[df["asset_type"] == "crypto"]
    df_stocks = df[df["asset_type"] == "stock"]

    # Features agrégées par jour
    agg_features = []

    for date in tqdm(df["date"].unique(), desc="   Aggregating by date"):
        date_crypto = df_crypto[df_crypto["date"] == date]
        date_stocks = df_stocks[df_stocks["date"] == date]

        features = {
            "date": date,
            # Crypto aggregates
            "crypto_avg_rsi": date_crypto["rsi"].mean(),
            "crypto_avg_returns_1d": date_crypto["returns_1d"].mean(),
            "crypto_avg_volatility": date_crypto["volatility"].mean(),
            # Stock aggregates
            "stocks_avg_rsi": date_stocks["rsi"].mean(),
            "stocks_avg_returns_1d": date_stocks["returns_1d"].mean(),
            "stocks_avg_volatility": date_stocks["volatility"].mean(),
            # Market breadth
            "crypto_positive_returns": (date_crypto["returns_1d"] > 0).sum(),
            "stocks_positive_returns": (date_stocks["returns_1d"] > 0).sum(),
        }

        agg_features.append(features)

    df_agg = pd.DataFrame(agg_features)

    print(f"   ✅ Aggregate features created for {len(df_agg)} days")

    return df_agg


# ============================================================================
# 5. MAIN FUNCTION
# ============================================================================


def main():
    """Fonction principale"""
    print("=" * 80)
    print("📈 TECHNICAL INDICATORS CALCULATION")
    print("=" * 80)

    # 1. Charger les données
    df = load_price_data()

    # 2. Calculer les indicateurs techniques
    df_features = calculate_technical_features(df)

    # 3. Créer features agrégées
    df_agg = create_aggregate_features(df_features)

    # 4. Sauvegarder
    output_file = PROCESSED_DIR / "technical_features.csv"
    df_features.to_csv(output_file, index=False)
    print(f"\n💾 Saved: {output_file}")

    agg_file = PROCESSED_DIR / "technical_aggregates.csv"
    df_agg.to_csv(agg_file, index=False)
    print(f"💾 Saved: {agg_file}")

    # 5. Résumé
    print("\n" + "=" * 80)
    print("📊 TECHNICAL INDICATORS SUMMARY")
    print("=" * 80)
    print(f"Total data points:          {len(df_features)}")
    print(f"Assets processed:           {df_features['asset'].nunique()}")
    print(
        f"Date range:                 {df_features['date'].min().date()} to {df_features['date'].max().date()}"
    )
    print(
        f"\nFeatures created per asset: {len([col for col in df_features.columns if col not in ['date', 'asset', 'asset_type', 'open', 'high', 'low', 'close', 'volume']])}"
    )
    print(f"Aggregate features:         {len(df_agg)} days")
    print("=" * 80)

    # Sample de quelques features
    print("\n📋 Sample technical features:")
    sample_cols = ["date", "asset", "close", "rsi", "macd", "volatility", "returns_1d"]
    print(df_features[sample_cols].tail(5))

    print("\n✅ Technical indicators calculation complete!")
    print(f"📁 Output files in: {PROCESSED_DIR}")

    return df_features, df_agg


if __name__ == "__main__":
    # Créer le dossier processed s'il n'existe pas
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Lancer le calcul
    main()
