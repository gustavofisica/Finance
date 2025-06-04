import sqlite3
import datetime

class FinanceDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.user_id: int | None = None
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL
                );"""
        )
        # Ensure user_id columns exist
        for table in ("transactions", "investments"):
            cols = [row[1] for row in cur.execute(f"PRAGMA table_info({table})")]
            if "user_id" not in cols:
                cur.execute(
                    f"ALTER TABLE {table} ADD COLUMN user_id INTEGER REFERENCES users(id)"
                )
        self.conn.commit()

    def execute_query(self, query: str, params: tuple = ()):  # -> sqlite3.Cursor
        cur = self.conn.execute(query, params)
        self.conn.commit()
        return cur

    def fetch_query(self, query: str, params: tuple = ()):  # -> list[sqlite3.Row]
        cur = self.conn.execute(query, params)
        return cur.fetchall()

    def _get_or_create(self, table: str, column: str, value: str) -> int:
        row = self.fetch_query(f"SELECT id FROM {table} WHERE {column} = ?", (value,))
        if row:
            return row[0][0]
        cur = self.execute_query(f"INSERT INTO {table} ({column}) VALUES (?)", (value,))
        return cur.lastrowid

    def convert_to_brl(self, amount: float, currency: str) -> float:
        if currency == "BRL":
            return amount
        row = self.fetch_query("SELECT rate FROM exchange WHERE currency = ?", (currency,))
        rate = row[0][0] if row else 1.0
        return amount * rate

    def update_exchange_rates(self) -> None:
        rates = {"BRL": 1.0, "USD": 5.0, "EUR": 6.0, "GBP": 7.0}
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute_query("DELETE FROM exchange")
        for currency, rate in rates.items():
            self.execute_query(
                "INSERT INTO exchange (currency, rate, date) VALUES (?, ?, ?)",
                (currency, rate, date),
            )

    def close(self) -> None:
        self.conn.close()


FINANCE_DB = FinanceDatabase("finance.db")
