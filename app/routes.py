from functools import lru_cache
import time
import traceback

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas

from app.memory import add_message, get_memory

from app.ai import (
    ask_general_ai,
    ask_document_ai,
    ask_combined_ai,
    get_fast_response,
)

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


# ================================================================
# ROUTER
# ================================================================

router = APIRouter()


# ================================================================
# SERVICES
# ================================================================

search_service = SearchService()

custom_ai_engine = CustomAIEngine()


# ================================================================
# PERFORMANCE SETTINGS
# ================================================================

# Keep only a small amount of conversation history.
MAX_HISTORY_MESSAGES = 2


# Document retrieval settings.
MAX_DOCUMENTS_FOR_AI = 4


# Maximum characters taken from each document.
MAX_DOCUMENT_CHARS = 2200


# Maximum total document context.
MAX_DOCUMENT_CONTEXT_CHARS = 10000


# ================================================================
# DATABASE ENGINE CACHE
# ================================================================

@lru_cache(maxsize=10)
def get_cached_database_engine(database_id: int):
    """
    Reuse the SQLAlchemy engine for the selected database.

    Creating a database engine for every /ask request adds
    unnecessary overhead.

    The engine is cached by database_id.
    """

    print(
        f"Creating database engine for database {database_id}..."
    )

    return create_database_engine_from_saved_connection(
        database_id
    )


# ================================================================
# MEMORY HELPER
# ================================================================

def get_short_history(user_id: str) -> list:
    """
    Retrieve only the recent conversation history.

    This keeps Ollama prompts small and improves response time.
    """

    try:

        history = get_memory(user_id)

        if not isinstance(history, list):
            return []

        return history[-MAX_HISTORY_MESSAGES:]

    except Exception as exc:

        print(
            f"Memory read warning: {exc}"
        )

        return []


# ================================================================
# HOME
# ================================================================

@router.get("/")
def home():

    return {
        "message": "Enterprise AI Assistant Running",
        "ai_engine": "Custom AI Engine",
        "external_llm": False,
        "openai": False,
        "ollama": True
    }


# ================================================================
# SALES
# ================================================================

@router.post("/sales")
def create_sale(
    sale: schemas.SalesCreate,
    db: Session = Depends(get_db)
):

    return crud.create_sale(
        db,
        sale
    )


@router.get("/sales")
def get_sales(
    db: Session = Depends(get_db)
):

    return crud.get_sales(
        db
    )


# ================================================================
# DOCUMENT SEARCH HELPER
# ================================================================

def search_document_context(
    question: str,
):
    """
    Search the local document knowledge base.

    Returns:

        {
            "documents": [...],
            "context": "...",
            "score": ...,
            "source": ...
        }

    This function intentionally limits the amount of text sent
    to Ollama.
    """

    print(
        "Searching local document knowledge base..."
    )

    result = search_service.search_local_documents(
        question
    )

    if not isinstance(result, dict):

        return {
            "documents": [],
            "context": "",
            "score": 0,
            "source": None,
        }

    documents = result.get(
        "documents",
        []
    )

    print(
        f"Documents matched: {len(documents)}"
    )

    if not documents:

        return {
            "documents": [],
            "context": "",
            "score": result.get(
                "score",
                0
            ),
            "source": result.get(
                "source"
            ),
        }

    context_parts = []

    total_chars = 0

    for doc in documents[:MAX_DOCUMENTS_FOR_AI]:

        content = getattr(
            doc,
            "page_content",
            "",
        )

        if not content:
            continue

        content = str(
            content
        ).strip()

        if not content:
            continue

        metadata = getattr(
            doc,
            "metadata",
            {},
        )

        source = ""

        if isinstance(
            metadata,
            dict
        ):

            source = (
                metadata.get(
                    "source",
                    ""
                )
                or metadata.get(
                    "file_name",
                    ""
                )
                or metadata.get(
                    "filename",
                    ""
                )
            )

        # --------------------------------------------------------
        # LIMIT EACH DOCUMENT
        # --------------------------------------------------------

        content = content[
            :MAX_DOCUMENT_CHARS
        ]

        if source:

            part = (
                f"SOURCE: {source}\n"
                f"{content}"
            )

        else:

            part = content

        # --------------------------------------------------------
        # LIMIT TOTAL CONTEXT
        # --------------------------------------------------------

        remaining = (
            MAX_DOCUMENT_CONTEXT_CHARS
            - total_chars
        )

        if remaining <= 0:
            break

        part = part[
            :remaining
        ]

        context_parts.append(
            part
        )

        total_chars += len(
            part
        )

    context = (
        "\n\n--- DOCUMENT ---\n\n"
        .join(context_parts)
    )

    return {
        "documents": documents,
        "context": context,
        "score": result.get(
            "score",
            0
        ),
        "source": result.get(
            "source"
        ),
    }


