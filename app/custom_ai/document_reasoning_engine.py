import re
from collections import defaultdict


class DocumentReasoningEngine:
    """
    Generic deterministic document reasoning engine.

    No external AI model.
    No embeddings.
    No document-specific rules.

    The engine works with document objects returned by the existing
    FileDetector / document loaders.

    Main pipeline:

        Question
            ↓
        Query analysis
            ↓
        Document grouping
            ↓
        Relevant passage detection
            ↓
        Local context reconstruction
            ↓
        Evidence ranking
            ↓
        Duplicate removal
            ↓
        Answer
    """

    # ============================================================
    # STOP WORDS
    # ============================================================

    STOP_WORDS = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "being",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "for",
        "from",
        "had",
        "has",
        "have",
        "how",
        "i",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "me",
        "of",
        "on",
        "or",
        "our",
        "please",
        "should",
        "that",
        "the",
        "their",
        "them",
        "this",
        "those",
        "these",
        "to",
        "was",
        "were",
        "we",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "would",
        "you",
        "your",
    }

    # ============================================================
    # QUESTION WORDS THAT SHOULD NOT DRIVE SEARCH
    # ============================================================

    WEAK_QUERY_WORDS = {
        "about",
        "mentioned",
        "mention",
        "information",
        "available",
        "content",
        "details",
        "detail",
        "related",
        "regarding",
        "say",
        "says",
        "said",
        "saying",
        "tell",
        "tells",
        "according",
        "discuss",
        "discussed",
        "discusses",
        "describe",
        "described",
        "description",
    }

    # ============================================================
    # GENERIC TERMS
    # ============================================================

    GENERIC_WORDS = {
        "document",
        "documents",
        "file",
        "files",
        "content",
        "information",
        "available",
        "mentioned",
        "mention",
        "say",
        "says",
        "said",
        "policy",
        "policies",
        "rule",
        "rules",
        "company",
        "companies",
        "employee",
        "employees",
        "data",
        "details",
        "detail",
    }

    # ============================================================
    # CONSTRUCTOR
    # ============================================================

    def __init__(self):
        pass

    # ============================================================
    # NORMALIZATION
    # ============================================================

    def normalize(self, text: str) -> str:

        if not text:
            return ""

        text = str(text).lower()

        text = text.replace("_", " ")
        text = text.replace("-", " ")

        text = re.sub(
            r"[^\w\s.%₹$€£/:]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ============================================================
    # TOKENIZATION
    # ============================================================

    def tokenize(self, text: str) -> list[str]:

        normalized = self.normalize(text)

        if not normalized:
            return []

        tokens = normalized.split()

        result = []

        for token in tokens:

            if len(token) <= 1:
                continue

            if token in self.STOP_WORDS:
                continue

            result.append(token)

        return result

    # ============================================================
    # QUESTION ANALYSIS
    # ============================================================

    def extract_question_terms(
        self,
        question: str,
    ) -> list[str]:

        tokens = self.tokenize(question)

        result = []
        seen = set()

        for token in tokens:

            if token in self.WEAK_QUERY_WORDS:
                continue

            if token in seen:
                continue

            seen.add(token)

            result.append(token)

        return result

    def extract_phrases(
        self,
        question: str,
    ) -> list[str]:

        terms = self.extract_question_terms(
            question
        )

        phrases = []

        for index in range(
            len(terms) - 1
        ):

            first = terms[index]
            second = terms[index + 1]

            phrase = (
                f"{first} {second}"
            )

            phrases.append(
                phrase
            )

        return phrases

    # ============================================================
    # WORD VARIANTS
    # ============================================================

    def word_variants(
        self,
        word: str,
    ) -> set[str]:

        word = self.normalize(word)

        if not word:
            return set()

        variants = {
            word
        }

        irregular = {
            "employee": {"employees"},
            "employees": {"employee"},
            "salary": {"salaries"},
            "salaries": {"salary"},
            "company": {"companies"},
            "companies": {"company"},
            "policy": {"policies"},
            "policies": {"policy"},
            "rule": {"rules"},
            "rules": {"rule"},
            "document": {"documents"},
            "documents": {"document"},
            "file": {"files"},
            "files": {"file"},
            "customer": {"customers"},
            "customers": {"customer"},
            "product": {"products"},
            "products": {"product"},
            "payment": {"payments"},
            "payments": {"payment"},
            "material": {"materials"},
            "materials": {"material"},
            "operation": {"operations"},
            "operations": {"operation"},
        }

        if word in irregular:

            variants.update(
                irregular[word]
            )

        # Basic plural handling.
        if word.endswith("y") and len(word) > 3:

            variants.add(
                word[:-1] + "ies"
            )

        if word.endswith("s") and len(word) > 3:

            variants.add(
                word[:-1]
            )

        return variants

    # ============================================================
    # DOCUMENT CONTENT
    # ============================================================

    def get_document_text(
        self,
        document,
    ) -> str:

        if document is None:
            return ""

        if hasattr(
            document,
            "page_content",
        ):

            return str(
                document.page_content or ""
            )

        if isinstance(
            document,
            dict,
        ):

            for key in (
                "page_content",
                "content",
                "text",
                "body",
            ):

                value = document.get(
                    key
                )

                if value is not None:
                    return str(value)

        return str(document)

    # ============================================================
    # DOCUMENT METADATA
    # ============================================================

    def get_document_metadata(
        self,
        document,
    ) -> dict:

        if document is None:
            return {}

        if hasattr(
            document,
            "metadata",
        ):

            metadata = document.metadata

            if isinstance(
                metadata,
                dict,
            ):

                return metadata

        if isinstance(
            document,
            dict,
        ):

            metadata = document.get(
                "metadata"
            )

            if isinstance(
                metadata,
                dict,
            ):

                return metadata

        return {}

    # ============================================================
    # SOURCE IDENTIFICATION
    # ============================================================

    def get_source(
        self,
        document,
    ) -> str:

        metadata = (
            self.get_document_metadata(
                document
            )
        )

        for key in (
            "source",
            "file_path",
            "filename",
            "path",
            "document_id",
            "file_id",
        ):

            value = metadata.get(
                key
            )

            if value:
                return str(value)

        return ""

    def get_source_name(
        self,
        document,
    ) -> str:

        source = self.get_source(
            document
        )

        if not source:
            return ""

        source = source.replace(
            "\\",
            "/",
        )

        return source.split("/")[-1]

    # ============================================================
    # PAGE INFORMATION
    # ============================================================

    def get_page_number(
        self,
        document,
    ):

        metadata = (
            self.get_document_metadata(
                document
            )
        )

        for key in (
            "page",
            "page_number",
            "page_index",
        ):

            value = metadata.get(
                key
            )

            if value is not None:

                try:
                    return int(value)
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        return None

    # ============================================================
    # CHUNK POSITION
    # ============================================================

    def get_chunk_position(
        self,
        document,
    ):

        metadata = (
            self.get_document_metadata(
                document
            )
        )

        for key in (
            "chunk",
            "chunk_index",
            "sequence",
            "position",
            "index",
        ):

            value = metadata.get(
                key
            )

            if value is not None:

                try:
                    return int(value)
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        return None

    # ============================================================
    # DOCUMENT GROUP KEY
    # ============================================================

    def document_group_key(
        self,
        document,
    ) -> str:

        source = self.get_source(
            document
        )

        if source:
            return source

        return "__unknown_document__"

    # ============================================================
    # GROUP DOCUMENTS
    # ============================================================

    def group_documents(
        self,
        documents: list,
    ) -> dict:

        groups = defaultdict(list)

        for document in documents:

            key = self.document_group_key(
                document
            )

            groups[key].append(
                document
            )

        return dict(groups)

    # ============================================================
    # TERM OCCURRENCES
    # ============================================================

    def term_occurrences(
        self,
        term: str,
        text: str,
    ) -> int:

        variants = self.word_variants(
            term
        )

        total = 0

        for variant in variants:

            pattern = (
                r"\b"
                + re.escape(variant)
                + r"\b"
            )

            total += len(
                re.findall(
                    pattern,
                    text,
                )
            )

        return total

    # ============================================================
    # TEXT SCORING
    # ============================================================

    def score_text(
        self,
        question_terms: list[str],
        question_phrases: list[str],
        text: str,
    ) -> float:

        normalized_text = self.normalize(
            text
        )

        if not normalized_text:
            return 0.0

        score = 0.0

        meaningful_matches = set()

        # --------------------------------------------------------
        # Phrase matches
        # --------------------------------------------------------

        for phrase in question_phrases:

            phrase = self.normalize(
                phrase
            )

            if phrase not in normalized_text:
                continue

            words = phrase.split()

            meaningful = [
                word
                for word in words
                if word not in self.GENERIC_WORDS
            ]

            if len(meaningful) >= 2:

                score += 15

            elif len(meaningful) == 1:

                score += 5

        # --------------------------------------------------------
        # Individual terms
        # --------------------------------------------------------

        for term in question_terms:

            occurrences = (
                self.term_occurrences(
                    term,
                    normalized_text,
                )
            )

            if occurrences <= 0:
                continue

            if term in self.GENERIC_WORDS:

                score += 0.5

                continue

            meaningful_matches.add(
                term
            )

            score += 5

            score += min(
                max(
                    occurrences - 1,
                    0,
                ),
                3,
            )

        # --------------------------------------------------------
        # Multiple meaningful terms
        # --------------------------------------------------------

        if len(meaningful_matches) >= 3:

            score += 12

        elif len(meaningful_matches) == 2:

            score += 8

        elif len(meaningful_matches) == 1:

            score += 1

        return score

    # ============================================================
    # DOCUMENT SCORING
    # ============================================================

    def score_document(
        self,
        question_terms: list[str],
        question_phrases: list[str],
        document,
    ) -> float:

        text = self.get_document_text(
            document
        )

        if not text:
            return 0.0

        content_score = (
            self.score_text(
                question_terms,
                question_phrases,
                text,
            )
        )

        source = self.get_source(
            document
        )

        source_score = 0.0

        if source:

            source_score = (
                self.score_text(
                    question_terms,
                    question_phrases,
                    source,
                )
            )

            source_score *= 1.5

        return (
            content_score
            + source_score
        )

    # ============================================================
    # TEXT BLOCK SPLITTING
    # ============================================================

    def split_blocks(
        self,
        text: str,
    ) -> list[str]:

        if not text:
            return []

        text = str(text)

        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        raw_blocks = re.split(
            r"\n\s*\n+",
            text,
        )

        blocks = []

        for block in raw_blocks:

            block = block.strip()

            if not block:
                continue

            block = re.sub(
                r"\s+",
                " ",
                block,
            )

            if len(block) >= 3:
                blocks.append(
                    block
                )

        return blocks

    # ============================================================
    # SENTENCE SPLITTING
    # ============================================================

    def split_sentences(
        self,
        text: str,
    ) -> list[str]:

        if not text:
            return []

        text = str(text)

        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        # Preserve line boundaries because many formats
        # such as TXT, Markdown, HTML and extracted PDFs
        # use lines to represent meaningful sections.
        pieces = re.split(
            r"(?<=[.!?])\s+|\n+",
            text,
        )

        sentences = []

        for piece in pieces:

            piece = piece.strip()

            piece = re.sub(
                r"^[•●▪◦\-*]+\s*",
                "",
                piece,
            )

            if len(piece) < 3:
                continue

            sentences.append(
                piece
            )

        return sentences

    # ============================================================
    # RECONSTRUCT LOADED CHUNKS
    # ============================================================

    def reconstruct_chunks(
        self,
        documents: list,
    ) -> str:

        if not documents:
            return ""

        indexed = []

        for original_index, document in enumerate(
            documents
        ):

            page = self.get_page_number(
                document
            )

            position = self.get_chunk_position(
                document
            )

            indexed.append(
                (
                    page
                    if page is not None
                    else 10**9,
                    position
                    if position is not None
                    else original_index,
                    original_index,
                    document,
                )
            )

        indexed.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[2],
            )
        )

        pieces = []

        for (
            _page,
            _position,
            _original_index,
            document,
        ) in indexed:

            text = self.get_document_text(
                document
            ).strip()

            if not text:
                continue

            pieces.append(
                text
            )

        if not pieces:
            return ""

        # --------------------------------------------------------
        # Important:
        #
        # We join chunks with spaces, but we DO NOT treat the
        # entire document as one answer.
        #
        # Later stages locate the relevant passage.
        # --------------------------------------------------------

        reconstructed = " ".join(
            pieces
        )

        reconstructed = re.sub(
            r"\s+",
            " ",
            reconstructed,
        )

        return reconstructed.strip()

    # ============================================================
    # RELEVANT SENTENCE INDEXES
    # ============================================================

    def find_relevant_indexes(
        self,
        sentences: list[str],
        question_terms: list[str],
    ) -> list[int]:

        indexes = []

        meaningful_terms = [
            term
            for term in question_terms
            if term not in self.GENERIC_WORDS
        ]

        for index, sentence in enumerate(
            sentences
        ):

            normalized = self.normalize(
                sentence
            )

            matched = False

            for term in meaningful_terms:

                if self.term_occurrences(
                    term,
                    normalized,
                ) > 0:

                    matched = True
                    break

            if matched:

                indexes.append(
                    index
                )

        return indexes

    # ============================================================
    # BUILD LOCAL PASSAGES
    # ============================================================

    def build_local_passages(
        self,
        text: str,
        question_terms: list[str],
        window: int = 1,
    ) -> list[str]:

        sentences = self.split_sentences(
            text
        )

        if not sentences:
            return []

        indexes = self.find_relevant_indexes(
            sentences,
            question_terms,
        )

        if not indexes:
            return []

        passages = []

        used_ranges = []

        for index in indexes:

            start = max(
                0,
                index - window,
            )

            end = min(
                len(sentences),
                index + window + 1,
            )

            merged = False

            for (
                existing_start,
                existing_end,
            ) in used_ranges:

                if (
                    start <= existing_end
                    and end >= existing_start
                ):

                    new_start = min(
                        start,
                        existing_start,
                    )

                    new_end = max(
                        end,
                        existing_end,
                    )

                    used_ranges.remove(
                        (
                            existing_start,
                            existing_end,
                        )
                    )

                    used_ranges.append(
                        (
                            new_start,
                            new_end,
                        )
                    )

                    merged = True
                    break

            if not merged:

                used_ranges.append(
                    (
                        start,
                        end,
                    )
                )

        used_ranges.sort()

        for start, end in used_ranges:

            passage = " ".join(
                sentences[start:end]
            )

            passage = passage.strip()

            if passage:
                passages.append(
                    passage
                )

        return passages

    # ============================================================
    # PASSAGE SCORING
    # ============================================================

    def score_passage(
        self,
        question_terms: list[str],
        question_phrases: list[str],
        passage: str,
    ) -> float:

        if not passage:
            return 0.0

        score = self.score_text(
            question_terms,
            question_phrases,
            passage,
        )

        sentences = self.split_sentences(
            passage
        )

        # Prefer passages containing multiple sentences,
        # but only slightly. Relevance remains more important.
        if len(sentences) >= 2:

            score += 1

        return score

    # ============================================================
    # EVIDENCE EXTRACTION
    # ============================================================

    def extract_evidence(
        self,
        question: str,
        documents: list,
        max_evidence: int = 5,
    ) -> list[dict]:

        question_terms = (
            self.extract_question_terms(
                question
            )
        )

        question_phrases = (
            self.extract_phrases(
                question
            )
        )

        grouped = self.group_documents(
            documents
        )

        candidates = []

        for source, source_documents in grouped.items():

            reconstructed = (
                self.reconstruct_chunks(
                    source_documents
                )
            )

            if not reconstructed:
                continue

            # ----------------------------------------------------
            # Start with a small local context.
            # ----------------------------------------------------

            passages = self.build_local_passages(
                reconstructed,
                question_terms,
                window=1,
            )

            # ----------------------------------------------------
            # If the passage is too weak, use a slightly wider
            # context. This is adaptive rather than fixed.
            # ----------------------------------------------------

            if not passages:

                passages = self.build_local_passages(
                    reconstructed,
                    question_terms,
                    window=2,
                )

            for passage in passages:

                score = self.score_passage(
                    question_terms,
                    question_phrases,
                    passage,
                )

                if score <= 0:
                    continue

                candidates.append(
                    {
                        "score": score,
                        "text": passage,
                        "source": source,
                        "document_count": len(
                            source_documents
                        ),
                    }
                )

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        # ========================================================
        # EVIDENCE THRESHOLD
        # ========================================================

        meaningful_terms = [
            term
            for term in question_terms
            if term not in self.GENERIC_WORDS
        ]

        if meaningful_terms:

            minimum_score = 5

        else:

            minimum_score = 8

        candidates = [
            item
            for item in candidates
            if item["score"] >= minimum_score
        ]

        if not candidates:
            return []

        # ========================================================
        # SOURCE SELECTION
        # ========================================================

        source_scores = defaultdict(
            float
        )

        for item in candidates:

            source_scores[
                item["source"]
            ] += item["score"]

        strongest_source = max(
            source_scores,
            key=source_scores.get,
        )

        source_candidates = [
            item
            for item in candidates
            if item["source"]
            == strongest_source
        ]

        # ========================================================
        # REMOVE DUPLICATE / OVERLAPPING PASSAGES
        # ========================================================

        result = []

        for candidate in source_candidates:

            candidate_text = self.normalize(
                candidate["text"]
            )

            if not candidate_text:
                continue

            duplicate = False

            for existing in result:

                existing_text = self.normalize(
                    existing["text"]
                )

                if (
                    candidate_text
                    == existing_text
                ):

                    duplicate = True
                    break

                if (
                    candidate_text
                    in existing_text
                ):

                    duplicate = True
                    break

                if (
                    existing_text
                    in candidate_text
                ):

                    duplicate = True
                    break

            if duplicate:
                continue

            result.append(
                candidate
            )

            if len(result) >= max_evidence:
                break

        return result

    # ============================================================
    # EVIDENCE VALIDATION
    # ============================================================

    def has_strong_evidence(
        self,
        evidence: list[dict],
        question: str,
    ) -> bool:

        if not evidence:
            return False

        terms = (
            self.extract_question_terms(
                question
            )
        )

        meaningful_terms = [
            term
            for term in terms
            if term not in self.GENERIC_WORDS
        ]

        if not meaningful_terms:

            return (
                evidence[0]["score"]
                >= 8
            )

        if evidence[0]["score"] < 5:
            return False

        # For multiple meaningful terms, make sure at least
        # one passage connects multiple terms.
        if len(meaningful_terms) >= 2:

            for item in evidence:

                normalized = self.normalize(
                    item["text"]
                )

                matches = 0

                for term in meaningful_terms:

                    if self.term_occurrences(
                        term,
                        normalized,
                    ) > 0:

                        matches += 1

                if matches >= 2:
                    return True

            return False

        return True

    # ============================================================
    # CLEAN PASSAGE
    # ============================================================

    def clean_passage(
        self,
        text: str,
    ) -> str:

        if not text:
            return ""

        text = str(text).strip()

        # Remove excessive whitespace.
        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        # Remove repeated punctuation.
        text = re.sub(
            r"\.{2,}",
            ".",
            text,
        )

        text = re.sub(
            r",\s*,+",
            ",",
            text,
        )

        # Clean spaces before punctuation.
        text = re.sub(
            r"\s+([,.;:!?])",
            r"\1",
            text,
        )

        return text.strip()

    # ============================================================
    # ANSWER CONSTRUCTION
    # ============================================================

    def build_answer(
        self,
        question: str,
        evidence: list[dict],
    ) -> str:

        if not evidence:

            return (
                "I could not find relevant information "
                "in the available documents."
            )

        if not self.has_strong_evidence(
            evidence,
            question,
        ):

            return (
                "I could not find enough relevant information "
                "in the available documents."
            )

        parts = []

        for item in evidence:

            text = self.clean_passage(
                item["text"]
            )

            if not text:
                continue

            parts.append(
                text
            )

        if not parts:

            return (
                "I could not find relevant information "
                "in the available documents."
            )

        # --------------------------------------------------------
        # Remove duplicate passages.
        # --------------------------------------------------------

        final_parts = []

        for part in parts:

            normalized_part = self.normalize(
                part
            )

            duplicate = False

            for existing in final_parts:

                normalized_existing = (
                    self.normalize(
                        existing
                    )
                )

                if (
                    normalized_part
                    == normalized_existing
                ):

                    duplicate = True
                    break

                if (
                    normalized_part
                    in normalized_existing
                ):

                    duplicate = True
                    break

                if (
                    normalized_existing
                    in normalized_part
                ):

                    duplicate = True
                    break

            if duplicate:
                continue

            final_parts.append(
                part
            )

        # Keep the response controlled.
        final_parts = final_parts[:3]

        return " ".join(
            final_parts
        )

    # ============================================================
    # MAIN PROCESS
    # ============================================================

    def process(
        self,
        question: str,
        documents: list,
        max_evidence: int = 5,
    ) -> dict:

        # --------------------------------------------------------
        # Empty question
        # --------------------------------------------------------

        if not question or not str(
            question
        ).strip():

            return {
                "success": False,
                "question": question,
                "answer": "Please enter a question.",
                "evidence": [],
                "document_count": 0,
                "matched_document_count": 0,
                "matched": False,
                "question_terms": [],
                "question_phrases": [],
            }

        # --------------------------------------------------------
        # No documents
        # --------------------------------------------------------

        if not documents:

            return {
                "success": True,
                "question": question,
                "answer": (
                    "I could not find relevant information "
                    "in the available documents."
                ),
                "evidence": [],
                "document_count": 0,
                "matched_document_count": 0,
                "matched": False,
                "question_terms": (
                    self.extract_question_terms(
                        question
                    )
                ),
                "question_phrases": (
                    self.extract_phrases(
                        question
                    )
                ),
            }

        # --------------------------------------------------------
        # Analyze question
        # --------------------------------------------------------

        question_terms = (
            self.extract_question_terms(
                question
            )
        )

        question_phrases = (
            self.extract_phrases(
                question
            )
        )

        # --------------------------------------------------------
        # Score source documents
        # --------------------------------------------------------

        scored_documents = []

        for document in documents:

            score = self.score_document(
                question_terms,
                question_phrases,
                document,
            )

            if score > 0:

                scored_documents.append(
                    (
                        score,
                        document,
                    )
                )

        scored_documents.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        # --------------------------------------------------------
        # Determine threshold
        # --------------------------------------------------------

        meaningful_terms = [
            term
            for term in question_terms
            if term not in self.GENERIC_WORDS
        ]

        if meaningful_terms:

            minimum_score = 5

        else:

            minimum_score = 8

        relevant_documents = [
            document
            for score, document
            in scored_documents
            if score >= minimum_score
        ]

        # --------------------------------------------------------
        # Extract actual evidence
        # --------------------------------------------------------

        evidence = self.extract_evidence(
            question,
            relevant_documents,
            max_evidence=max_evidence,
        )

        answer = self.build_answer(
            question,
            evidence,
        )

        return {
            "success": True,
            "question": question,
            "answer": answer,
            "evidence": evidence,
            "document_count": len(
                documents
            ),
            "matched_document_count": len(
                relevant_documents
            ),
            "matched": bool(
                evidence
            ),
            "question_terms": question_terms,
            "question_phrases": question_phrases,
        }


# ================================================================
# GLOBAL ENGINE INSTANCE
# ================================================================

document_reasoning_engine = (
    DocumentReasoningEngine()
)