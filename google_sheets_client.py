"""
Google Sheets Client for TradeBot
Handles all interactions with Google Sheets for storing and retrieving trading data
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import os
from datetime import datetime


class GoogleSheetsClient:
    """Client for managing TradeBot data in Google Sheets"""

    def __init__(self):
        """Initialize Google Sheets client with credentials from environment"""
        # Get credentials from environment
        sheets_id = os.getenv("GOOGLE_SHEETS_ID")
        creds_json = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")

        if not sheets_id:
            raise ValueError("GOOGLE_SHEETS_ID environment variable not set")
        if not creds_json:
            raise ValueError(
                "GOOGLE_SHEETS_CREDENTIALS_JSON environment variable not set"
            )

        # Parse credentials JSON
        creds_dict = json.loads(creds_json)

        # Create credentials
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)

        # Initialize gspread client
        self.client = gspread.authorize(credentials)
        self.spreadsheet = self.client.open_by_key(sheets_id)

        print(f"✅ Connected to Google Sheets: {self.spreadsheet.title}")

    def _get_or_create_worksheet(self, name, headers=None):
        """Get existing worksheet or create new one"""
        try:
            worksheet = self.spreadsheet.worksheet(name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=name, rows=1000, cols=20)
            if headers:
                worksheet.append_row(headers)
        return worksheet

    def save_portfolio_history(self, df):
        """Save portfolio history to Google Sheets"""
        worksheet = self._get_or_create_worksheet(
            "portfolio_history",
            headers=[
                "date",
                "cash",
                "positions_value",
                "total_value",
                "return",
                "positions_count",
            ],
        )

        # Convert DataFrame to list of lists
        data = df.to_dict("records")
        rows = [
            [
                str(row["date"]),
                float(row["cash"]),
                float(row["positions_value"]),
                float(row["total_value"]),
                float(row["return"]),
                int(row["positions_count"]),
            ]
            for row in data
        ]

        # Clear existing data and append new
        worksheet.clear()
        worksheet.append_row(
            [
                "date",
                "cash",
                "positions_value",
                "total_value",
                "return",
                "positions_count",
            ]
        )
        if rows:
            worksheet.append_rows(rows)

        print(f"   ✅ Saved {len(rows)} portfolio history records")

    def save_trades(self, df):
        """Save trades to Google Sheets"""
        worksheet = self._get_or_create_worksheet(
            "trades",
            headers=[
                "asset",
                "entry_date",
                "exit_date",
                "entry_price",
                "exit_price",
                "quantity",
                "return",
                "holding_days",
                "reason",
            ],
        )

        # Convert DataFrame to list of lists
        data = df.to_dict("records")
        rows = [
            [
                str(row["asset"]),
                str(row["entry_date"]),
                str(row["exit_date"]),
                float(row["entry_price"]),
                float(row["exit_price"]),
                float(row.get("quantity", 0)),
                float(row["return"]),
                int(row["holding_days"]),
                str(row["reason"]),
            ]
            for row in data
        ]

        # Clear existing data and append new
        worksheet.clear()
        worksheet.append_row(
            [
                "asset",
                "entry_date",
                "exit_date",
                "entry_price",
                "exit_price",
                "quantity",
                "return",
                "holding_days",
                "reason",
            ]
        )
        if rows:
            worksheet.append_rows(rows)

        print(f"   ✅ Saved {len(rows)} trades")

    def save_rss_articles(self, df):
        """Save RSS articles to Google Sheets"""
        worksheet = self._get_or_create_worksheet(
            "rss_articles", headers=["date", "title", "category", "description", "link"]
        )

        # Sort by date descending (most recent first)
        df_sorted = df.sort_values("date", ascending=False)

        # Convert DataFrame to list of lists
        data = df_sorted.to_dict("records")
        rows = [
            [
                str(row["date"]),
                str(row["title"]),
                str(row.get("category", "")),
                str(row.get("description", ""))[:200],  # Limit description length
                str(row.get("link", "")),
            ]
            for row in data
        ]

        # Clear existing data and append new
        worksheet.clear()
        worksheet.append_row(["date", "title", "category", "description", "link"])
        if rows:
            worksheet.append_rows(rows)

        print(f"   ✅ Saved {len(rows)} RSS articles")

    def save_daily_summary(self, summary_dict):
        """Save daily summary metrics to Google Sheets"""
        worksheet = self._get_or_create_worksheet(
            "daily_summary",
            headers=[
                "timestamp",
                "portfolio_value",
                "total_return",
                "total_trades",
                "open_positions",
                "articles_count",
            ],
        )

        # Append new row
        row = [
            summary_dict["timestamp"],
            float(summary_dict["portfolio_value"]),
            float(summary_dict["total_return"]),
            int(summary_dict["total_trades"]),
            int(summary_dict["portfolio_open_positions"]),
            int(summary_dict.get("articles_count", 0)),
        ]

        worksheet.append_row(row)
        print(f"   ✅ Saved daily summary")

    def get_portfolio_history(self):
        """Read portfolio history from Google Sheets"""
        try:
            worksheet = self.spreadsheet.worksheet("portfolio_history")
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except:
            return pd.DataFrame()

    def get_trades(self):
        """Read trades from Google Sheets"""
        try:
            worksheet = self.spreadsheet.worksheet("trades")
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except:
            return pd.DataFrame()

    def get_rss_articles(self):
        """Read RSS articles from Google Sheets"""
        try:
            worksheet = self.spreadsheet.worksheet("rss_articles")
            data = worksheet.get_all_records()
            return pd.DataFrame(data)
        except:
            return pd.DataFrame()

    def save_open_positions(self, positions_dict, current_prices=None):
        """Save current open positions to Google Sheets

        Args:
            positions_dict: {asset: {'quantity': X, 'entry_price': Y, 'entry_date': Z}}
            current_prices: dict with current prices for each asset (optional)
        """
        worksheet = self._get_or_create_worksheet(
            "open_positions",
            headers=["asset", "quantity", "entry_price", "current_price", "entry_date"],
        )

        # Convert positions dict to list of lists
        rows = [
            [
                str(asset),
                float(data["quantity"]),
                float(data["entry_price"]),
                float(
                    current_prices.get(asset, data["entry_price"])
                    if current_prices
                    else data["entry_price"]
                ),
                str(data["entry_date"]),
            ]
            for asset, data in positions_dict.items()
        ]

        # Clear existing data and append new
        worksheet.clear()
        worksheet.append_row(
            ["asset", "quantity", "entry_price", "current_price", "entry_date"]
        )
        if rows:
            worksheet.append_rows(rows)

        print(f"   ✅ Saved {len(rows)} open positions")

    def get_open_positions(self):
        """Read open positions from Google Sheets

        Returns:
            dict: {asset: {'quantity': X, 'entry_price': Y, 'entry_date': Z, 'current_price': P}}
        """
        try:
            worksheet = self.spreadsheet.worksheet("open_positions")
            data = worksheet.get_all_records()

            # Convert to positions dict
            positions = {}
            for row in data:
                if row["asset"]:  # Skip empty rows
                    positions[row["asset"]] = {
                        "quantity": float(row["quantity"]),
                        "entry_price": float(row["entry_price"]),
                        "entry_date": pd.to_datetime(row["entry_date"]).date(),
                    }

            return positions
        except Exception as e:
            print(f"   ⚠️  No open positions found: {e}")
            return {}
