from typing import Optional

from pydantic import BaseModel, Field


class DatabaseConnectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class DatabaseConnectionTestRequest(BaseModel):
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class DatabaseConnectionResponse(BaseModel):
    id: int
    name: str
    db_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None

    class Config:
        from_attributes = True


class DatabaseConnectionTestResponse(BaseModel):
    success: bool
    message: str


class DatabaseColumnResponse(BaseModel):
    name: str
    type: str


class DatabaseTableResponse(BaseModel):
    table_name: str
    columns: list[DatabaseColumnResponse]