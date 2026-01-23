
from __future__ import annotations
from dataclasses import dataclass, is_dataclass, asdict
from typing import Generic, List, Optional, TypeVar, Iterable, Any
from collections import deque
import sqlite3
import json
import time
import os

T = TypeVar("T")

class RingBuffer(Generic[T]):
    """
    Fixed-size ring buffer. Stores latest N items.
    """
    def __init__(self, maxlen: int):
        self._dq = deque(maxlen=maxlen)

    def append(self, item: T) -> None:
        self._dq.append(item)

    def snapshot(self) -> List[T]:
        return list(self._dq)

    def last(self) -> Optional[T]:
        return self._dq[-1] if self._dq else None

    def __len__(self) -> int:
        return len(self._dq)

class SQLiteRingBuffer(Generic[T]):
    """
    Persistent Ring Buffer using SQLite.
    Stores up to `maxlen` items, strictly ordered by timestamp.
    Handles Dataclasses by converting to dict before JSON serialization.
    """
    def __init__(self, db_path: str, table_name: str, maxlen: int, item_class: Any = None):
        self.db_path = db_path
        self.table_name = table_name
        self.maxlen = maxlen
        self.item_class = item_class # Optional: to reconstruct dataclass on load
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL,
                    data TEXT
                )
            """)
            conn.commit()

    def _serialize(self, item: T) -> str:
        if is_dataclass(item):
            return json.dumps(asdict(item))
        if isinstance(item, dict):
            return json.dumps(item)
        return str(item) # Fallback

    def _deserialize(self, data_str: str) -> T:
        try:
            d = json.loads(data_str)
            if self.item_class and is_dataclass(self.item_class) and isinstance(d, dict):
                return self.item_class(**d)
            return d
        except:
            return data_str

    def append(self, item: T, timestamp: float = None) -> None:
        if timestamp is None:
            # Try to extract ts from item if it has it
            timestamp = getattr(item, 'ts', time.time())
            if not isinstance(timestamp, (int, float)):
                 timestamp = time.time()
            
        data_str = self._serialize(item)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert
            cursor.execute(f"INSERT INTO {self.table_name} (ts, data) VALUES (?, ?)", (timestamp, data_str))
            
            # Prune
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            count = cursor.fetchone()[0]
            
            if count > self.maxlen:
                diff = count - self.maxlen
                cursor.execute(f"""
                    DELETE FROM {self.table_name} 
                    WHERE id IN (
                        SELECT id FROM {self.table_name} ORDER BY id ASC LIMIT ?
                    )
                """, (diff,))
            conn.commit()

    def snapshot(self) -> List[T]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT data FROM {self.table_name} ORDER BY id ASC")
            rows = cursor.fetchall()
            return [self._deserialize(r[0]) for r in rows]

    def last(self) -> Optional[T]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT data FROM {self.table_name} ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            return self._deserialize(row[0]) if row else None

    def __len__(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            return cursor.fetchone()[0]
