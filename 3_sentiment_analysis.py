"""
ÉTAPE 2.1 : SENTIMENT ANALYSIS
Analyse le sentiment des articles L'Agefi avec CamemBERT

Entrée : data/raw/agefi_rss.csv ou data/raw/agefi_articles.jsonl
Sortie : data/processed/sentiment_scores.csv

Usage:
    python sentiment_analysis.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from transformers import pipeline
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

# ============================================================================
# CONFIGURATION
# ============================================================================

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Assets à détecter dans les articles
ASSETS = {
    "BTC": ["bitcoin", "btc", "crypto", "cryptomonnaie"],
    "ETH": ["ethereum", "eth", "ether"],
    "MC.PA": ["lvmh", "louis vuitton", "luxe"],
    "RMS.PA": ["hermès", "hermes"],
    "TTE.PA": ["totalenergies", "total", "énergie", "pétrole"],
    "ENGI.PA": ["engie", "gaz", "électricité"],
    "BNP.PA": ["bnp", "bnp paribas", "banque"],
    "GLE.PA": ["société générale", "socgen", "societe generale"],
    "CAP.PA": ["capgemini", "tech", "technologie"],
    "SU.PA": ["schneider", "schneider electric", "industrie"],
}

# Keywords pour détecter le sentiment du marché
POSITIVE_KEYWORDS = [
    "hausse",
    "progression",
    "rebond",
    "optimisme",
    "croissance",
    "record",
    "succès",
    "performance",
    "dynamique",
    "confiance",
]

NEGATIVE_KEYWORDS = [
    "baisse",
    "chute",
    "recul",
    "inquiétude",
    "crise",
    "correction",
    "volatilité",
    "incertitude",
    "panique",
    "ralentissement",
]


# ============================================================================
# 1. CHARGER LES DONNÉES
# ============================================================================


def load_agefi_articles():
    """Charge les articles L'Agefi depuis CSV ou JSONL"""
    print("\n📂 Loading L'Agefi articles...")

    # Try JSONL first (new format with more articles)
    # Check for any JSONL file in raw directory
    jsonl_files = list(RAW_DIR.glob("*.jsonl"))
    jsonl_path = jsonl_files[0] if jsonl_files else None
    csv_path = RAW_DIR / "agefi_rss.csv"

    if jsonl_path and jsonl_path.exists():
        print(f"   Loading from JSONL: {jsonl_path}")
        import json

        articles = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    articles.append(
                        {
                            "date": data.get("datePublished")
                            or data.get("date")
                            or data.get("published"),
                            "title": data.get("headline") or data.get("title", ""),
                            "description": data.get("combined_content")
                            or data.get("articleBodyRendered")
                            or data.get("description")
                            or data.get("summary", ""),
                            "link": data.get("url") or data.get("link", ""),
                            "category": data.get("category", ""),
                        }
                    )
                except Exception as e:
                    continue
        df = pd.DataFrame(articles)
    elif csv_path.exists():
        print(f"   Loading from CSV: {csv_path}")
        df = pd.read_csv(csv_path)
    else:
        raise FileNotFoundError(
            f"No data found. Need either {jsonl_path} or {csv_path}"
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    print(f"✅ Loaded {len(df)} articles")
    print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")

    return df


# ============================================================================
# 2. SENTIMENT ANALYSIS
# ============================================================================


def analyze_sentiment_simple(text):
    """
    Analyse de sentiment simple basée sur keywords
    (Fallback si CamemBERT trop lent)

    Returns:
        float: Score entre -1 (négatif) et 1 (positif)
    """
    text_lower = text.lower()

    positive_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
    negative_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)

    total = positive_count + negative_count
    if total == 0:
        return 0.0

    return (positive_count - negative_count) / total


