import pandas as pd

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas
from app.ai import ask_llm
from app.memory import add_message, get_memory

from app.agents.sales_agent import generate_sales_sql
from app.agents.hr_agent import generate_hr_sql
from app.agents.finance_agent import generate_finance_sql

from app.agents.router_agent import route_question

from app.services.search_service import SearchService





from app.database_manager import (
    create_database_engine_from_saved_connection
)

from app.custom_ai.custom_ai_engine import (
    CustomAIEngine
)


from app.custom_ai.document_knowledge_cache import (
    document_knowledge_cache
)


from app.custom_ai.knowledge_router import (
    knowledge_router
)


router = APIRouter()

search_service = SearchService()

custom_ai_engine = CustomAIEngine()


# ================================================================
# HOME
# ================================================================

@router.get("/")
def home():
    return {
        "message": "Enterprise AI Assistant Running"
    }


# ================================================================
# SALES
# ================================================================

@router.post("/sales")
def create_sale(
    sale: schemas.SalesCreate,
    db: Session = Depends(get_db)
):
    return crud.create_sale(db, sale)


@router.get("/sales")
def get_sales(
    db: Session = Depends(get_db)
):
    return crud.get_sales(db)


# ================================================================
# ASK AI
# ================================================================

@router.post("/ask")
def ask_ai(
    request: schemas.QuestionRequest,
    db: Session = Depends(get_db)
):

    print("\n" + "=" * 60)
    print("🚀 NEW REQUEST")
    print("=" * 60)

    print(f"Question    : {request.question}")
    print(f"User ID     : {request.user_id}")
    print(f"Language    : {request.language}")
    print(f"Database ID : {request.database_id}")

    user_id = request.user_id

    # ------------------------------------------------------------
    # MEMORY
    # ------------------------------------------------------------

    add_message(
        user_id,
        "user",
        request.question
    )

    history = get_memory(user_id)

    # ============================================================
    # CASE 1:
    # DATABASE SELECTED
    #
    # The selected database is available, but the Knowledge Router
    # decides whether the question belongs to the database or
    # local documents.
    # ============================================================

    if request.database_id is not None:

        knowledge_source = knowledge_router.route(
            request.question
        )

        print(
            f"Knowledge Source : {knowledge_source}"
        )

        # ========================================================
        # DOCUMENT QUESTION
        # ========================================================

        if knowledge_source == "documents":

            print(
                "Routing question to local documents."
            )

            result = (
                search_service.search_local_documents(
                    request.question
                )
            )

            documents = result["documents"]

            if documents:

                context = "\n\n".join(
                    doc.page_content
                    for doc in documents
                )

                document_df = pd.DataFrame(
                    {
                        "Document Content": [
                            context
                        ]
                    }
                )

                answer = ask_llm(
                    request.question,
                    document_df,
                    request.language
                )

                add_message(
                    user_id,
                    "assistant",
                    answer
                )

                return {
                    "source": "documents",

                    "data_source": (
                        "local_documents"
                    ),

                    "database_id": (
                        request.database_id
                    ),

                    "question": (
                        request.question
                    ),

                    "sql": None,

                    "answer": answer,

                    "rows": [],

                    "columns": [],

                    "memory_count": (
                        len(history)
                    ),

                    "ai_engine": (
                        "document_search"
                    )
                }

            return {
                "source": "documents",

                "data_source": (
                    "local_documents"
                ),

                "database_id": (
                    request.database_id
                ),

                "question": (
                    request.question
                ),

                "sql": None,

                "answer": (
                    "No matching local "
                    "documents found."
                ),

                "rows": [],

                "columns": [],

                "memory_count": (
                    len(history)
                ),

                "ai_engine": (
                    "document_search"
                )
            }

        # ========================================================
        # DATABASE QUESTION
        # ========================================================

        print(
            "Routing question to selected database."
        )

        selected_engine = None

        try:

            print(
                f"Connecting to database "
                f"{request.database_id}..."
            )

            selected_engine = (
                create_database_engine_from_saved_connection(
                    request.database_id
                )
            )

            print(
                "Selected database connection successful."
            )

            # ----------------------------------------------------
            # CUSTOM AI PROCESSING
            # ----------------------------------------------------

            print(
                "Starting Custom AI Engine..."
            )

            # IMPORTANT:
            # Pass database_id so the database knowledge cache
            # uses "database 2" instead of "engine:<id>".

            ai_result = custom_ai_engine.process(
                request.question,
                selected_engine,
                database_id=request.database_id
            )

            print(
                "Custom AI processing completed."
            )

            print(
                "Generated SQL:"
            )

            print(
                ai_result.get("sql")
            )

            # ----------------------------------------------------
            # CHECK CUSTOM AI EXECUTION RESULT
            # ----------------------------------------------------

            execution = ai_result.get(
                "execution",
                {}
            )

            if not isinstance(
                execution,
                dict
            ):
                execution = {}

            if not execution.get(
                "success",
                False
            ):

                reason = execution.get(
                    "reason"
                )

                if not reason:

                    query_result = ai_result.get(
                        "query",
                        {}
                    )

                    if isinstance(
                        query_result,
                        dict
                    ):
                        reason = query_result.get(
                            "reason"
                        )

                if not reason:

                    reason = (
                        "The Custom AI could not "
                        "answer the question."
                    )

                raise HTTPException(
                    status_code=400,
                    detail=reason
                )

            # ----------------------------------------------------
            # GET EXECUTION RESULT
            # ----------------------------------------------------

            rows = execution.get(
                "rows",
                []
            )

            columns = execution.get(
                "columns",
                []
            )

            sql = ai_result.get(
                "sql"
            )

            answer = ai_result.get(
                "answer"
            )

            if not answer:

                answer = (
                    "The Custom AI could not "
                    "generate an answer."
                )

            print(
                f"Rows returned: {len(rows)}"
            )

            print(
                f"Answer: {answer}"
            )

            # ----------------------------------------------------
            # SAVE ASSISTANT RESPONSE TO MEMORY
            # ----------------------------------------------------

            add_message(
                user_id,
                "assistant",
                answer
            )

            # ----------------------------------------------------
            # RETURN DATABASE RESPONSE
            # ----------------------------------------------------

            return {
                "source": "database",

                "data_source": (
                    "selected_database"
                ),

                "database_id": (
                    request.database_id
                ),

                "question": (
                    request.question
                ),

                "sql": sql,

                "answer": answer,

                "rows": rows,

                "columns": columns,

                "memory_count": (
                    len(history)
                ),

                # Custom AI information
                "ai_engine": "custom_ai",

                "intent": ai_result.get(
                    "intent"
                ),

                "entities": ai_result.get(
                    "entities"
                ),

                "metric": ai_result.get(
                    "metric"
                ),

                "query_plan": ai_result.get(
                    "query_plan"
                ),

                "processing_time": ai_result.get(
                    "processing_time"
                )
            }

        except HTTPException:

            raise

        except ValueError as exc:

            print(
                f"Database validation error: {exc}"
            )

            raise HTTPException(
                status_code=400,
                detail=str(exc)
            )

        except Exception as exc:

            import traceback

            print(
                f"Custom AI database error: {exc}"
            )

            traceback.print_exc()

            raise HTTPException(
                status_code=400,
                detail=str(exc)
            )

        finally:

            # IMPORTANT:
            #
            # Do NOT call:
            #
            # selected_engine.dispose()
            #
            # The database manager keeps engines in an
            # in-memory connection cache.
            #
            # Disposing here would destroy the connection pool
            # and cause a new connection to be created repeatedly.

            pass

    # ============================================================
    # CASE 2:
    # NO DATABASE SELECTED
    #
    # Keep existing application behavior.
    # ============================================================

    source = route_question(
        request.question
    )

    print(
        f"Detected Source : {source}"
    )

    # ============================================================
    # DOCUMENT SEARCH
    # ============================================================

    if source == "documents":

        result = (
            search_service.search_local_documents(
                request.question
            )
        )

        documents = result["documents"]

        if documents:

            context = "\n\n".join(
                doc.page_content
                for doc in documents
            )

            document_df = pd.DataFrame(
                {
                    "Document Content": [
                        context
                    ]
                }
            )

            answer = ask_llm(
                request.question,
                document_df,
                request.language
            )

            add_message(
                user_id,
                "assistant",
                answer
            )

            return {
                "source": "documents",

                "data_source": (
                    "local_documents"
                ),

                "question": (
                    request.question
                ),

                "sql": None,

                "answer": answer,

                "rows": [],

                "memory_count": (
                    len(history)
                )
            }

        return {
            "source": "documents",

            "data_source": (
                "local_documents"
            ),

            "question": (
                request.question
            ),

            "sql": None,

            "answer": (
                "No matching local "
                "documents found."
            ),

            "rows": [],

            "memory_count": (
                len(history)
            )
        }

    # ============================================================
    # EXISTING ROUTING
    # ============================================================

    sql = None

    if source == "sales":

        sql = generate_sales_sql(
            request.question
        )

    elif source == "hr":

        sql = generate_hr_sql(
            request.question
        )

    elif source == "finance":

        sql = generate_finance_sql(
            request.question
        )

    elif source in [
        "operations",
        "inventory",
        "production"
    ]:

        sql = None

    else:

        sql = None

    # ============================================================
    # FALLBACK TO DOCUMENT SEARCH
    # ============================================================

    if sql is None:

        result = (
            search_service.search_local_documents(
                request.question
            )
        )

        documents = result["documents"]

        if documents:

            context = "\n\n".join(
                doc.page_content
                for doc in documents
            )

            document_df = pd.DataFrame(
                {
                    "Document Content": [
                        context
                    ]
                }
            )

            answer = ask_llm(
                request.question,
                document_df,
                request.language
            )

            return {
                "source": source,

                "data_source": (
                    "local_documents"
                ),

                "question": (
                    request.question
                ),

                "sql": None,

                "answer": answer,

                "rows": [],

                "memory_count": (
                    len(history)
                )
            }

        return {
            "source": source,

            "data_source": "none",

            "question": (
                request.question
            ),

            "sql": None,

            "answer": (
                "No information found."
            ),

            "rows": [],

            "memory_count": (
                len(history)
            )
        }

    # ============================================================
    # EXISTING DATABASE QUERY
    # ============================================================

    try:

        dataframe = pd.read_sql(
            sql,
            db.bind
        )

    except Exception as e:

        return {
            "source": source,

            "question": (
                request.question
            ),

            "sql": sql,

            "answer": (
                f"SQL Error: {str(e)}"
            ),

            "rows": []
        }

    # ============================================================
    # EMPTY DATABASE RESULT
    # ============================================================

    if dataframe.empty:

        result = (
            search_service.search_local_documents(
                request.question
            )
        )

        documents = result["documents"]

        if documents:

            context = "\n\n".join(
                doc.page_content
                for doc in documents
            )

            document_df = pd.DataFrame(
                {
                    "Document Content": [
                        context
                    ]
                }
            )

            answer = ask_llm(
                request.question,
                document_df,
                request.language
            )

            return {
                "source": "documents",

                "data_source": (
                    "local_documents"
                ),

                "question": (
                    request.question
                ),

                "sql": sql,

                "answer": answer,

                "rows": [],

                "memory_count": (
                    len(history)
                )
            }

    # ============================================================
    # EXISTING LLM RESPONSE
    # ============================================================

    answer = ask_llm(
        request.question,
        dataframe,
        request.language
    )

    add_message(
        user_id,
        "assistant",
        answer
    )

    return {
        "source": "database",

        "data_source": "database",

        "question": (
            request.question
        ),

        "sql": sql,

        "answer": answer,

        "rows": dataframe.to_dict(
            orient="records"
        ),

        "memory_count": (
            len(history)
        )
    }