# ================================================================
# GENERIC DOCUMENT PROCESSING
# ================================================================

def answer_from_documents(
    question: str,
    language: str,
    user_id: str,
    history: list,
    database_id=None,
):
    """
    Search local documents and use Ollama to generate
    the final answer.

    Context is deliberately limited for performance.
    """

    try:

        search_result = search_document_context(
            question
        )

    except Exception as exc:

        print(
            f"Document search error: {exc}"
        )

        answer = (
            "The local document search could not "
            "be completed."
        )

        add_message(
            user_id,
            "assistant",
            answer,
        )

        return {
            "success": False,
            "source": "documents",
            "data_source": "local_documents",
            "database_id": database_id,
            "question": question,
            "sql": None,
            "answer": answer,
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "ollama",
            "document_count": 0,
            "document_score": 0,
            "document_source": None,
            "evidence": [],
        }

    documents = search_result.get(
        "documents",
        []
    )

    context = search_result.get(
        "context",
        ""
    )

    score = search_result.get(
        "score",
        0
    )

    source = search_result.get(
        "source"
    )

    # ============================================================
    # NO DOCUMENTS
    # ============================================================

    if not documents:

        answer = (
            "I could not find relevant information "
            "in the local documents."
        )

        add_message(
            user_id,
            "assistant",
            answer,
        )

        return {
            "success": True,
            "source": "documents",
            "data_source": "local_documents",
            "database_id": database_id,
            "question": question,
            "sql": None,
            "answer": answer,
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "ollama",
            "document_count": 0,
            "document_score": score,
            "document_source": source,
            "evidence": [],
        }

    # ============================================================
    # NO READABLE CONTENT
    # ============================================================

    if not context:

        answer = (
            "Relevant documents were found, "
            "but they do not contain readable text."
        )

        add_message(
            user_id,
            "assistant",
            answer,
        )

        return {
            "success": True,
            "source": "documents",
            "data_source": "local_documents",
            "database_id": database_id,
            "question": question,
            "sql": None,
            "answer": answer,
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "ollama",
            "document_count": len(documents),
            "document_score": score,
            "document_source": source,
            "evidence": [],
        }

    # ============================================================
    # OLLAMA
    # ============================================================

    print(
        "Generating document answer using Ollama..."
    )

    answer = ask_document_ai(
        question=question,
        context=context,
        language=language,
        history=history,
    )

    add_message(
        user_id,
        "assistant",
        answer,
    )

    print(
        "Document answer generated."
    )

    # ============================================================
    # EVIDENCE
    # ============================================================

    evidence = []

    for doc in documents[
        :MAX_DOCUMENTS_FOR_AI
    ]:

        content = getattr(
            doc,
            "page_content",
            "",
        )

        if not content:
            continue

        metadata = getattr(
            doc,
            "metadata",
            {},
        )

        doc_source = ""

        if isinstance(
            metadata,
            dict
        ):

            doc_source = (
                metadata.get(
                    "source",
                    ""
                )
                or metadata.get(
                    "file_name",
                    ""
                )
                or metadata.get(
                    "filename",
                    ""
                )
            )

        evidence.append(
            {
                "source": doc_source,
                "text": str(
                    content
                )[
                    :MAX_DOCUMENT_CHARS
                ]
            }
        )

    return {
        "success": True,
        "source": "documents",
        "data_source": "local_documents",
        "database_id": database_id,
        "question": question,
        "sql": None,
        "answer": answer,
        "rows": [],
        "columns": [],
        "memory_count": len(history),
        "ai_engine": "ollama",
        "document_count": len(documents),
        "document_score": score,
        "document_source": source,
        "evidence": evidence,
    }


# ================================================================
# GENERIC DATABASE PROCESSING
# ================================================================

