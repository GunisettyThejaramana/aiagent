from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy import (
    create_engine,
    inspect,
    MetaData,
    Table,
    select,
    func,
)
from sqlalchemy.orm import Session

from app.db_connection_models import (
    DatabaseConnectionBase,
    DatabaseConnection,
)
from app.encryption import encrypt_password
from app.encryption import decrypt_password


# ============================================================
# DATABASE CONNECTION METADATA DATABASE
# ============================================================

# This SQLite database stores the saved connection information.
#
# IMPORTANT:
# The actual database password is encrypted before it is stored.
#
CONNECTION_DATABASE_URL = (
    "sqlite:///./database_connections.db"
)


connection_engine = create_engine(
    CONNECTION_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
)


# Create the database_connections table automatically.
DatabaseConnectionBase.metadata.create_all(
    bind=connection_engine
)


# ============================================================
# CREATE ENGINE FOR EXTERNAL DATABASE
# ============================================================

def get_connection_engine(
    db_type: str,
    host: str | None,
    port: int | None,
    database_name: str | None,
    username: str | None,
    password: str | None,
):
    """
    Create a SQLAlchemy engine for a selected database.
    """

    db_type = (
        db_type
        .strip()
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )

    # --------------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------------

    if db_type in (
        "postgresql",
        "postgres",
    ):

        if not host:
            raise ValueError(
                "PostgreSQL host is required."
            )

        if not database_name:
            raise ValueError(
                "PostgreSQL database name is required."
            )

        if not username:
            raise ValueError(
                "PostgreSQL username is required."
            )

        if port is None:
            port = 5432

        encoded_username = quote_plus(
            username
        )

        encoded_password = quote_plus(
            password or ""
        )

        encoded_database = quote_plus(
            database_name
        )

        url = (
            "postgresql+psycopg2://"
            f"{encoded_username}:"
            f"{encoded_password}@"
            f"{host}:{port}/"
            f"{encoded_database}"
        )

        return create_engine(
            url,
            pool_pre_ping=True,
        )

    # --------------------------------------------------------
    # MySQL
    # --------------------------------------------------------

    if db_type in (
        "mysql",
    ):

        if not host:
            raise ValueError(
                "MySQL host is required."
            )

        if not database_name:
            raise ValueError(
                "MySQL database name is required."
            )

        if not username:
            raise ValueError(
                "MySQL username is required."
            )

        if port is None:
            port = 3306

        encoded_username = quote_plus(
            username
        )

        encoded_password = quote_plus(
            password or ""
        )

        encoded_database = quote_plus(
            database_name
        )

        url = (
            "mysql+pymysql://"
            f"{encoded_username}:"
            f"{encoded_password}@"
            f"{host}:{port}/"
            f"{encoded_database}"
        )

        return create_engine(
            url,
            pool_pre_ping=True,
        )

    # --------------------------------------------------------
    # SQL Server
    # --------------------------------------------------------

    if db_type in (
        "sqlserver",
        "mssql",
        "microsoftsqlserver",
    ):

        if not host:
            raise ValueError(
                "SQL Server host is required."
            )

        if not database_name:
            raise ValueError(
                "SQL Server database name is required."
            )

        if not username:
            raise ValueError(
                "SQL Server username is required."
            )

        if port is None:
            port = 1433

        encoded_username = quote_plus(
            username
        )

        encoded_password = quote_plus(
            password or ""
        )

        encoded_database = quote_plus(
            database_name
        )

        connection_string = (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={host},{port};"
            f"DATABASE={database_name};"
            f"UID={username};"
            f"PWD={password or ''};"
            "TrustServerCertificate=yes;"
        )

        encoded_connection_string = quote_plus(
            connection_string
        )

        url = (
            "mssql+pyodbc:///?odbc_connect="
            f"{encoded_connection_string}"
        )

        return create_engine(
            url,
            pool_pre_ping=True,
        )

    # --------------------------------------------------------
    # SQLite
    # --------------------------------------------------------

    if db_type == "sqlite":

        if not database_name:
            raise ValueError(
                "SQLite database path is required."
            )

        return create_engine(
            f"sqlite:///{database_name}",
            connect_args={
                "check_same_thread": False
            },
        )

    # --------------------------------------------------------
    # Unsupported database
    # --------------------------------------------------------

    raise ValueError(
        f"Unsupported database type: {db_type}"
    )


# ============================================================
# TEST DATABASE CONNECTION
# ============================================================

def test_database_connection(
    db_type: str,
    host: str | None,
    port: int | None,
    database_name: str | None,
    username: str | None,
    password: str | None,
):
    """
    Test whether the supplied database credentials work.
    """

    engine = None

    try:

        engine = get_connection_engine(
            db_type=db_type,
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password=password,
        )

        with engine.connect() as connection:

            connection.exec_driver_sql(
                "SELECT 1"
            )

        return {
            "success": True,
            "message": "Database connection successful.",
        }

    except Exception as exc:

        return {
            "success": False,
            "message": str(exc),
        }

    finally:

        if engine is not None:
            engine.dispose()


