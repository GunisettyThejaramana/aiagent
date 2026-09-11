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
    search_result=None,
    save_memory: bool = True,
):
    """
    Search local documents and use Ollama for the final answer.

    ``search_result`` can be supplied by AUTO routing so the document
    index is searched only once.
    """
    try:
        if search_result is None:
            search_result = search_document_context(question)
    except Exception as exc:
        print(f"Document search error: {exc}")

        answer = "The local document search could not be completed."

        if save_memory:
            add_message(user_id, "assistant", answer)

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

    if not isinstance(search_result, dict):
        search_result = {}

    documents = search_result.get("documents", [])
    context = search_result.get("context", "")
    score = search_result.get("score", 0)
    source = search_result.get("source")

    if not documents:
        answer = "I could not find relevant information in the local documents."

        if save_memory:
            add_message(user_id, "assistant", answer)

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

    if not context:
        answer = (
            "Relevant documents were found, "
            "but they do not contain readable text."
        )

        if save_memory:
            add_message(user_id, "assistant", answer)

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

    print("Generating document answer using Ollama...")

    answer = ask_document_ai(
        question=question,
        context=context,
        language=language,
        history=history,
    )

    if save_memory:
        add_message(user_id, "assistant", answer)

    evidence = []

    for doc in documents[:MAX_DOCUMENTS_FOR_AI]:
        content = getattr(doc, "page_content", "")
        if not content:
            continue

        metadata = getattr(doc, "metadata", {})
        doc_source = ""

        if isinstance(metadata, dict):
            doc_source = (
                metadata.get("source", "")
                or metadata.get("file_name", "")
                or metadata.get("filename", "")
            )

        evidence.append(
            {
                "source": doc_source,
                "text": str(content)[:MAX_DOCUMENT_CHARS],
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
# ================================================================
# GENERIC DATABASE PROCESSING
# ================================================================

def answer_from_database(
    question: str,
    user_id: str,
    history: list,
    database_id: int,
    allow_ollama_fallback: bool = True,
    save_memory: bool = True,
):
    """
    Process a database question using the Custom AI Engine.

    AUTO mode sets ``allow_ollama_fallback=False``. This makes the
    database engine act as a fast capability probe and prevents a
    slow Ollama SQL generation call from being used for routing.

    Explicit database mode keeps the Ollama SQL fallback enabled.
    """
    if database_id is None:
        answer = (
            "Please connect or select a database "
            "for this question."
        )

        if save_memory:
            add_message(user_id, "assistant", answer)

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
            "ai_engine": "custom_ai",
        }

    try:
        print(f"Using database {database_id}...")

        selected_engine = get_cached_database_engine(
            int(database_id)
        )

        print("Database engine ready.")

        ai_result = custom_ai_engine.process(
            question,
            selected_engine,
            database_id=database_id,
            allow_ollama_fallback=allow_ollama_fallback,
        )

        if not isinstance(ai_result, dict):
            ai_result = {}

        sql = ai_result.get("sql")
        print(f"Generated SQL: {sql}")

        execution = ai_result.get("execution", {})

        if not isinstance(execution, dict):
            execution = {}

        if not execution.get("success", False):
            reason = execution.get("reason")

            if not reason:
                query_result = ai_result.get("query", {})
                if isinstance(query_result, dict):
                    reason = query_result.get("reason")

            if not reason:
                reason = (
                    "The Custom AI Engine could not "
                    "answer the database question."
                )

            if save_memory:
                add_message(user_id, "assistant", reason)

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
                "ai_engine": ai_result.get(
                    "ai_engine",
                    "custom_ai",
                ),
                "intent": ai_result.get("intent"),
                "entities": ai_result.get("entities"),
                "metric": ai_result.get("metric"),
                "query_plan": ai_result.get("query_plan"),
                "processing_time": ai_result.get("processing_time"),
            }

        rows = execution.get("rows", [])
        columns = execution.get("columns", [])

        if not isinstance(rows, list):
            rows = []

        if not isinstance(columns, list):
            columns = []

        answer = str(
            ai_result.get("answer") or ""
        ).strip()

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

        print(f"Rows returned: {len(rows)}")

        if save_memory:
            add_message(user_id, "assistant", answer)

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
            "ai_engine": ai_result.get(
                "ai_engine",
                "custom_ai",
            ),
            "intent": ai_result.get("intent"),
            "entities": ai_result.get("entities"),
            "metric": ai_result.get("metric"),
            "query_plan": ai_result.get("query_plan"),
            "processing_time": ai_result.get("processing_time"),
        }

    except ValueError as exc:
        print(f"Database validation error: {exc}")

        answer = str(exc)

        if save_memory:
            add_message(user_id, "assistant", answer)

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
            "ai_engine": "custom_ai",
        }

    except Exception as exc:
        print(f"Custom AI database error: {exc}")
        traceback.print_exc()

        answer = (
            "The database question could not be processed: "
            f"{str(exc)}"
        )

        if save_memory:
            add_message(user_id, "assistant", answer)

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
            "ai_engine": "custom_ai",
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

    AUTO mode is evidence-based, not keyword-based.

    AUTO flow:
        1. Fast local response for greetings.
        2. If the user explicitly asks for a source, honor it.
        3. Otherwise probe the connected database with the deterministic
           pipeline and search the local document index.
        4. Database evidence only -> database.
        5. Document evidence only -> documents.
        6. Both evidence sources -> one combined Ollama call.
        7. No evidence -> normal Ollama chat.

    Ollama is never called merely to decide the source.
    """

    request_start = time.perf_counter()

    question = str(
        request.question or ""
    ).strip()

    user_id = str(
        request.user_id or "default_user"
    )

    language = (
        request.language
        or "en-US"
    )

    database_id = request.database_id

    requested_source = str(
        request.knowledge_source or "auto"
    ).strip().lower()

    if requested_source not in {
        "auto",
        "database",
        "documents",
        "both",
        "chat",
    }:
        requested_source = "auto"

    print()
    print("========================================")
    print("NEW REQUEST")
    print("========================================")
    print("Question    :", question)
    print("User ID     :", user_id)
    print("Language    :", language)
    print("Database ID :", database_id)
    print("Knowledge Source Requested :", requested_source)

    if not question:
        return {
            "success": False,
            "answer": "Please enter a question.",
            "source": "chat",
            "data_source": "validation",
            "sql": None,
            "database_id": database_id,
        }

    # ---------------------------------------------------------------
    # FAST CHAT RESPONSE
    # ---------------------------------------------------------------

    if requested_source in {"auto", "chat"}:
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

            print("FAST RESPONSE - Ollama skipped")
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

    # ---------------------------------------------------------------
    # MEMORY
    # ---------------------------------------------------------------

    history = get_short_history(user_id)

    add_message(
        user_id,
        "user",
        question,
    )

    # ---------------------------------------------------------------
    # EXPLICIT SOURCE SELECTION
    # ---------------------------------------------------------------

    # The router is now only an explicit-instruction helper.
    # It does NOT classify ordinary business words.
    explicit_source = None

    if requested_source == "auto":
        try:
            explicit_source = (
                knowledge_router.explicit_route(
                    question
                )
            )
        except Exception as exc:
            print(
                "Explicit source hint error:",
                exc,
            )

    if requested_source == "auto" and explicit_source:
        knowledge_source = explicit_source
    elif requested_source == "auto":
        knowledge_source = "auto"
    else:
        knowledge_source = requested_source

    print(
        "Initial source decision:",
        knowledge_source,
    )

    # ===============================================================
    # TRUE AUTO ROUTING
    # ===============================================================

    auto_database_result = None
    auto_document_search = None

    if knowledge_source == "auto":
        print(
            "AUTO routing: checking real database and "
            "document evidence."
        )

        # -----------------------------------------------------------
        # DATABASE CAPABILITY PROBE
        # -----------------------------------------------------------
        #
        # This uses the existing deterministic Metric -> Intent ->
        # Entity -> Reasoning -> QueryBuilder pipeline.
        #
        # IMPORTANT:
        # allow_ollama_fallback=False prevents the expensive Ollama
        # SQL fallback from being used for source detection.
        # -----------------------------------------------------------

        if database_id is not None:
            try:
                auto_database_result = answer_from_database(
                    question=question,
                    user_id=user_id,
                    history=history,
                    database_id=database_id,
                    allow_ollama_fallback=False,
                    save_memory=False,
                )
            except Exception as exc:
                print(
                    "AUTO database probe error:",
                    exc,
                )
                auto_database_result = None
        else:
            print(
                "AUTO database probe skipped: "
                "no database selected."
            )

        database_evidence = bool(
            isinstance(auto_database_result, dict)
            and auto_database_result.get("success")
            and isinstance(
                auto_database_result.get("execution"),
                dict,
            )
        )

        # answer_from_database() returns the normalized result and
        # keeps execution information out of the public response in
        # most cases, so also accept a successful database result.
        database_evidence = bool(
            isinstance(auto_database_result, dict)
            and auto_database_result.get("success")
        )

        print(
            "AUTO database evidence:",
            database_evidence,
        )

        # -----------------------------------------------------------
        # DOCUMENT EVIDENCE PROBE
        # -----------------------------------------------------------

        try:
            auto_document_search = search_document_context(
                question
            )
        except Exception as exc:
            print(
                "AUTO document search error:",
                exc,
            )
            auto_document_search = {
                "documents": [],
                "context": "",
                "score": 0,
                "source": None,
            }

        if not isinstance(
            auto_document_search,
            dict,
        ):
            auto_document_search = {
                "documents": [],
                "context": "",
                "score": 0,
                "source": None,
            }

        document_evidence = bool(
            auto_document_search.get("documents")
            and auto_document_search.get("context")
        )

        print(
            "AUTO document evidence:",
            document_evidence,
        )

        # -----------------------------------------------------------
        # EVIDENCE DECISION
        # -----------------------------------------------------------

        if database_evidence and document_evidence:
            knowledge_source = "both"

        elif database_evidence:
            knowledge_source = "database"

        elif document_evidence:
            knowledge_source = "documents"

        else:
            knowledge_source = "chat"

        print(
            "AUTO final source:",
            knowledge_source,
        )

    print(
        "Final knowledge source:",
        knowledge_source,
    )

    # ===============================================================
    # CHAT
    # ===============================================================

    if knowledge_source == "chat":
        print(
            "Routing question to Ollama general chat."
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

    # ===============================================================
    # DOCUMENTS
    # ===============================================================

    if knowledge_source in {
        "document",
        "documents",
        "docs",
    }:
        print(
            "Routing question to local document knowledge."
        )

        result = answer_from_documents(
            question=question,
            language=language,
            user_id=user_id,
            history=history,
            database_id=database_id,
            search_result=(
                auto_document_search
                if requested_source == "auto"
                and auto_document_search is not None
                else None
            ),
            save_memory=True,
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

    # ===============================================================
    # DATABASE
    # ===============================================================

    if knowledge_source == "database":
        print(
            "Routing question to database."
        )

        # AUTO already performed the deterministic database query.
        # Reuse it instead of querying the database twice.
        if (
            requested_source == "auto"
            and isinstance(
                auto_database_result,
                dict,
            )
            and auto_database_result.get("success")
        ):
            result = dict(
                auto_database_result
            )

            result["source"] = "database"
            result["data_source"] = "selected_database"

            answer = str(
                result.get("answer") or ""
            ).strip()

            if not answer:
                rows = result.get("rows", [])

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

            result["answer"] = answer

            add_message(
                user_id,
                "assistant",
                answer,
            )

        else:
            # Explicit database mode keeps the normal Ollama SQL
            # fallback available.
            result = answer_from_database(
                question=question,
                user_id=user_id,
                history=history,
                database_id=database_id,
                allow_ollama_fallback=True,
                save_memory=True,
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

    # ===============================================================
    # BOTH DATABASE + DOCUMENTS
    # ===============================================================

    if knowledge_source in {
        "both",
        "database_and_documents",
        "database_documents",
    }:
        print(
            "Routing question to database + documents."
        )

        # -----------------------------------------------------------
        # DATABASE
        # -----------------------------------------------------------

        if (
            requested_source == "auto"
            and isinstance(
                auto_database_result,
                dict,
            )
            and auto_database_result.get("success")
        ):
            database_result = auto_database_result
        else:
            database_result = answer_from_database(
                question=question,
                user_id=user_id,
                history=history,
                database_id=database_id,
                allow_ollama_fallback=True,
                save_memory=False,
            )

        database_records = database_result.get(
            "rows",
            [],
        )

        if not isinstance(
            database_records,
            list,
        ):
            database_records = []

        sql = database_result.get(
            "sql"
        )

        # -----------------------------------------------------------
        # DOCUMENTS
        # -----------------------------------------------------------

        if (
            requested_source == "auto"
            and isinstance(
                auto_document_search,
                dict,
            )
        ):
            document_search = auto_document_search
        else:
            try:
                document_search = search_document_context(
                    question
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

        documents = document_search.get(
            "documents",
            [],
        )

        document_context = document_search.get(
            "context",
            "",
        )

        # -----------------------------------------------------------
        # COMBINED AI
        # -----------------------------------------------------------

        # If one side unexpectedly has no evidence, do not force a
        # combined hallucination. Use the evidence that actually exists.
        database_ok = bool(
            isinstance(database_result, dict)
            and database_result.get("success")
        )

        document_ok = bool(
            documents
            and document_context
        )

        if database_ok and document_ok:
            answer = ask_combined_ai(
                question=question,
                database_records=database_records,
                document_context=document_context,
                sql=sql,
                language=language,
                history=history,
            )

            source = "both"
            data_source = "database_and_documents"

        elif database_ok:
            answer = database_result.get(
                "answer",
                "",
            )

            source = "database"
            data_source = "selected_database"

        elif document_ok:
            answer = ask_document_ai(
                question=question,
                context=document_context,
                language=language,
                history=history,
            )

            source = "documents"
            data_source = "local_documents"

        else:
            answer = ask_general_ai(
                question,
                history=history,
                language=language,
            )

            source = "chat"
            data_source = "ollama"

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
            "source": source,
            "data_source": data_source,
            "sql": sql if source in {
                "database",
                "both",
            } else None,
            "database_id": database_id,
            "records": database_records,
            "document_count": len(documents),
            "document_score": document_search.get(
                "score",
                0,
            ),
            "document_source": document_search.get(
                "source"
            ),
        }

    # ===============================================================
    # UNKNOWN / SAFE FALLBACK
    # ===============================================================

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