def analyze_sentiment_transformer(df, use_transformer=True):
    """
    Analyse de sentiment avec transformers (CamemBERT)
    ou fallback sur keywords

    Args:
        df: DataFrame avec colonnes ['title', 'description']
        use_transformer: Si False, utilise keywords seulement

    Returns:
        DataFrame avec colonnes ['sentiment_score', 'sentiment_label']
    """
    print("\n🧠 Analyzing sentiment...")

    # Combiner titre + description
    df["full_text"] = df["title"].fillna("") + " " + df["description"].fillna("")

    if use_transformer:
        try:
            print("   Loading CamemBERT model (French sentiment)...")
            # Modèle optimisé pour le français
            sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                device=-1,  # CPU
            )

            print("   Analyzing articles with transformer...")
            sentiments = []

            for text in tqdm(df["full_text"], desc="   Processing"):
                try:
                    # Tronquer à 512 tokens max
                    text_truncated = text[:512]
                    result = sentiment_analyzer(text_truncated)[0]

                    # Convertir les étoiles (1-5) en score (-1 à 1)
                    # 1 star = -1, 3 stars = 0, 5 stars = 1
                    stars = int(result["label"].split()[0])
                    score = (stars - 3) / 2  # Map 1-5 to -1 to 1

                    sentiments.append(
                        {
                            "sentiment_score": score,
                            "sentiment_label": (
                                "positive"
                                if score > 0.2
                                else "negative" if score < -0.2 else "neutral"
                            ),
                            "confidence": result["score"],
                        }
                    )
                except:
                    # Fallback sur keywords
                    score = analyze_sentiment_simple(text)
                    sentiments.append(
                        {
                            "sentiment_score": score,
                            "sentiment_label": (
                                "positive"
                                if score > 0.2
                                else "negative" if score < -0.2 else "neutral"
                            ),
                            "confidence": 0.5,
                        }
                    )

            sentiment_df = pd.DataFrame(sentiments)
            print("   ✅ Sentiment analysis complete (transformer)")

        except Exception as e:
            print(f"   ⚠️  Transformer failed: {e}")
            print("   Falling back to keyword-based sentiment...")
            use_transformer = False

    if not use_transformer:
        print("   Using keyword-based sentiment analysis...")
        sentiments = []

        for text in tqdm(df["full_text"], desc="   Processing"):
            score = analyze_sentiment_simple(text)
            sentiments.append(
                {
                    "sentiment_score": score,
                    "sentiment_label": (
                        "positive"
                        if score > 0.2
                        else "negative" if score < -0.2 else "neutral"
                    ),
                    "confidence": 0.6,
                }
            )

        sentiment_df = pd.DataFrame(sentiments)
        print("   ✅ Sentiment analysis complete (keywords)")

    return sentiment_df


# ============================================================================
# 3. DÉTECTION D'ASSETS
# ============================================================================


def detect_asset_mentions(df):
    """
    Détecte quels assets sont mentionnés dans chaque article

    Returns:
        DataFrame avec une colonne par asset (0/1)
    """
    print("\n🔍 Detecting asset mentions...")

    df["full_text_lower"] = df["full_text"].str.lower()

    asset_mentions = {}

    for asset, keywords in ASSETS.items():
        mentions = df["full_text_lower"].apply(
            lambda text: int(any(kw in text for kw in keywords))
        )
        asset_mentions[f"mentions_{asset}"] = mentions

    mentions_df = pd.DataFrame(asset_mentions)

    # Stats
    total_mentions = mentions_df.sum()
    print(f"   Asset mentions found:")
    for col in mentions_df.columns:
        asset = col.replace("mentions_", "")
        count = total_mentions[col]
        if count > 0:
            print(f"     {asset}: {count} articles")

    return mentions_df


# ============================================================================
# 4. MARKET SENTIMENT INDEX
# ============================================================================


