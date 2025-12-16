"""
ÉTAPE 2.3 : FEATURE ENGINEERING
Combine sentiment + technical indicators et crée le dataset final pour ML

Entrée :
    - data/processed/sentiment_scores.csv
    - data/processed/market_sentiment.csv
    - data/processed/technical_features.csv
Sortie :
    - data/processed/features_final.csv (prêt pour training!)

Usage:
    python feature_engineering.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
import warnings

warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"

# Forward returns à prédire (jours dans le futur)
FORWARD_PERIODS = [3, 7, 14]  # Prédire returns à 3j, 7j et 14j

# Paramètres de features
SENTIMENT_LAG_DAYS = 7  # Utiliser le sentiment des 7 derniers jours


# ============================================================================
# 1. CHARGER TOUTES LES DONNÉES
# ============================================================================


def load_all_data():
    """Charge toutes les données processed"""
    print("\n📂 Loading processed data...")

    data = {}

    # Sentiment des articles
    sentiment_file = PROCESSED_DIR / "sentiment_scores.csv"
    if sentiment_file.exists():
        data["sentiment"] = pd.read_csv(sentiment_file)
        data["sentiment"]["date"] = pd.to_datetime(data["sentiment"]["date"])
        print(f"   ✅ Sentiment: {len(data['sentiment'])} articles")
    else:
        print(f"   ⚠️  Sentiment file not found")
        data["sentiment"] = None

    # Market sentiment agrégé
    market_file = PROCESSED_DIR / "market_sentiment.csv"
    if market_file.exists():
        data["market_sentiment"] = pd.read_csv(market_file)
        data["market_sentiment"]["date"] = pd.to_datetime(
            data["market_sentiment"]["date"]
        )
        print(f"   ✅ Market sentiment: {len(data['market_sentiment'])} days")
    else:
        print(f"   ⚠️  Market sentiment file not found")
        data["market_sentiment"] = None

    # Google Trends
    RAW_DIR = DATA_DIR / "raw"
    trends_file = RAW_DIR / "google_trends.csv"
    if trends_file.exists():
        data["google_trends"] = pd.read_csv(trends_file)
        data["google_trends"]["date"] = pd.to_datetime(data["google_trends"]["date"])
        print(
            f"   ✅ Google Trends: {len(data['google_trends'])} rows, {data['google_trends']['asset'].nunique()} assets"
        )
    else:
        print(f"   ⚠️  Google Trends file not found")
        data["google_trends"] = None

    # Technical features
    technical_file = PROCESSED_DIR / "technical_features.csv"
    if not technical_file.exists():
        raise FileNotFoundError(f"Technical features not found: {technical_file}")

    data["technical"] = pd.read_csv(technical_file)
    data["technical"]["date"] = pd.to_datetime(data["technical"]["date"])
    print(
        f"   ✅ Technical: {len(data['technical'])} rows, {data['technical']['asset'].nunique()} assets"
    )

    return data


# ============================================================================
# 2. CRÉER LES TARGETS (FORWARD RETURNS)
# ============================================================================


def create_targets(df, forward_periods=[3, 7]):
    """
    Crée les variables target (returns futurs)

    Args:
        df: DataFrame avec colonnes ['date', 'asset', 'close']
        forward_periods: Liste des périodes forward (en jours)

    Returns:
        DataFrame avec colonnes target_return_Xd
    """
    print("\n🎯 Creating target variables (forward returns)...")

    df_with_targets = df.copy()

    for period in forward_periods:
        # Pour chaque asset, calculer le return futur
        df_with_targets[f"target_return_{period}d"] = df_with_targets.groupby("asset")[
            "close"
        ].transform(
            lambda x: x.pct_change(periods=-period)  # Negative = look forward
        )

        # Créer variable binaire avec seuil significatif (éviter le bruit autour de 0)
        # Pour 14j: >3% = UP, <-3% = DOWN, entre = neutral (exclu)
        threshold = 0.03 if period >= 14 else 0.02 if period >= 7 else 0.015
        df_with_targets[f"target_direction_{period}d"] = (
            df_with_targets[f"target_return_{period}d"] > threshold
        ).astype(int)
        df_with_targets[f"target_direction_{period}d"][
            df_with_targets[f"target_return_{period}d"] < -threshold
        ] = 0

    # Statistiques
    for period in forward_periods:
        valid_count = df_with_targets[f"target_return_{period}d"].notna().sum()
        positive_pct = (
            (df_with_targets[f"target_direction_{period}d"] == 1).sum()
            / valid_count
            * 100
        )
        print(
            f"   {period}d forward: {valid_count} valid samples, {positive_pct:.1f}% positive"
        )

    return df_with_targets


# ============================================================================
# 3. MERGER SENTIMENT AVEC TECHNICAL
# ============================================================================


def merge_sentiment_features(df_technical, df_market_sentiment, sentiment_lag_days=7):
    """
    Merge les features de sentiment avec les features techniques

    Args:
        df_technical: DataFrame avec features techniques
        df_market_sentiment: DataFrame avec sentiment agrégé par jour
        sentiment_lag_days: Nombre de jours de lag pour le sentiment

    Returns:
        DataFrame combiné
    """
    print("\n🔄 Merging sentiment with technical features...")

    if df_market_sentiment is None:
        print("   ⚠️  No sentiment data to merge")
        return df_technical

    df_merged = df_technical.copy()

    # Pour chaque ligne (date + asset), trouver le sentiment des N derniers jours
    sentiment_features = []

    for idx, row in df_merged.iterrows():
        date = row["date"]

        # Sentiment des N derniers jours
        sentiment_window = df_market_sentiment[
            (df_market_sentiment["date"] >= (date - timedelta(days=sentiment_lag_days)))
            & (df_market_sentiment["date"] <= date)
        ]

        if len(sentiment_window) > 0:
            features = {
                "sentiment_mean_7d": sentiment_window["sentiment_mean"].mean(),
                "sentiment_std_7d": sentiment_window["sentiment_std"].mean(),
                "sentiment_trend_7d": (
                    sentiment_window["sentiment_mean"].iloc[-1]
                    - sentiment_window["sentiment_mean"].iloc[0]
                    if len(sentiment_window) > 1
                    else 0
                ),
                "stress_index_7d": sentiment_window["stress_index"].mean(),
            }
        else:
            # Pas de sentiment disponible pour cette date
            features = {
                "sentiment_mean_7d": 0,
                "sentiment_std_7d": 0,
                "sentiment_trend_7d": 0,
                "stress_index_7d": 0,
            }

        sentiment_features.append(features)

    sentiment_df = pd.DataFrame(sentiment_features)
    df_merged = pd.concat([df_merged, sentiment_df], axis=1)

    print(f"   ✅ Sentiment features merged: {len(sentiment_df.columns)} new columns")

    return df_merged


def merge_google_trends(df_technical, df_trends, trend_lag_days=7):
    """
    Merge Google Trends data with technical features

    Args:
        df_technical: DataFrame with technical features
        df_trends: DataFrame with Google Trends data
        trend_lag_days: Number of days to look back for trends

    Returns:
        DataFrame combined
    """
    print("\n🔍 Merging Google Trends with technical features...")

    if df_trends is None:
        print("   ⚠️  No Google Trends data to merge")
        return df_technical

    df_merged = df_technical.copy()

    # For each row (date + asset), find the trends over last N days
    trends_features = []

    for idx, row in df_merged.iterrows():
        date = row["date"]
        asset = row["asset"]

        # Get trends for this asset over last N days
        trends_window = df_trends[
            (df_trends["asset"] == asset)
            & (df_trends["date"] >= (date - timedelta(days=trend_lag_days)))
            & (df_trends["date"] <= date)
        ]

        if len(trends_window) > 0:
            features = {
                "trends_interest_mean_7d": trends_window["interest"].mean(),
                "trends_interest_max_7d": trends_window["interest"].max(),
                "trends_interest_min_7d": trends_window["interest"].min(),
                "trends_interest_std_7d": trends_window["interest"].std(),
                "trends_interest_trend_7d": (
                    trends_window["interest"].iloc[-1]
                    - trends_window["interest"].iloc[0]
                    if len(trends_window) > 1
                    else 0
                ),
                "trends_interest_current": (
                    trends_window["interest"].iloc[-1] if len(trends_window) > 0 else 50
                ),
            }
        else:
            # No trends data for this date/asset
            features = {
                "trends_interest_mean_7d": 50,  # Neutral
                "trends_interest_max_7d": 50,
                "trends_interest_min_7d": 50,
                "trends_interest_std_7d": 0,
                "trends_interest_trend_7d": 0,
                "trends_interest_current": 50,
            }

        trends_features.append(features)

    trends_df = pd.DataFrame(trends_features)
    df_merged = pd.concat([df_merged, trends_df], axis=1)

    print(f"   ✅ Google Trends features merged: {len(trends_df.columns)} new columns")

    return df_merged


# ============================================================================
# 4. FEATURE SELECTION & ENGINEERING
# ============================================================================


def engineer_additional_features(df):
    """
    Crée des features additionnelles par combinaison

    Returns:
        DataFrame avec features additionnelles
    """
    print("\n⚙️  Engineering additional features...")

    df_eng = df.copy()

    # 1. Interaction features (sentiment × technical)
    if "sentiment_mean_7d" in df_eng.columns:
        df_eng["sentiment_rsi_interaction"] = (
            df_eng["sentiment_mean_7d"] * df_eng["rsi"]
        )
        df_eng["sentiment_volatility_interaction"] = (
            df_eng["sentiment_mean_7d"] * df_eng["volatility"]
        )

    # 1b. Google Trends interaction features
    if "trends_interest_mean_7d" in df_eng.columns:
        df_eng["trends_rsi_interaction"] = (
            df_eng["trends_interest_mean_7d"] / 100
        ) * df_eng["rsi"]
        df_eng["trends_volatility_interaction"] = (
            df_eng["trends_interest_mean_7d"] / 100
        ) * df_eng["volatility"]
        df_eng["trends_momentum_interaction"] = (
            df_eng["trends_interest_trend_7d"] * df_eng["returns_7d"]
        )
        # High interest + positive sentiment = bullish
        if "sentiment_mean_7d" in df_eng.columns:
            df_eng["trends_sentiment_combined"] = (
                df_eng["trends_interest_mean_7d"] / 100
            ) * df_eng["sentiment_mean_7d"]
        # Interest spike detection
        df_eng["trends_spike"] = (
            df_eng["trends_interest_current"] > df_eng["trends_interest_mean_7d"] * 1.5
        ).astype(int)

    # 2. Momentum patterns (multi-timeframe)
    grouped = df_eng.groupby("asset")
    df_eng["momentum_3d"] = grouped["close"].transform(lambda x: x.pct_change(3))
    df_eng["momentum_14d"] = grouped["close"].transform(lambda x: x.pct_change(14))
    df_eng["momentum_21d"] = grouped["close"].transform(lambda x: x.pct_change(21))

    # 3. Volatility features (rolling)
    df_eng["volatility_7d"] = grouped["returns_1d"].transform(
        lambda x: x.rolling(7, min_periods=1).std()
    )
    df_eng["volatility_30d"] = grouped["returns_1d"].transform(
        lambda x: x.rolling(30, min_periods=1).std()
    )
    df_eng["volatility_regime"] = (
        df_eng["volatility_7d"] > df_eng["volatility_30d"]
    ).astype(int)

    # 4. Price momentum vs MA
    df_eng["price_to_ma7"] = (df_eng["close"] - df_eng["ma_7"]) / (
        df_eng["ma_7"] + 1e-8
    )
    df_eng["price_to_ma30"] = (df_eng["close"] - df_eng["ma_30"]) / (
        df_eng["ma_30"] + 1e-8
    )

    # 5. RSI momentum
    df_eng["rsi_change_3d"] = grouped["rsi"].transform(lambda x: x.diff(3))
    df_eng["rsi_ma"] = grouped["rsi"].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
    )

    # 6. Volume patterns
    df_eng["volume_surge"] = (df_eng["volume_ratio"] > 1.5).astype(int)
    df_eng["volume_trend"] = grouped["volume"].transform(
        lambda x: x.rolling(7, min_periods=1).mean()
        / x.rolling(30, min_periods=1).mean()
    )

    # 7. Trend consistency
    df_eng["returns_positive"] = (df_eng["returns_1d"] > 0).astype(int)
    df_eng["trend_days_7d"] = grouped["returns_positive"].transform(
        lambda x: x.rolling(7, min_periods=1).sum()
    )

    # 8. Relative performance (vs asset type average)
    df_eng["return_7d_relative"] = df_eng["returns_7d"] - df_eng.groupby(
        ["date", "asset_type"]
    )["returns_7d"].transform("mean")

    # 9. Ratio features
    df_eng["volume_to_volatility"] = df_eng["volume_ratio"] / (
        df_eng["volatility"] + 0.001
    )

    # 10. Trend strength
    df_eng["trend_strength"] = abs(df_eng["returns_7d"]) * (
        1 / (df_eng["volatility"] + 0.001)
    )

    # 4. EXTREME RSI conditions (strong predictors of reversals)
    df_eng["rsi_extreme_oversold"] = (df_eng["rsi"] < 25).astype(int)
    df_eng["rsi_extreme_overbought"] = (df_eng["rsi"] > 75).astype(int)
    df_eng["rsi_recovery"] = (
        (df_eng["rsi"] > 30) & (grouped["rsi"].shift(1) < 30)
    ).astype(int)
    df_eng["rsi_breakdown"] = (
        (df_eng["rsi"] < 70) & (grouped["rsi"].shift(1) > 70)
    ).astype(int)

    # 5. VOLUME SPIKES (often predict big moves)
    df_eng["volume_spike_2x"] = (df_eng["volume_ratio"] > 2.0).astype(int)
    df_eng["volume_spike_3x"] = (df_eng["volume_ratio"] > 3.0).astype(int)
    df_eng["volume_with_price_up"] = (
        (df_eng["volume_ratio"] > 1.5) & (df_eng["returns_1d"] > 0)
    ).astype(int)
    df_eng["volume_with_price_down"] = (
        (df_eng["volume_ratio"] > 1.5) & (df_eng["returns_1d"] < 0)
    ).astype(int)

    # 6. BOLLINGER BREAKOUTS (predict trend continuation)
    df_eng["bb_lower_touch"] = (df_eng["bb_position"] < 0.1).astype(int)
    df_eng["bb_upper_touch"] = (df_eng["bb_position"] > 0.9).astype(int)
    df_eng["bb_squeeze_extreme"] = (
        df_eng["bb_width"] < df_eng["bb_width"].rolling(20, min_periods=1).quantile(0.2)
    ).astype(int)

    # 7. SENTIMENT EXTREMES (strong contrarian signals)
    if "sentiment_mean_7d" in df_eng.columns:
        sentiment_high = df_eng["sentiment_mean_7d"] > df_eng[
            "sentiment_mean_7d"
        ].quantile(0.8)
        sentiment_low = df_eng["sentiment_mean_7d"] < df_eng[
            "sentiment_mean_7d"
        ].quantile(0.2)
        df_eng["sentiment_extreme_positive"] = sentiment_high.astype(int)
        df_eng["sentiment_extreme_negative"] = sentiment_low.astype(int)
        df_eng["sentiment_stress_high"] = (
            df_eng["stress_index_7d"] > df_eng["stress_index_7d"].quantile(0.8)
        ).astype(int)

    # 8. LAGGED FEATURES (yesterday predicts tomorrow)
    df_eng["returns_1d_lag1"] = grouped["returns_1d"].shift(1)
    df_eng["returns_1d_lag2"] = grouped["returns_1d"].shift(2)
    df_eng["returns_1d_lag3"] = grouped["returns_1d"].shift(3)
    df_eng["volatility_lag1"] = grouped["volatility"].shift(1)
    df_eng["rsi_lag1"] = grouped["rsi"].shift(1)

    # 9. MOMENTUM DIVERGENCE (price up but momentum down = reversal)
    df_eng["momentum_divergence"] = (
        (df_eng["returns_7d"] > 0) & (df_eng["momentum_7d"] < 0)
    ).astype(int)

    # 10. COMBINED SIGNALS (multiple confirmations)
    df_eng["bullish_confluence"] = (
        (df_eng["rsi"] < 35)
        & (df_eng["bb_position"] < 0.2)
        & (df_eng["returns_7d"] < -0.05)
    ).astype(int)

    df_eng["bearish_confluence"] = (
        (df_eng["rsi"] > 65)
        & (df_eng["bb_position"] > 0.8)
        & (df_eng["returns_7d"] > 0.05)
    ).astype(int)

    # 11. Momentum score
    df_eng["momentum_score"] = (
        (df_eng["rsi"] > 50).astype(int)
        + (df_eng["macd"] > 0).astype(int)
        + (df_eng["ma_cross_short_medium"] == 1).astype(int)
    ) / 3

    # 12. Market position (overbought/oversold)
    df_eng["market_position"] = pd.cut(
        df_eng["rsi"],
        bins=[0, 30, 70, 100],
        labels=["oversold", "neutral", "overbought"],
    )
    df_eng["is_oversold"] = (df_eng["market_position"] == "oversold").astype(int)
    df_eng["is_overbought"] = (df_eng["market_position"] == "overbought").astype(int)

    new_count = len([c for c in df_eng.columns if c not in df.columns])
    print(
        f"   ✅ Created {new_count} additional features (total features: {len([c for c in df_eng.columns if c not in ['date', 'asset', 'asset_type', 'open', 'high', 'low', 'close', 'volume'] and not c.startswith('target_')])})"
    )

    return df_eng


# ============================================================================
# 5. NETTOYER & FINALISER
# ============================================================================


def finalize_dataset(df):
    """
    Nettoie et prépare le dataset final

    Returns:
        DataFrame final prêt pour ML
    """
    print("\n🧹 Finalizing dataset...")

    df_final = df.copy()

    # 1. Supprimer les lignes avec targets manquants (derniers jours)
    target_cols = [col for col in df_final.columns if col.startswith("target_")]
    df_final = df_final.dropna(subset=target_cols)

    print(f"   Rows after removing missing targets: {len(df_final)}")

    # 2. Supprimer les lignes avec trop de NaN dans les features
    feature_cols = [
        col
        for col in df_final.columns
        if col
        not in [
            "date",
            "asset",
            "asset_type",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "market_position",
        ]
        and not col.startswith("target_")
    ]

    # Remplir les NaN avec forward/backward fill par asset
    for asset in df_final["asset"].unique():
        mask = df_final["asset"] == asset
        df_final.loc[mask, feature_cols] = (
            df_final.loc[mask, feature_cols]
            .fillna(method="ffill")
            .fillna(method="bfill")
        )

    # Supprimer les lignes avec encore des NaN
    before_dropna = len(df_final)
    df_final = df_final.dropna(subset=feature_cols)
    print(
        f"   Rows after removing NaN features: {len(df_final)} (dropped {before_dropna - len(df_final)})"
    )

    # 3. Réorganiser les colonnes
    meta_cols = ["date", "asset", "asset_type"]
    price_cols = ["open", "high", "low", "close", "volume"]

    # Colonnes dans l'ordre : meta, price, features, targets
    ordered_cols = (
        meta_cols
        + price_cols
        + [c for c in df_final.columns if c not in meta_cols + price_cols + target_cols]
        + target_cols
    )

    df_final = df_final[ordered_cols]

    # 4. Trier par asset et date
    df_final = df_final.sort_values(["asset", "date"]).reset_index(drop=True)

    print(
        f"   ✅ Final dataset: {len(df_final)} rows × {len(df_final.columns)} columns"
    )

    return df_final


# ============================================================================
# 6. STATISTIQUES & VALIDATION
# ============================================================================


def print_dataset_statistics(df):
    """Affiche des statistiques sur le dataset final"""
    print("\n" + "=" * 80)
    print("📊 DATASET STATISTICS")
    print("=" * 80)

    print(f"\n📏 Shape: {df.shape[0]} rows × {df.shape[1]} columns")

    print(f"\n📅 Date range:")
    print(f"   Start: {df['date'].min().date()}")
    print(f"   End:   {df['date'].max().date()}")
    print(f"   Days:  {(df['date'].max() - df['date'].min()).days}")

    print(f"\n💼 Assets:")
    for asset_type in df["asset_type"].unique():
        count = df[df["asset_type"] == asset_type]["asset"].nunique()
        rows = len(df[df["asset_type"] == asset_type])
        print(f"   {asset_type}: {count} assets, {rows} rows")

    print(f"\n📈 Features:")
    feature_cols = [
        col
        for col in df.columns
        if col
        not in ["date", "asset", "asset_type", "open", "high", "low", "close", "volume"]
        and not col.startswith("target_")
    ]
    print(f"   Total features: {len(feature_cols)}")
    print(
        f"   Technical: {len([c for c in feature_cols if any(x in c for x in ['rsi', 'macd', 'ma_', 'bb_', 'volatility'])])}"
    )
    print(
        f"   Sentiment: {len([c for c in feature_cols if 'sentiment' in c or 'stress' in c])}"
    )
    print(f"   Google Trends: {len([c for c in feature_cols if 'trends' in c])}")
    print(
        f"   Engineered: {len([c for c in feature_cols if any(x in c for x in ['interaction', 'score', 'strength'])])}"
    )

    print(f"\n🎯 Targets:")
    target_cols = [col for col in df.columns if col.startswith("target_")]
    for target_col in target_cols:
        if "direction" in target_col:
            positive_pct = (df[target_col] == 1).sum() / len(df) * 100
            print(f"   {target_col}: {positive_pct:.1f}% positive")
        else:
            print(
                f"   {target_col}: mean={df[target_col].mean():.4f}, std={df[target_col].std():.4f}"
            )

    print(f"\n✅ Missing values: {df.isnull().sum().sum()} total")

    print("=" * 80)


# ============================================================================
# 7. MAIN FUNCTION
# ============================================================================


def main():
    """Fonction principale"""
    print("=" * 80)
    print("⚙️  FEATURE ENGINEERING - Final Dataset Creation")
    print("=" * 80)

    # 1. Charger toutes les données
    data = load_all_data()

    # 2. Créer les targets
    df_with_targets = create_targets(data["technical"], forward_periods=FORWARD_PERIODS)

    # 3. Merger avec sentiment
    df_merged = merge_sentiment_features(
        df_with_targets, data["market_sentiment"], sentiment_lag_days=SENTIMENT_LAG_DAYS
    )

    # 3b. Merger avec Google Trends
    df_merged = merge_google_trends(
        df_merged, data["google_trends"], trend_lag_days=SENTIMENT_LAG_DAYS
    )

    # 4. Engineer additional features
    df_engineered = engineer_additional_features(df_merged)

    # 5. Finaliser le dataset
    df_final = finalize_dataset(df_engineered)

    # 6. Sauvegarder
    output_file = PROCESSED_DIR / "features_final.csv"
    df_final.to_csv(output_file, index=False)
    print(f"\n💾 Saved: {output_file}")

    # 7. Statistiques
    print_dataset_statistics(df_final)

    # 8. Créer un sample pour inspection
    sample_file = PROCESSED_DIR / "features_sample.csv"
    df_final.head(100).to_csv(sample_file, index=False)
    print(f"\n💾 Saved sample: {sample_file}")

    print("\n✅ Feature engineering complete!")
    print(f"📁 Output files in: {PROCESSED_DIR}")
    print(f"\n🎯 Next step: Model training (Étape 3)")

    return df_final


if __name__ == "__main__":
    # Lancer le feature engineering
    main()