def answer_from_database(
    question: str,
    user_id: str,
    history: list,
    database_id: int
):
    """
    Process a database question using the Custom AI Engine.

    The database engine is cached so repeated questions do not
    recreate the SQLAlchemy engine.
    """

    if database_id is None:

        answer = (
            "Please connect or select a database "
            "for this question."
        )

        add_message(
            user_id,
            "assistant",
            answer
        )

        return {
            "success": False,
            "source": "database",
            "data_source": "database",
            "database_id": None,
            "question": question,
            "sql": None,
            "answer": answer,
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "custom_ai"
        }

    try:

        # ========================================================
        # DATABASE CONNECTION
        # ========================================================

        print(
            f"Using database {database_id}..."
        )

        selected_engine = (
            get_cached_database_engine(
                int(database_id)
            )
        )

        print(
            "Database engine ready."
        )

        # ========================================================
        # CUSTOM AI
        # ========================================================

        ai_result = custom_ai_engine.process(
            question,
            selected_engine,
            database_id=database_id
        )

        if not isinstance(
            ai_result,
            dict
        ):

            ai_result = {}

        # ========================================================
        # SQL
        # ========================================================

        sql = ai_result.get(
            "sql"
        )

        print(
            f"Generated SQL: {sql}"
        )

        # ========================================================
        # EXECUTION
        # ========================================================

        execution = ai_result.get(
            "execution",
            {}
        )

        if not isinstance(
            execution,
            dict
        ):

            execution = {}

        # ========================================================
        # EXECUTION FAILED
        # ========================================================

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
                    "The Custom AI Engine could not "
                    "answer the database question."
                )

            add_message(
                user_id,
                "assistant",
                reason
            )

            return {
                "success": False,
                "source": "database",
                "data_source": "selected_database",
                "database_id": database_id,
                "question": question,
                "sql": sql,
                "answer": reason,
                "rows": [],
                "columns": [],
                "memory_count": len(history),
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

        # ========================================================
        # RESULT
        # ========================================================

        rows = execution.get(
            "rows",
            []
        )

        columns = execution.get(
            "columns",
            []
        )

        if not isinstance(
            rows,
            list
        ):

            rows = []

        if not isinstance(
            columns,
            list
        ):

            columns = []

        answer = ai_result.get(
            "answer"
        )

        if answer is None:
            answer = ""

        answer = str(
            answer
        ).strip()

        # ========================================================
        # FALLBACK ANSWER
        # ========================================================

        if not answer:

            if rows:

                answer = (
                    "The database query completed successfully. "
                    "The returned data is available in the result."
                )

            else:

                answer = (
                    "The database query completed successfully, "
                    "but no matching records were returned."
                )

        print(
            f"Rows returned: {len(rows)}"
        )

        # ========================================================
        # MEMORY
        # ========================================================

        add_message(
            user_id,
            "assistant",
            answer
        )

        # ========================================================
        # RETURN
        # ========================================================

        return {
            "success": True,
            "source": "database",
            "data_source": "selected_database",
            "database_id": database_id,
            "question": question,
            "sql": sql,
            "answer": answer,
            "rows": rows,
            "columns": columns,
            "memory_count": len(history),
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

    except ValueError as exc:

        print(
            f"Database validation error: {exc}"
        )

        answer = str(exc)

        add_message(
            user_id,
            "assistant",
            answer
        )

        return {
            "success": False,
            "source": "database",
            "data_source": "selected_database",
            "database_id": database_id,
            "question": question,
            "sql": None,
            "answer": answer,
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "custom_ai"
        }

    except Exception as exc:

        print(
            f"Custom AI database error: {exc}"
        )

        traceback.print_exc()

        answer = (
            "The database question could not be "
            "processed: "
            f"{str(exc)}"
        )

        add_message(
            user_id,
            "assistant",
            answer
        )

        return {
            "success": False,
            "source": "database",
            "data_source": "selected_database",
            "database_id": database_id,
            "question": question,
            "sql": None,
            "answer": answer,
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "custom_ai"
        }


# ================================================================
# ASK AI
# ================================================================

@router.post("/ask")
def ask_ai(
    request: schemas.QuestionRequest,
):
    """
    Main Enterprise AI Assistant endpoint.

    Flow:

    1. Normalize request.
    2. Handle very simple chat instantly.
    3. Route normal questions.
    4. Save conversation memory.
    5. Process database/documents/both/chat.
    6. Save assistant response.
    """

    request_start = time.perf_counter()

    question = (
        str(request.question or "")
        .strip()
    )

    user_id = (
        str(request.user_id or "default_user")
    )

    language = (
        request.language
        or "en-US"
    )

    database_id = request.database_id

    requested_source = (
        request.knowledge_source
        or "auto"
    )

    requested_source = (
        str(requested_source)
        .strip()
        .lower()
    )

    print()
    print("========================================")
    print("NEW REQUEST")
    print("========================================")
    print("Question    :", question)
    print("User ID     :", user_id)
    print("Language    :", language)
    print("Database ID :", database_id)
    print(
        "Knowledge Source :",
        requested_source,
    )

    # ---------------------------------------------------------
    # VALIDATE QUESTION
    # ---------------------------------------------------------

    if not question:

        return {
            "success": False,
            "answer": "Please enter a question.",
            "source": "chat",
        }

    # ---------------------------------------------------------
    # FAST CHAT RESPONSE
    # ---------------------------------------------------------
    #
    # Greetings / simple messages are handled directly by
    # Python without calling Ollama.
    #
    # This is the biggest improvement for messages such as:
    #
    # hello
    # hi
    # thanks
    # bye
    #
    # ---------------------------------------------------------

    if requested_source in {
        "auto",
        "chat",
    }:

        fast_answer = get_fast_response(
            question,
            language,
        )

        if fast_answer is not None:

            add_message(
                user_id,
                "user",
                question,
            )

            add_message(
                user_id,
                "assistant",
                fast_answer,
            )

            total_time = (
                time.perf_counter()
                - request_start
            )

            print(
                "FAST RESPONSE - Ollama skipped"
            )

            print(
                f"Total request time: "
                f"{total_time:.3f} seconds"
            )

            print("========================================")
            print()

            return {
                "success": True,
                "answer": fast_answer,
                "source": "chat",
                "data_source": "local_fast_response",
                "sql": None,
                "database_id": database_id,
            }

    # ---------------------------------------------------------
    # KNOWLEDGE SOURCE ROUTING
    # ---------------------------------------------------------

    knowledge_source = requested_source

    if knowledge_source in {
        "",
        "auto",
        "automatic",
    }:

        print(
            "Routing question "
            "using knowledge router."
        )

        try:

            knowledge_source = (
                knowledge_router.route(
                    question
                )
            )

        except Exception as exc:

            print(
                "Knowledge router error:",
                exc,
            )

            knowledge_source = "chat"

        knowledge_source = (
            str(
                knowledge_source
            )
            .strip()
            .lower()
        )

    print(
        "Final knowledge source:",
        knowledge_source,
    )

    # ---------------------------------------------------------
    # GET MEMORY
    # ---------------------------------------------------------

    history = get_short_history(
        user_id
    )

    # ---------------------------------------------------------
    # SAVE USER MESSAGE
    # ---------------------------------------------------------

    add_message(
        user_id,
        "user",
        question,
    )

    # =========================================================
    # CHAT
    # =========================================================

    if knowledge_source == "chat":

        print(
            "Routing question to "
            "Ollama general chat."
        )

        answer = ask_general_ai(
            question,
            history=history,
            language=language,
        )

        add_message(
            user_id,
            "assistant",
            answer,
        )

        total_time = (
            time.perf_counter()
            - request_start
        )

        print(
            f"Total request time: "
            f"{total_time:.2f} seconds"
        )

        return {
            "success": True,
            "answer": answer,
            "source": "chat",
            "data_source": "ollama",
            "sql": None,
            "database_id": database_id,
        }

    # =========================================================
    # DOCUMENTS
    # =========================================================

    if knowledge_source in {
        "document",
        "documents",
        "docs",
    }:

        print(
            "Routing question to "
            "document knowledge."
        )

        result = answer_from_documents(
            question=question,
            language=language,
            user_id=user_id,
            history=history,
            database_id=database_id,
        )

        total_time = (
            time.perf_counter()
            - request_start
        )

        print(
            f"Total request time: "
            f"{total_time:.2f} seconds"
        )

        return result

    # =========================================================
    # DATABASE
    # =========================================================

    if knowledge_source == "database":

        print(
            "Routing question to "
            "database."
        )

        # IMPORTANT:
        #
        # answer_from_database() accepts:
        #
        # question
        # user_id
        # history
        # database_id
        #
        # It does NOT accept language.
        #

        result = answer_from_database(
            question=question,
            user_id=user_id,
            history=history,
            database_id=database_id,
        )

        total_time = (
            time.perf_counter()
            - request_start
        )

        print(
            f"Total request time: "
            f"{total_time:.2f} seconds"
        )

        return result

    # =========================================================
    # BOTH DATABASE + DOCUMENTS
    # =========================================================

    if knowledge_source in {
        "both",
        "database_and_documents",
        "database_documents",
    }:

        print(
            "Routing question to "
            "database + documents."
        )

        # -----------------------------------------------------
        # DATABASE
        # -----------------------------------------------------

        database_result = answer_from_database(
            question=question,
            user_id=user_id,
            history=history,
            database_id=database_id,
        )

        database_records = (
            database_result.get(
                "rows",
                []
            )
        )

        sql = database_result.get(
            "sql"
        )

        # -----------------------------------------------------
        # DOCUMENT SEARCH
        # -----------------------------------------------------

        try:

            document_search = (
                search_document_context(
                    question
                )
            )

        except Exception as exc:

            print(
                "Document search error:",
                exc,
            )

            document_search = {
                "documents": [],
                "context": "",
                "score": 0,
                "source": None,
            }

        documents = (
            document_search.get(
                "documents",
                []
            )
        )

        document_context = (
            document_search.get(
                "context",
                ""
            )
        )

        # -----------------------------------------------------
        # COMBINED AI
        # -----------------------------------------------------

        answer = ask_combined_ai(
            question=question,
            database_records=database_records,
            document_context=document_context,
            sql=sql,
            language=language,
            history=history,
        )

        add_message(
            user_id,
            "assistant",
            answer,
        )

        total_time = (
            time.perf_counter()
            - request_start
        )

        print(
            f"Total request time: "
            f"{total_time:.2f} seconds"
        )

        return {
            "success": True,
            "answer": answer,
            "source": "both",
            "data_source": "database_and_documents",
            "sql": sql,
            "database_id": database_id,
            "records": database_records,
            "document_count": len(documents),
            "document_score": document_search.get(
                "score",
                0
            ),
            "document_source": document_search.get(
                "source"
            ),
        }

    # =========================================================
    # UNKNOWN SOURCE
    # =========================================================

    print(
        "Unknown knowledge source. "
        "Falling back to general chat."
    )

    answer = ask_general_ai(
        question,
        history=history,
        language=language,
    )

    add_message(
        user_id,
        "assistant",
        answer,
    )

    total_time = (
        time.perf_counter()
        - request_start
    )

    print(
        f"Total request time: "
        f"{total_time:.2f} seconds"
    )

    return {
        "success": True,
        "answer": answer,
        "source": "chat",
        "data_source": "ollama",
        "sql": None,
        "database_id": database_id,
    }


# ================================================================
# DOCUMENTS
# ================================================================

@router.get("/documents")
def get_documents():
    """
    Return locally scanned documents and cache information.

    The cache is only built when it is not already ready.
    """

    try:

        # ========================================================
        # BUILD CACHE IF REQUIRED
        # ========================================================

        if not document_knowledge_cache.is_ready():

            print(
                "Document knowledge cache is not ready."
            )

            try:

                document_knowledge_cache.build()

            except Exception as build_err:

                print(
                    "Document cache build warning: "
                    f"{build_err}"
                )

        # ========================================================
        # CACHE INFORMATION
        # ========================================================

        info = (
            document_knowledge_cache.get_info()
        )

        metadata = (
            document_knowledge_cache.get_file_metadata()
        )

        files = []

        for path, meta in metadata.items():

            files.append(
                {
                    "name": meta.get(
                        "name",
                        ""
                    ),

                    "path": meta.get(
                        "path",
                        path
                    ),

                    "suffix": meta.get(
                        "suffix",
                        ""
                    ),

                    "size": meta.get(
                        "size",
                        0
                    ),

                    "modified_time": meta.get(
                        "modified_time",
                        0
                    ),

                    "document_count": meta.get(
                        "document_count",
                        0
                    )
                }
            )

        # ========================================================
        # SORT FILES
        # ========================================================

        files.sort(
            key=lambda item: (
                item.get(
                    "name",
                    ""
                )
                or ""
            ).lower()
        )

        # ========================================================
        # RESPONSE
        # ========================================================

        return {
            "ready": info.get(
                "ready",
                False
            ),

            "document_count": info.get(
                "document_count",
                0
            ),

            "file_count": info.get(
                "file_count",
                0
            ),

            "scan_paths": info.get(
                "scan_paths",
                []
            ),

            "files": files
        }

    except Exception as exc:

        print(
            f"/documents error: {exc}"
        )

        traceback.print_exc()

        return {
            "ready": False,
            "document_count": 0,
            "file_count": 0,
            "scan_paths": [],
            "files": [],
            "error": str(exc)
        }