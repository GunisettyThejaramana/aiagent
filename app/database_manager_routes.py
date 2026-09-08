from fastapi import APIRouter
from fastapi import HTTPException

from app.db_connection_schemas import (
    DatabaseConnectionCreate,
    DatabaseConnectionTestRequest,
    DatabaseConnectionResponse,
    DatabaseConnectionTestResponse,
    DatabaseTableResponse,
)

from app.database_manager import (
    get_all_saved_connections,
    save_database_connection,
    test_database_connection,
    delete_saved_connection,
    get_saved_connection,
    get_database_schema,
    get_database_sample_data,
    get_database_table_counts,
)


router = APIRouter(
    prefix="/api/databases",
    tags=["Databases"],
)


# ============================================================
# GET ALL SAVED DATABASES
# ============================================================

@router.get(
    "",
    response_model=list[DatabaseConnectionResponse]
)
def list_databases():

    return get_all_saved_connections()


# ============================================================
# TEST DATABASE CONNECTION
# ============================================================

@router.post("/test", response_model=DatabaseConnectionTestResponse)
def test_connection(data: DatabaseConnectionTestRequest):

    result = test_database_connection(
        db_type=data.db_type,
        host=data.host,
        port=data.port,
        database_name=data.database_name,
        username=data.username,
        password=data.password,
    )

    return result


# ============================================================
# SAVE DATABASE
# ============================================================

@router.post(
    "",
    response_model=DatabaseConnectionResponse
)
def create_database(
    data: DatabaseConnectionCreate
):

    try:

        connection = save_database_connection(
            name=data.name,
            db_type=data.db_type,
            host=data.host,
            port=data.port,
            database_name=data.database_name,
            username=data.username,
            password=data.password,
        )

        return connection

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# ============================================================
# GET ONE DATABASE
# ============================================================

@router.get(
    "/{connection_id}",
    response_model=DatabaseConnectionResponse
)
def get_database(
    connection_id: int
):

    connection = get_saved_connection(
        connection_id
    )

    if not connection:

        raise HTTPException(
            status_code=404,
            detail="Database connection not found."
        )

    return connection


# ============================================================
# DELETE DATABASE
# ============================================================

@router.delete(
    "/{connection_id}"
)
def delete_database(
    connection_id: int
):

    deleted = delete_saved_connection(
        connection_id
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Database connection not found."
        )

    return {
        "success": True,
        "message": "Database connection deleted."
    }


# ============================================================
# GET DATABASE SCHEMA
# ============================================================

@router.get(
    "/{connection_id}/schema",
    response_model=list[DatabaseTableResponse]
)
def database_schema(
    connection_id: int
):

    try:

        schema = get_database_schema(
            connection_id
        )

        return schema

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )





# ============================================================
# GET SAMPLE DATA
# ============================================================

@router.get(
    "/{connection_id}/sample-data"
)
def database_sample_data(
    connection_id: int
):

    try:

        return get_database_sample_data(
            connection_id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )





# ============================================================
# GET TABLE ROW COUNTS
# ============================================================

@router.get(
    "/{connection_id}/table-counts"
)
def database_table_counts(
    connection_id: int
):

    try:

        return get_database_table_counts(
            connection_id
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )

    