import re

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
# DOCUMENT FALLBACK ANSWER
# ================================================================

def generate_document_fallback_answer(
    question: str,
    context: str
):
    """
    Generate a useful answer directly from retrieved document
    content when the LLM cannot generate the answer.

    This is a fallback only.

    It is especially useful for simple questions such as:

        What were the total sales in August 2026?
        What was the revenue in August 2026?
        What is the sales target?
        What was the actual sales amount?

    The fallback does NOT replace the LLM.
    """

    if not context:
        return (
            "I found a relevant document, "
            "but it did not contain readable content."
        )

    normalized_question = (
        question
        .lower()
        .strip()
    )

    normalized_context = (
        context
        .replace("\u20b9", "₹")
    )

    # ============================================================
    # TOTAL SALES / SALES VALUE
    # ============================================================

    sales_question = any(
        phrase in normalized_question
        for phrase in [
            "total sales",
            "sales total",
            "total sale",
            "sales value",
            "total revenue",
            "revenue"
        ]
    )

    if sales_question:

        patterns = [

            # Total Sales: ₹1,301,950
            r"(?:total\s+sales|sales\s+total)"
            r"\s*[:\-]?\s*"
            r"(?:₹|rs\.?|inr)?\s*"
            r"([\d,]+(?:\.\d+)?)",

            # Total Sales Value: 1,301,950
            r"(?:total\s+sales\s+value)"
            r"\s*[:\-]?\s*"
            r"(?:₹|rs\.?|inr)?\s*"
            r"([\d,]+(?:\.\d+)?)",

            # Revenue: ₹1,301,950
            r"(?:revenue)"
            r"\s*[:\-]?\s*"
            r"(?:₹|rs\.?|inr)?\s*"
            r"([\d,]+(?:\.\d+)?)",

            # Sales: ₹1,301,950
            r"(?:sales)"
            r"\s*[:\-]?\s*"
            r"(?:₹|rs\.?|inr)?\s*"
            r"([\d,]+(?:\.\d+)?)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                normalized_context,
                flags=re.IGNORECASE
            )

            if match:

                value = match.group(1)

                value = value.replace(
                    ",",
                    ""
                )

                try:

                    numeric_value = float(
                        value
                    )

                    if numeric_value.is_integer():

                        formatted_value = (
                            f"{int(numeric_value):,}"
                        )

                    else:

                        formatted_value = (
                            f"{numeric_value:,.2f}"
                        )

                    return (
                        f"The total sales were "
                        f"₹{formatted_value}."
                    )

                except ValueError:

                    pass

    # ============================================================
    # TARGET
    # ============================================================

    target_question = any(
        word in normalized_question
        for word in [
            "target",
            "sales target"
        ]
    )

    if target_question:

        patterns = [

            r"(?:sales\s+target|target)"
            r"\s*[:\-]?\s*"
            r"(?:₹|rs\.?|inr)?\s*"
            r"([\d,]+(?:\.\d+)?)"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                normalized_context,
                flags=re.IGNORECASE
            )

            if match:

                value = match.group(1)

                value = value.replace(
                    ",",
                    ""
                )

                try:

                    numeric_value = float(
                        value
                    )

                    if numeric_value.is_integer():

                        formatted_value = (
                            f"{int(numeric_value):,}"
                        )

                    else:

                        formatted_value = (
                            f"{numeric_value:,.2f}"
                        )

                    return (
                        f"The sales target was "
                        f"₹{formatted_value}."
                    )

                except ValueError:

                    pass

    # ============================================================
    # ACTUAL SALES
    # ============================================================

    if (
        "actual sales" in normalized_question
        or "actual" in normalized_question
    ):

        patterns = [

            r"(?:actual\s+sales|actual)"
            r"\s*[:\-]?\s*"
            r"(?:₹|rs\.?|inr)?\s*"
            r"([\d,]+(?:\.\d+)?)"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                normalized_context,
                flags=re.IGNORECASE
            )

            if match:

                value = match.group(1)

                value = value.replace(
                    ",",
                    ""
                )

                try:

                    numeric_value = float(
                        value
                    )

                    if numeric_value.is_integer():

                        formatted_value = (
                            f"{int(numeric_value):,}"
                        )

                    else:

                        formatted_value = (
                            f"{numeric_value:,.2f}"
                        )

                    return (
                        f"The actual sales were "
                        f"₹{formatted_value}."
                    )

                except ValueError:

                    pass

    # ============================================================
    # VARIANCE
    # ============================================================

    if "variance" in normalized_question:

        pattern = (
            r"(?:variance)"
            r"\s*[:\-]?\s*"
            r"([+\-]?\s*[\d.]+)"
            r"\s*%"
        )

        match = re.search(
            pattern,
            normalized_context,
            flags=re.IGNORECASE
        )

        if match:

            variance = (
                match.group(1)
                .replace(" ", "")
            )

            return (
                f"The variance was "
                f"{variance}%."
            )

    # ============================================================
    # GENERAL FALLBACK
    # ============================================================

    # Return a short portion of the actual document content
    # rather than an error message.

    clean_context = re.sub(
        r"\s+",
        " ",
        context
    ).strip()

    if len(clean_context) > 1000:

        clean_context = (
            clean_context[:1000]
            + "..."
        )

    return (
        "I found relevant information in "
        "the local documents:\n\n"
        f"{clean_context}"
    )