# ================================================================
# DOCUMENTS
# ================================================================

@router.get("/documents")
def get_documents():
    """
    Return list of locally scanned documents
    and cache status for the Documents UI.
    """

    try:
        # Prefer already-built cache; avoid long blocking scans when possible
        if not document_knowledge_cache.is_ready():
            try:
                document_knowledge_cache.build()
            except Exception as build_err:
                print(f"Document cache build warning: {build_err}")

        info = document_knowledge_cache.get_info()
        metadata = document_knowledge_cache.get_file_metadata()

        files = []

        for path, meta in metadata.items():
            files.append({
                "name": meta.get("name", ""),
                "path": meta.get("path", path),
                "suffix": meta.get("suffix", ""),
                "size": meta.get("size", 0),
                "modified_time": meta.get("modified_time", 0),
                "document_count": meta.get("document_count", 0),
            })

        files.sort(key=lambda f: f["name"].lower())

        return {
            "ready": info.get("ready", False),
            "document_count": info.get("document_count", 0),
            "file_count": info.get("file_count", 0),
            "scan_paths": info.get("scan_paths", []),
            "files": files,
        }

    except Exception as e:
        # Never hang the UI — return empty list with error message
        print(f"/documents error: {e}")
        return {
            "ready": False,
            "document_count": 0,
            "file_count": 0,
            "scan_paths": [],
            "files": [],
            "error": str(e),
        }