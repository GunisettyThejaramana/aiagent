
import time

from app.custom_ai.intent_engine import intent_engine
from app.custom_ai.entity_engine import entity_engine
from app.custom_ai.metric_engine import metric_engine
from app.custom_ai.schema_engine import schema_engine
from app.custom_ai.reasoning_engine import reasoning_engine
from app.custom_ai.relationship_engine import relationship_engine
from app.custom_ai.query_planner import query_planner
from app.custom_ai.query_builder import query_builder
from app.custom_ai.sql_executor import sql_executor
from app.custom_ai.response_engine import response_engine

from app.custom_ai.business_language_engine import business_language_engine
from app.custom_ai.business_schema_mapper import business_schema_mapper
from app.custom_ai.business_context_engine import business_context_engine

from app.custom_ai.database_knowledge_cache import (
    database_knowledge_cache,
)


class CustomAIEngine:
    """
    Main orchestration engine for the custom enterprise AI.

    Database schema and relationship information are cached
    per database so they are not rediscovered for every question.

    Pipeline:

    Question
        ↓
    Business Language Understanding
        ↓
    Business Context
        ↓
    Intent
        ↓
    Entity
        ↓
    Metric
        ↓
    Cached Database Knowledge
        ↓
    Business Schema Mapping
        ↓
    Reasoning
        ↓
    Query Planning
        ↓
    Query Building
        ↓
    SQL Execution
        ↓
    Response Generation
    """

    def process(
        self,
        question,
        engine,
        database_id=None,
    ):
        start_time = time.perf_counter()

        def timer(stage):
            elapsed = time.perf_counter() - start_time
            print(f"⏱️ {stage}: {elapsed:.3f}s")

        # ---------------------------------------------------------
        # 1. BUSINESS LANGUAGE UNDERSTANDING
        # ---------------------------------------------------------

        business_language_result = (
            business_language_engine.understand(
                question
            )
        )

        timer("Business Language")

        # ---------------------------------------------------------
        # 2. BUSINESS CONTEXT
        # ---------------------------------------------------------

        business_context_result = (
            business_context_engine.understand(
                question,
                business_language_result,
            )
        )

        timer("Business Context")

        # ---------------------------------------------------------
        # 3. INTENT
        # ---------------------------------------------------------

        intent_result = (
            intent_engine.understand(
                question
            )
        )

        timer("Intent")

        # ---------------------------------------------------------
        # 4. ENTITY
        # ---------------------------------------------------------

        entity_result = (
            entity_engine.extract(
                question
            )
        )

        timer("Entity")

        # ---------------------------------------------------------
        # 5. METRIC
        # ---------------------------------------------------------

        metric_result = (
            metric_engine.understand(
                question
            )
        )

        timer("Metric")

        # ---------------------------------------------------------
        # 6. DATABASE KNOWLEDGE CACHE
        # ---------------------------------------------------------

        cache_key = (
            database_id
            if database_id is not None
            else f"engine:{id(engine)}"
        )

        database_knowledge = (
            database_knowledge_cache.get_or_build(
                cache_key,
                engine,
            )
        )

        timer("Database Knowledge Cache")

        # ---------------------------------------------------------
        # BUILD SCHEMA FROM CACHE
        # ---------------------------------------------------------

        schema = {
            "tables": [
                {
                    "table_name": table_name,
                    "columns": table_info.get(
                        "columns",
                        [],
                    ),
                }
                for table_name, table_info
                in database_knowledge.get(
                    "tables",
                    {},
                ).items()
            ],
            "table_names": database_knowledge.get(
                "table_names",
                [],
            ),
        }

        # Cached relationships
        relationships = (
            database_knowledge.get(
                "relationships",
                [],
            )
        )

        # ---------------------------------------------------------
        # 7. BUSINESS SCHEMA MAPPING
        # ---------------------------------------------------------

        try:
            business_schema_result = (
                business_schema_mapper.map(
                    question,
                    schema,
                    business_context_result,
                )
            )

        except (AttributeError, TypeError):

            try:
                business_schema_result = (
                    business_schema_mapper.map(
                        question,
                        schema,
                    )
                )

            except Exception:
                business_schema_result = {}

        timer("Business Schema Mapping")

        # ---------------------------------------------------------
        # 8. REASONING
        # ---------------------------------------------------------

        reasoning_result = (
            reasoning_engine.reason(
                question,
                intent_result,
                entity_result,
                schema,
                metric_result=metric_result,
                business_context_result=business_context_result,
            )
        )

        timer("Reasoning")

        # ---------------------------------------------------------
        # 9. QUERY PLANNING
        # ---------------------------------------------------------

        query_plan = (
            query_planner.plan(
                question,
                intent_result,
                entity_result,
                metric_result,
                reasoning_result,
                relationships,
                schema,
            )
        )

        timer("Query Planning")

        # ---------------------------------------------------------
        # 10. QUERY BUILDING
        # ---------------------------------------------------------

        query_result = (
            query_builder.build(
                question,
                intent_result,
                entity_result,
                reasoning_result,
                schema,
                metric_result=metric_result,
                query_plan=query_plan,
            )
        )

        timer("Query Building")

        # ---------------------------------------------------------
        # 11. SQL EXECUTION
        # ---------------------------------------------------------

        execution_result = (
            sql_executor.execute(
                engine,
                query_result,
            )
        )

        timer("SQL Execution")

        # ---------------------------------------------------------
        # 12. RESPONSE GENERATION
        # ---------------------------------------------------------

        response_result = (
            response_engine.generate(
                question,
                intent_result,
                entity_result,
                metric_result,
                query_result,
                execution_result,
            )
        )

        timer("Response Generation")

        # ---------------------------------------------------------
        # TOTAL TIME
        # ---------------------------------------------------------

        total_elapsed = time.perf_counter() - start_time

        print(
            f"⏱️ TOTAL Custom AI Time: "
            f"{total_elapsed:.3f}s"
        )

        # ---------------------------------------------------------
        # FINAL RESULT
        # ---------------------------------------------------------

        return {
            "question": question,

            "intent": intent_result,

            "entities": entity_result,

            # Keep both names for compatibility
            "metric": metric_result,
            "metrics": metric_result,

            "business_language": (
                business_language_result
            ),

            "business_context": (
                business_context_result
            ),

            "business_schema": (
                business_schema_result
            ),

            "reasoning": reasoning_result,

            "relationships": relationships,

            # Keep both names for compatibility
            "query_plan": query_plan,
            "plan": query_plan,

            "query": query_result,

            "sql": (
                query_result.get("sql")
                if query_result
                else None
            ),

            "execution": execution_result,

            "answer": (
                response_result.get(
                    "answer",
                    "",
                )
                if isinstance(
                    response_result,
                    dict,
                )
                else str(response_result)
            ),

            "response": response_result,

            "database_knowledge_cached": True,

            "processing_time": round(
                total_elapsed,
                3,
            ),
        }

    # -------------------------------------------------------------
    # BUILD SCHEMA FROM CACHE
    # -------------------------------------------------------------

    @staticmethod
    def _build_schema_from_knowledge(
        database_knowledge,
    ):
        tables = database_knowledge.get(
            "tables",
            {},
        )

        schema = []

        for table_name, table_info in tables.items():

            schema.append(
                {
                    "table_name": table_name,
                    "columns": table_info.get(
                        "columns",
                        [],
                    ),
                }
            )

        return schema

    # -------------------------------------------------------------
    # COMPATIBILITY METHOD
    # -------------------------------------------------------------

    def answer(
        self,
        question,
        engine,
        database_id=None,
    ):
        """
        Compatibility wrapper.

        Existing code/tests can continue calling:

            custom_ai_engine.answer(...)

        while internally using the full pipeline.
        """

        return self.process(
            question,
            engine,
            database_id=database_id,
        )


custom_ai_engine = CustomAIEngine()