from typing import List, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal


class DatabaseLoader:
    """
    Loads structured data from the company database.
    """

    def __init__(self):
        self.db: Session = SessionLocal()

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        """

        try:
            result = self.db.execute(text(query))

            return [
                dict(row._mapping)
                for row in result
            ]

        except Exception as e:
            print(f"[DATABASE ERROR] {e}")
            return []

    def load_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Load an entire table.
        """

        query = f"SELECT * FROM {table_name}"

        return self.execute_query(query)

    def load_multiple_tables(
        self,
        table_names: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:

        data = {}

        for table in table_names:
            data[table] = self.load_table(table)

        return data

    def close(self):
        self.db.close()