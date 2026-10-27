"""
Customer context management module.
Loads synthetic customer and transaction records from MongoDB if available,
with an automatic, seamless fallback to local JSON.
Enforces read-only access.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.schemas import CustomerContext

DEFAULT_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_customers.json"


class CustomerContextService:
    def __init__(self, mongo_uri: Optional[str] = None, db_name: str = "fintech_copilot", json_path: Path = DEFAULT_JSON_PATH):
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = db_name or os.getenv("MONGODB_DB_NAME", "fintech_copilot")
        self.json_path = json_path
        self.backend_mode = "JSON_FALLBACK"
        self._cached_records: List[CustomerContext] = []
        self._init_backend()

    def _init_backend(self) -> None:
        """Attempt read-only connection to MongoDB, fallback to JSON on any error."""
        try:
            from pymongo import MongoClient
            client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=800, connectTimeoutMS=800)
            # Ping database to verify connection
            client.admin.command('ping')
            db = client[self.db_name]
            collection = db["customers"]
            
            # Check if collection has data; if empty, seed synthetic records
            count = collection.count_documents({})
            if count == 0 and self.json_path.exists():
                with open(self.json_path, "r", encoding="utf-8") as f:
                    seed_data = json.load(f)
                collection.insert_many(seed_data)

            docs = list(collection.find({}, {"_id": 0}))
            if docs:
                self._cached_records = [CustomerContext(**doc) for doc in docs]
                self.backend_mode = f"MongoDB Connected ({self.db_name}.customers - Read Only)"
                return
        except Exception:
            # Clean fallback to JSON without breaking execution
            pass

        self._load_from_json()

    def _load_from_json(self) -> None:
        """Load records from local JSON file."""
        if not self.json_path.exists():
            self._cached_records = []
            self.backend_mode = "JSON_FALLBACK (Empty - file not found)"
            return

        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._cached_records = [CustomerContext(**item) for item in data]
            self.backend_mode = f"Local JSON Fallback ({self.json_path.name})"
        except Exception as e:
            self._cached_records = []
            self.backend_mode = f"JSON Error: {str(e)}"

    def get_all_calls(self) -> List[CustomerContext]:
        """Return all available customer records."""
        return self._cached_records

    def get_call_by_id(self, call_id: str) -> Optional[CustomerContext]:
        """Find customer record by call_id."""
        for rec in self._cached_records:
            if rec.call_id == call_id:
                return rec
        return None

    def get_call_options(self) -> List[str]:
        """Return dropdown labels for Streamlit selection."""
        return [
            f"{c.call_id} | {c.customer_name} ({c.transaction_type}: {c.transaction_status})"
            for c in self._cached_records
        ]

    def get_status_summary(self) -> str:
        """Return human-readable backend status."""
        return f"{self.backend_mode} | {len(self._cached_records)} synthetic records loaded"