# ============================================================
# SAVE DATABASE CONNECTION
# ============================================================

def save_database_connection(
    name: str,
    db_type: str,
    host: str | None,
    port: int | None,
    database_name: str | None,
    username: str | None,
    password: str | None,
):
    """
    Save a database connection.

    Password is encrypted before storing.
    """

    encrypted_password = encrypt_password(
        password or ""
    )

    connection = DatabaseConnection(
        name=name,
        db_type=db_type,
        host=host,
        port=port,
        database_name=database_name,
        username=username,
        encrypted_password=encrypted_password,
    )

    with Session(
        connection_engine
    ) as db:

        db.add(connection)

        db.commit()

        db.refresh(connection)

        return connection


# ============================================================
# GET ALL SAVED CONNECTIONS
# ============================================================

def get_all_saved_connections():

    with Session(
        connection_engine
    ) as db:

        return (
            db.query(DatabaseConnection)
            .order_by(
                DatabaseConnection.id.desc()
            )
            .all()
        )


# ============================================================
# GET ONE SAVED CONNECTION
# ============================================================

def get_saved_connection(
    connection_id: int
):

    with Session(
        connection_engine
    ) as db:

        return (
            db.query(DatabaseConnection)
            .filter(
                DatabaseConnection.id
                == connection_id
            )
            .first()
        )


# ============================================================
# DELETE CONNECTION
# ============================================================

def delete_saved_connection(
    connection_id: int
):

    with Session(
        connection_engine
    ) as db:

        connection = (
            db.query(DatabaseConnection)
            .filter(
                DatabaseConnection.id
                == connection_id
            )
            .first()
        )

        if not connection:
            return False

        db.delete(connection)

        db.commit()

        return True


# ============================================================
# CREATE ENGINE FROM SAVED CONNECTION
# ============================================================

def create_database_engine_from_saved_connection(
    connection_id: int
):

    connection = get_saved_connection(
        connection_id
    )

    if not connection:
        raise ValueError(
            "Database connection not found."
        )

    password = decrypt_password(
        connection.encrypted_password or ""
    )

    return get_connection_engine(
        db_type=connection.db_type,
        host=connection.host,
        port=connection.port,
        database_name=connection.database_name,
        username=connection.username,
        password=password,
    )


# ============================================================
# GET DATABASE SCHEMA
# ============================================================

def get_database_schema(
    connection_id: int
):

    engine = None

    try:

        engine = (
            create_database_engine_from_saved_connection(
                connection_id
            )
        )

        inspector = inspect(
            engine
        )

        tables = []

        for table_name in inspector.get_table_names():

            columns = []

            for column in inspector.get_columns(
                table_name
            ):

                columns.append(
                    {
                        "name": str(
                            column["name"]
                        ),
                        "type": str(
                            column["type"]
                        ),
                    }
                )

            tables.append(
                {
                    "table_name": table_name,
                    "columns": columns,
                }
            )

        return tables

    finally:

        if engine is not None:
            engine.dispose()





# ============================================================
# GET SAMPLE DATA FROM DATABASE
# ============================================================

def get_database_sample_data(connection_id: int, limit: int = 5):

    engine = None

    try:
        engine = create_database_engine_from_saved_connection(
            connection_id
        )

        inspector = inspect(engine)

        table_names = inspector.get_table_names()

        if not table_names:
            return {
                "table_name": None,
                "columns": [],
                "rows": [],
                "message": "No tables found in this database."
            }

        # Use the first available table
        table_name = table_names[0]

        table = Table(
            table_name,
            MetaData(),
            autoload_with=engine
        )

        statement = select(table).limit(limit)

        with engine.connect() as connection:

            result = connection.execute(statement)

            rows = [
                dict(row._mapping)
                for row in result
            ]

        columns = [
            str(column.name)
            for column in table.columns
        ]

        return {
            "table_name": table_name,
            "columns": columns,
            "rows": rows,
            "message": "Sample data retrieved successfully."
        }

    finally:

        if engine is not None:
            engine.dispose()





# ============================================================
# GET TABLE ROW COUNTS
# ============================================================

def get_database_table_counts(connection_id: int):

    engine = None

    try:
        engine = create_database_engine_from_saved_connection(
            connection_id
        )

        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        results = []

        for table_name in table_names:

            table = Table(
                table_name,
                MetaData(),
                autoload_with=engine
            )

            statement = select(
                func.count()
            ).select_from(table)

            with engine.connect() as connection:
                count = connection.execute(statement).scalar()

            results.append({
                "table_name": table_name,
                "row_count": int(count or 0)
            })

        return results

    finally:

        if engine is not None:
            engine.dispose()



