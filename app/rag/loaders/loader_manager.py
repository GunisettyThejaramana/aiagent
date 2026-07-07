from typing import List, Dict, Any

from app.rag.loaders.database_loader import DatabaseLoader
from app.rag.loaders.local_drive_loader import LocalDriveLoader


class LoaderManager:
    """
    Manages all enterprise data sources.

    Current Sources:
        1. PostgreSQL Database
        2. Local Drive Documents

    Future Sources:
        - SharePoint
        - Google Drive
        - OneDrive
        - CRM
        - ERP
    """

    def __init__(self):
        self.database_loader = DatabaseLoader()
        self.local_drive_loader = LocalDriveLoader()

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    def load_database(
        self,
        table_names: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Load data from multiple database tables.
        """

        return self.database_loader.load_multiple_tables(
            table_names
        )

    # ---------------------------------------------------------
    # Local Drive
    # ---------------------------------------------------------

    def load_local_documents(self):
        """
        Scan configured local folders.

        Returns list of file paths.
        """

        return self.local_drive_loader.scan()

    # ---------------------------------------------------------
    # Unified Loader
    # ---------------------------------------------------------

    def load_all(
        self,
        table_names: List[str]
    ) -> Dict[str, Any]:
        """
        Load data from all configured enterprise sources.
        """

        return {
            "database": self.load_database(table_names),
            "local_documents": self.load_local_documents(),
        }

    # ---------------------------------------------------------

    def close(self):
        self.database_loader.close()