# ================================================================
# DOCUMENT SEARCH HELPER
# ================================================================

def answer_from_documents(
    question: str,
    language: str,
    user_id: str,
    history: list,
    database_id=None
):

    print(
        "Searching local document knowledge base..."
    )

    # ------------------------------------------------------------
    # SEARCH DOCUMENTS
    # ------------------------------------------------------------

    result = (
        search_service.search_local_documents(
            question
        )
    )

    documents = result.get(
        "documents",
        []
    )

    print(
        f"Documents matched: {len(documents)}"
    )

    if documents:

        # --------------------------------------------------------
        # BUILD DOCUMENT CONTEXT
        # --------------------------------------------------------

        document_parts = []

        for doc in documents:

            page_content = getattr(
                doc,
                "page_content",
                ""
            )

            if page_content:

                document_parts.append(
                    page_content
                )

        context = "\n\n".join(
            document_parts
        )

        if not context:

            return {
                "source": "documents",

                "data_source": (
                    "local_documents"
                ),

                "database_id": (
                    database_id
                ),

                "question": (
                    question
                ),

                "sql": None,

                "answer": (
                    "I found a matching document, "
                    "but it contains no readable text."
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

        # --------------------------------------------------------
        # DOCUMENT DATAFRAME
        # --------------------------------------------------------

        document_df = pd.DataFrame(
            {
                "Document Content": [
                    context
                ]
            }
        )

        print(
            "Generating answer from document context..."
        )

        # --------------------------------------------------------
        # TRY LLM
        # --------------------------------------------------------

        answer = None

        try:

            answer = ask_llm(
                question,
                document_df,
                language
            )

            if answer:

                answer = str(
                    answer
                ).strip()

        except Exception as exc:

            import traceback

            print(
                "Document LLM generation failed:"
                f" {exc}"
            )

            traceback.print_exc()

            answer = None

        # --------------------------------------------------------
        # FALLBACK
        # --------------------------------------------------------

        if not answer:

            print(
                "Using document content fallback."
            )

            answer = (
                generate_document_fallback_answer(
                    question,
                    context
                )
            )

        # --------------------------------------------------------
        # SAVE MEMORY
        # --------------------------------------------------------

        add_message(
            user_id,
            "assistant",
            answer
        )

        print(
            f"Document Answer: {answer}"
        )

        # --------------------------------------------------------
        # RETURN DOCUMENT RESULT
        # --------------------------------------------------------

        return {
            "source": "documents",

            "data_source": (
                "local_documents"
            ),

            "database_id": (
                database_id
            ),

            "question": (
                question
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
            ),

            "document_count": (
                len(documents)
            ),

            "document_score": (
                result.get(
                    "score",
                    0
                )
            ),

            "document_source": (
                result.get(
                    "source"
                )
            )
        }

    # ------------------------------------------------------------
    # NO DOCUMENTS
    # ------------------------------------------------------------

    print(
        "No matching local documents found."
    )

    return {
        "source": "documents",

        "data_source": (
            "local_documents"
        ),

        "database_id": (
            database_id
        ),

        "question": (
            question
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
        ),

        "document_count": 0,

        "document_score": 0,

        "document_source": None
    }


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

    # ============================================================
    # KNOWLEDGE SOURCE
    # ============================================================

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
        "both",
    }:

        requested_source = "auto"

    # ============================================================
    # MEMORY
    # ============================================================

    add_message(
        user_id,
        "user",
        request.question
    )

    history = get_memory(
        user_id
    )

    # ============================================================
    # DETERMINE KNOWLEDGE SOURCE
    # ============================================================

    if requested_source == "auto":

        knowledge_source = (
            knowledge_router.route(
                request.question
            )
        )

    else:

        knowledge_source = (
            requested_source
        )

    print(
        f"Knowledge Source : {knowledge_source}"
    )

    # ============================================================
    # DOCUMENT QUESTION
    # ============================================================

    if knowledge_source == "documents":

        print(
            "Routing question to local documents."
        )

        return answer_from_documents(
            question=request.question,
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

        document_result = (
            answer_from_documents(
                question=request.question,
                language=request.language,
                user_id=user_id,
                history=history,
                database_id=request.database_id
            )
        )

        if document_result.get(
            "rows"
        ):

            return document_result

        if document_result.get(
            "answer"
        ) != "No matching local documents found.":

            return document_result

        if request.database_id is None:

            return document_result

        print(
            "No useful document result. "
            "Continuing with database."
        )

        knowledge_source = "database"

    # ============================================================
    # DATABASE QUESTION
    # ============================================================

    if knowledge_source == "database":

        if request.database_id is None:

            return {
                "source": "database",

                "data_source": "database",

                "database_id": None,

                "question": (
                    request.question
                ),

                "sql": None,

                "answer": (
                    "Please connect or select "
                    "a database for this "
                    "database question."
                ),

                "rows": [],

                "columns": [],

                "memory_count": (
                    len(history)
                ),

                "ai_engine": "custom_ai",
            }

        print(
            "Routing question to selected database."
        )

        selected_engine = None

        try:

            # ----------------------------------------------------
            # DATABASE CONNECTION
            # ----------------------------------------------------

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

            ai_result = (
                custom_ai_engine.process(
                    request.question,
                    selected_engine,
                    database_id=request.database_id
                )
            )

            print(
                "Custom AI processing completed."
            )

            print(
                "Generated SQL:"
            )

            print(
                ai_result.get(
                    "sql"
                )
            )

            # ----------------------------------------------------
            # EXECUTION RESULT
            # ----------------------------------------------------

            execution = (
                ai_result.get(
                    "execution",
                    {}
                )
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

                reason = (
                    execution.get(
                        "reason"
                    )
                )

                if not reason:

                    query_result = (
                        ai_result.get(
                            "query",
                            {}
                        )
                    )

                    if isinstance(
                        query_result,
                        dict
                    ):

                        reason = (
                            query_result.get(
                                "reason"
                            )
                        )

                if not reason:

                    reason = (
                        "The Custom AI "
                        "could not answer "
                        "the question."
                    )

                raise HTTPException(
                    status_code=400,
                    detail=reason
                )

            # ----------------------------------------------------
            # GET RESULT
            # ----------------------------------------------------

            rows = (
                execution.get(
                    "rows",
                    []
                )
            )

            columns = (
                execution.get(
                    "columns",
                    []
                )
            )

            sql = (
                ai_result.get(
                    "sql"
                )
            )

            answer = (
                ai_result.get(
                    "answer"
                )
            )

            if not answer:

                answer = (
                    "The Custom AI "
                    "could not generate "
                    "an answer."
                )

            print(
                f"Rows returned: {len(rows)}"
            )

            print(
                f"Answer: {answer}"
            )

            # ----------------------------------------------------
            # SAVE RESPONSE
            # ----------------------------------------------------

            add_message(
                user_id,
                "assistant",
                answer
            )

            # ----------------------------------------------------
            # RETURN
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

                "ai_engine": "custom_ai",

                "intent": (
                    ai_result.get(
                        "intent"
                    )
                ),

                "entities": (
                    ai_result.get(
                        "entities"
                    )
                ),

                "metric": (
                    ai_result.get(
                        "metric"
                    )
                ),

                "query_plan": (
                    ai_result.get(
                        "query_plan"
                    )
                ),

                "processing_time": (
                    ai_result.get(
                        "processing_time"
                    )
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

            # The database manager maintains
            # its own engine connection cache.

            pass

    # ============================================================
    # LEGACY ROUTING
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

        return answer_from_documents(
            question=request.question,
            language=request.language,
            user_id=user_id,
            history=history
        )

    # ============================================================
    # GENERATE SQL
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

        return answer_from_documents(
            question=request.question,
            language=request.language,
            user_id=user_id,
            history=history
        )

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

        document_result = (
            answer_from_documents(
                question=request.question,
                language=request.language,
                user_id=user_id,
                history=history
            )
        )

        if document_result.get(
            "data_source"
        ) == "local_documents":

            if document_result.get(
                "answer"
            ) != "No matching local documents found.":

                document_result[
                    "sql"
                ] = sql

                return document_result

    # ============================================================
    # EXISTING LLM DATABASE RESPONSE
    # ============================================================

    try:

        answer = ask_llm(
            request.question,
            dataframe,
            request.language
        )

    except Exception as exc:

        import traceback

        print(
            f"Database LLM response failed: {exc}"
        )

        traceback.print_exc()

        # --------------------------------------------------------
        # Basic database fallback
        # --------------------------------------------------------

        if (
            len(dataframe) == 1
            and len(dataframe.columns) == 1
        ):

            column_name = (
                dataframe.columns[0]
            )

            value = dataframe.iloc[
                0,
                0
            ]

            if pd.notna(value):

                try:

                    numeric_value = float(
                        value
                    )

                    if numeric_value.is_integer():

                        formatted_value = (
                            f"{int(numeric_value):,}"
                        )

                    else:

                        formatted_value = (
                            f"{numeric_value:,.2f}"
                        )

                    answer = (
                        f"The {column_name.replace('_', ' ')} "
                        f"is {formatted_value}."
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    answer = (
                        f"The {column_name.replace('_', ' ')} "
                        f"is {value}."
                    )

            else:

                answer = (
                    "The database returned no value."
                )

        else:

            answer = (
                "The database query completed "
                "successfully, but I could not "
                "generate a natural-language answer."
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

        # --------------------------------------------------------
        # BUILD CACHE IF NEEDED
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
                    ),
                }
            )

        files.sort(
            key=lambda f: f["name"].lower()
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

            "files": files,
        }

    except Exception as e:

        print(
            f"/documents error: {e}"
        )

        return {
            "ready": False,

            "document_count": 0,

            "file_count": 0,

            "scan_paths": [],

            "files": [],

            "error": str(e),
        }