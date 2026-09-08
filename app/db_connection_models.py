from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import declarative_base


DatabaseConnectionBase = declarative_base()


class DatabaseConnection(DatabaseConnectionBase):

    __tablename__ = "database_connections"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    db_type = Column(
        String(30),
        nullable=False
    )

    host = Column(
        String(255),
        nullable=True
    )

    port = Column(
        Integer,
        nullable=True
    )

    database_name = Column(
        String(255),
        nullable=True
    )

    username = Column(
        String(255),
        nullable=True
    )

    encrypted_password = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )