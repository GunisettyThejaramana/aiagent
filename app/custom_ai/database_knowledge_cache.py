
from __future__ import annotations

from threading import Lock
from typing import Any

from sqlalchemy import MetaData


class DatabaseKnowledgeCache:
    """
    Persistent in-memory cache for database schema and relationships.

    The cache is keyed by database_id, not by SQLAlchemy engine.
    Therefore a new SQLAlchemy engine can still reuse the previously
    discovered database knowledge.

    Database metadata is reflected only once per database_id.
    """

    def __init__(self):
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    # -------------------------------------------------------------
    # CACHE KEY
    # -------------------------------------------------------------

    def _key(self, database_id):
        return str(database_id)

    # -------------------------------------------------------------
    # GET
    # -------------------------------------------------------------

    def get(self, database_id):
        key = self._key(database_id)

        with self._lock:
            knowledge = self._cache.get(key)

        return knowledge

    # -------------------------------------------------------------
    # HAS
    # -------------------------------------------------------------

    def has(self, database_id):
        key = self._key(database_id)

        with self._lock:
            return key in self._cache

    # -------------------------------------------------------------
    # BUILD
    # -------------------------------------------------------------

    def build(self, database_id, engine):
        """
        Build database knowledge.

        A second check is performed while holding the lock so that
        two simultaneous requests cannot both perform the expensive
        metadata reflection.
        """

        key = self._key(database_id)

        # ---------------------------------------------------------
        # First cache check
        # ---------------------------------------------------------

        with self._lock:
            cached = self._cache.get(key)

            if cached is not None:
                print(
                    f"🟢 Database knowledge cache HIT: "
                    f"database {database_id}"
                )
                return cached

            print(
                f"🔵 Database knowledge cache MISS: "
                f"database {database_id}"
            )

            # -----------------------------------------------------
            # IMPORTANT
            # -----------------------------------------------------
            # Keep the lock while building.
            #
            # This prevents multiple requests from simultaneously
            # reflecting the same remote database.
            # -----------------------------------------------------

            metadata = MetaData()

            metadata.reflect(
                bind=engine
            )

            # -----------------------------------------------------
            # BUILD TABLE INFORMATION
            # -----------------------------------------------------

            tables = {}

            for table_name, table in metadata.tables.items():

                columns = []

                for column in table.columns:

                    columns.append(
                        {
                            "name": str(
                                column.name
                            ),
                            "type": str(
                                column.type
                            ),
                        }
                    )

                tables[table_name] = {
                    "table_name": table_name,
                    "columns": columns,
                }

            # -----------------------------------------------------
            # BUILD RELATIONSHIPS
            # -----------------------------------------------------

            relationships = []

            for table_name, table in metadata.tables.items():

                for foreign_key in table.foreign_keys:

                    referred_column = (
                        foreign_key.column
                    )

                    relationships.append(
                        {
                            "source_table": table_name,
                            "source_column": str(
                                foreign_key.parent.name
                            ),
                            "target_table": str(
                                referred_column.table.name
                            ),
                            "target_column": str(
                                referred_column.name
                            ),
                        }
                    )

            # -----------------------------------------------------
            # FINAL KNOWLEDGE
            # -----------------------------------------------------

            knowledge = {
                "database_id": database_id,

                "tables": tables,

                "table_names": list(
                    tables.keys()
                ),

                "relationships": relationships,
            }

            # -----------------------------------------------------
            # SAVE TO CACHE
            # -----------------------------------------------------

            self._cache[key] = knowledge

            print(
                f"✅ Database knowledge cached: "
                f"database {database_id} | "
                f"tables={len(tables)} | "
                f"relationships={len(relationships)}"
            )

            return knowledge

    # -------------------------------------------------------------
    # GET OR BUILD
    # -------------------------------------------------------------

    def get_or_build(
        self,
        database_id,
        engine,
    ):
        key = self._key(database_id)

        # ---------------------------------------------------------
        # FAST PATH
        # ---------------------------------------------------------
        # This is what every normal request should use.
        # No database call happens here.
        # ---------------------------------------------------------

        with self._lock:
            cached = self._cache.get(key)

        if cached is not None:
            print(
                f"⚡ Database knowledge cache HIT: "
                f"database {database_id}"
            )
            return cached

        # ---------------------------------------------------------
        # CACHE MISS
        # ---------------------------------------------------------

        return self.build(
            database_id,
            engine,
        )

    # -------------------------------------------------------------
    # INVALIDATE
    # -------------------------------------------------------------

    def invalidate(self, database_id):

        key = self._key(database_id)

        with self._lock:
            removed = self._cache.pop(
                key,
                None,
            )

        if removed is not None:
            print(
                f"🗑️ Database knowledge cache cleared: "
                f"database {database_id}"
            )

    # -------------------------------------------------------------
    # CLEAR
    # -------------------------------------------------------------

    def clear(self):

        with self._lock:
            count = len(
                self._cache
            )

            self._cache.clear()

        print(
            f"🗑️ Database knowledge cache cleared "
            f"({count} database(s))"
        )

    # -------------------------------------------------------------
    # SIZE
    # -------------------------------------------------------------

    def size(self):

        with self._lock:
            return len(
                self._cache
            )

    # -------------------------------------------------------------
    # DEBUG
    # -------------------------------------------------------------

    def debug(self):

        with self._lock:
            keys = list(
                self._cache.keys()
            )

        print(
            f"📦 Database knowledge cache: "
            f"{len(keys)} database(s)"
        )

        for key in keys:
            knowledge = self._cache[key]

            print(
                f"   Database {key}: "
                f"{len(knowledge.get('tables', {}))} tables, "
                f"{len(knowledge.get('relationships', []))} relationships"
            )


database_knowledge_cache = DatabaseKnowledgeCache()