def calculate_market_sentiment(df, sentiment_df):
    """
    Calcule un indice de sentiment global du marché par jour

    Returns:
        DataFrame avec [date, market_sentiment, stress_index]
    """
    print("\n📊 Calculating market sentiment index...")

    # Ajouter le sentiment au df principal
    df_with_sentiment = pd.concat([df, sentiment_df], axis=1)

    # Agréger par jour
    daily_sentiment = (
        df_with_sentiment.groupby(df_with_sentiment["date"].dt.date)
        .agg(
            {
                "sentiment_score": ["mean", "std", "min", "max"],
                "sentiment_label": lambda x: (x == "positive").sum()
                - (x == "negative").sum(),
            }
        )
        .reset_index()
    )

    daily_sentiment.columns = [
        "date",
        "sentiment_mean",
        "sentiment_std",
        "sentiment_min",
        "sentiment_max",
        "sentiment_balance",
    ]

    # Calculer un stress index (volatilité du sentiment)
    daily_sentiment["stress_index"] = daily_sentiment["sentiment_std"].fillna(0) * 100

    print(f"   ✅ Market sentiment calculated for {len(daily_sentiment)} days")
    print(f"   Average sentiment: {daily_sentiment['sentiment_mean'].mean():.3f}")

    return daily_sentiment


# ============================================================================
# 5. MAIN FUNCTION
# ============================================================================


def main(use_transformer=False):
    """
    Fonction principale

    Args:
        use_transformer: Si True, utilise CamemBERT (plus lent mais meilleur)
                        Si False, utilise keywords (plus rapide)
    """
    print("=" * 80)
    print("🧠 SENTIMENT ANALYSIS - L'Agefi Articles")
    print("=" * 80)
    print(f"Mode: {'Transformer (CamemBERT)' if use_transformer else 'Keywords'}")
    print("=" * 80)

    # 1. Charger les articles
    df = load_agefi_articles()

    # 2. Analyse de sentiment
    sentiment_df = analyze_sentiment_transformer(df, use_transformer=use_transformer)

    # 3. Détection d'assets
    mentions_df = detect_asset_mentions(df)

    # 4. Combiner tout
    df_final = pd.concat(
        [
            df[["date", "title", "description", "link", "category"]],
            sentiment_df,
            mentions_df,
        ],
        axis=1,
    )

    # 5. Market sentiment index
    market_sentiment = calculate_market_sentiment(df, sentiment_df)

    # 6. Sauvegarder
    output_file = PROCESSED_DIR / "sentiment_scores.csv"
    df_final.to_csv(output_file, index=False)
    print(f"\n💾 Saved: {output_file}")

    market_file = PROCESSED_DIR / "market_sentiment.csv"
    market_sentiment.to_csv(market_file, index=False)
    print(f"💾 Saved: {market_file}")

    # 7. Résumé
    print("\n" + "=" * 80)
    print("📊 SENTIMENT ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"Total articles analyzed:    {len(df_final)}")
    print(
        f"Positive articles:          {(sentiment_df['sentiment_label'] == 'positive').sum()}"
    )
    print(
        f"Negative articles:          {(sentiment_df['sentiment_label'] == 'negative').sum()}"
    )
    print(
        f"Neutral articles:           {(sentiment_df['sentiment_label'] == 'neutral').sum()}"
    )
    print(f"\nAverage sentiment score:    {sentiment_df['sentiment_score'].mean():.3f}")
    print(f"Sentiment std deviation:    {sentiment_df['sentiment_score'].std():.3f}")
    print(f"\nMarket sentiment days:      {len(market_sentiment)}")
    print("=" * 80)

    print("\n✅ Sentiment analysis complete!")
    print(f"📁 Output files in: {PROCESSED_DIR}")

    return df_final, market_sentiment


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze sentiment of L'Agefi articles"
    )
    parser.add_argument(
        "--use-transformer",
        action="store_true",
        help="Use CamemBERT transformer (slower but more accurate)",
    )

    args = parser.parse_args()

    # Créer le dossier processed s'il n'existe pas
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Lancer l'analyse
    main(use_transformer=args.use_transformer)
