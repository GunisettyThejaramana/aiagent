
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas

from app.memory import add_message, get_memory

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
        "message": "Enterprise AI Assistant Running",
        "ai_engine": "Custom AI Engine",
        "external_llm": False,
        "openai": False,
        "ollama": False
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
# GENERIC DOCUMENT PROCESSING
# ================================================================

def answer_from_documents(
    question: str,
    language: str,
    user_id: str,
    history: list,
    database_id=None
):
    """
    Search the local document knowledge base and process the
    retrieved documents using the application's own document
    reasoning engine.

    No OpenAI.
    No Ollama.
    No external LLM.
    No question-specific answer rules.
    """

    print(
        "Searching local document knowledge base..."
    )

    # ------------------------------------------------------------
    # SEARCH LOCAL DOCUMENTS
    # ------------------------------------------------------------

    try:
        result = search_service.search_local_documents(
            question
        )
    except Exception as exc:
        print(
            f"Document search error: {exc}"
        )

        return {
            "source": "documents",
            "data_source": "local_documents",
            "database_id": database_id,
            "question": question,
            "sql": None,
            "answer": (
                "The local document search could not be "
                "completed."
            ),
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "custom_document_reasoning",
            "document_count": 0,
            "document_score": 0,
            "document_source": None
        }

    documents = result.get(
        "documents",
        []
    )

    print(
        f"Documents matched: {len(documents)}"
    )

    # ------------------------------------------------------------
    # NO DOCUMENTS
    # ------------------------------------------------------------

    if not documents:

        return {
            "source": "documents",
            "data_source": "local_documents",
            "database_id": database_id,
            "question": question,
            "sql": None,
            "answer": (
                "I could not find relevant information "
                "in the local documents."
            ),
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "custom_document_reasoning",
            "document_count": 0,
            "document_score": result.get(
                "score",
                0
            ),
            "document_source": result.get(
                "source"
            )
        }

    # ------------------------------------------------------------
    # BUILD DOCUMENT OBJECTS
    # ------------------------------------------------------------

    usable_documents = []

    for doc in documents:

        page_content = getattr(
            doc,
            "page_content",
            ""
        )

        if not page_content:
            continue

        usable_documents.append(
            doc
        )

    if not usable_documents:

        return {
            "source": "documents",
            "data_source": "local_documents",
            "database_id": database_id,
            "question": question,
            "sql": None,
            "answer": (
                "Relevant documents were found, but "
                "they do not contain readable text."
            ),
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "custom_document_reasoning",
            "document_count": len(documents),
            "document_score": result.get(
                "score",
                0
            ),
            "document_source": result.get(
                "source"
            )
        }

    # ------------------------------------------------------------
    # USE OUR OWN DOCUMENT REASONING ENGINE
    # ------------------------------------------------------------

    print(
        "Generating answer using custom document reasoning..."
    )

    try:

        document_result = (
            custom_ai_engine.document_reasoning_engine.process(
                question,
                usable_documents
            )
        )

    except AttributeError:

        # --------------------------------------------------------
        # FALLBACK: DIRECT IMPORT
        # --------------------------------------------------------

        try:

            from app.custom_ai.document_reasoning_engine import (
                DocumentReasoningEngine
            )

            document_engine = DocumentReasoningEngine()

            document_result = document_engine.process(
                question,
                usable_documents
            )

        except Exception as exc:

            print(
                f"Document reasoning error: {exc}"
            )

            return {
                "source": "documents",
                "data_source": "local_documents",
                "database_id": database_id,
                "question": question,
                "sql": None,
                "answer": (
                    "Relevant documents were found, but "
                    "the local document reasoning engine "
                    "could not process them."
                ),
                "rows": [],
                "columns": [],
                "memory_count": len(history),
                "ai_engine": "custom_document_reasoning",
                "document_count": len(documents),
                "document_score": result.get(
                    "score",
                    0
                ),
                "document_source": result.get(
                    "source"
                )
            }

    except Exception as exc:

        print(
            f"Document reasoning error: {exc}"
        )

        document_result = {
            "success": False,
            "answer": "",
            "evidence": []
        }

    # ------------------------------------------------------------
    # GET GENERATED ANSWER
    # ------------------------------------------------------------

    answer = ""

    if isinstance(
        document_result,
        dict
    ):
        answer = document_result.get(
            "answer",
            ""
        )

    if answer is None:
        answer = ""

    answer = str(
        answer
    ).strip()

    # ------------------------------------------------------------
    # IF ENGINE RETURNED EVIDENCE BUT NO ANSWER
    # ------------------------------------------------------------

    if not answer:

        evidence = []

        if isinstance(
            document_result,
            dict
        ):
            evidence = document_result.get(
                "evidence",
                []
            )

        if evidence:

            evidence_parts = []

            for item in evidence:

                if isinstance(
                    item,
                    str
                ):
                    text = item.strip()

                elif isinstance(
                    item,
                    dict
                ):
                    text = str(
                        item.get(
                            "text",
                            item.get(
                                "content",
                                ""
                            )
                        )
                    ).strip()

                else:
                    text = str(
                        item
                    ).strip()

                if text:
                    evidence_parts.append(
                        text
                    )

            if evidence_parts:

                answer = "\n\n".join(
                    evidence_parts
                )

    # ------------------------------------------------------------
    # FINAL EMPTY RESULT
    # ------------------------------------------------------------

    if not answer:

        answer = (
            "I found relevant documents, but the local "
            "reasoning engine could not derive an answer "
            "from their contents."
        )

    # ------------------------------------------------------------
    # SAVE MEMORY
    # ------------------------------------------------------------

    add_message(
        user_id,
        "assistant",
        answer
    )

    print(
        f"Document Answer: {answer}"
    )

    # ------------------------------------------------------------
    # RETURN
    # ------------------------------------------------------------

    return {
        "source": "documents",
        "data_source": "local_documents",
        "database_id": database_id,
        "question": question,
        "sql": None,
        "answer": answer,
        "rows": [],
        "columns": [],
        "memory_count": len(history),
        "ai_engine": "custom_document_reasoning",
        "document_count": len(documents),
        "document_score": result.get(
            "score",
            0
        ),
        "document_source": result.get(
            "source"
        ),
        "evidence": (
            document_result.get(
                "evidence",
                []
            )
            if isinstance(
                document_result,
                dict
            )
            else []
        )
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
    Process a database question using the application's
    own Custom AI Engine.

    No OpenAI.
    No Ollama.
    No external LLM.
    """

    if database_id is None:

        return {
            "source": "database",
            "data_source": "database",
            "database_id": None,
            "question": question,
            "sql": None,
            "answer": (
                "Please connect or select a database "
                "for this question."
            ),
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "custom_ai"
        }

    selected_engine = None

    try:

        # --------------------------------------------------------
        # CONNECT TO SELECTED DATABASE
        # --------------------------------------------------------

        print(
            f"Connecting to database {database_id}..."
        )

        selected_engine = (
            create_database_engine_from_saved_connection(
                database_id
            )
        )

        print(
            "Selected database connection successful."
        )

        # --------------------------------------------------------
        # CUSTOM AI ENGINE
        # --------------------------------------------------------

        print(
            "Starting Custom AI Engine..."
        )

        ai_result = custom_ai_engine.process(
            question,
            selected_engine,
            database_id=database_id
        )

        print(
            "Custom AI processing completed."
        )

        sql = ai_result.get(
            "sql"
        )

        print(
            "Generated SQL:"
        )

        print(
            sql
        )

        # --------------------------------------------------------
        # EXECUTION
        # --------------------------------------------------------

        execution = ai_result.get(
            "execution",
            {}
        )

        if not isinstance(
            execution,
            dict
        ):
            execution = {}

        # --------------------------------------------------------
        # EXECUTION FAILED
        # --------------------------------------------------------

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

            return {
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

        # --------------------------------------------------------
        # RESULT
        # --------------------------------------------------------

        rows = execution.get(
            "rows",
            []
        )

        columns = execution.get(
            "columns",
            []
        )

        answer = ai_result.get(
            "answer"
        )

        if answer is None:
            answer = ""

        answer = str(
            answer
        ).strip()

        # --------------------------------------------------------
        # IF CUSTOM ENGINE HAS NO ANSWER
        # --------------------------------------------------------

        if not answer:

            if rows:

                # Return the actual result rather than inventing
                # an answer.

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

        print(
            f"Answer: {answer}"
        )

        # --------------------------------------------------------
        # MEMORY
        # --------------------------------------------------------

        add_message(
            user_id,
            "assistant",
            answer
        )

        # --------------------------------------------------------
        # RETURN
        # --------------------------------------------------------

        return {
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

        return {
            "source": "database",
            "data_source": "selected_database",
            "database_id": database_id,
            "question": question,
            "sql": None,
            "answer": str(exc),
            "rows": [],
            "columns": [],
            "memory_count": len(history),
            "ai_engine": "custom_ai"
        }

    except Exception as exc:

        import traceback

        print(
            f"Custom AI database error: {exc}"
        )

        traceback.print_exc()

        return {
            "source": "database",
            "data_source": "selected_database",
            "database_id": database_id,
            "question": question,
            "sql": None,
            "answer": (
                "The database question could not be "
                "processed: "
                f"{str(exc)}"
            ),
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
    db: Session = Depends(get_db)
):
    """
    Main Enterprise AI endpoint.

    Processing flow:

        User Question
              |
              v
        Memory
              |
              v
        Knowledge Router
          /       \
         /         \
    Database     Documents
       |             |
       v             v
    Custom AI    Document
      Engine     Reasoning
       |             |
       +-------> Answer

    No OpenAI.
    No Ollama.
    No external LLM.
    """

    print("\n" + "=" * 60)

    print(
        "NEW REQUEST"
    )

    print("=" * 60)

    print(
        f"Question    : {request.question}"
    )

    print(
        f"User ID     : {request.user_id}"
    )

    print(
        f"Language    : {request.language}"
    )

    print(
        f"Database ID : {request.database_id}"
    )

    print(
        "Knowledge Source Requested : "
        f"{request.knowledge_source}"
    )

    user_id = request.user_id

    question = (
        str(
            request.question
            or ""
        )
        .strip()
    )

    # ------------------------------------------------------------
    # EMPTY QUESTION
    # ------------------------------------------------------------

    if not question:

        return {
            "source": "system",
            "data_source": None,
            "database_id": request.database_id,
            "question": "",
            "sql": None,
            "answer": (
                "Please enter a question."
            ),
            "rows": [],
            "columns": [],
            "memory_count": 0,
            "ai_engine": "custom_ai"
        }

    # ------------------------------------------------------------
    # KNOWLEDGE SOURCE
    # ------------------------------------------------------------

    requested_source = (
        str(
            request.knowledge_source
            or "auto"
        )
        .strip()
        .lower()
    )

    if requested_source not in {
        "auto",
        "database",
        "documents",
        "both"
    }:

        requested_source = "auto"

    # ------------------------------------------------------------
    # MEMORY
    # ------------------------------------------------------------

    add_message(
        user_id,
        "user",
        question
    )

    history = get_memory(
        user_id
    )

    # ------------------------------------------------------------
    # DETERMINE SOURCE
    # ------------------------------------------------------------

    if requested_source == "auto":

        try:

            knowledge_source = (
                knowledge_router.route(
                    question
                )
            )

        except Exception as exc:

            print(
                f"Knowledge router error: {exc}"
            )

            knowledge_source = "database"

    else:

        knowledge_source = requested_source

    print(
        f"Knowledge Source : {knowledge_source}"
    )

    # ============================================================
    # DOCUMENTS
    # ============================================================

    if knowledge_source == "documents":

        print(
            "Routing question to local documents."
        )

        return answer_from_documents(
            question=question,
            language=request.language,
            user_id=user_id,
            history=history,
            database_id=request.database_id
        )

    # ============================================================
    # BOTH
    # ============================================================

    if knowledge_source == "both":

        print(
            "Routing question to both sources."
        )

        # --------------------------------------------------------
        # DOCUMENT SEARCH
        # --------------------------------------------------------

        document_result = answer_from_documents(
            question=question,
            language=request.language,
            user_id=user_id,
            history=history,
            database_id=request.database_id
        )

        document_answer = str(
            document_result.get(
                "answer",
                ""
            )
        ).strip()

        document_count = document_result.get(
            "document_count",
            0
        )

        # --------------------------------------------------------
        # IF DOCUMENTS PRODUCED USEFUL DATA
        # --------------------------------------------------------

        if (
            document_count > 0
            and document_answer
            and not document_answer.startswith(
                "I could not find relevant information"
            )
        ):

            return document_result

        # --------------------------------------------------------
        # DATABASE FALLBACK
        # --------------------------------------------------------

        if request.database_id is not None:

            print(
                "No useful document result. "
                "Continuing with database."
            )

            return answer_from_database(
                question=question,
                user_id=user_id,
                history=history,
                database_id=request.database_id
            )

        return document_result

    # ============================================================
    # DATABASE
    # ============================================================

    if knowledge_source == "database":

        return answer_from_database(
            question=question,
            user_id=user_id,
            history=history,
            database_id=request.database_id
        )

    # ============================================================
    # LEGACY ROUTING
    # ============================================================

    print(
        "Using legacy router..."
    )

    try:

        source = route_question(
            question
        )

    except Exception as exc:

        print(
            f"Legacy router error: {exc}"
        )

        source = None

    print(
        f"Detected Source : {source}"
    )

    # ------------------------------------------------------------
    # LEGACY DOCUMENT ROUTING
    # ------------------------------------------------------------

    if source == "documents":

        return answer_from_documents(
            question=question,
            language=request.language,
            user_id=user_id,
            history=history,
            database_id=request.database_id
        )

    # ------------------------------------------------------------
    # IF A DATABASE WAS SELECTED, ALWAYS PREFER THE
    # GENERIC CUSTOM DATABASE ENGINE
    # ------------------------------------------------------------

    if request.database_id is not None:

        return answer_from_database(
            question=question,
            user_id=user_id,
            history=history,
            database_id=request.database_id
        )

    # ============================================================
    # FINAL LOCAL DOCUMENT FALLBACK
    # ============================================================

    document_result = answer_from_documents(
        question=question,
        language=request.language,
        user_id=user_id,
        history=history,
        database_id=None
    )

    if document_result.get(
        "document_count",
        0
    ) > 0:

        return document_result

    # ============================================================
    # NOTHING AVAILABLE
    # ============================================================

    answer = (
        "I could not find enough information in the "
        "connected databases or local documents to "
        "answer this question."
    )

    add_message(
        user_id,
        "assistant",
        answer
    )

    return {
        "source": "custom_ai",
        "data_source": None,
        "database_id": request.database_id,
        "question": question,
        "sql": None,
        "answer": answer,
        "rows": [],
        "columns": [],
        "memory_count": len(history),
        "ai_engine": "custom_ai"
    }


# ================================================================
# DOCUMENTS
# ================================================================

@router.get("/documents")
def get_documents():
    """
    Return locally scanned documents and cache information.
    """

    try:

        # --------------------------------------------------------
        # BUILD CACHE IF REQUIRED
        # --------------------------------------------------------

        if not document_knowledge_cache.is_ready():

            try:

                document_knowledge_cache.build()

            except Exception as build_err:

                print(
                    "Document cache build warning: "
                    f"{build_err}"
                )

        # --------------------------------------------------------
        # CACHE INFORMATION
        # --------------------------------------------------------

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

        files.sort(
            key=lambda item: (
                item["name"]
                or ""
            ).lower()
        )

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

        return {
            "ready": False,
            "document_count": 0,
            "file_count": 0,
            "scan_paths": [],
            "files": [],
            "error": str(exc)
        }

